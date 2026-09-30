export const categories = {
  sabotage: { label: 'Sabotaż', icon: 'flame' },
  arms_explosion: { label: 'Infrastruktura', icon: 'landmark' },
  military_preparation: { label: 'Logistyka wojskowa', icon: 'train-front' },
  airspace_breach: { label: 'Przestrzeń powietrzna', icon: 'plane' },
  air_activity: { label: 'Lotnictwo', icon: 'plane' },
  cyberattack: { label: 'Cyberbezpieczeństwo', icon: 'shield-alert' },
  border_pressure: { label: 'Granica', icon: 'flag' },
  gps_jamming: { label: 'Nawigacja satelitarna', icon: 'satellite' },
  context: { label: 'Sytuacja w regionie', icon: 'newspaper' },
};
export const statuses = { unverified: 'Pojedyncze doniesienie', confirmed_primary: 'Potwierdzenie źródła pierwotnego', corroborated: 'Potwierdzenie z niezależnych źródeł', disputed: 'Sprzeczne informacje', refuted: 'Informacja obalona' };
export const sourceStatuses = { current: 'Aktualne', stale: 'Wymaga odświeżenia', partial: 'Niepełne', unavailable: 'Niedostępne' };
export const scoreLabel = n => n == null ? '—' : new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 1 }).format(n);
export const visibleWarnings = rtb => (rtb?.official_warnings ?? []).filter(w => ['active', 'unknown'].includes(w.status));
export const timeZone = 'Europe/Warsaw';
const formatter = new Intl.DateTimeFormat('sv-SE', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
export const parts = value => Object.fromEntries(formatter.formatToParts(new Date(value)).map(p => [p.type, p.value]));
export const dateKey = value => { const p = parts(value); return `${p.year}-${p.month}-${p.day}`; };
export const calendarDate = key => new Date(`${key}T12:00:00Z`);
export const shiftDay = (key, n) => { const d = calendarDate(key); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
export const weekStart = key => shiftDay(key, -((calendarDate(key).getUTCDay() + 6) % 7));
export function isoWeek(key) { const d = calendarDate(key); d.setUTCDate(d.getUTCDate() + 3 - ((d.getUTCDay() + 6) % 7)); return Math.ceil((((d - new Date(Date.UTC(d.getUTCFullYear(), 0, 1, 12))) / 86400000) + 1) / 7); }
export const shortDate = key => `${key.slice(8, 10)}.${key.slice(5, 7)}`;
export const fullTime = value => value ? new Intl.DateTimeFormat('pl-PL', { timeZone, day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(value)) : 'Nieustalony';
export const signalCount = n => `${n} ${n === 1 ? 'sygnał' : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14) ? 'sygnały' : 'sygnałów'}`;

export function timelineGroups(records, asOf, scale) {
  const today = dateKey(asOf), start = scale === 'day' ? today : scale === 'week' ? weekStart(today) : today.slice(0, 8) + '01';
  const eligible = records.filter(e => e.published_at && Date.parse(e.published_at) <= Date.parse(asOf) && dateKey(e.published_at) >= start);
  const buckets = new Map();
  if (scale === 'day') {
    for (let h = 0; h <= Number(parts(asOf).hour); h++) buckets.set(`${today}T${String(h).padStart(2, '0')}`, []);
  } else if (scale === 'week') {
    for (let day = start; day <= today; day = shiftDay(day, 1)) buckets.set(day, []);
  } else {
    for (let day = weekStart(start); day <= today; day = shiftDay(day, 7)) buckets.set(day, []);
  }
  for (const event of eligible) {
    const day = dateKey(event.published_at), key = scale === 'day' ? `${day}T${parts(event.published_at).hour}` : scale === 'week' ? day : weekStart(day);
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(event);
  }
  return { start, today, eligible, groups: [...buckets].sort((a, b) => b[0].localeCompare(a[0])) };
}

export function comparable(a, b) {
  return a && b && ['methodology_version', 'config_hash', 'source_config_hash', 'code_hash'].every(k => a[k] === b[k]);
}

export function checkEnvelope(value) {
  if (value === null) return null;
  const r = value?.report;
  if (!r || r.contract_version !== 'dashboard-v1' || !/^rpt_[a-f0-9]{64}$/.test(r.report_id) ||
      !['live', 'fixture'].includes(r.mode) || !Number.isFinite(Date.parse(r.as_of)) ||
      !Array.isArray(r.incidents) || !Array.isArray(r.sources) || !r.provenance?.methodology_version ||
      !r.rtb || !['available', 'insufficient_data'].includes(r.rtb.status) ||
      (r.rtb.status === 'insufficient_data' ? r.rtb.score !== null : !Number.isFinite(r.rtb.score) || r.rtb.score < 1 || r.rtb.score > 100)) throw new Error('invalid_report');
  // Full JSON Schema and content hash validation happen on the server. The UI
  // additionally refuses conflicting numeric states instead of displaying them.
  if (new Set(r.incidents.map(i => i.id)).size !== r.incidents.length) throw new Error('duplicate_incidents');
  return value;
}

export function safeLink(url) {
  try { const u = new URL(url); return ['http:', 'https:'].includes(u.protocol) && !u.username && !u.password ? u.href : null; } catch { return null; }
}

export function reportText(report) {
  const score = report.rtb.score === null ? 'Za mało danych do wyliczenia indeksu' : `${report.rtb.score}/100`;
  return [`Red Threat Meter · ${fullTime(report.as_of)}`, `RTB: ${score}`, `Metodologia: ${report.provenance.methodology_version}`, '',
    ...report.limitations, '', ...report.gaps.map(g => g.message), '',
    ...report.incidents.flatMap(i => [i.title, i.summary, `Opublikowano: ${fullTime(i.published_at)}`, `Data zdarzenia: ${i.occurred_on ?? 'nieustalona'}`, statuses[i.status], ...i.sources.map(s => `${s.publisher}: ${s.url}`), ''])].join('\n');
}
