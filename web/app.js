import { commentaryRows } from './commentary.js';
import { createIcons, Radar, Menu, X, LayoutDashboard, Map as MapIcon, ListFilter, Files, ArrowUpRight, TrendingUp, TrendingDown, Minus, Plus, Scan, Maximize, CircleDot, Flag, Flame, Landmark, TrainFront, Plane, ShieldAlert, Satellite, Newspaper, ChevronDown, ChevronUp, Coffee } from 'lucide';
import { select, scaleLinear, line, extent } from 'd3';
import { categories, statuses, sourceStatuses, scoreLabel, threatLevel, visibleWarnings, fullTime, shortDate, dateKey, isoWeek, parts, signalCount, timelineGroups, comparable, checkEnvelope, safeLink, reportText } from './data.js';
import { signalTime } from './signal-time.js';
import { signalTimeText } from './data.js';
import { initializeMaps, mapPoints } from './map.js';
import { topics, regions, kinds, presentation, regionLabel, filterSignals, topicCounts, periodRange, mapReport, SignalArchive, WEEK } from './signals.js';

const root = document.querySelector('#rtb-dashboard');
const $ = s => root.querySelector(s), $$ = s => [...root.querySelectorAll(s)];
const icons = () => createIcons({ icons: { Radar, Menu, X, LayoutDashboard, Map: MapIcon, ListFilter, Files, ArrowUpRight, TrendingUp, TrendingDown, Minus, Plus, Scan, Maximize, CircleDot, Flag, Flame, Landmark, TrainFront, Plane, ShieldAlert, Satellite, Newspaper, ChevronDown, ChevronUp, Coffee }, attrs: { width: 16, height: 16, 'aria-hidden': 'true' } });
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
const button = (text, action, cls = 'r-button') => { const b = el('button', cls, text); b.type = 'button'; b.addEventListener('click', action); return b; };
const pages = { overview: 'Przegląd', map: 'Mapa Operacyjna', journal: 'Dziennik Sygnałów', reports: 'Raporty' };
const state = { page: 'overview', selected: null, related: [], scale: 'day', expanded: new Set(), category: 'all', source: 'all', historyType: 'daily', area: 'macro', mapArea: 'macro', mapPeriod: 'day', mapTopic: 'all', journalArea: 'macro', journalPeriod: 'all' };
try { const saved = localStorage.getItem('rta-region'); if (Object.hasOwn(regions, saved)) state.area = state.mapArea = state.journalArea = saved; } catch {}
let archive = null, detailOpener = null, expandedFrom = 'overview';
let envelope = null, loaded = false, failed = false, busy = false, history = [], dailyHistory = [], nextOffset = null, historyAnchor = null, historyGeneration = 0;
let config = { refresh_seconds: 30, stale_after_hours: 30 };
const report = () => envelope?.report ?? null;
const records = () => archive?.records ?? report()?.incidents ?? [];
const scoped = () => report() ? filterSignals(records(), { asOf: report().as_of, area: state.area }) : [];
const mapRecords = () => report() ? filterSignals(records(), { asOf: report().as_of, area: state.mapArea, period: state.mapPeriod, topic: state.mapTopic }) : [];
const journalRecords = () => report() ? filterSignals(records(), { asOf: report().as_of, area: state.journalArea, period: state.journalPeriod, topic: state.category, source: state.source }) : [];
const shownMap = slot => { const view = slot === 'expanded' ? expandedFrom : slot; return mapReport(report(), view === 'overview' ? (report() ? filterSignals(records(), { asOf: report().as_of, area: state.area, period: state.scale }) : []) : mapRecords()); };
$('.r-main').id = 'main';
$('.r-overview').prepend($('.r-context'));
root.style.setProperty('--r-kpi-size', '104px');
const notice = el('p', 'r-data-notice'); notice.setAttribute('role', 'status'); $('.r-hero').after(notice);
const official = el('section', 'r-official-warnings'); official.setAttribute('aria-label', 'Oficjalne ostrzeżenia'); $('.r-hero').before(official);
const coverage = el('details', 'r-coverage'); $('.r-bottom-line').before(coverage);
for (const panel of $$('[data-detail]')) panel.append($('template[data-template=detail]').content.cloneNode(true));
for (const [key, value] of Object.entries(topics)) { const option = el('option', '', value.label); option.value = key; $('[data-category]').append(option); }

async function api(path) {
  const response = await fetch(path, { cache: 'no-store', credentials: 'same-origin', signal: AbortSignal.timeout(15000) });
  if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw new Error('unavailable');
  return response.json();
}

function freshness() {
  const r = report(), texts = [];
  if (failed) texts.push(r ? 'Nie udało się odświeżyć danych. Poniżej ostatni dostępny raport.' : 'Dane są chwilowo niedostępne. Spróbuj odświeżyć widok.');
  else if (loaded && !r) texts.push('Czekamy na pierwszy opublikowany raport.');
  if (r && Date.now() - Date.parse(r.as_of) > config.stale_after_hours * 3600000) texts.push('Ten raport nie przedstawia bieżącej sytuacji. Sprawdź datę ostatniej analizy.');
  if (archive?.failed && ['map', 'journal'].includes(state.page)) texts.push('Część archiwum jest chwilowo niedostępna. Poniżej dostępne sygnały.');
  if (r?.mode === 'fixture') texts.push('Podgląd testowy · dane syntetyczne, bez oceny rzeczywistej sytuacji.');
  notice.textContent = texts.join(' '); notice.hidden = !texts.length;
}

function renderMetric() {
  const r = report(), regional = state.area !== 'macro', metric = regional ? r?.rtb.regions?.[state.area] : r?.rtb, score = metric?.score ?? null;
  $('.r-kpi').textContent = scoreLabel(score);
  const level = threatLevel(metric ? { ...metric, official_warnings: r?.rtb.official_warnings } : null);
  root.dataset.threatLevel = level.tone;
  $('[data-threat-level]').textContent = level.label;
  $('.r-kpi').setAttribute('aria-label', score === null ? 'Indeks niewyliczony' : `${score} na 100`);
  for (const e of $$('[data-dialog-score]')) e.textContent = scoreLabel(score);
  $('[data-as-of]').textContent = r ? `Stan na ${fullTime(r.as_of)}` : failed ? 'Odczyt chwilowo niedostępny' : loaded ? 'Brak opublikowanego raportu' : 'Ładowanie raportu…';
  $('.r-metric .r-eyebrow').textContent = `Indeks RTA · ${regional ? regions[state.area] : 'raport dobowy'}`;
  $('[data-region]').value = state.area; $('[data-macro]').setAttribute('aria-pressed', String(!regional));
  $('[data-scope-label]').textContent = regional ? `Wybrany region: ${regions[state.area]}` : 'Polska i wschodnia flanka NATO';
  $('[data-confidence]').textContent = regional ? 'Nieustalona dla regionu' : r?.rtb.confidence.percent == null ? 'Nieokreślona' : `${r.rtb.confidence.percent}%`;
  $('.r-confidence').title = 'Pewność opisuje zakres obserwacji, ukończony przegląd i dostępność historii. Nie jest prawdopodobieństwem eskalacji.';
  let status = $('[data-score-status]');
  if (!status) { status = el('p', 'r-small'); status.dataset.scoreStatus = ''; $('.r-metric').append(status); }
  status.textContent = r && score === null ? 'Za mało danych do wyliczenia indeksu' : !regional && r?.rtb.review_required ? 'Wzrost indeksu wymaga pogłębionej oceny sytuacji' : score === 0 ? 'Brak naliczonych sygnałów. Zero nie potwierdza bezpieczeństwa.' : r?.rtb.status === 'provisional' ? 'Ocena oparta na częściowych obserwacjach' : '';
  if (score > 60 && metric.red_priority?.eligible === false) status.textContent += ' Brakuje niezależnych potwierdzeń bezpośrednich zdarzeń, by nadać najwyższy priorytet.';
  for (const b of $$('[data-component]')) b.textContent = score === null ? '—' : `${scoreLabel(metric.components[b.dataset.component])} pkt`;
  $('[data-regional-note]').textContent = regional ? 'Wynik obejmuje zdarzenia lokalne i wpływ z sąsiednich regionów. Pewność regionalna nie została jeszcze oszacowana.' : 'Indeks uwzględnia ocenę zdarzeń i upływ czasu; nie jest sumą sygnałów na mapie.';
  official.replaceChildren(); official.hidden = !visibleWarnings(r?.rtb).length;
  for (const w of visibleWarnings(r?.rtb)) {
    const article = el('article'); article.dataset.shelter = String(w.level === 'L3_shelter');
    article.append(el('strong', '', w.level === 'L3_shelter' ? 'Oficjalne zalecenie ochronne' : 'Oficjalny komunikat'), el('p', '', w.instruction_pl),
      el('p', 'r-small', `${w.authority} · ${w.area} · od ${fullTime(w.effective_at)}${w.valid_until ? ` do ${fullTime(w.valid_until)}` : ''}`));
    if (w.status === 'unknown') article.append(el('p', 'r-small', 'Ostatnia znana instrukcja. Sprawdź jej aktualność u wydającej ją instytucji.'));
    official.append(article);
  }
  const t = regional ? null : r?.rtb.trend, visible = score !== null && t?.delta_points != null;
  $('[data-trend]').hidden = !visible; root.dataset.trend = t?.direction ?? 'unavailable';
  if (visible) {
    $('[data-delta]').textContent = `${t.delta_points > 0 ? '+' : ''}${t.delta_points}`;
    const old = $('[data-trend]').querySelector('i,svg'), icon = el('i'); icon.dataset.lucide = t.direction === 'up' ? 'trending-up' : t.direction === 'down' ? 'trending-down' : 'minus'; old?.replaceWith(icon);
  }
  renderCommentary();
  coverage.replaceChildren(); coverage.hidden = !r;
  if (r) {
    coverage.append(el('summary', '', r.rtb.confidence.percent == null ? 'Zakres obserwacji i źródła' : `Pewność danych dla całego obszaru: ${r.rtb.confidence.percent}% · zobacz zakres obserwacji`));
    const content = el('div', 'r-coverage-content');
    content.append(el('p', 'r-small', 'Dotyczy całego obszaru analizy i obserwowanych źródeł. Pewność dla poszczególnych województw nie została jeszcze wyliczona.'));
    for (const domain of r.rtb.confidence.domains ?? []) content.append(el('p', 'r-small', `${domain.label}: ${domain.percent}% pokrycia`));
    for (const gap of r.gaps) content.append(el('p', '', gap.message));
    for (const source of r.sources) {
      const row = el('p', 'r-source-state'); row.append(el('strong', '', source.name), el('span', '', sourceStatuses[source.status]), el('span', 'r-small', source.checked_at ? `Sprawdzono ${fullTime(source.checked_at)}` : 'Jeszcze nie sprawdzono')); content.append(row);
    }
    content.append(el('p', 'r-small', `Zasady obliczeń: ${r.provenance.methodology_version}. ${r.limitations[0]}`)); coverage.append(content);
  }
  freshness(); drawTrend();
}

function drawTrend() {
  const r = report(), target = $('.r-spark'), svg = select(target); svg.selectAll('*').remove();
  const note = $('[data-history-note]'), footer = note.parentElement;
  target.hidden = true; footer.hidden = true; note.textContent = '';
  if (state.area !== 'macro') return;
  const all = dailyHistory.slice(0, 14).reverse();
  const compatible = all.map(row => ({ ...row, valid: r && comparable(row, r.provenance) && (r.provenance.methodology_version !== 'rtb-v0.4' || row.confidence_key === r.rtb.confidence.comparison_key) && row.score !== null }));
  const values = compatible.filter(p => p.valid);
  target.hidden = values.length < 2;
  footer.hidden = values.length < 2;
  if (values.length >= 2) note.textContent = 'Historia RTA · przerwy oznaczają brak porównywalnego wyniku';
  if (values.length < 2 || target.clientWidth < 10) return;
  const w = target.clientWidth, h = 40, bounds = extent(values, d => d.score);
  const x = scaleLinear().domain([0, Math.max(1, compatible.length - 1)]).range([4, w - 4]);
  const y = scaleLinear().domain([bounds[0] - 2, bounds[1] + 2]).range([h - 4, 4]);
  svg.attr('viewBox', `0 0 ${w} ${h}`); svg.append('title').text(values.map(v => `${fullTime(v.as_of)}: ${v.score}`).join('; '));
  svg.append('path').datum(compatible).attr('d', line().defined(d => d.valid).x((d, i) => x(i)).y(d => y(d.score))).attr('fill', 'none').attr('stroke', 'var(--r-trend)').attr('stroke-width', 2);
  compatible.forEach((d, i) => { if (d.valid) svg.append('circle').attr('cx', x(i)).attr('cy', y(d.score)).attr('r', 2).attr('fill', 'var(--r-trend)'); });
}

function selectSignals(ids) {
  detailOpener = document.activeElement; state.selected = ids[0]; state.related = ids;
  renderDetails(); maps.draw(); icons();
  const panel = $(`[data-detail="${mapDialog.open ? 'expanded' : state.page}"]`);
  const heading = panel?.querySelector('h3');
  if (heading) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); if (!mapDialog.open) panel.scrollIntoView({ block: 'nearest', behavior: 'instant' }); }
}
function clearSelection() { state.selected = null; state.related = []; }
function closeDetails() { clearSelection(); renderDetails(); maps.draw(); if (detailOpener?.isConnected) detailOpener.focus({ preventScroll: true }); }
function renderDetails() {
  const event = records().find(e => e.id === state.selected);
  $('[data-timeline]').hidden = Boolean(event);
  $('[data-operational]').dataset.selected = String(Boolean(event));
  $('.r-expanded-grid').dataset.selected = String(Boolean(event));
  for (const panel of $$('[data-detail]')) {
    panel.hidden = !event; if (!event) continue;
    const set = (sel, value) => { panel.querySelector(sel).textContent = value; };
    set('[data-detail-title]', event.title); set('[data-detail-summary]', event.summary);
    set('[data-detail-time]', signalTimeText(event));
    panel.querySelector('[data-detail-time]').previousElementSibling.textContent = signalTime(event).basis === 'measurement' ? 'Pomiar' : 'Publikacja';
    set('[data-detail-status]', `${statuses[event.status]}${event.review_current ? '' : ' · dostępna nowsza wersja materiału'}`);
    set('[data-detail-tag] span:last-child', presentation(event).topics.map(t => topics[t].label).join(' · '));
    const precision = { unknown: 'dokładność nieustalona', country: 'zasięg krajowy', region: 'region', city: 'miasto', approximate: 'położenie przybliżone', exact: 'miejsce wskazane w źródle' };
    set('[data-detail-location]', `${event.location.label ?? 'Miejsce nieustalone'} · ${precision[event.location.precision]}`);
    const national = panel.querySelector('[data-national-note]'); national.hidden = presentation(event).scope !== 'national';
    national.textContent = 'Flaga w stolicy reprezentuje cały kraj. Nie oznacza miejsca incydentu.';
    let cityNote = panel.querySelector('[data-city-note]');
    if (!cityNote) { cityNote = el('p', 'r-small'); cityNote.dataset.cityNote = ''; national.after(cityNote); }
    const anchor = presentation(event).map_anchor; cityNote.hidden = !anchor; cityNote.replaceChildren();
    if (anchor) {
      cityNote.append(document.createTextNode(`Punkt wskazuje miasto ${anchor.label}, nie dokładne miejsce zdarzenia. `));
      const href = safeLink(anchor.reference_url);
      if (href) { const a = el('a', 'r-source-link', 'Źródło położenia miasta'); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; cityNote.append(a); }
    }
    const sources = panel.querySelector('[data-detail-source]'); sources.replaceChildren();
    for (const source of event.sources) {
      const href = safeLink(source.url); if (!href) continue;
      const a = el('a', 'r-source-link', source.publisher); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; sources.append(a);
    }
    let date = panel.querySelector('[data-event-date]'); if (!date) { date = el('p', 'r-small'); date.dataset.eventDate = ''; panel.querySelector('dl').after(date); }
    date.textContent = `Data zdarzenia: ${event.occurred_on ?? 'nieustalona'}.`;
    const choices = panel.querySelector('[data-cluster-choices]'); choices.replaceChildren(); choices.hidden = state.related.length < 2;
    for (const id of state.related) { const other = records().find(e => e.id === id); if (!other) continue; const b = button(other.title, () => selectSignals([id, ...state.related.filter(x => x !== id)])); b.setAttribute('aria-pressed', String(event.id === id)); choices.append(b); }
  }
}

function renderTimeline() {
  const host = $('[data-timeline]'), r = report(); host.replaceChildren();
  const head = el('div', 'r-section-heading r-timeline-heading'); head.append(el('h2', '', 'Oś czasu')); host.append(head);
  const toggles = el('div', 'r-time-scale'); toggles.setAttribute('aria-label', 'Skala osi czasu');
  for (const [scale, label] of [['day', 'Dzień'], ['week', 'Tydzień'], ['month', 'Miesiąc']]) {
    const b = button(label, () => { state.scale = scale; clearSelection(); renderTimeline(); renderDetails(); maps.draw(); ensureArchive(); host.querySelector(`[data-scale=${scale}]`)?.focus(); }, ''); b.dataset.scale = scale; b.setAttribute('aria-pressed', String(state.scale === scale)); toggles.append(b);
  }
  host.append(toggles);
  if (!r) { host.append(el('p', 'r-empty', 'Oś czasu pojawi się po opublikowaniu raportu.')); return; }
  const data = timelineGroups(scoped(), r.as_of, state.scale);
  host.append(el('p', 'r-timeline-period', `${shortDate(data.start)} – ${shortDate(data.today)} · ${signalCount(data.eligible.length)}`));
  const rail = el('div', 'r-timeline-rail'); rail.setAttribute('role', 'list'); host.append(rail);
  if (!data.eligible.length) host.append(el('p', 'r-empty', 'Brak sygnałów w wybranym okresie.'));
  for (const [key, events] of data.groups.filter(([, events]) => data.eligible.length && (state.scale !== 'day' || events.length))) {
    const row = el('div', 'r-time-row'); row.setAttribute('role', 'listitem'); row.dataset.empty = String(!events.length); row.dataset.count = events.length;
    row.append(el('span', 'r-time-label', state.scale === 'day' ? key.endsWith('Tdaily') ? 'Pomiar dobowy' : key.slice(11) + ':00' : state.scale === 'week' ? shortDate(key) : `T${isoWeek(key)}`));
    const dot = el('span', 'r-time-node'); dot.append(el('i')); row.append(dot);
    if (!events.length) row.append(el('span', 'r-time-empty', 'Brak wpisów'));
    else {
      if (state.scale === 'day' && events.length === 1) { const b = signalButton(events[0]); row.append(b); rail.append(row); continue; }
      const group = `${state.scale}:${key}`, expanded = state.expanded.has(group), content = el('div');
      const counts = Object.entries(topics).map(([id, c]) => ({ label: c.label, count: events.filter(e => presentation(e).topics.includes(id)).length })).filter(c => c.count).sort((a, b) => b.count - a.count);
      const title = state.scale === 'day' && events.length === 1 ? events[0].title : signalCount(events.length);
      const open = button('', () => { if (expanded) state.expanded.delete(group); else state.expanded.add(group); renderTimeline(); host.querySelector(`[data-group="${group}"]`)?.focus(); }, 'r-time-button');
      open.dataset.group = group; open.setAttribute('aria-expanded', String(expanded)); open.setAttribute('aria-controls', `group-${group}`);
      open.append(el('span', 'r-time-title', title), el('span', 'r-time-subtitle', state.scale === 'month' ? 'Dominujące: ' + counts.filter(c => c.count === counts[0]?.count).map(c => c.label).join(', ') : counts.map(c => `${c.count}× ${c.label}`).join(' · ')), el('span', 'r-time-action', expanded ? 'Zwiń' : 'Rozwiń'));
      const badges = el('span', 'r-badges'); for (const label of [...new Set(events.map(regionLabel))]) badges.append(el('span', 'r-region-badge', label)); open.append(badges);
      const items = el('div', 'r-time-items'); items.id = `group-${group}`; items.hidden = !expanded;
      for (const event of events) items.append(signalButton(event));
      content.append(open, items); row.append(content);
    }
    rail.append(row);
  }
  const foot = el('div', 'r-timeline-footer'); foot.append(el('span', 'r-small', 'Według publikacji i dni pomiarów'), button('Zobacz w dzienniku', () => { state.journalArea = state.area; state.journalPeriod = state.scale; state.category = state.source = 'all'; navigate('journal'); }, 'r-link')); host.append(foot);
  const undated = scoped().filter(r => !signalTime(r).value).length;
  if (undated) host.append(el('p', 'r-small', `${signalCount(undated)} bez ustalonej daty znajdziesz w dzienniku.`));
}

function signalButton(event) {
  const b = button('', () => selectSignals([event.id]), 'r-signal-button'); b.dataset.signalId = event.id;
  b.append(el('span', 'r-time-title', event.title), el('span', 'r-region-badge', regionLabel(event)),
    el('span', 'r-small', `${presentation(event).topics.map(t => topics[t].label).join(' · ')} · ${[...new Set(event.sources.map(s => s.publisher))].join(' · ')}`));
  return b;
}
function renderList(host, filtered) {
  host.replaceChildren();
  for (const event of filtered) {
    const row = el('article', 'r-journal-row'), text = el('div'); row.dataset.signalId = event.id;
    const date = signalTime(event), time = el('time', '', date.value ? shortDate(date.day ?? dateKey(date.value)) : 'Bez daty');
    time.title = signalTimeText(event); row.append(time);
    text.append(button(event.title, () => selectSignals([event.id]), 'r-journal-title'));
    const meta = el('p', 'r-journal-meta'); meta.append(el('span', 'r-region-badge', regionLabel(event)), el('span', '', presentation(event).topics.map(t => topics[t].label).join(' · ')), el('span', '', kinds[presentation(event).kind]));
    if (!mapPoints(mapReport(report(), [event])).length) meta.append(el('span', '', 'Bez punktu na mapie'));
    text.append(meta);
    const source = el('div', 'r-journal-source', [...new Set(event.sources.map(s => s.publisher))].join(' · ')); source.append(el('p', 'r-small', statuses[event.status])); row.append(text, source); host.append(row);
  }
  if (!filtered.length) host.append(el('p', 'r-empty', archive?.loading ? 'Wczytywanie sygnałów…' : 'Brak sygnałów dla wybranych filtrów.'));
}
function areaSummary(filtered, area) {
  if (!regions[area]) return signalCount(filtered.length);
  const national = filtered.filter(e => presentation(e).scope === 'national' && e.country === 'PL').length;
  return `Lokalne: ${filtered.length - national} · ogólnopolskie: ${national}`;
}
function renderJournal() {
  const filtered = journalRecords();
  $('[data-journal-count]').textContent = areaSummary(filtered, state.journalArea);
  $('[data-journal-period-note]').textContent = periodCaption(state.journalPeriod) + ' · publikacje i dni pomiarów';
  renderList($('[data-journal]'), filtered);
}
function renderOperational() {
  const filtered = mapRecords(), mapped = mapPoints(mapReport(report(), filtered)).length;
  $('[data-map-count]').textContent = `${areaSummary(filtered, state.mapArea)} · ${mapped} na mapie · ${filtered.length - mapped} bez wskazanego miejsca. ${periodCaption(state.mapPeriod)}`;
  renderList($('[data-map-list]'), filtered);
}

function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type })), a = el('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
let reportOpener;
function showReportPreview(title, body, opener) {
  const preview = $('[data-report-preview]'), heading = $('[data-report-title]');
  reportOpener = opener;
  heading.textContent = title; $('[data-report-body]').textContent = body; preview.hidden = false;
  if (state.page === 'reports') {
    heading.setAttribute('tabindex', '-1'); heading.focus({ preventScroll: true });
    preview.scrollIntoView({ block: 'start', behavior: 'instant' });
  }
}
async function readReport(id, action) {
  const opener = document.activeElement;
  try {
    const item = checkEnvelope(await api(`/api/reports/${id}`)); if (!item) throw new Error('missing');
    if (action === 'read') showReportPreview(`Raport · ${fullTime(item.report.as_of)}`, reportText(item.report), opener);
    else if (action === 'text') download(`rtb-${item.report.as_of.slice(0, 10)}.txt`, reportText(item.report), 'text/plain;charset=utf-8');
    else download(`${id}.${action}`, JSON.stringify(action === 'geojson' ? item.report.geojson : item.report, null, 2), 'application/json');
  } catch { showReportPreview('Raport chwilowo niedostępny', 'Spróbuj otworzyć go ponownie.', opener); }
}
function renderReports() {
  const host = $('[data-reports]'); host.replaceChildren();
  for (const r of history) {
    const row = el('article', 'r-report-row'), mark = el('span', 'r-report-icon'); const icon = el('i'); icon.dataset.lucide = 'files'; mark.append(icon);
    const info = el('div'); info.append(el('h3', '', `${r.report_type === 'daily' ? 'Raport dobowy' : 'Raport tygodniowy'} · ${fullTime(r.as_of)}`), el('p', 'r-small', `RTA ${r.score === null ? 'niewyliczony' : scoreLabel(r.score) + '/100'} · ${r.methodology_version}${r.supersedes ? ' · korekta' : ''}`));
    const actions = el('div', 'r-report-actions'); actions.append(button('Czytaj', () => readReport(r.report_id, 'read')), button('Pobierz', () => readReport(r.report_id, 'text')),
      button('JSON', () => readReport(r.report_id, 'json'), 'r-link'), button('GeoJSON', () => readReport(r.report_id, 'geojson'), 'r-link'));
    row.append(mark, info, actions); host.append(row);
  }
  if (!history.length) host.append(el('p', 'r-empty', 'Brak opublikowanych raportów tego rodzaju.'));
  $('[data-more-reports]').hidden = nextOffset === null; icons();
}
async function loadHistory(more = false) {
  const generation = ++historyGeneration, kind = state.historyType;
  const q = new URLSearchParams({ type: kind });
  if (more && nextOffset !== null) { q.set('offset', nextOffset); q.set('anchor', historyAnchor); }
  try {
    const response = await api(`/api/reports?${q}`); if (generation !== historyGeneration) return;
    if (!Array.isArray(response.items)) throw new Error('invalid_history');
    history = more ? [...history, ...response.items.filter(r => !history.some(old => old.report_id === r.report_id))] : response.items;
    nextOffset = response.next_offset; historyAnchor = response.anchor;
    if (kind === 'daily') { dailyHistory = history; drawTrend(); }
    renderReports();
  } catch { if (generation === historyGeneration) { $('[data-reports]').replaceChildren(el('p', 'r-empty', 'Archiwum jest chwilowo niedostępne. Odśwież widok, aby spróbować ponownie.')); } }
}

function render() {
  const available = new Set(records().map(i => i.id)); if (!available.has(state.selected)) clearSelection();
  const sources = new Map((report()?.sources ?? []).map(s => [s.id, s.name]));
  for (const e of records()) for (const s of e.sources) sources.set(s.source_id, s.publisher);
  setOptions($('[data-source]'), [['all', 'Wszystkie źródła'], ...sources], state.source);
  renderFilters(); renderMetric(); renderTopicCounts(); renderTimeline(); renderJournal(); renderOperational(); renderDetails();
  maps.draw(); icons();
}
function navigate(page) {
  $('.r-hero').hidden = page !== 'overview';
  state.page = page; state.selected = null; state.related = [];
  for (const b of $$('[data-page]')) { if (b.dataset.page === page) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current'); }
  for (const view of $$('[data-view]')) view.hidden = view.dataset.view !== page;
  $('[data-page-title]').textContent = pages[page]; render(); ensureArchive();
  if (page === 'reports') loadHistory();
  window.scrollTo({ top: 0, behavior: 'instant' });
  $('[data-page-title]').setAttribute('tabindex', '-1');
  $('[data-page-title]').focus({ preventScroll: true });
}

const mapDialog = $('[data-map-dialog]'); let mapOpener;
const maps = initializeMaps(root, shownMap, () => state.selected, selectSignals, icons, b => { mapOpener = b; expandedFrom = b.closest('[data-map-slot]').dataset.mapSlot; mapDialog.showModal(); maps.draw(); if (document.fullscreenEnabled) root.requestFullscreen?.().catch(() => {}); });
$('[data-close-map]').addEventListener('click', () => mapDialog.close());
mapDialog.addEventListener('close', () => { if (document.fullscreenElement === root) document.exitFullscreen().catch(() => {}); maps.draw(); mapOpener?.focus({ preventScroll: true }); });
let wasFullscreen = false;
document.addEventListener('fullscreenchange', () => { if (document.fullscreenElement === root) { wasFullscreen = true; maps.draw(); } else if (wasFullscreen) { wasFullscreen = false; if (mapDialog.open) mapDialog.close(); } });
for (const dialog of [mapDialog]) dialog.addEventListener('keydown', event => {
  if (event.key !== 'Tab') return;
  const controls = [...dialog.querySelectorAll('button:not(:disabled),a[href],select')].filter(e => e.getClientRects().length), first = controls[0], last = controls.at(-1);
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
});
for (const b of $$('[data-page]')) b.addEventListener('click', () => navigate(b.dataset.page));
for (const b of $$('[data-go]')) b.addEventListener('click', () => { if (b.dataset.go === 'map') { state.mapArea = state.area; state.mapPeriod = state.scale; state.mapTopic = 'all'; } navigate(b.dataset.go); });
for (const b of $$('[data-close-detail]')) b.addEventListener('click', closeDetails);
document.addEventListener('keydown', e => { if (e.key === 'Escape' && state.selected && !mapDialog.open) closeDetails(); });
$('[data-category]').addEventListener('change', e => { state.category = e.target.value; clearSelection(); render(); });
$('[data-source]').addEventListener('change', e => { state.source = e.target.value; clearSelection(); render(); });
$('[data-close-report]').addEventListener('click', () => {
  $('[data-report-preview]').hidden = true;
  (reportOpener?.isConnected ? reportOpener : $('[data-report-type]')).focus();
});
$('[data-report-type]').addEventListener('change', e => { state.historyType = e.target.value; history = []; nextOffset = null; $('[data-report-preview]').hidden = true; loadHistory(); });
$('[data-more-reports]').addEventListener('click', () => loadHistory(true));

const periods = [['day', 'Dzisiaj'], ['week', 'Ten tydzień'], ['month', 'Ten miesiąc'], ['quarter', 'Ten kwartał'], ['year', 'Ten rok'], ['current7', 'Ostatnie 7 dni'], ['previous7', 'Poprzednie 7 dni'], ['undated', 'Bez daty']];
function setOptions(select, values, selected) {
  const signature = JSON.stringify(values);
  if (select.dataset.options !== signature) { select.replaceChildren(...values.map(([value, label]) => { const option = el('option', '', label); option.value = value; return option; })); select.dataset.options = signature; }
  select.value = selected;
}
function periodCaption(period) {
  if (!report()) return '';
  const range = periodRange(report().as_of, period);
  if (range.undated) return 'Bez ustalonej daty';
  if (range.rolling) return `${fullTime(new Date(range.start))} – ${fullTime(new Date(range.end))}`;
  return range.dateStart ? `${shortDate(range.dateStart)} – ${fullTime(report().as_of)}` : 'Całe dostępne archiwum';
}
function renderFilters() {
  setOptions($('[data-region]'), [['macro', 'Wybierz województwo'], ...Object.entries(regions)], state.area);
  for (const view of ['map', 'journal']) {
    const topic = view === 'map' ? state.mapTopic : state.category, period = state[view + 'Period'];
    const values = [['macro', 'Flanka wschodnia'], ['PL', 'Cała Polska'], ...Object.entries(regions).map(([id, name]) => [id, `${name} (${report() ? filterSignals(records(), { asOf: report().as_of, area: id, period, topic, source: view === 'journal' ? state.source : 'all', includeNational: false }).length : 0})`])];
    setOptions($(`[data-${view}-area]`), values, state[view + 'Area']);
    setOptions($(`[data-${view}-period]`), view === 'journal' ? [['all', 'Całe archiwum'], ...periods] : periods, period);
  }
  setOptions($('[data-map-topic]'), [['all', 'Wszystkie tematy'], ...Object.entries(topics).map(([key, value]) => [key, value.label])], state.mapTopic);
  $('[data-category]').value = state.category;
}
function renderTopicCounts() {
  const host = $('[data-topic-counts]'); host.replaceChildren();
  $('[data-count-period]').textContent = report() ? periodCaption('current7') : '';
  $('[data-count-note]').textContent = archive?.loading ? 'Wczytywanie historii…' : archive?.failed ? 'Nie udało się pobrać całej historii. Liczby mogą być niepełne.' : 'Liczba zapisanych sygnałów, nie liczba ataków.';
  if (!report()) return;
  const counts = topicCounts(records(), [...(archive?.reports.values() ?? [report()])], report().as_of, state.area, { failed: archive?.failed, loading: archive?.loading, earliestLoaded: archive?.earliestLoaded });
  for (const item of counts) {
    const b = button('', () => { state.journalArea = state.area; state.category = item.topic; state.source = 'all'; state.journalPeriod = 'current7'; navigate('journal'); }, 'r-topic-button');
    const label = el('span', 'r-topic-label'), icon = el('i'); icon.dataset.lucide = topics[item.topic].icon; label.append(icon, el('span', '', topics[item.topic].label));
    const delta = item.delta == null ? null : item.delta > 0 ? `↑ ${item.delta} więcej` : item.delta < 0 ? `↓ ${Math.abs(item.delta)} mniej` : '— bez zmian';
    b.append(label, el('strong', 'r-topic-number', String(item.current.length)));
    if (delta !== null) b.append(el('span', 'r-small', delta));
    b.setAttribute('aria-label', `${topics[item.topic].label}: ${signalCount(item.current.length)}.${delta !== null ? ` ${delta}.` : ''} Zobacz w dzienniku.`);
    if (item.delta !== null) b.title = `Poprzednie 7 dni: ${item.previous.length}. ${periodCaption('previous7')}`;
    host.append(b);
  }
  if (counts.some(item => item.delta !== null)) $('[data-count-note]').append(document.createTextNode(' Porównanie z poprzednimi 7 dniami.'));
  if (report().sources.some(s => s.status !== 'current')) $('[data-count-note]').append(document.createTextNode(' Dane częściowe.'));
}
function renderCommentary() {
  const host = $('[data-commentary]'); host.replaceChildren();
  const rows = commentaryRows(report(), state.area, records());
  host.hidden = !rows.length;
  host.previousElementSibling.hidden = !rows.length;
  for (const [label, text] of rows) { const row = el('p', 'r-commentary-row'); row.append(el('strong', '', label), el('span', '', text)); host.append(row); }
  // Recommendations are prose, with no underline or pretend-link behavior.
}
function selectArea(area) {
  state.area = area; state.mapArea = area; state.journalArea = area; clearSelection();
  try { localStorage.setItem('rta-region', area); } catch {}
  render(); ensureArchive();
}
$('[data-macro]').addEventListener('click', () => selectArea('macro'));
$('[data-region]').addEventListener('change', e => selectArea(e.target.value));
for (const view of ['map', 'journal']) for (const field of ['area', 'period', ...(view === 'map' ? ['topic'] : [])]) {
  $(`[data-${view}-${field}]`).addEventListener('change', e => {
    state[view + field[0].toUpperCase() + field.slice(1)] = e.target.value; clearSelection(); render(); ensureArchive();
  });
}
function ensureArchive() {
  if (!archive || !report()) return;
  let start = Date.parse(report().as_of) - 2 * WEEK;
  const period = state.page === 'map' ? state.mapPeriod : state.page === 'journal' ? state.journalPeriod : state.scale;
  const range = periodRange(report().as_of, period);
  if (range.start != null) start = Math.min(start, range.start);
  // All/undated means all retained public history, capped to avoid unbounded work.
  if (['all', 'undated'].includes(period)) start = 0;
  if (start < archive.earliestLoaded || archive.failed) archive.loadThrough(start);
}

async function refresh() {
  if (busy) return; busy = true;
  try {
    const next = checkEnvelope(await api('/api/latest'));
    const changed = !loaded || next?.report.report_id !== envelope?.report.report_id;
    envelope = next; loaded = true; failed = false;
    if (changed) {
      archive?.dispose();
      archive = next ? new SignalArchive(next, api, () => { if (archive?.envelope === next) render(); }) : null;
      render(); ensureArchive(); await loadHistory(); if (state.historyType !== 'daily') { const h = await api('/api/reports?type=daily'); dailyHistory = h.items; drawTrend(); } }
    else freshness();
  } catch { failed = true; loaded = true; if (!envelope) renderMetric(); else freshness(); }
  finally { busy = false; }
}
document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
new ResizeObserver(drawTrend).observe($('.r-analysis'));
render(); renderReports();
api('/api/config').then(value => { if (value.refresh_seconds >= 10 && value.stale_after_hours >= 1) config = value; }).catch(() => {});
await refresh();
// These reads refresh the screen, not the analysis pipeline. No scheduled jobs.
setInterval(() => { if (!document.hidden) refresh(); }, config.refresh_seconds * 1000);
