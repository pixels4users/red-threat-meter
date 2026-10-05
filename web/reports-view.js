import { checkEnvelope, dateKey, parts, scoreLabel } from './data.js';
import { buildReportPresentation, reportPresentationText, reportHref, reportRoute } from './report-presentation.js';
import { renderReportContent } from './report-content.js';

const dayLabel = value => new Intl.DateTimeFormat('pl-PL', { timeZone: 'Europe/Warsaw', day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(value));
const monthLabel = value => new Intl.DateTimeFormat('pl-PL', { timeZone: 'Europe/Warsaw', month: 'long', year: 'numeric' }).format(new Date(value));
const node = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
const action = (text, fn, cls = 'r-button') => { const b = node('button', cls, text); b.type = 'button'; b.addEventListener('click', fn); return b; };

export function initializeReports(root, api, isActive) {
  const $ = s => root.querySelector(s);
  const archive = $('[data-report-archive]'), reader = $('[data-report-preview]'), body = $('[data-report-body]'), heading = $('[data-report-title]');
  const type = $('[data-report-type]'), more = $('[data-more-reports]'), status = $('[data-report-status]'), host = $('[data-reports]');
  let rows = [], offset = null, anchor = null, generation = 0, reading = 0, current = null, opener = null, scrollY = 0, model = null, printMode = false;
  const formatSelect = $('[data-report-format]');
  const active = () => isActive() && !reader.hidden;
  const focusReader = () => { heading.focus({ preventScroll: true }); reader.scrollIntoView({ block: 'start', behavior: 'instant' }); };
  function back() {
    history.replaceState(null, '', '#raporty'); root.classList.remove('r-report-print');
    reading++; current = null; reader.hidden = true; archive.hidden = false;
    window.scrollTo({ top: scrollY, behavior: 'instant' });
    (opener?.isConnected ? opener : $('[data-page-title]')).focus({ preventScroll: true });
  }
  function showError(id) {
    heading.textContent = 'Raport chwilowo niedostępny'; body.replaceChildren(node('p', '', 'Nie udało się wczytać tej publikacji.'), action('Spróbuj ponownie', () => read(id, opener)));
  }
  async function read(id, from, print = false) {
    printMode = print; root.classList.toggle('r-report-print', print);
    window.history.replaceState(null, '', reportHref(id, print));
    const token = ++reading;
    if (reader.hidden) scrollY = window.scrollY;
    opener = from; current = null; archive.hidden = true; reader.hidden = false;
    $('[data-report-downloads]').hidden = true;
    $('[data-report-kicker]').textContent = ''; heading.textContent = 'Wczytywanie raportu…'; body.replaceChildren(); reader.setAttribute('aria-busy', 'true'); focusReader();
    try {
      const item = checkEnvelope(await api(`/api/reports/${id}`));
      if (token !== reading || !active()) return;
      if (!item) throw new Error('missing_report');
      if (item.report.report_id !== id) throw new Error('wrong_report');
      current = item.report;
      let reference = null;
      if (current.rtb.trend?.reference_report_id) {
        try { reference = checkEnvelope(await api(`/api/reports/${current.rtb.trend.reference_report_id}`))?.report; } catch {}
        if (token !== reading || !active()) return;
      }
      model = buildReportPresentation(current, { reference, baseUrl: window.location.href, newerId: rows.find(row => row.supersedes === current.report_id)?.report_id });
      renderReader(); $('[data-report-downloads]').hidden = false; focusReader();

    } catch { if (token === reading && active()) showError(id); }
    finally { if (token === reading) reader.removeAttribute('aria-busy'); }
  }
  function renderReader() {
    heading.textContent = model.title;
    $('[data-report-kicker]').textContent = printMode ? 'Wersja do druku' : '';
    renderReportContent(body, model, printMode);
    $('[data-print-preview]').textContent = printMode ? 'Wróć do czytnika' : 'Wersja do druku';
    $('[data-print-report]').hidden = !printMode;
    if (!printMode && !matchMedia('(prefers-reduced-motion: reduce)').matches) body.animate([{ opacity: 0, transform: 'translateY(4px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: 240, easing: 'ease-out' });
  }
  function renderList() {
    host.replaceChildren(); let month = '', group;
    rows.forEach((r, index) => {
      const key = dateKey(r.as_of).slice(0, 7);
      if (key !== month) { month = key; group = node('section', 'r-report-month'); group.append(node('h2', '', monthLabel(r.as_of))); host.append(group); }
      const b = action('', () => read(r.report_id, b), 'r-report-choice'); b.dataset.reportId = r.report_id;
      const mark = node('span', 'r-report-glyph', '→'); mark.setAttribute('aria-hidden', 'true');
      const info = node('span', 'r-report-info'); info.append(node('strong', '', dayLabel(r.as_of)));
      const p = parts(r.as_of); info.append(node('span', '', `Stan na ${p.hour}:${p.minute}${r.supersedes ? ' · Korekta' : ''} · ${r.methodology_version}`));
      const metric = node('span', 'r-report-number'); metric.append(node('span', '', 'Indeks RTA'), node('strong', '', r.score === null ? 'Niewyliczony' : `${scoreLabel(r.score)} /100`));
      b.append(mark, info, metric); if (index === 0) b.dataset.latest = 'true'; group.append(b);
    });
    if (!rows.length) host.append(node('p', 'r-empty', 'Brak opublikowanych raportów tego rodzaju.'));
    $('[data-report-count]').textContent = rows.length ? `${rows.length} ${rows.length === 1 ? 'publikacja' : 'publikacji'}${offset !== null ? ' · dostępne starsze' : ''}` : '';
    more.hidden = offset === null;
  }
  async function load(append = false) {
    const token = ++generation; const q = new URLSearchParams({ type: type.value });
    if (append && offset !== null) { q.set('offset', offset); q.set('anchor', anchor); }
    more.disabled = true; status.replaceChildren(node('span', '', 'Wczytywanie archiwum…')); host.setAttribute('aria-busy', 'true');
    try {
      const response = await api(`/api/reports?${q}`); if (token !== generation || !isActive()) return;
      if (!Array.isArray(response.items)) throw new Error('invalid_history');
      const previousLength = rows.length;
      rows = append ? [...rows, ...response.items.filter(r => !rows.some(old => old.report_id === r.report_id))] : response.items;
      offset = response.next_offset; anchor = response.anchor; renderList(); status.replaceChildren();
      if (append) host.querySelectorAll('[data-report-id]')[previousLength]?.focus();
    } catch { if (token === generation && isActive()) { status.replaceChildren(node('span', '', 'Archiwum jest chwilowo niedostępne.'), action('Spróbuj ponownie', () => load(append), 'r-link')); } }
    finally { if (token === generation) { more.disabled = false; host.removeAttribute('aria-busy'); } }
  }
  $('[data-close-report]').addEventListener('click', back);
  reader.addEventListener('keydown', e => { if (e.key === 'Escape') { e.preventDefault(); back(); } });
  type.addEventListener('change', () => { reading++; rows = []; offset = null; anchor = null; renderList(); load(); });
  more.addEventListener('click', () => load(true));
  $('[data-download-report]').addEventListener('click', () => {
    if (!current) return; const format = formatSelect.value;
    const content = format === 'txt' ? reportPresentationText(model) : JSON.stringify(format === 'geojson' ? current.geojson : current, null, 2);
    const url = URL.createObjectURL(new Blob([content], { type: format === 'txt' ? 'text/plain;charset=utf-8' : 'application/json' }));
    const a = node('a'); a.href = url; a.download = `${current.report_id}.${format}`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  $('[data-print-preview]').addEventListener('click', () => {
    if (!model) return;
    printMode = !printMode; root.classList.toggle('r-report-print', printMode);
    history.replaceState(null, '', reportHref(current.report_id, printMode)); renderReader(); focusReader();
  });
  $('[data-print-report]').addEventListener('click', () => window.print());
  let printState = [];
  window.addEventListener('beforeprint', () => { printState = [...reader.querySelectorAll('details')].map(d => [d,d.open]); printState.forEach(([d]) => { d.open = true; }); });
  window.addEventListener('afterprint', () => { printState.forEach(([d,open]) => { d.open = open; }); printState = []; });
  return {
    open() {
      const route = reportRoute(location.hash);
      if (route) { load(); read(route.id, null, route.print); }
      else { archive.hidden = false; reader.hidden = true; root.classList.remove('r-report-print'); load(); }
    },
    refresh() { if (isActive() && reader.hidden) load(); },
    leave() { if (reportRoute(location.hash) || location.hash === '#raporty') history.replaceState(null, '', location.pathname + location.search); root.classList.remove('r-report-print'); generation++; reading++; current = null; reader.hidden = true; archive.hidden = false; },
  };
}
