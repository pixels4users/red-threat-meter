import { comparable, fullTime, parts, scoreLabel, threatLevel, statuses, sourceStatuses, safeLink, signalTimeText } from './data.js';
import { topics, presentation, regionLabel } from './signals.js';
import { signalTime } from './signal-time.js';

export const REPORT_TEMPLATE = 'rta-report-v1';
export const reportIdPattern = /^rpt_[a-f0-9]{64}$/;
export function reportRoute(hash) {
  const match = /^#raport\/(rpt_[a-f0-9]{64})(\/druk)?$/.exec(hash);
  return match ? { id: match[1], print: Boolean(match[2]) } : null;
}
export const reportHref = (id, print = false) => reportIdPattern.test(id ?? '') ? `#raport/${id}${print ? '/druk' : ''}` : null;
const text = value => typeof value === 'string' && value.trim() ? value : null;
const stamp = value => Number.isFinite(Date.parse(value)) ? fullTime(value) : null;
const warningStatuses = { active: 'Aktywne w chwili wydania', expired: 'Wygasłe w chwili wydania', cancelled: 'Odwołane w chwili wydania', revoked: 'Odwołane w chwili wydania', unknown: 'Status nieustalony w chwili wydania' };

export function buildReportPresentation(r, { reference = null, baseUrl = 'https://redthreatalert.pl/', newerId = null } = {}) {
  const id = r.report_id, p = parts(r.as_of), level = threatLevel(r.rtb);
  const sections = r.commentary?.sections;
  const summary = sections ? [['situation', 'Sytuacja'], ['impact', 'Wpływ na Polskę'], ['recommendation', 'Zalecenia']]
    .filter(([key]) => text(sections[key])).map(([key, label]) => ({ label, text: sections[key] })) : [];
  if (!summary.length && text(r.commentary?.text)) summary.push({ label: null, text: r.commentary.text });
  const trend = r.rtb.trend;
  const canCompare = reference && reference.report_id === trend?.reference_report_id && reference.report_type === r.report_type &&
    Date.parse(reference.as_of) < Date.parse(r.as_of) && ['methodology_version','config_hash','source_config_hash','code_hash'].every(key => typeof r.provenance[key] === 'string' && r.provenance[key].length > 0) && comparable(r.provenance, reference.provenance) &&
    (r.rtb.confidence?.comparison_key ?? null) === (reference.rtb.confidence?.comparison_key ?? null) &&
    r.rtb.score !== null && reference.rtb.score !== null && trend.direction !== 'unavailable' && Number.isFinite(trend.delta_points);
  const delta = canCompare ? `${trend.delta_points > 0 ? '+' : ''}${scoreLabel(trend.delta_points)} pkt względem ${fullTime(reference.as_of)}` : null;
  const groups = new Map(Object.entries(topics).map(([key, value]) => [key, { key, label: value.label, events: [] }]));
  const used = new Set(), seen = new Set();
  for (const event of [...r.incidents].sort((a,b) => (Date.parse(signalTime(b).value) || 0) - (Date.parse(signalTime(a).value) || 0))) {
    if (seen.has(event.id)) continue; seen.add(event.id);
    const meta = presentation(event), keys = [...new Set(meta.topics)].filter(key => topics[key]);
    const primary = Object.keys(topics).find(key => keys.includes(key)) ?? 'other';
    const sources = event.sources.map(s => ({ publisher: s.publisher, url: safeLink(s.url) })).filter(s => s.url);
    event.sources.forEach(s => used.add(s.publisher));
    groups.get(primary).events.push({ id: event.id, title: event.title, summary: event.summary,
      place: regionLabel(event), occurred: text(event.occurred_on) ?? 'Nieustalona',
      publication: event.published_at ? fullTime(event.published_at) : 'Nieustalona',
      measurement: signalTime(event).precision === 'day' ? signalTimeText(event) : null,
      topics: (keys.length ? keys : ['other']).map(key => topics[key].label),
      status: statuses[event.status] ?? 'Status nieustalony',
      revisionNote: event.review_current === false ? 'W tym wydaniu: dostępna nowsza wersja materiału.' : null, sources });
  }
  const warnings = (r.rtb.official_warnings ?? []).map(w => ({ authority: text(w.authority) ?? 'Instytucja nieustalona', area: text(w.area) ?? 'Obszar nieustalony',
    instruction: text(w.instruction_pl), status: warningStatuses[w.status] ?? warningStatuses.unknown,
    from: stamp(w.effective_at), until: stamp(w.valid_until) }));
  const version = r.provenance.methodology_version;
  const methodPath = version === 'rtb-v0.4' ? 'docs/methodology.md' : /^rtb-v0\.[123]$/.test(version) ? `docs/archive/methodology-${version.slice(4)}.md` : null;
  const url = new URL(baseUrl); url.hash = reportHref(id).slice(1);
  return { template: REPORT_TEMPLATE, id, url: url.href,
    title: `Red Threat Alert — raport ${r.report_type === 'weekly' ? 'tygodniowy' : 'dzienny'}`,
    date: new Intl.DateTimeFormat('pl-PL', { timeZone: 'Europe/Warsaw', day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(r.as_of)),
    asOf: `Stan na godz. ${p.hour}:${p.minute} czasu polskiego`,
    snapshotNote: 'Raport przedstawia stan wiedzy w chwili analizy, nie wyłącznie zdarzenia z tego dnia.',
    metric: { score: scoreLabel(r.rtb.score), hasScore: r.rtb.score !== null, level: level.label, tone: level.tone,
      confidence: r.rtb.confidence?.percent == null ? 'Nieokreślona' : `${r.rtb.confidence.percent}%`, delta,
      note: r.rtb.score === null ? 'Indeks niewyliczony.' : r.rtb.score === 0 ? 'Brak naliczonych sygnałów. Zero nie potwierdza bezpieczeństwa.' : r.rtb.status === 'provisional' ? 'Ocena oparta na częściowych obserwacjach.' : null },
    explanation: 'Indeks opisuje nasilenie sygnałów zagrożenia, nie prawdopodobieństwo wojny',
    summary, warnings, groups: [...groups.values()].filter(g => g.events.length), count: seen.size,
    usedPublishers: [...used].sort((a,b) => a.localeCompare(b,'pl')),
    sources: r.sources.map(s => ({ name: s.name, url: safeLink(s.url), status: sourceStatuses[s.status] ?? 'Stan nieustalony',
      checked: stamp(s.checked_at), incompleteWindow: s.window_complete === false })),
    domains: (r.rtb.confidence?.domains ?? []).map(d => `${d.label}: ${d.percent == null ? 'pokrycie nieustalone' : d.percent + '% pokrycia'}`),
    limitations: r.limitations ?? [], gaps: (r.gaps ?? []).map(g => g.message),
    methodology: version, methodologyUrl: methodPath ? `https://github.com/pixels4users/red-threat-meter/blob/main/${methodPath}` : null,
    window: `${fullTime(r.window.start)} — ${fullTime(r.window.end)} (czas polski)`, windowNote: text(r.window.definition),
    previous: reportIdPattern.test(r.supersedes ?? '') ? r.supersedes : null,
    newer: reportIdPattern.test(newerId ?? '') && newerId !== id ? newerId : null,
    credit: 'RedThreatAlert by Pixels4Users' };
}

export function reportPresentationText(m) {
  const lines = [m.title, m.date, m.asOf, m.snapshotNote, '', `Indeks RTA: ${m.metric.hasScore ? m.metric.score + '/100' : 'niewyliczony'}`, m.metric.level,
    `Pewność danych: ${m.metric.confidence}`, m.metric.delta, m.metric.note, m.explanation];
  if (m.previous) lines.push('Korekta', new URL(reportHref(m.previous), m.url).href);
  if (m.newer) lines.push('Dostępna korekta', new URL(reportHref(m.newer), m.url).href);
  if (m.summary.length) lines.push('', 'Najważniejsze ustalenia', ...m.summary.flatMap(s => [s.label, s.text]));
  if (m.warnings.length) lines.push('', 'Oficjalne ostrzeżenia — stan w chwili wydania', ...m.warnings.flatMap(w => [w.authority, w.area, w.status, w.instruction, w.from && `Od: ${w.from}`, w.until && `Do: ${w.until}`]));
  lines.push('', 'Wydarzenia i kontekst');
  if (!m.count) lines.push('Brak wydarzeń ujętych w tym wydaniu');
  for (const group of m.groups) {
    lines.push('', group.label);
    for (const e of group.events) lines.push('', e.title, e.topics.join(' · '), e.place, `Data zdarzenia: ${e.occurred}`, `Publikacja: ${e.publication}`, e.measurement, e.status, e.revisionNote, e.summary, ...e.sources.map(s => `${s.publisher}: ${s.url}`));
  }
  lines.push('', 'Źródła i zakres obserwacji', 'Wydawcy materiałów wykorzystanych w raporcie', ...m.usedPublishers, '', 'Monitorowani wydawcy — dostępność w chwili wydania',
    ...m.sources.map(s => `${s.name}: ${s.status}${s.incompleteWindow ? ' · niepełne okno obserwacji' : ''}${s.checked ? ' · sprawdzono '+s.checked : ''}${s.url ? ' · '+s.url : ''}`),
    ...m.domains, ...m.limitations, ...m.gaps,
    '', 'Informacje o wydaniu', `Metodologia: ${m.methodology}`, m.methodologyUrl, `Okno raportu: ${m.window}`, m.windowNote, m.url, m.credit, `Wersja szablonu: ${m.template}`);
  return lines.filter(line => line !== null && line !== undefined).join('\n');
}
