import { createSignalItem, prepareSignalDetail } from '../ui/components/signal-item.js';
import { reportRoute } from './report-presentation.js';
import { initializeReports } from './reports-view.js';
import { commentaryRows } from './commentary.js';
import { createIcons, Radar, Menu, X, LayoutDashboard, Map as MapIcon, ListFilter, Files, ArrowUpRight, ArrowRight, TrendingUp, TrendingDown, Minus, Plus, Scan, Maximize, CircleDot, Flag, Flame, Landmark, TrainFront, Plane, ShieldAlert, Satellite, Newspaper, ChevronDown, ChevronUp, Coffee } from 'lucide';
import { select, scaleLinear } from 'd3';
import { historyDays, canJoinDays, ReportHistory, SnapshotSelection } from './index-history.js';
import { categories, statuses, sourceStatuses, scoreLabel, threatLevel, visibleWarnings, fullTime, shortDate, dateKey, isoWeek, parts, signalCount, timelineGroups, checkEnvelope, safeLink } from './data.js';
import { signalTime } from './signal-time.js';
import { journalDays, journalClock, journalCaution } from './journal.js';
import { signalTimeText } from './data.js';
import { initializeMaps } from './map.js';
import { eventAreas, mappedSignalIds, areaLocationNote } from './map-geography.js';
import { topics, regions, kinds, presentation, regionLabel, filterSignals, topicCounts, periodRange, mapReport, SignalArchive, WEEK } from './signals.js';

const root = document.querySelector('#rtb-dashboard');
const $ = s => root.querySelector(s), $$ = s => [...root.querySelectorAll(s)];
const icons = () => createIcons({ icons: { Radar, Menu, X, LayoutDashboard, Map: MapIcon, ListFilter, Files, ArrowUpRight, ArrowRight, TrendingUp, TrendingDown, Minus, Plus, Scan, Maximize, CircleDot, Flag, Flame, Landmark, TrainFront, Plane, ShieldAlert, Satellite, Newspaper, ChevronDown, ChevronUp, Coffee }, attrs: { width: 16, height: 16, 'aria-hidden': 'true' } });
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
const button = (text, action, cls = 'r-button') => { const b = el('button', cls, text); b.type = 'button'; b.addEventListener('click', action); return b; };
const pages = { overview: 'Przegląd', map: 'Mapa Operacyjna', journal: 'Dziennik Sygnałów', reports: 'Raporty' };
const state = { page: 'overview', selected: null, related: [], scale: 'day', expanded: new Set(), category: 'all', source: 'all', area: 'macro', mapArea: 'macro', mapPeriod: 'day', mapTopic: 'all', journalArea: 'macro', journalPeriod: 'all' };
try { const saved = localStorage.getItem('rta-region'); if (Object.hasOwn(regions, saved)) state.area = state.mapArea = state.journalArea = saved; } catch {}
let archive = null, detailOpener = null, expandedFrom = 'overview', topicReturn = null;
let envelope = null, latestEnvelope = null, loaded = false, failed = false, busy = false, reportView;
const reportHistory = new ReportHistory(api);
const historical = () => Boolean(envelope && latestEnvelope && envelope.report.report_id !== latestEnvelope.report.report_id);
const selection = new SnapshotSelection(id => reportHistory.get(id), value => {
  if (value.report.mode !== latestEnvelope?.report.mode || Date.parse(value.report.as_of) > Date.parse(latestEnvelope.report.as_of)) throw new Error('invalid_snapshot');
  activateReport(value);
}, () => drawTrend());
let config = { refresh_seconds: 30, stale_after_hours: 30 };
const report = () => envelope?.report ?? null;
const records = () => archive?.records ?? report()?.incidents ?? [];
const scoped = () => report() ? filterSignals(records(), { asOf: report().as_of, area: state.area }) : [];
const mapRecords = () => report() ? filterSignals(records(), { asOf: report().as_of, area: state.mapArea, period: state.mapPeriod, topic: state.mapTopic }) : [];
const journalRecords = () => report() ? filterSignals(records(), { asOf: report().as_of, area: state.journalArea, period: state.journalPeriod, topic: state.category, source: state.source }) : [];
const shownMap = slot => { const view = slot === 'expanded' ? expandedFrom : slot; return mapReport(report(), view === 'overview' ? (report() ? filterSignals(records(), { asOf: report().as_of, area: state.area, period: state.scale }) : []) : mapRecords()); };
$('.r-main').id = 'main';
$('.r-overview').prepend($('.r-context'));
root.dataset.page = 'overview';
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const journalMobile = matchMedia('(max-width: 620px)');
let journalFiltersOpen = false;
function showJournalFilters() {
  const show = !journalMobile.matches || journalFiltersOpen;
  $('#journal-filters').hidden = !show;
  $('[data-journal-filter-toggle]').setAttribute('aria-expanded', String(show));
}
$('[data-journal-filter-toggle]').addEventListener('click', () => { journalFiltersOpen = !journalFiltersOpen; showJournalFilters(); });
journalMobile.addEventListener('change', showJournalFilters); showJournalFilters();
const historyToggle = $('[data-history-toggle]'), historyFrame = $('.r-history-frame');
historyFrame.hidden = matchMedia('(max-width: 760px)').matches;
historyToggle.setAttribute('aria-expanded', String(!historyFrame.hidden));
historyToggle.addEventListener('click', () => {
  historyFrame.hidden = !historyFrame.hidden;
  historyToggle.setAttribute('aria-expanded', String(!historyFrame.hidden));
  drawTrend();
});
const notice = el('p', 'r-data-notice'); notice.setAttribute('role', 'status'); $('.r-hero').after(notice);
const official = el('section', 'r-official-warnings'); official.setAttribute('aria-label', 'Oficjalne ostrzeżenia'); $('.r-hero').before(official);
const coverage = el('details', 'r-coverage'); $('.r-bottom-line').before(coverage);
for (const panel of $$('[data-detail]')) panel.append($('template[data-template=detail]').content.cloneNode(true));
const overviewDetail = $('[data-detail=overview]'); overviewDetail.id = 'overview-signal-detail';
const mapDetail = $('[data-detail=map]'); mapDetail.id = 'map-signal-detail';
const journalDetail = $('[data-detail=journal]'); journalDetail.id = 'journal-signal-detail';
const inlineDetails = [overviewDetail, mapDetail, journalDetail];
for (const panel of inlineDetails) prepareSignalDetail(panel, { compact: panel !== journalDetail });
const journalReturn = button('← Wróć do Przeglądu', () => navigate('overview'), 'r-link r-journal-return');
journalReturn.hidden = true; $('[data-view=journal]').prepend(journalReturn);
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
  if (r && !historical() && Date.now() - Date.parse(r.as_of) > config.stale_after_hours * 3600000) texts.push('Ten raport nie przedstawia bieżącej sytuacji. Sprawdź datę ostatniej analizy.');
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
  $('[data-as-of]').textContent = r ? `${historical() ? 'Raport z' : 'Stan na'} ${fullTime(r.as_of)}` : failed ? 'Odczyt chwilowo niedostępny' : loaded ? 'Brak opublikowanego raportu' : 'Ładowanie raportu…';
  $('[data-latest-report]').hidden = !historical();
  root.dataset.reportId = r?.report_id ?? '';
  root.dataset.reportDate = r?.as_of ?? '';
  $('.r-metric .r-eyebrow').textContent = `Indeks RTA · ${regional ? regions[state.area] : 'raport dobowy'}`;
  $('[data-region]').value = state.area;
  $('[data-confidence]').textContent = regional ? 'Nieustalona dla regionu' : r?.rtb.confidence.percent == null ? 'Nieokreślona' : `${r.rtb.confidence.percent}%`;
  $('.r-confidence').title = 'Pewność opisuje zakres obserwacji, ukończony przegląd i dostępność historii. Nie jest prawdopodobieństwem eskalacji.';
  const status = $('[data-score-status]');
  status.textContent = r && score === null ? 'Za mało danych do wyliczenia indeksu' : !regional && r?.rtb.review_required ? 'Wzrost indeksu wymaga pogłębionej oceny sytuacji' : score === 0 ? 'Brak naliczonych sygnałów. Zero nie potwierdza bezpieczeństwa.' : r?.rtb.status === 'provisional' ? 'Ocena oparta na częściowych obserwacjach' : '';
  if (score > 60 && metric.red_priority?.eligible === false) status.textContent += ' Brakuje niezależnych potwierdzeń bezpośrednich zdarzeń, by nadać najwyższy priorytet.';
  // Routine coverage detail belongs in the disclosure. Keep zero, missing
  // scores and review warnings visible without requiring that interaction.
  if (status.textContent && (score === null || score === 0 || r?.rtb.review_required || score > 60)) $('.r-index-details').before(status);
  else $('.r-index-details').append(status);
  for (const b of $$('[data-component]')) b.textContent = score === null ? '—' : `${scoreLabel(metric.components[b.dataset.component])} pkt`;
  $('[data-regional-note]').textContent = regional ? 'Wynik obejmuje zdarzenia lokalne i wpływ z sąsiednich regionów. Pewność regionalna nie została jeszcze oszacowana.' : 'Indeks uwzględnia ocenę zdarzeń i upływ czasu; nie jest sumą sygnałów na mapie.';
  official.replaceChildren(); official.hidden = !visibleWarnings(r?.rtb).length;
  for (const w of visibleWarnings(r?.rtb)) {
    const article = el('article'); article.dataset.shelter = String(w.level === 'L3_shelter');
    article.append(el('strong', '', historical() ? 'Komunikat zapisany w tym raporcie' : w.level === 'L3_shelter' ? 'Oficjalne zalecenie ochronne' : 'Oficjalny komunikat'), el('p', '', w.instruction_pl),
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

let chartSignature = '';
function drawTrend() {
  const host = $('[data-index-history]'), target = $('.r-index-chart'), svg = select(target);
  const status = $('[data-history-status]');
  status.textContent = selection.pending ? 'Wczytywanie raportu…' : selection.failed ? 'Nie udało się otworzyć raportu. Spróbuj ponownie.' : reportHistory.failed ? 'Część historii jest chwilowo niedostępna.' : '';
  status.hidden = !status.textContent;
  $('.r-hero').setAttribute('aria-busy', String(Boolean(selection.pending)));
  host.hidden = !latestEnvelope;
  if (!latestEnvelope || state.page !== 'overview') return;
  const r = report(), focused = document.activeElement?.closest('[data-history-report]')?.dataset.historyReport;
  const days = historyDays(reportHistory.rows, latestEnvelope.report.as_of, reportHistory.cache, state.area);
  $('[data-selected-day]').textContent = r ? new Intl.DateTimeFormat('pl-PL', { timeZone: 'Europe/Warsaw', day: 'numeric', month: 'long' }).format(new Date(r.as_of)) : '';
  const w = target.clientWidth, h = target.clientHeight;
  if (w < 10 || h < 10) return;
  const signature = JSON.stringify([r?.report_id, state.area, w, h, $('.r-history-scroll').clientWidth, days]);
  // Archive updates must not keep restarting the selected point's pulse.
  if (signature === chartSignature) return;
  chartSignature = signature;
  const left = 40, right = 8, step = (w - left - right) / days.length;
  const x = i => left + step * (i + .5), y = scaleLinear().domain([0, 100]).range([h - 12, 12]);
  svg.selectAll('*').remove(); svg.attr('viewBox', `0 0 ${w} ${h}`);
  svg.append('title').text(days.filter(d => d.row).map(d => `${shortDate(d.day)}: ${d.score === null ? 'brak wyniku' : scoreLabel(d.score)}`).join('; '));
  const axis = $('.r-history-axis-labels'); axis.replaceChildren();
  for (const tick of [0, 50, 100]) {
    svg.append('line').attr('class', 'r-history-grid').attr('x1', left).attr('x2', w - right).attr('y1', y(tick)).attr('y2', y(tick));
    const label = el('span', '', String(tick)); label.style.top = `${y(tick)}px`; axis.append(label);
  }
  days.forEach((day, i) => {
    if (i && canJoinDays(days[i - 1], day)) svg.append('path').attr('class', 'r-history-line').attr('d', `M${x(i - 1)},${y(days[i - 1].score)}L${x(i)},${y(day.score)}`);
    if (day.score === null) return;
    const active = day.row.report_id === r?.report_id;
    if (active) {
      svg.append('line').attr('class', 'r-history-guide').attr('x1', x(i)).attr('x2', x(i)).attr('y1', 0).attr('y2', h);
      svg.append('circle').attr('class', 'r-history-pulse').attr('data-tone', day.tone).attr('cx', x(i)).attr('cy', y(day.score)).attr('r', 9);
      svg.append('circle').attr('class', 'r-history-halo').attr('data-tone', day.tone).attr('cx', x(i)).attr('cy', y(day.score)).attr('r', 8);
    }
    svg.append('circle').attr('class', 'r-history-dot').attr('data-tone', day.tone).attr('data-selected', active).attr('cx', x(i)).attr('cy', y(day.score)).attr('r', active ? 4 : 3.5);
  });
  const controls = $('.r-history-points'); controls.replaceChildren();
  for (const [index, day] of days.entries()) {
    const control = day.row ? button('', () => selection.choose(day.row.report_id), 'r-history-day') : el('span', 'r-history-gap');
    control.style.left = `${left + index * step}px`; control.style.width = `${step}px`;
    control.append(el('span', 'r-history-day-label', shortDate(day.day)));
    if (day.row) {
      const value = day.score === null ? 'Indeks niewyliczony' : `RTA ${scoreLabel(day.score)}`;
      control.dataset.historyReport = day.row.report_id;
      control.setAttribute('aria-label', `${fullTime(day.row.as_of)} · ${value}. Otwórz raport.`);
      control.setAttribute('aria-pressed', String(day.row.report_id === r?.report_id));
      control.append(el('span', 'r-history-value', `${shortDate(day.day)} · ${value}`));
      control.addEventListener('keydown', event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        const buttons = [...controls.querySelectorAll('button')], i = buttons.indexOf(control);
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : Math.max(0, Math.min(buttons.length - 1, i + (event.key === 'ArrowLeft' ? -1 : 1)));
        buttons[next]?.focus();
      });
    } else control.setAttribute('aria-label', `${shortDate(day.day)}: brak raportu`);
    controls.append(control);
  }
  if (focused) controls.querySelector(`[data-history-report="${focused}"]`)?.focus({ preventScroll: true });
  const scroll = $('.r-history-scroll');
  const positionKey = `${r?.report_id}:${scroll.clientWidth}`;
  if (scroll.dataset.positioned !== positionKey) {
    const i = days.findIndex(day => day.row?.report_id === r?.report_id);
    if (i >= 0) {
      const start = left + i * step, end = start + step;
      if (start < scroll.scrollLeft + left) scroll.scrollLeft = Math.max(0, start - left);
      else if (end > scroll.scrollLeft + scroll.clientWidth - right) scroll.scrollLeft = end - scroll.clientWidth + right;
      scroll.dataset.positioned = positionKey;
    }
  }
}

function selectSignals(ids, opener = null) {
  if (ids.length === 1 && ids[0] === state.selected && opener) { detailOpener = opener; closeDetails(); return; }
  if (opener || !document.activeElement?.closest('[data-detail]')) detailOpener = opener ?? document.activeElement;
  state.selected = ids[0]; state.related = ids;
  renderDetails();
  if (state.page === 'map' && !mapDialog.open) maps.reveal(state.selected, 'operational');
  maps.draw(); icons();
  const panel = $(`[data-detail="${mapDialog.open ? 'expanded' : state.page}"]`);
  if (!mapDialog.open) {
    const trigger = $(`[data-view="${state.page}"] .r-signal-toggle[aria-expanded=true]`);
    if (trigger) {
      trigger.focus({ preventScroll: true });
      trigger.scrollIntoView({ block: 'nearest', behavior: 'instant' });
      return;
    }
  }
  const heading = panel?.querySelector('h3');
  if (heading && !heading.hidden) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); if (!mapDialog.open) panel.scrollIntoView({ block: 'nearest', behavior: 'instant' }); }
}
function clearSelection() { state.selected = null; state.related = []; }
function closeDetails() {
  const signal = state.selected, marker = detailOpener?.dataset.pointIds, area = detailOpener?.dataset.areaId;
  clearSelection(); renderDetails(); maps.draw();
  const fallback = marker ? $$('[data-point-ids]').find(b => b.dataset.pointIds === marker && b.getClientRects().length) : area ? $$('[data-area-id]').find(b => b.dataset.areaId === area && b.getClientRects().length) : $$('button[data-signal-id]').find(b => b.dataset.signalId === signal && b.getClientRects().length);
  (detailOpener?.isConnected ? detailOpener : fallback)?.focus({ preventScroll: state.page !== 'journal' });
}
function renderDetails() {
  const event = records().find(e => e.id === state.selected);
  const previous = overviewDetail.dataset.eventId, previousMap = mapDetail.dataset.eventId, previousJournal = journalDetail.dataset.eventId;
  overviewDetail.dataset.eventId = event?.id ?? '';
  mapDetail.dataset.eventId = event?.id ?? '';
  journalDetail.dataset.eventId = event?.id ?? '';
  $('[data-timeline]').hidden = false;
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
    let cityNote = panel.querySelector('[data-city-note]');
    if (!cityNote) { cityNote = el('p', 'r-small'); cityNote.dataset.cityNote = ''; panel.querySelector('[data-detail-summary]').after(cityNote); }
    const anchor = presentation(event).map_anchor; cityNote.hidden = !anchor; cityNote.replaceChildren();
    if (anchor) {
      cityNote.append(document.createTextNode(`Punkt wskazuje miasto ${anchor.label}, nie dokładne miejsce zdarzenia. `));
      const href = safeLink(anchor.reference_url);
      if (href) { const a = el('a', 'r-source-link', 'Źródło położenia miasta'); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; cityNote.append(a); }
    }
    const areaNote = areaLocationNote(event);
    if (areaNote) { cityNote.hidden = false; cityNote.textContent = areaNote; }
    const sources = panel.querySelector('[data-detail-source]'); sources.replaceChildren();
    if (inlineDetails.includes(panel)) {
      const publishers = new Map();
      for (const source of event.sources) {
        const href = safeLink(source.url); if (!href) continue;
        if (!publishers.has(source.publisher)) publishers.set(source.publisher, new Set());
        publishers.get(source.publisher).add(href);
      }
      for (const [publisher, urls] of publishers) {
        const group = el('div', 'r-signal-source-group');
        if (urls.size > 1) group.append(el('span', '', publisher));
        const links = el('div', 'r-signal-source-links'); let index = 0;
        for (const href of urls) {
          const a = el('a', 'r-source-link', urls.size > 1 ? `Materiał ${++index}` : publisher);
          a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer';
          if (urls.size > 1) a.setAttribute('aria-label', `${publisher} — materiał ${index}`);
          links.append(a);
        }
        group.append(links); sources.append(group);
      }
    } else for (const source of event.sources) {
      const href = safeLink(source.url); if (!href) continue;
      const a = el('a', 'r-source-link', source.publisher); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; sources.append(a);
    }
    let date = panel.querySelector('[data-event-date]'); if (!date) { date = el('p', 'r-small'); date.dataset.eventDate = ''; panel.querySelector('dl').after(date); }
    date.textContent = `Data zdarzenia: ${event.occurred_on ?? 'nieustalona'}.`;
    if (inlineDetails.includes(panel)) {
      panel.querySelector('.r-signal-detail-copy').append(date);
      cityNote.hidden = true; // Geography qualifiers stay with the map; location precision remains in the facts.
      date.textContent = signalTime(event).basis === 'measurement' ? `Dzień pomiaru: ${event.occurred_on} (UTC).` : date.textContent;
    }
    const choices = panel.querySelector('[data-cluster-choices]'); choices.replaceChildren(); choices.hidden = state.related.length < 2;
    for (const id of state.related) { const other = records().find(e => e.id === id); if (!other) continue; const b = button(other.title, () => selectSignals([id, ...state.related.filter(x => x !== id)])); b.setAttribute('aria-pressed', String(event.id === id)); choices.append(b); }
  }
  for (const [selector, detail] of [['[data-timeline]', overviewDetail], ['[data-map-list]', mapDetail], ['[data-journal]', journalDetail]]) {
    for (const b of $$(`${selector} .r-signal-toggle`)) {
      const selected = b.dataset.signalId === event?.id;
      b.setAttribute('aria-expanded', String(selected));
      b.closest('.r-signal-disclosure').dataset.selected = String(selected);
      if (!selected) continue;
      const items = b.closest('.r-time-items');
      if (items?.hidden) {
        items.hidden = false;
        const toggle = items.previousElementSibling;
        state.expanded.add(toggle.dataset.group); toggle.setAttribute('aria-expanded', 'true');
        toggle.querySelector('.r-time-action').textContent = 'Zwiń';
      }
      b.after(detail); detail.setAttribute('aria-labelledby', b.id);
    }
  }
  const activeDetail = state.page === 'journal' ? journalDetail : state.page === 'map' ? mapDetail : overviewDetail;
  const previousEvent = state.page === 'journal' ? previousJournal : state.page === 'map' ? previousMap : previous;
  if (event && previousEvent !== event.id && ['map', 'overview', 'journal'].includes(state.page) && !mapDialog.open && !reducedMotion.matches) {
    activeDetail.getAnimations().forEach(a => a.cancel());
    const frames = state.page !== 'overview'
      ? [{ opacity: 0, transform: 'translateY(4px)' }, { opacity: 1, transform: 'translateY(0)' }]
      : [{ height: '0px', opacity: 0 }, { height: `${activeDetail.offsetHeight}px`, opacity: 1 }];
    activeDetail.animate(frames, { duration: 280, easing: 'cubic-bezier(.22,.61,.36,1)' });
  }
}

function renderTimeline() {
  // The one details panel moves with its row, but survives archive rerenders.
  $('.r-context').append(overviewDetail);
  const host = $('[data-timeline]'), r = report(); host.replaceChildren();
  const head = el('div', 'r-section-heading r-timeline-heading'); head.append(el('h2', '', 'Oś czasu')); host.append(head);
  const toggles = el('div', 'r-time-scale'); toggles.setAttribute('aria-label', 'Skala osi czasu');
  for (const [scale, label] of [['day', 'Dzień'], ['week', 'Tydzień'], ['month', 'Miesiąc']]) {
    const b = button(label, () => { state.scale = scale; clearSelection(); renderTimeline(); renderDetails(); maps.draw(); ensureArchive(); host.querySelector(`[data-scale=${scale}]`)?.focus(); }, ''); b.dataset.scale = scale; b.setAttribute('aria-pressed', String(state.scale === scale)); toggles.append(b);
  }
  head.append(toggles);
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
      if (state.scale === 'day' && events.length === 1) { row.append(timelineSignal(events[0])); rail.append(row); continue; }
      const group = `${state.scale}:${key}`, expanded = state.expanded.has(group), content = el('div');
      const counts = Object.entries(topics).map(([id, c]) => ({ label: c.label, count: events.filter(e => presentation(e).topics.includes(id)).length })).filter(c => c.count).sort((a, b) => b.count - a.count);
      const title = state.scale === 'day' && events.length === 1 ? events[0].title : signalCount(events.length);
      const open = button('', () => {
        if (state.expanded.has(group)) { state.expanded.delete(group); if (events.some(e => e.id === state.selected)) clearSelection(); }
        else state.expanded.add(group);
        renderTimeline(); renderDetails(); maps.draw(); host.querySelector(`[data-group="${group}"]`)?.focus();
      }, 'r-time-button');
      open.dataset.group = group; open.setAttribute('aria-expanded', String(expanded)); open.setAttribute('aria-controls', `group-${group}`);
      open.append(el('span', 'r-time-title', title), el('span', 'r-time-subtitle', state.scale === 'month' ? 'Dominujące: ' + counts.filter(c => c.count === counts[0]?.count).map(c => c.label).join(', ') : counts.map(c => `${c.count}× ${c.label}`).join(' · ')), el('span', 'r-time-action', expanded ? 'Zwiń' : 'Rozwiń'));
      const badges = el('span', 'r-badges'); for (const label of [...new Set(events.map(regionLabel))]) badges.append(el('span', 'r-region-badge', label)); open.append(badges);
      const items = el('div', 'r-time-items'); items.id = `group-${group}`; items.hidden = !expanded;
      for (const event of events) items.append(timelineSignal(event));
      content.append(open, items); row.append(content);
    }
    rail.append(row);
  }
  const foot = el('div', 'r-timeline-footer'); foot.append(el('span', 'r-small', 'Według publikacji i dni pomiarów'), button('Zobacz w dzienniku', () => { state.journalArea = state.area; state.journalPeriod = state.scale; state.category = state.source = 'all'; navigate('journal'); }, 'r-link')); host.append(foot);
  const undated = scoped().filter(r => !signalTime(r).value).length;
  if (undated) host.append(el('p', 'r-small', `${signalCount(undated)} bez ustalonej daty znajdziesz w dzienniku.`));
}

function timelineSignal(event) {
  return createSignalItem({
    id: `overview-entry-${event.id}`, signalId: event.id, controls: overviewDetail.id,
    title: event.title, compact: true,
    after: [el('span', 'r-region-badge', regionLabel(event)),
      el('span', 'r-signal-meta', `${presentation(event).topics.map(t => topics[t].label).join(' · ')} · ${[...new Set(event.sources.map(s => s.publisher))].join(' · ')}`)],
    onToggle: trigger => selectSignals([event.id], trigger),
  }).row;
}
function areaSummary(filtered, area) {
  if (!regions[area]) return signalCount(filtered.length);
  const national = filtered.filter(e => presentation(e).scope === 'national' && e.country === 'PL').length;
  return `Lokalne: ${filtered.length - national} · ogólnopolskie: ${national}`;
}
function renderJournal() {
  const filtered = journalRecords(), host = $('[data-journal]');
  $('[data-journal-count]').textContent = areaSummary(filtered, state.journalArea);
  $('[data-journal-period-note]').textContent = periodCaption(state.journalPeriod) + ' · publikacje i pomiary';
  const active = [['[data-journal-area]', 'macro'], ['[data-journal-period]', 'all'], ['[data-category]', 'all'], ['[data-source]', 'all']]
    .filter(([selector, value]) => $(selector).value !== value).map(([selector]) => $(selector).selectedOptions[0]?.textContent).filter(Boolean);
  $('[data-journal-filter-count]').textContent = active.length ? `· ${active.length}` : '';
  $('[data-journal-active-filters]').hidden = !active.length;
  $('[data-journal-active-filters]').textContent = active.join(' · ');
  $('[data-view=journal]').append(journalDetail); host.replaceChildren();
  for (const group of journalDays(filtered)) {
    const section = el('section', 'r-journal-day'), heading = el('div', 'r-journal-day-heading');
    const title = el('h2', '', group.label); title.id = `journal-day-${group.day || 'undated'}`;
    section.setAttribute('aria-labelledby', title.id); section.dataset.day = group.day || 'undated';
    heading.append(title, el('span', '', signalCount(group.events.length))); section.append(heading);
    for (const event of group.events) {
      const time = el('time', '', journalClock(event)), t = signalTime(event);
      if (t.value) time.dateTime = t.precision === 'day' ? t.day : t.value;
      time.title = signalTimeText(event); time.setAttribute('aria-label', t.value ? signalTimeText(event) : 'Data nieustalona');
      const p = presentation(event), meta = el('span', 'r-signal-meta');
      for (const value of [p.topics.map(t => topics[t].label).join(', '), kinds[p.kind], regionLabel(event), [...new Set(event.sources.map(s => s.publisher))].join(', ')].filter(Boolean)) meta.append(el('span', '', value));
      const after = [meta], caution = journalCaution(event);
      if (caution) after.push(el('span', 'r-signal-caution', caution));
      section.append(createSignalItem({
        id: `journal-entry-${event.id}`, signalId: event.id, controls: journalDetail.id,
        title: event.title, icon: topics[p.topics[0]]?.icon ?? 'newspaper', clock: time, after,
        onToggle: trigger => selectSignals([event.id], trigger),
      }).row);
    }
    host.append(section);
  }
  if (!filtered.length) host.append(el('p', 'r-empty', archive?.loading ? 'Wczytywanie sygnałów…' : 'Brak sygnałów dla wybranych filtrów.'));
}
function renderOperational() {
  const filtered = mapRecords(), mapped = mappedSignalIds(mapReport(report(), filtered));
  $('[data-map-count]').textContent = areaSummary(filtered, state.mapArea);
  $('[data-map-period-note]').textContent = periodCaption(state.mapPeriod);
  $('[data-map-location-count]').textContent = `${mapped.size} na mapie · ${filtered.length - mapped.size} bez lokalizacji na mapie`;
  const host = $('[data-map-list]');
  $('[data-map-list-body]').append(mapDetail); host.replaceChildren();
  for (const event of filtered) {
    const p = presentation(event), date = signalTime(event);
    const meta = el('span', 'r-signal-meta', `${date.value ? shortDate(date.day ?? dateKey(date.value)) : 'Bez daty'} · ${kinds[p.kind]}`);
    meta.title = signalTimeText(event);
    const location = el('span', 'r-signal-meta', regionLabel(event));
    const areas = eventAreas(event);
    if (areas.length) location.textContent = areas.map(a => a.feature.properties.label).join(', ') + (areas.some(a => a.context) ? ' · orientacyjnie' : '');
    if (!mapped.has(event.id)) location.textContent += ' · bez zaznaczenia';
    const { row } = createSignalItem({
      id: `map-entry-${event.id}`, signalId: event.id, controls: mapDetail.id,
      title: event.title, icon: topics[p.topics[0]]?.icon ?? 'newspaper', compact: true,
      before: [meta], after: [location], onToggle: trigger => selectSignals([event.id], trigger),
    });
    row.classList.add('r-map-signal'); host.append(row);
  }
  if (!filtered.length) host.append(el('p', 'r-empty', archive?.loading ? 'Wczytywanie sygnałów…' : 'Brak sygnałów dla wybranych filtrów.'));
}

reportView = initializeReports(root, api, () => state.page === 'reports');

function render() {
  const available = new Set(records().map(i => i.id)); if (!available.has(state.selected)) clearSelection();
  const sources = new Map((report()?.sources ?? []).map(s => [s.id, s.name]));
  for (const e of records()) for (const s of e.sources) sources.set(s.source_id, s.publisher);
  setOptions($('[data-source]'), [['all', 'Wszystkie'], ...sources], state.source);
  renderFilters(); renderMetric(); renderTopicCounts(); renderTimeline(); renderJournal(); renderOperational(); renderDetails();
  maps.draw(); icons();
}
function navigate(page) {
  const returnToTopic = page === 'overview' && state.page === 'journal' ? topicReturn : null;
  if (page !== 'journal') topicReturn = null;
  journalReturn.hidden = page !== 'journal' || !topicReturn;
  $('.r-hero').hidden = page !== 'overview';
  $('[data-overview-area]').hidden = page !== 'overview';
  if (state.page === 'reports' && page !== 'reports') reportView.leave();
  state.page = page; root.dataset.page = page; state.selected = null; state.related = [];
  for (const b of $$('[data-page]')) { if (b.dataset.page === page) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current'); }
  for (const view of $$('[data-view]')) view.hidden = view.dataset.view !== page;
  $('[data-page-title]').textContent = pages[page]; render(); ensureArchive();
  if (page === 'reports') reportView.open();
  if (returnToTopic && returnToTopic.reportId === report()?.report_id) {
    window.scrollTo({ top: returnToTopic.scrollY, behavior: 'instant' });
    $(`[data-topic="${returnToTopic.topic}"]`)?.focus({ preventScroll: true });
    return;
  }
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
$('[data-latest-report]').addEventListener('click', async () => {
  if (!latestEnvelope) return;
  await selection.choose(latestEnvelope.report.report_id);
  if (!historical()) { $('[data-page-title]').tabIndex = -1; $('[data-page-title]').focus({ preventScroll: true }); }
});

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
  setOptions($('[data-region]'), [['macro', 'Cały obszar'], ...Object.entries(regions)], state.area);
  for (const view of ['map', 'journal']) {
    const topic = view === 'map' ? state.mapTopic : state.category, period = state[view + 'Period'];
    const values = [['macro', 'Flanka wschodnia'], ['PL', 'Cała Polska'], ...Object.entries(regions).map(([id, name]) => [id, `${name} (${report() ? filterSignals(records(), { asOf: report().as_of, area: id, period, topic, source: view === 'journal' ? state.source : 'all', includeNational: false }).length : 0})`])];
    setOptions($(`[data-${view}-area]`), values, state[view + 'Area']);
    const labels = historical() ? periods.map(([key, name]) => [key, ({ day: 'Wybrany dzień', week: 'Tydzień raportu', month: 'Miesiąc raportu', quarter: 'Kwartał raportu', year: 'Rok raportu' })[key] ?? name]) : periods;
    setOptions($(`[data-${view}-period]`), view === 'journal' ? [['all', 'Całe archiwum'], ...labels] : labels, period);
  }
  setOptions($('[data-map-topic]'), [['all', 'Wszystkie'], ...Object.entries(topics).map(([key, value]) => [key, value.label])], state.mapTopic);
  $('[data-category]').value = state.category;
}
function renderTopicCounts() {
  const focusedTopic = document.activeElement?.closest('[data-topic]')?.dataset.topic;
  const host = $('[data-topic-counts]'); host.replaceChildren();
  $('[data-count-period]').textContent = report() ? periodCaption('current7') : '';
  $('[data-count-note]').textContent = archive?.loading ? 'Wczytywanie historii…' : archive?.failed ? 'Nie udało się pobrać całej historii. Liczby mogą być niepełne.' : 'Liczba zapisanych sygnałów, nie liczba ataków.';
  if (!report()) return;
  const counts = topicCounts(records(), [...(archive?.reports.values() ?? [report()])], report().as_of, state.area, { failed: archive?.failed, loading: archive?.loading, earliestLoaded: archive?.earliestLoaded });
  for (const item of counts) {
    const b = button('', () => {
      topicReturn = { topic: item.topic, scrollY: window.scrollY, reportId: report().report_id };
      state.journalArea = state.area; state.category = item.topic; state.source = 'all'; state.journalPeriod = 'current7';
      navigate('journal');
    }, 'r-topic-button');
    b.dataset.topic = item.topic;
    const icon = el('i'); icon.dataset.lucide = topics[item.topic].icon;
    const content = el('span', 'r-topic-content'), label = el('span', 'r-topic-label', topics[item.topic].label), numbers = el('span', 'r-topic-numbers');
    const delta = item.delta == null ? null : item.delta > 0 ? `↑ ${item.delta} więcej` : item.delta < 0 ? `↓ ${Math.abs(item.delta)} mniej` : '— bez zmian';
    numbers.append(el('strong', 'r-topic-number', String(item.current.length)));
    if (delta !== null) numbers.append(el('span', 'r-small', delta));
    content.append(label, numbers); const arrow = el('i', 'r-topic-arrow'); arrow.dataset.lucide = 'arrow-right'; b.append(icon, content, arrow);
    b.setAttribute('aria-label', `${topics[item.topic].label}: ${signalCount(item.current.length)}.${delta !== null ? ` ${delta}.` : ''} Otwórz Dziennik Sygnałów.`);
    if (item.delta !== null) b.title = `Poprzednie 7 dni: ${item.previous.length}. ${periodCaption('previous7')}`;
    host.append(b);

  }
  if (counts.some(item => item.delta !== null)) $('[data-count-note]').append(document.createTextNode(' Porównanie z poprzednimi 7 dniami.'));
  if (report().sources.some(s => s.status !== 'current')) $('[data-count-note]').append(document.createTextNode(' Dane częściowe.'));
  if (focusedTopic) host.querySelector(`[data-topic="${focusedTopic}"]`)?.focus({ preventScroll: true });
}
function renderCommentary() {
  const host = $('[data-commentary]'); host.replaceChildren();
  const rows = commentaryRows(report(), state.area, records());
  host.closest('.r-analysis').hidden = !rows.length;
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

function activateReport(value) {
  if (topicReturn?.reportId !== value?.report.report_id) { topicReturn = null; journalReturn.hidden = true; }
  archive?.dispose(); envelope = value;
  state.selected = null; state.related = []; state.expanded.clear();
  archive = value ? new SignalArchive(value, path => reportHistory.read(path), () => { if (archive?.envelope === value) render(); }) : null;
  render(); ensureArchive();
}

async function refresh() {
  if (busy) return; busy = true;
  try {
    const next = checkEnvelope(await api('/api/latest'));
    if (!next && latestEnvelope) throw new Error('latest_missing');
    // Polls update the available latest report without interrupting a user's
    // historical selection or an in-flight choice of date.
    const followLatest = !historical() && !selection.pending && !topicReturn;
    const changed = !loaded || next?.report.report_id !== latestEnvelope?.report.report_id;
    latestEnvelope = next; reportHistory.remember(next); loaded = true; failed = false;
    if (changed) {
      if (followLatest || !envelope) activateReport(next);
      else renderMetric();
      if (next) reportHistory.load(next, drawTrend);
      reportView.refresh(); }
    else freshness();
  } catch { failed = true; loaded = true; if (!envelope) renderMetric(); else freshness(); }
  finally { busy = false; }
}
document.addEventListener('visibilitychange', () => { root.dataset.pageHidden = String(document.hidden); if (!document.hidden) refresh(); });
new ResizeObserver(drawTrend).observe($('.r-hero'));
render();
window.addEventListener('hashchange', () => { if (reportRoute(location.hash) || location.hash === '#raporty') navigate('reports'); });
if (reportRoute(location.hash) || location.hash === '#raporty') navigate('reports');
api('/api/config').then(value => { if (value.refresh_seconds >= 10 && value.stale_after_hours >= 1) config = value; }).catch(() => {});
await refresh();
// These reads refresh the screen, not the analysis pipeline. No scheduled jobs.
setInterval(() => { if (!document.hidden) refresh(); }, config.refresh_seconds * 1000);
