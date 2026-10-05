import { checkEnvelope, comparable, dateKey, shiftDay, threatLevel } from './data.js';

export const HISTORY_DAYS = 14;
const validScore = value => Number.isFinite(value) && value >= 0 && value <= 100;
const idPattern = /^rpt_[a-f0-9]{64}$/;

export function historyRow(value) {
  const r = value.report;
  return { ...r.provenance, report_id: r.report_id, report_type: r.report_type,
    as_of: r.as_of, published_at: value.published_at, score: r.rtb.score,
    supersedes: r.supersedes, confidence_key: r.rtb.confidence.comparison_key };
}

// Fourteen calendar days in Warsaw, not fourteen publications. An intraday
// rerun or correction does not gain an extra place on the time axis.
export function historyDays(rows, asOf, reports = new Map(), area = 'macro') {
  const end = dateKey(asOf), start = shiftDay(end, 1 - HISTORY_DAYS), byDay = new Map();
  const ordered = [...rows].filter(r => r.report_type === 'daily' && Number.isFinite(Date.parse(r.as_of)))
    .sort((a, b) => Date.parse(b.as_of) - Date.parse(a.as_of) || Date.parse(b.published_at) - Date.parse(a.published_at) || b.report_id.localeCompare(a.report_id));
  for (const row of ordered) {
    const day = dateKey(row.as_of);
    if (day >= start && day <= end && Date.parse(row.as_of) <= Date.parse(asOf) && !byDay.has(day)) byDay.set(day, row);
  }
  return Array.from({ length: HISTORY_DAYS }, (_, index) => {
    const day = shiftDay(start, index), row = byDay.get(day) ?? null;
    const report = row ? reports.get(row.report_id)?.report : null;
    const score = area === 'macro' ? row?.score : report?.rtb.regions?.[area]?.score;
    const metric = area === 'macro' ? report?.rtb : report?.rtb.regions?.[area];
    // Warnings and red eligibility belong to this frozen edition. Metadata
    // alone cannot establish a tone; keep it neutral until the report loads.
    const tone = threatLevel(metric ? { ...metric, official_warnings: report.rtb.official_warnings } : null).tone;
    return { day, row, score: validScore(score) ? score : null, tone };
  });
}

export function canJoinDays(a, b) {
  return a?.row && b?.row && a.score !== null && b.score !== null && shiftDay(a.day, 1) === b.day &&
    comparable(a.row, b.row) && (a.row.methodology_version !== 'rtb-v0.4' || a.row.confidence_key === b.row.confidence_key);
}

export class ReportHistory {
  constructor(api) { this.api = api; this.cache = new Map(); this.pending = new Map(); this.rows = []; this.generation = 0; this.loading = false; this.failed = false; }
  remember(value) { if (value) this.cache.set(value.report.report_id, value); }
  async get(id) {
    if (!idPattern.test(id)) throw new Error('invalid_report_id');
    if (this.cache.has(id)) return this.cache.get(id);
    if (!this.pending.has(id)) {
      const request = this.api(`/api/reports/${id}`).then(raw => {
        const value = checkEnvelope(raw);
        if (!value || value.report.report_id !== id || !Number.isFinite(Date.parse(value.published_at))) throw new Error('invalid_history_report');
        this.remember(value); return value;
      }).finally(() => this.pending.delete(id));
      this.pending.set(id, request);
    }
    return this.pending.get(id);
  }
  async read(path) {
    const match = /^\/api\/reports\/(rpt_[a-f0-9]{64})$/.exec(path);
    return match ? this.get(match[1]) : this.api(path);
  }
  async load(latest, onChange = () => {}) {
    const generation = ++this.generation;
    this.remember(latest); this.loading = true; this.failed = false;
    this.rows = [historyRow(latest)]; onChange();
    const start = shiftDay(dateKey(latest.report.as_of), 1 - HISTORY_DAYS), rows = new Map();
    rows.set(latest.report.report_id, historyRow(latest));
    try {
      let offset = 0;
      for (let pageNumber = 0; ; pageNumber++) {
        if (pageNumber >= 30) throw new Error('history_limit');
        const q = new URLSearchParams({ type: 'daily', offset: String(offset), anchor: latest.published_at });
        const page = await this.api(`/api/reports?${q}`);
        if (generation !== this.generation) return;
        if (!Array.isArray(page.items) || (page.next_offset !== null && (!Number.isInteger(page.next_offset) || page.next_offset <= offset))) throw new Error('invalid_history_page');
        for (const row of page.items) {
          if (!idPattern.test(row.report_id) || !Number.isFinite(Date.parse(row.as_of)) || !Number.isFinite(Date.parse(row.published_at))) throw new Error('invalid_history_row');
          if (row.report_type === 'daily' && Date.parse(row.as_of) <= Date.parse(latest.report.as_of) && Date.parse(row.published_at) <= Date.parse(latest.published_at) && dateKey(row.as_of) >= start) rows.set(row.report_id, row);
        }
        if (page.next_offset === null || (page.items.length && dateKey(page.items.at(-1).as_of) < start)) break;
        offset = page.next_offset;
      }
      this.rows = [...rows.values()]; onChange();
      // Regional scores live in the frozen report, never inferred from the
      // country-wide score or from today's region metadata.
      const days = historyDays(this.rows, latest.report.as_of);
      for (const day of days.filter(d => d.row)) {
        await this.get(day.row.report_id);
        if (generation !== this.generation) return;
        onChange();
      }
    } catch { if (generation === this.generation) { this.failed = true; console.info('index_history_unavailable'); } }
    finally { if (generation === this.generation) { this.loading = false; onChange(); } }
  }
}

// Apply only the most recent user choice. A failed/slow request must not mix
// one report's metric with another report's map, counters or commentary.
export class SnapshotSelection {
  constructor(read, activate, onChange = () => {}) { this.read = read; this.activate = activate; this.onChange = onChange; this.generation = 0; this.pending = null; this.failed = false; }
  async choose(id) {
    const generation = ++this.generation; this.pending = id; this.failed = false; this.onChange();
    try {
      const value = await this.read(id);
      if (generation !== this.generation) return;
      this.activate(value);
    } catch { if (generation === this.generation) { this.failed = true; console.info('report_selection_unavailable'); } }
    finally { if (generation === this.generation) { this.pending = null; this.onChange(); } }
  }
}
