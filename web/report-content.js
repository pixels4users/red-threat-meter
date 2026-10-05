import { reportHref } from './report-presentation.js';

const el = (tag, cls, value) => { const n = document.createElement(tag); if (cls) n.className = cls; if (value != null) n.textContent = value; return n; };
const link = (label, url) => { const a = el('a', '', label); a.href = url; if (/^https?:/.test(url)) { a.target = '_blank'; a.rel = 'noopener noreferrer'; } return a; };
const section = title => { const s = el('section', 'r-report-section'); s.append(el('h3', '', title)); return s; };

export function renderReportContent(host, m, print = false) {
  host.replaceChildren(); host.dataset.template = m.template;
  const date = el('div', 'r-report-dateline'); date.append(el('p', 'r-report-date', m.date), el('p', '', m.asOf)); host.append(date);
  const revision = el('p', 'r-report-revision');
  if (m.previous) revision.append(document.createTextNode('Korekta · '), link('Poprzednia wersja', reportHref(m.previous)));
  if (m.newer) revision.append(document.createTextNode(m.previous ? ' · ' : ''), link('Dostępna nowsza korekta', reportHref(m.newer)));
  if (revision.childNodes.length) host.append(revision);
  const metric = el('section', 'r-card r-report-index'); metric.setAttribute('aria-label', 'Indeks RTA');
  const value = el('div'); value.append(el('p', 'r-eyebrow', 'Indeks RTA'));
  const line = el('div', 'r-report-index-line'), number = el('strong', 'r-report-index-number', m.metric.score); number.dataset.tone = m.metric.tone;
  line.append(number); if (m.metric.hasScore) line.append(el('span', 'r-unit', '/100')); value.append(line);
  const context = el('div', 'r-report-index-context'); context.append(el('p', 'r-report-level', m.metric.level), el('p', '', `Pewność danych: ${m.metric.confidence}`));
  if (m.metric.delta) context.append(el('p', 'r-report-delta', m.metric.delta));
  if (m.metric.note) context.append(el('p', 'r-small', m.metric.note)); metric.append(value, context); host.append(metric);
  host.append(el('p', 'r-reader-caveat', m.explanation), el('p', 'r-report-snapshot-note', m.snapshotNote));
  if (m.summary.length) {
    const summary = section('Najważniejsze ustalenia'); summary.classList.add('r-report-findings');
    for (const row of m.summary) { const block = el('div'); if (row.label) block.append(el('h4', '', row.label)); block.append(el('p', '', row.text)); summary.append(block); } host.append(summary);
  }
  if (m.warnings.length) {
    const warnings = section('Oficjalne ostrzeżenia'); warnings.classList.add('r-report-warnings'); warnings.append(el('p', 'r-small', 'Status i instrukcje zapisane w chwili wydania raportu. Niski indeks nie odwołuje zaleceń służb.'));
    for (const w of m.warnings) {
      const a = el('article'); a.append(el('h4', '', `${w.authority} · ${w.area}`), el('p', 'r-small', w.status));
      if (w.instruction) a.append(el('p', '', w.instruction));
      if (w.from || w.until) a.append(el('p', 'r-small', [w.from && `Od: ${w.from}`, w.until && `Do: ${w.until}`].filter(Boolean).join(' · ')));
      warnings.append(a);
    } host.append(warnings);
  }
  const events = section('Wydarzenia i kontekst'); events.classList.add('r-report-events');
  if (!m.count) events.append(el('p', '', 'Brak wydarzeń ujętych w tym wydaniu'));
  for (const g of m.groups) {
    const group = el('details', 'r-report-topic'); group.open = print;
    group.append(el('summary', '', `${g.label} · ${g.events.length}`));
    for (const e of g.events) {
      const a = el('article', 'r-report-event'); a.dataset.eventId = e.id;
      a.append(el('h4', '', e.title), el('p', 'r-report-event-meta', `${e.topics.join(' · ')} · ${e.status}`));
      if (e.revisionNote) a.append(el('p', 'r-report-event-meta', e.revisionNote));
      a.append(el('p', '', e.summary));
      const facts = el('dl', 'r-report-event-facts');
      for (const [label, content] of [['Miejsce',e.place], ['Data zdarzenia',e.occurred], ['Publikacja',e.publication], ...(e.measurement ? [['Pomiar',e.measurement]] : [])]) { const row = el('div'); row.append(el('dt','',label),el('dd','',content));facts.append(row); } a.append(facts);
      const sources = el('ul', 'r-report-event-sources'); e.sources.forEach(s => { const li=el('li'); li.append(link(s.publisher,s.url),el('span','r-print-url',s.url));sources.append(li); });a.append(sources); group.append(a);
    } events.append(group);
  } host.append(events);
  const coverage = el('details','r-report-coverage'); coverage.open = print; coverage.append(el('summary','','Źródła i zakres obserwacji'));
  const content = el('div'); content.append(el('h4','','Wydawcy materiałów wykorzystanych w raporcie'),el('p','',m.usedPublishers.length ? m.usedPublishers.join(' · ') : 'Brak materiałów przypisanych do wydarzeń.'));
  content.append(el('h4','','Monitorowani wydawcy — dostępność w chwili wydania'));
  const sources = el('ul','r-report-monitoring');
  for (const s of m.sources) { const li=el('li');li.append(s.url ? link(s.name,s.url) : el('strong','',s.name),el('span','',`${s.status}${s.incompleteWindow ? ' · niepełne okno obserwacji' : ''}`)); if(s.checked)li.append(el('span','r-small',`Sprawdzono ${s.checked}`));sources.append(li); } content.append(sources);
  if(m.domains.length){content.append(el('h4','','Pokrycie obszarów obserwacji'));const ul=el('ul');m.domains.forEach(v=>ul.append(el('li','',v)));content.append(ul);}
  if(m.limitations.length || m.gaps.length){content.append(el('h4','','Ograniczenia i braki'));const ul=el('ul');[...m.limitations,...m.gaps].forEach(v=>ul.append(el('li','',v)));content.append(ul);}
  coverage.append(content); host.append(coverage);
  const info = section('Informacje o wydaniu');info.classList.add('r-report-edition');
  const method=el('p');method.append(document.createTextNode('Metodologia: '),m.methodologyUrl ? link(m.methodology,m.methodologyUrl) : document.createTextNode(m.methodology)); info.append(method,el('p','',`Okno raportu: ${m.window}`));
  if(m.windowNote)info.append(el('p','',m.windowNote));
  const permalink=el('p');permalink.append(link('Stały adres tego wydania',m.url),el('span','r-print-url',m.url));info.append(permalink,el('p','',m.credit),el('p','r-small',`Wersja szablonu: ${m.template}`));host.append(info);
}
