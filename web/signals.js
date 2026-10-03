// One presentation model for the overview, journal and operational map.
import taxonomy from '../config/signal-presentation.json' with { type: 'json' };
import { dateKey, weekStart, checkEnvelope } from './data.js';
export const topics = taxonomy.topics;
export const regions = taxonomy.regions;
export const kinds = { event: 'Zdarzenie', warning: 'Ostrzeżenie', plan: 'Zapowiedź', measurement: 'Pomiar', context: 'Informacja' };
export const WEEK = 168 * 3600000;
const fold = value => (value ?? '').toLocaleLowerCase('pl').replace(/^województwo\s+/, '').trim();
const countryNames = { PL: 'Ogólnopolskie', UA: 'Ukraina', BY: 'Białoruś', RU: 'Rosja', LT: 'Litwa', LV: 'Łotwa', EE: 'Estonia', DE: 'Niemcy' };

export function presentation(event) {
  if (event.presentation?.version === taxonomy.version) return event.presentation;
  // Legacy reports stay immutable. These are topic labels, never assessments.
  const sources = new Set(event.sources.map(s => s.source_id));
  const topicSet = new Set([...sources].map(s => taxonomy.source_topics[s]).filter(Boolean));
  if (taxonomy.category_topics[event.category]) topicSet.add(taxonomy.category_topics[event.category]);
  const region = event.country === 'PL' && event.location.precision === 'region'
    ? Object.entries(regions).find(([, name]) => fold(event.location.label) === name)?.[0] : null;
  const national = event.location.precision === 'country' && !sources.has('rso_public');
  const sourceKinds = [...new Set([...sources].map(s => taxonomy.source_kinds[s]).filter(Boolean))];
  return { version: 'legacy', topics: [...topicSet].sort().length ? [...topicSet].sort() : ['other'],
    kind: sourceKinds.length === 1 ? sourceKinds[0] : event.category === 'context' ? 'context' : 'event',
    scope: region ? 'regional' : national ? 'national' : event.country && event.country !== 'PL' ? 'foreign' : 'unknown',
    region_ids: region ? [region] : [], episode_id: event.id };
}
export function regionLabel(event) {
  const p = presentation(event);
  if (p.region_ids.length) return p.region_ids.map(id => regions[id]).join(', ');
  if (p.scope === 'national') return countryNames[event.country] ?? event.location.label ?? 'Zasięg krajowy';
  if (event.country && event.country !== 'PL') return event.location.label ?? countryNames[event.country] ?? event.country;
  return event.location.precision !== 'country' && event.location.label ? event.location.label : 'Obszar nieustalony';
}
export function matchesArea(event, area, includeNational = true) {
  if (area === 'macro') return true;
  if (area === 'PL') return event.country === 'PL';
  const p = presentation(event);
  return p.region_ids.includes(area) || (includeNational && event.country === 'PL' && p.scope === 'national');
}
export function matchesTopic(event, topic) { return topic === 'all' || presentation(event).topics.includes(topic); }
export function periodRange(asOf, period) {
  const end = Date.parse(asOf), today = dateKey(asOf);
  if (period === 'current7') return { start: end - WEEK, end, rolling: true };
  if (period === 'previous7') return { start: end - 2 * WEEK, end: end - WEEK, rolling: true };
  if (period === 'undated') return { undated: true, end };
  if (period === 'all') return { start: null, end, dateStart: null };
  const month = Number(today.slice(5, 7));
  const dateStart = period === 'day' ? today : period === 'week' ? weekStart(today) : period === 'month' ? today.slice(0, 7) + '-01' : period === 'quarter' ? `${today.slice(0, 4)}-${String(Math.floor((month - 1) / 3) * 3 + 1).padStart(2, '0')}-01` : today.slice(0, 4) + '-01-01';
  // Fetch conservatively one day earlier; filtering uses Warsaw calendar dates,
  // so both sides of a daylight-saving transition belong to the right day.
  return { dateStart, start: Date.parse(dateStart + 'T00:00:00Z') - 86400000, end };
}
export function inPeriod(event, asOf, period) {
  const range = periodRange(asOf, period), t = Date.parse(event.published_at);
  if (range.undated) return !event.published_at;
  if (period === 'all') return !event.published_at || t <= range.end;
  if (!Number.isFinite(t) || t > range.end) return false;
  return range.rolling ? t >= range.start && t < range.end : dateKey(event.published_at) >= range.dateStart;
}
export function filterSignals(records, { asOf, area = 'macro', topic = 'all', period = 'all', source = 'all', includeNational = true }) {
  return records.filter(e => matchesArea(e, area, includeNational) && matchesTopic(e, topic) && inPeriod(e, asOf, period) && (source === 'all' || e.sources.some(s => s.source_id === source)))
    .sort((a, b) => (b.published_at ?? '').localeCompare(a.published_at ?? '') || a.id.localeCompare(b.id));
}
export function mergeSignals(reports, asOf) {
  const cutoff = Date.parse(asOf), byId = new Map();
  for (const report of [...reports].sort((a, b) => Date.parse(a.as_of) - Date.parse(b.as_of))) {
    if (Date.parse(report.as_of) > cutoff) continue;
    for (const event of report.incidents) {
      if (Date.parse(event.recorded_at) > cutoff) continue;
      const old = byId.get(event.id);
      const current = !old || event.revision >= old.revision ? event : old;
      // A reviewed correction can also correct the publication date. Do not
      // silently resurrect an erroneous timestamp from an older revision.
      byId.set(event.id, current);
    }
  }
  const episodes = new Map();
  for (const event of byId.values()) {
    const key = presentation(event).episode_id, old = episodes.get(key);
    if (!old) { episodes.set(key, event); continue; }
    const current = Date.parse(event.recorded_at) > Date.parse(old.recorded_at) ? event : old;
    const dates = [event.published_at, old.published_at].filter(Boolean).sort((a, b) => Date.parse(a) - Date.parse(b));
    episodes.set(key, { ...current, published_at: dates[0] ?? null });
  }
  return [...episodes.values()];
}
export function comparisonState(reports, asOf, { failed = false, loading = false } = {}) {
  if (loading) return 'loading';
  if (failed) return 'unavailable';
  const end = Date.parse(asOf), start = end - 2 * WEEK;
  const rows = [...new Map(reports.filter(r => Date.parse(r.as_of) <= end).map(r => [Date.parse(r.as_of), r])).values()].sort((a, b) => Date.parse(a.as_of) - Date.parse(b.as_of));
  const before = rows.filter(r => Date.parse(r.as_of) <= start).at(-1);
  if (!before) return 'unavailable';
  const covered = [before, ...rows.filter(r => Date.parse(r.as_of) > start)];
  if (end - Date.parse(covered.at(-1).as_of) > 36 * 3600000 || covered.some((r, i) => i && Date.parse(r.as_of) - Date.parse(covered[i - 1].as_of) > 36 * 3600000)) return 'unavailable';
  const latest = covered.at(-1), key = r => `${r.provenance.source_config_hash}:${r.provenance.exporter_version}`;
  if (covered.some(r => key(r) !== key(latest))) return 'unavailable';
  if (covered.some(r => r.coverage.pending_review || r.sources.some(s => s.status !== 'current' || !s.window_complete))) return 'partial';
  return 'available';
}
export function topicCounts(records, reports, asOf, area, options) {
  const status = comparisonState(reports, asOf, options);
  return ['aviation', 'cyber', 'navigation'].map(topic => {
    const current = filterSignals(records, { asOf, area, topic, period: 'current7' });
    const previous = filterSignals(records, { asOf, area, topic, period: 'previous7' });
    return { topic, current, previous, delta: status === 'available' ? current.length - previous.length : null, status };
  });
}
export function mapReport(report, records) {
  if (!report) return null;
  return { ...report, incidents: records, geojson: { type: 'FeatureCollection', features: records.filter(e => e.location.geometry?.type === 'Point').map(e => ({ type: 'Feature', id: e.id, geometry: e.location.geometry, properties: { incident_id: e.id } })) } };
}

// Existing read-only API; no extra data collection. Pagination is pinned to the
// publication we opened, and old requests cannot mutate a newer archive object.
export class SignalArchive {
  constructor(envelope, api, onChange = () => {}) {
    this.envelope = envelope; this.api = api; this.onChange = onChange;
    this.reports = new Map([[envelope.report.report_id, envelope.report]]);
    this.rows = []; this.offset = 0; this.exhausted = false; this.failed = false; this.loading = false;
    this.target = Date.parse(envelope.report.as_of); this.promise = null; this.earliestLoaded = Infinity;
  }
  get records() {
    if (this.cachedSize !== this.reports.size) { this.cachedRecords = mergeSignals([...this.reports.values()], this.envelope.report.as_of); this.cachedSize = this.reports.size; }
    return this.cachedRecords;
  }
  dispose() { this.disposed = true; }
  async loadThrough(start) {
    this.target = Math.min(this.target, start);
    if (this.promise) return this.promise;
    this.promise = this.load().finally(() => { this.promise = null; });
    return this.promise;
  }
  async load() {
    this.loading = true; this.failed = false; this.onChange();
    try {
      for (;;) {
        if (this.disposed) return;
        while (!this.exhausted && (!this.rows.length || Date.parse(this.rows.at(-1).as_of) >= this.target)) {
          const q = new URLSearchParams({ type: 'daily', offset: String(this.offset), anchor: this.envelope.published_at });
          const page = await this.api(`/api/reports?${q}`);
          if (this.disposed) return;
          if (!Array.isArray(page.items) || (page.next_offset !== null && page.next_offset <= this.offset)) throw new Error('invalid_signal_history');
          this.rows.push(...page.items.filter(r => Date.parse(r.as_of) <= Date.parse(this.envelope.report.as_of) && Date.parse(r.published_at) <= Date.parse(this.envelope.published_at)));
          this.exhausted = page.next_offset === null; this.offset = page.next_offset ?? this.offset;
          if (this.rows.length > 800) throw new Error('signal_history_limit');
        }
        // Keep the most recently published correction for each analysis cutoff.
        const latest = new Map();
        for (const row of this.rows) if (!latest.has(Date.parse(row.as_of))) latest.set(Date.parse(row.as_of), row);
        const ordered = [...latest.values()].sort((a, b) => Date.parse(b.as_of) - Date.parse(a.as_of));
        const before = ordered.find(r => Date.parse(r.as_of) < this.target);
        const needed = ordered.filter(r => Date.parse(r.as_of) >= this.target || r === before);
        const pending = needed.filter(r => !this.reports.has(r.report_id));
        if (!pending.length) { this.earliestLoaded = this.target; break; }
        for (const row of pending) {
          const value = checkEnvelope(await this.api(`/api/reports/${row.report_id}`));
          if (this.disposed) return;
          if (!value || value.report.report_id !== row.report_id || value.report.mode !== this.envelope.report.mode || Date.parse(value.report.as_of) > Date.parse(this.envelope.report.as_of)) throw new Error('invalid_signal_report');
          this.reports.set(row.report_id, value.report);
        }
      }
    } catch { this.failed = true; console.info('signal_history_unavailable'); }
    finally { this.loading = false; this.onChange(); }
  }
}
