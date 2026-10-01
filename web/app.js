import { createIcons, Radar, Menu, X, LayoutDashboard, Map, ListFilter, Files, ArrowUpRight, TrendingUp, TrendingDown, Minus, Plus, Scan, Maximize, CircleDot, Flag, Flame, Landmark, TrainFront, Plane, ShieldAlert, Satellite, Newspaper, ChevronDown, ChevronUp, Coffee } from 'lucide';
import { select, scaleLinear, line, extent } from 'd3';
import { categories, statuses, sourceStatuses, scoreLabel, visibleWarnings, fullTime, shortDate, dateKey, isoWeek, parts, signalCount, timelineGroups, comparable, checkEnvelope, safeLink, reportText } from './data.js';
import { initializeMaps, mapPoints } from './map.js';

const root = document.querySelector('#rtb-dashboard');
const $ = s => root.querySelector(s), $$ = s => [...root.querySelectorAll(s)];
const icons = () => createIcons({ icons: { Radar, Menu, X, LayoutDashboard, Map, ListFilter, Files, ArrowUpRight, TrendingUp, TrendingDown, Minus, Plus, Scan, Maximize, CircleDot, Flag, Flame, Landmark, TrainFront, Plane, ShieldAlert, Satellite, Newspaper, ChevronDown, ChevronUp, Coffee }, attrs: { width: 16, height: 16, 'aria-hidden': 'true' } });
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
const button = (text, action, cls = 'r-button') => { const b = el('button', cls, text); b.type = 'button'; b.addEventListener('click', action); return b; };
const pages = { overview: 'Przegląd', map: 'Mapa Operacyjna', journal: 'Dziennik Sygnałów', reports: 'Raporty' };
const state = { page: 'overview', selected: null, related: [], scale: 'day', expanded: new Set(), category: 'all', source: 'all', historyType: 'daily' };
let envelope = null, loaded = false, failed = false, busy = false, history = [], dailyHistory = [], nextOffset = null, historyAnchor = null, historyGeneration = 0;
let config = { refresh_seconds: 30, stale_after_hours: 30 };
const report = () => envelope?.report ?? null;
const records = () => report()?.incidents ?? [];
$('.r-main').id = 'main';
$('.r-overview').prepend($('.r-context'));
root.style.setProperty('--r-kpi-size', '104px');
const notice = el('p', 'r-data-notice'); notice.setAttribute('role', 'status'); $('.r-hero').after(notice);
const official = el('section', 'r-official-warnings'); official.setAttribute('aria-label', 'Oficjalne ostrzeżenia'); $('.r-hero').before(official);
const coverage = el('details', 'r-coverage'); $('.r-hero').after(coverage);
for (const panel of $$('[data-detail]')) panel.append($('template[data-template=detail]').content.cloneNode(true));
for (const [key, value] of Object.entries(categories)) { const option = el('option', '', value.label); option.value = key; $('[data-category]').append(option); }

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
  if (r?.mode === 'fixture') texts.push('Podgląd testowy · dane syntetyczne, bez oceny rzeczywistej sytuacji.');
  notice.textContent = texts.join(' '); notice.hidden = !texts.length;
}

function renderMetric() {
  const r = report(), score = r?.rtb.score ?? null;
  $('.r-kpi').textContent = scoreLabel(score);
  root.dataset.redPriority = String(r?.rtb.red_priority?.eligible === true);
  $('.r-kpi').setAttribute('aria-label', score === null ? 'Indeks niewyliczony' : `${score} na 100`);
  for (const e of $$('[data-dialog-score]')) e.textContent = scoreLabel(score);
  $('[data-as-of]').textContent = r ? `Stan na ${fullTime(r.as_of)}` : failed ? 'Odczyt chwilowo niedostępny' : loaded ? 'Brak opublikowanego raportu' : 'Ładowanie raportu…';
  $('.r-metric .r-eyebrow').textContent = 'Indeks RTB · raport dobowy';
  $('[data-confidence]').textContent = r?.rtb.confidence.percent == null ? 'Nieokreślona' : `${r.rtb.confidence.percent}%`;
  $('.r-confidence').title = 'Pewność opisuje zakres obserwacji, ukończony przegląd i dostępność historii. Nie jest prawdopodobieństwem eskalacji.';
  let status = $('[data-score-status]');
  if (!status) { status = el('p', 'r-small'); status.dataset.scoreStatus = ''; $('.r-metric').append(status); }
  status.textContent = r && score === null ? 'Za mało danych do wyliczenia indeksu' : r?.rtb.review_required ? 'Wzrost indeksu wymaga pogłębionej oceny sytuacji' : score === 0 ? 'Brak naliczonych sygnałów. Sprawdź pewność danych — zero nie oznacza braku zagrożenia.' : r?.rtb.status === 'provisional' ? 'Ocena oparta na częściowych obserwacjach' : '';
  if (score > 60 && r.rtb.red_priority?.eligible === false) status.textContent += ' Brakuje niezależnych potwierdzeń bezpośrednich zdarzeń, by nadać najwyższy priorytet.';
  for (const b of $$('[data-component]')) b.textContent = score === null ? '—' : `${scoreLabel(r.rtb.components[b.dataset.component])} pkt`;
  official.replaceChildren(); official.hidden = !visibleWarnings(r?.rtb).length;
  for (const w of visibleWarnings(r?.rtb)) {
    const article = el('article'); article.dataset.shelter = String(w.level === 'L3_shelter');
    article.append(el('strong', '', w.level === 'L3_shelter' ? 'Oficjalne zalecenie ochronne' : 'Oficjalny komunikat'), el('p', '', w.instruction_pl),
      el('p', 'r-small', `${w.authority} · ${w.area} · od ${fullTime(w.effective_at)}${w.valid_until ? ` do ${fullTime(w.valid_until)}` : ''}`));
    if (w.status === 'unknown') article.append(el('p', 'r-small', 'Ostatnia znana instrukcja. Sprawdź jej aktualność u wydającej ją instytucji.'));
    official.append(article);
  }
  const t = r?.rtb.trend, visible = score !== null && t?.delta_points !== null;
  $('[data-trend]').hidden = !visible; root.dataset.trend = t?.direction ?? 'unavailable';
  if (visible) {
    $('[data-delta]').textContent = `${t.delta_points > 0 ? '+' : ''}${t.delta_points}`;
    const old = $('[data-trend]').querySelector('i,svg'), icon = el('i'); icon.dataset.lucide = t.direction === 'up' ? 'trending-up' : t.direction === 'down' ? 'trending-down' : 'minus'; old?.replaceWith(icon);
  }
  $('[data-commentary]').textContent = r?.commentary.text ?? 'Podsumowanie niedostępne';
  coverage.replaceChildren(); coverage.hidden = !r;
  if (r) {
    coverage.append(el('summary', '', r.rtb.confidence.percent == null ? 'Zakres obserwacji i źródła' : `Pewność danych: ${r.rtb.confidence.percent}% · zobacz zakres obserwacji`));
    const content = el('div', 'r-coverage-content');
    content.append(el('p', 'r-small', 'Dotyczy obserwowanych źródeł, nie wszystkich zdarzeń w regionie.'));
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
  const all = dailyHistory.slice(0, 14).reverse();
  const compatible = all.map(row => ({ ...row, valid: r && comparable(row, r.provenance) && (r.provenance.methodology_version !== 'rtb-v0.4' || row.confidence_key === r.rtb.confidence.comparison_key) && row.score !== null }));
  const values = compatible.filter(p => p.valid);
  target.hidden = values.length < 2;
  $('[data-history-note]').textContent = values.length < 2 ? 'Brak porównywalnego trendu' : 'Historia RTB · przerwy oznaczają brak porównywalnego wyniku';
  if (values.length < 2 || target.clientWidth < 10) return;
  const w = target.clientWidth, h = 40, bounds = extent(values, d => d.score);
  const x = scaleLinear().domain([0, Math.max(1, compatible.length - 1)]).range([4, w - 4]);
  const y = scaleLinear().domain([bounds[0] - 2, bounds[1] + 2]).range([h - 4, 4]);
  svg.attr('viewBox', `0 0 ${w} ${h}`); svg.append('title').text(values.map(v => `${fullTime(v.as_of)}: ${v.score}`).join('; '));
  svg.append('path').datum(compatible).attr('d', line().defined(d => d.valid).x((d, i) => x(i)).y(d => y(d.score))).attr('fill', 'none').attr('stroke', 'var(--r-trend)').attr('stroke-width', 2);
  compatible.forEach((d, i) => { if (d.valid) svg.append('circle').attr('cx', x(i)).attr('cy', y(d.score)).attr('r', 2).attr('fill', 'var(--r-trend)'); });
}

function selectSignals(ids) { state.selected = ids[0]; state.related = ids; renderDetails(); maps.draw(); icons(); }
function renderDetails() {
  const event = records().find(e => e.id === state.selected);
  $('[data-timeline]').hidden = Boolean(event);
  $('[data-operational]').dataset.selected = String(Boolean(event));
  $('.r-expanded-grid').dataset.selected = String(Boolean(event));
  for (const panel of $$('[data-detail]')) {
    panel.hidden = !event; if (!event) continue;
    const set = (sel, value) => { panel.querySelector(sel).textContent = value; };
    set('[data-detail-title]', event.title); set('[data-detail-summary]', event.summary);
    set('[data-detail-time]', fullTime(event.published_at));
    set('[data-detail-status]', `${statuses[event.status]}${event.review_current ? '' : ' · dostępna nowsza wersja materiału'}`);
    set('[data-detail-tag] span:last-child', categories[event.category]?.label ?? 'Sygnał');
    const precision = { unknown: 'dokładność nieustalona', country: 'zasięg krajowy', region: 'region', city: 'miasto', approximate: 'położenie przybliżone', exact: 'miejsce wskazane w źródle' };
    set('[data-detail-location]', `${event.location.label ?? 'Miejsce nieustalone'} · ${precision[event.location.precision]}`);
    const national = panel.querySelector('[data-national-note]'); national.hidden = event.location.precision !== 'country';
    national.textContent = 'Flaga w stolicy reprezentuje cały kraj. Nie oznacza miejsca incydentu.';
    const sources = panel.querySelector('[data-detail-source]'); sources.replaceChildren();
    for (const source of event.sources) {
      const href = safeLink(source.url); if (!href) continue;
      const a = el('a', 'r-source-link', source.publisher); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; sources.append(a);
    }
    let date = panel.querySelector('[data-event-date]'); if (!date) { date = el('p', 'r-small'); date.dataset.eventDate = ''; panel.querySelector('dl').after(date); }
    date.textContent = `Data zdarzenia: ${event.occurred_on ?? 'nieustalona'}. Opublikowano i wydarzyło się to odrębne daty.`;
    const choices = panel.querySelector('[data-cluster-choices]'); choices.replaceChildren(); choices.hidden = state.related.length < 2;
    for (const id of state.related) { const other = records().find(e => e.id === id); if (!other) continue; const b = button(other.title, () => selectSignals([id, ...state.related.filter(x => x !== id)])); b.setAttribute('aria-pressed', String(event.id === id)); choices.append(b); }
  }
}

function renderTimeline() {
  const host = $('[data-timeline]'), r = report(); host.replaceChildren();
  const head = el('div', 'r-section-heading r-timeline-heading'); head.append(el('h2', '', 'Oś czasu')); host.append(head);
  const toggles = el('div', 'r-time-scale'); toggles.setAttribute('aria-label', 'Skala osi czasu');
  for (const [scale, label] of [['day', 'Dzień'], ['week', 'Tydzień'], ['month', 'Miesiąc']]) {
    const b = button(label, () => { state.scale = scale; renderTimeline(); host.querySelector(`[data-scale=${scale}]`)?.focus(); }, ''); b.dataset.scale = scale; b.setAttribute('aria-pressed', String(state.scale === scale)); toggles.append(b);
  }
  host.append(toggles);
  if (!r) { host.append(el('p', 'r-empty', 'Oś czasu pojawi się po opublikowaniu raportu.')); return; }
  const data = timelineGroups(records(), r.as_of, state.scale);
  host.append(el('p', 'r-timeline-period', `${shortDate(data.start)} – ${shortDate(data.today)} · ${signalCount(data.eligible.length)}`));
  const rail = el('div', 'r-timeline-rail'); rail.setAttribute('role', 'list'); host.append(rail);
  if (!data.eligible.length) host.append(el('p', 'r-empty', 'Brak wpisów z datą publikacji w tym okresie.'));
  for (const [key, events] of data.groups.filter(([, events]) => data.eligible.length && (state.scale !== 'day' || events.length))) {
    const row = el('div', 'r-time-row'); row.setAttribute('role', 'listitem'); row.dataset.empty = String(!events.length); row.dataset.count = events.length;
    row.append(el('span', 'r-time-label', state.scale === 'day' ? key.slice(11) + ':00' : state.scale === 'week' ? shortDate(key) : `T${isoWeek(key)}`));
    const dot = el('span', 'r-time-node'); dot.append(el('i')); row.append(dot);
    if (!events.length) row.append(el('span', 'r-time-empty', 'Brak wpisów'));
    else {
      const group = `${state.scale}:${key}`, expanded = state.expanded.has(group), content = el('div');
      const counts = Object.entries(categories).map(([id, c]) => ({ label: c.label, count: events.filter(e => e.category === id).length })).filter(c => c.count).sort((a, b) => b.count - a.count);
      const title = state.scale === 'day' && events.length === 1 ? events[0].title : signalCount(events.length);
      const open = button('', () => { if (expanded) state.expanded.delete(group); else state.expanded.add(group); renderTimeline(); host.querySelector(`[data-group="${group}"]`)?.focus(); }, 'r-time-button');
      open.dataset.group = group; open.setAttribute('aria-expanded', String(expanded)); open.setAttribute('aria-controls', `group-${group}`);
      open.append(el('span', 'r-time-title', title), el('span', 'r-time-subtitle', state.scale === 'month' ? 'Dominujące: ' + counts.filter(c => c.count === counts[0]?.count).map(c => c.label).join(', ') : counts.map(c => `${c.count}× ${c.label}`).join(' · ')), el('span', 'r-time-action', expanded ? 'Zwiń' : 'Rozwiń'));
      const items = el('div', 'r-time-items'); items.id = `group-${group}`; items.hidden = !expanded;
      for (const event of events) { const b = button('', () => selectSignals([event.id]), ''); b.dataset.signalId = event.id; b.append(el('time', '', state.scale === 'day' ? `${parts(event.published_at).hour}:${parts(event.published_at).minute}` : fullTime(event.published_at)), el('span', '', event.title), el('span', 'r-small', [...new Set(event.sources.map(s => s.publisher))].join(' · '))); items.append(b); }
      content.append(open, items); row.append(content);
    }
    rail.append(row);
  }
  const foot = el('div', 'r-timeline-footer'); foot.append(el('span', 'r-small', 'Według czasu publikacji'), button('Cały dziennik', () => navigate('journal'), 'r-link')); host.append(foot);
  const undated = records().filter(r => !r.published_at).length;
  if (undated) host.append(el('p', 'r-small', `${signalCount(undated)} bez daty publikacji znajdziesz w dzienniku.`));
}

function renderJournal() {
  const host = $('[data-journal]'); host.replaceChildren();
  const filtered = records().filter(e => (state.category === 'all' || e.category === state.category) && (state.source === 'all' || e.sources.some(s => s.source_id === state.source))).sort((a, b) => (b.published_at ?? '').localeCompare(a.published_at ?? ''));
  $('[data-journal-count]').textContent = `${filtered.length} z ${signalCount(records().length)}`;
  for (const event of filtered) {
    const row = el('article', 'r-journal-row'), text = el('div');
    row.append(el('time', '', event.published_at ? shortDate(dateKey(event.published_at)) : '—'));
    text.append(button(event.title, () => selectSignals([event.id]), 'r-journal-title'), el('p', 'r-journal-meta', `${categories[event.category]?.label ?? 'Sygnał'} · ${event.location.label ?? 'Lokalizacja nieustalona'}`));
    const source = el('div', 'r-journal-source', [...new Set(event.sources.map(s => s.publisher))].join(' · ')); source.append(el('p', 'r-small', statuses[event.status])); row.append(text, source); host.append(row);
  }
  if (!filtered.length) host.append(el('p', 'r-empty', 'Brak wpisów dla wybranego tematu i źródła.'));
}

function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type })), a = el('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function readReport(id, action) {
  try {
    const item = checkEnvelope(await api(`/api/reports/${id}`)); if (!item) throw new Error('missing');
    if (action === 'read') { $('[data-report-preview]').hidden = false; $('[data-report-title]').textContent = `Raport · ${fullTime(item.report.as_of)}`; $('[data-report-body]').textContent = reportText(item.report); }
    else if (action === 'text') download(`rtb-${item.report.as_of.slice(0, 10)}.txt`, reportText(item.report), 'text/plain;charset=utf-8');
    else download(`${id}.${action}`, JSON.stringify(action === 'geojson' ? item.report.geojson : item.report, null, 2), 'application/json');
  } catch { $('[data-report-preview]').hidden = false; $('[data-report-title]').textContent = 'Raport chwilowo niedostępny'; $('[data-report-body]').textContent = 'Spróbuj otworzyć go ponownie.'; }
}
function renderReports() {
  const host = $('[data-reports]'); host.replaceChildren();
  for (const r of history) {
    const row = el('article', 'r-report-row'), mark = el('span', 'r-report-icon'); const icon = el('i'); icon.dataset.lucide = 'files'; mark.append(icon);
    const info = el('div'); info.append(el('h3', '', `${r.report_type === 'daily' ? 'Raport dobowy' : 'Raport tygodniowy'} · ${fullTime(r.as_of)}`), el('p', 'r-small', `RTB ${r.score === null ? 'niewyliczony' : r.score + '/100'} · ${r.methodology_version}${r.supersedes ? ' · korekta' : ''}`));
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
  const available = new Set(records().map(i => i.id)); if (!available.has(state.selected)) { state.selected = null; state.related = []; }
  $('[data-source]').replaceChildren(); const all = el('option', '', 'Wszystkie źródła'); all.value = 'all'; $('[data-source]').append(all);
  for (const source of report()?.sources ?? []) { const option = el('option', '', source.name); option.value = source.id; $('[data-source]').append(option); }
  if (state.source !== 'all' && !(report()?.sources.some(s => s.id === state.source))) state.source = 'all';
  $('[data-source]').value = state.source;
  renderMetric(); renderTimeline(); renderJournal(); renderDetails();
  const points = mapPoints(report()), mapped = new Set(points.map(p => p.id)).size;
  $('[data-map-count]').textContent = `${mapped} na mapie · ${records().length - mapped} bez wskazanego miejsca`;
  maps.draw(); icons();
}
function navigate(page) {
  state.page = page; state.selected = null; state.related = [];
  for (const b of $$('[data-page]')) { if (b.dataset.page === page) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current'); }
  for (const view of $$('[data-view]')) view.hidden = view.dataset.view !== page;
  $('[data-page-title]').textContent = pages[page]; renderDetails(); maps.draw(); icons();
  if (page === 'reports') loadHistory();
}

const menu = $('[data-mobile-menu]'), menuToggle = $('[data-open-menu]'), mapDialog = $('[data-map-dialog]'); let mapOpener;
menu.id = 'rtb-mobile-menu';
const closeMenu = () => { menu.close(); menuToggle.setAttribute('aria-expanded', 'false'); menuToggle.focus({ preventScroll: true }); };
const maps = initializeMaps(root, report, () => state.selected, selectSignals, icons, b => { mapOpener = b; mapDialog.showModal(); maps.draw(); if (document.fullscreenEnabled) root.requestFullscreen?.().catch(() => {}); });
menuToggle.addEventListener('click', () => { menu.showModal(); menuToggle.setAttribute('aria-expanded', 'true'); });
$('[data-close-menu]').addEventListener('click', closeMenu);
menu.addEventListener('cancel', e => { e.preventDefault(); closeMenu(); });
menu.addEventListener('close', () => menuToggle.setAttribute('aria-expanded', 'false'));
$('[data-close-map]').addEventListener('click', () => mapDialog.close());
mapDialog.addEventListener('close', () => { if (document.fullscreenElement === root) document.exitFullscreen().catch(() => {}); maps.draw(); mapOpener?.focus({ preventScroll: true }); });
let wasFullscreen = false;
document.addEventListener('fullscreenchange', () => { if (document.fullscreenElement === root) { wasFullscreen = true; maps.draw(); } else if (wasFullscreen) { wasFullscreen = false; if (mapDialog.open) mapDialog.close(); } });
for (const dialog of [menu, mapDialog]) dialog.addEventListener('keydown', event => {
  if (event.key !== 'Tab') return;
  const controls = [...dialog.querySelectorAll('button:not(:disabled),a[href],select')].filter(e => e.getClientRects().length), first = controls[0], last = controls.at(-1);
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
});
matchMedia('(max-width:620px)').addEventListener('change', e => { if (!e.matches && menu.open) closeMenu(); });
for (const b of $$('[data-page]')) b.addEventListener('click', () => { navigate(b.dataset.page); if (menu.open) closeMenu(); });
for (const b of $$('[data-go]')) b.addEventListener('click', () => navigate(b.dataset.go));
for (const b of $$('[data-close-detail]')) b.addEventListener('click', () => { state.selected = null; state.related = []; renderDetails(); maps.draw(); });
$('[data-category]').addEventListener('change', e => { state.category = e.target.value; renderJournal(); });
$('[data-source]').addEventListener('change', e => { state.source = e.target.value; renderJournal(); });
$('[data-close-report]').addEventListener('click', () => { $('[data-report-preview]').hidden = true; });
$('[data-report-type]').addEventListener('change', e => { state.historyType = e.target.value; history = []; nextOffset = null; $('[data-report-preview]').hidden = true; loadHistory(); });
$('[data-more-reports]').addEventListener('click', () => loadHistory(true));

async function refresh() {
  if (busy) return; busy = true; $('[data-refresh]').disabled = true;
  try {
    const next = checkEnvelope(await api('/api/latest'));
    const changed = !loaded || next?.report.report_id !== envelope?.report.report_id;
    envelope = next; loaded = true; failed = false;
    if (changed) { render(); await loadHistory(); if (state.historyType !== 'daily') { const h = await api('/api/reports?type=daily'); dailyHistory = h.items; drawTrend(); } }
    else freshness();
  } catch { failed = true; loaded = true; if (!envelope) renderMetric(); else freshness(); }
  finally { busy = false; $('[data-refresh]').disabled = false; }
}
$('[data-refresh]').addEventListener('click', () => { refresh(); if (state.page === 'reports') loadHistory(); });
document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
new ResizeObserver(drawTrend).observe($('.r-analysis'));
render(); renderReports();
api('/api/config').then(value => { if (value.refresh_seconds >= 10 && value.stale_after_hours >= 1) config = value; }).catch(() => {});
await refresh();
// These reads refresh the screen, not the analysis pipeline. No scheduled jobs.
setInterval(() => { if (!document.hidden) refresh(); }, config.refresh_seconds * 1000);
