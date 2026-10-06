import { buildReportPresentation, reportPresentationText } from '../web/report-presentation.js';
import config from '../config/newsletter.json' with { type: 'json' };

export const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const p = value => value ? `<p>${escapeHTML(value).replace(/\n/g, '<br>')}</p>` : '';
const heading = (value, level = 2) => `<h${level}>${escapeHTML(value)}</h${level}>`;
const link = (label, url) => `<a href="${escapeHTML(url)}">${escapeHTML(label)}</a>`;
const list = rows => rows.length ? `<ul>${rows.map(value => `<li>${escapeHTML(value)}</li>`).join('')}</ul>` : '';
const privacy = new URL('#newsletter/prywatnosc', config.site_url).href;
const legalText = `${config.operator.name}\n${config.operator.address}\nNIP: ${config.operator.nip}\n${config.reply_to}`;
function frame(title, content, unsubscribe = null) {
  return `<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHTML(title)}</title></head><body style="margin:0;background:#fff;color:#171717;font:16px/1.6 Arial,Helvetica,sans-serif"><div style="max-width:680px;margin:auto;padding:24px 16px">${heading(title, 1)}${content}<hr><footer style="font-size:13px;color:#626262">${p(legalText)}${link('Informacja o prywatności', privacy)}${unsubscribe ? `<p>${link('Wypisz się z newslettera', unsubscribe)}</p>` : ''}</footer></div></body></html>`;
}

export function confirmationEmail(token) {
  if (!/^[a-f0-9]{64}$/.test(token)) throw new Error('invalid_token');
  const url = new URL(`#newsletter/potwierdz/${token}`, config.site_url).href;
  const subject = 'Potwierdź zapis do newslettera RedThreatAlert';
  const message = 'Potwierdź swój adres, aby otrzymywać opublikowane raporty dzienne RedThreatAlert. Link jest ważny przez 24 godziny.';
  const ignore = 'Jeśli to nie Ty prosisz o zapis, zignoruj tę wiadomość. Nie dodamy adresu do newslettera bez potwierdzenia.';
  return { from: config.from, reply_to: config.reply_to, subject,
    html: frame(subject, p(message) + p('Na stronie potwierdzenia wybierz „Potwierdzam zapis”.') + `<p>${link('Potwierdź adres e-mail', url)}</p>` + p(ignore)),
    text: `${subject}\n\n${message}\n${url}\n\n${ignore}\n\n${legalText}\n${privacy}` };
}

// Use the same frozen model as the website, print view and TXT export.
// Email contains the entire report, including uncertainty and source status.
export function reportEmail(report, options = {}) {
  const m = buildReportPresentation(report, { ...options, baseUrl: config.site_url });
  const subject = `RedThreatAlert — raport dzienny · ${m.date}`;
  const unsubscribe = '{{{RESEND_UNSUBSCRIBE_URL}}}';
  let html = p(`${m.date} · ${m.asOf}`) + `<p>${link('Otwórz ten raport na stronie', m.url)} · ${link('Postaw kawę', config.support_url)} · ${link('Wypisz się',unsubscribe)}</p>`;
  html += heading('Indeks RTA') + `<p style="font-size:40px;font-weight:bold;margin:8px 0">${escapeHTML(m.metric.score)}${m.metric.hasScore ? '<span style="font-size:18px"> /100</span>' : ''}</p>`;
  html += p(m.metric.level) + p(`Pewność danych: ${m.metric.confidence}`) + p(m.metric.delta) + p(m.metric.note) + p(m.explanation) + p(m.snapshotNote);
  if (m.previous) html += p('Korekta wcześniejszego wydania.') + `<p>${link('Poprzednia wersja', new URL(`#raport/${m.previous}`, config.site_url).href)}</p>`;
  if (m.summary.length) html += heading('Najważniejsze ustalenia') + m.summary.map(row => (row.label ? heading(row.label, 3) : '') + p(row.text)).join('');
  if (m.warnings.length) html += heading('Oficjalne ostrzeżenia') + p('Status i instrukcje zapisane w chwili wydania raportu. Niski indeks nie odwołuje zaleceń służb.') + m.warnings.map(w => heading(`${w.authority} · ${w.area}`, 3) + p(w.status) + p(w.instruction) + p([w.from && `Od: ${w.from}`, w.until && `Do: ${w.until}`].filter(Boolean).join(' · '))).join('');
  html += heading('Wydarzenia i kontekst');
  if (!m.count) html += p('Brak wydarzeń ujętych w tym wydaniu');
  for (const group of m.groups) {
    html += heading(`${group.label} · ${group.events.length}`, 3);
    for (const event of group.events) {
      html += heading(event.title, 4) + p(`${event.topics.join(' · ')} · ${event.status}`) + p(event.revisionNote) + p(event.summary);
      html += p(`Miejsce: ${event.place}\nData zdarzenia: ${event.occurred}\nPublikacja: ${event.publication}`) + p(event.measurement);
      html += `<p>${event.sources.map(s => link(s.publisher, s.url)).join(' · ')}</p>`;
    }
  }
  html += heading('Źródła i zakres obserwacji') + heading('Wydawcy materiałów wykorzystanych w raporcie', 3) + p(m.usedPublishers.join(' · '));
  html += heading('Monitorowani wydawcy — dostępność w chwili wydania', 3) + `<ul>${m.sources.map(s => `<li>${s.url ? link(s.name, s.url) : escapeHTML(s.name)}: ${escapeHTML(s.status)}${s.incompleteWindow ? ' · niepełne okno obserwacji' : ''}${s.checked ? ` · sprawdzono ${escapeHTML(s.checked)}` : ''}</li>`).join('')}</ul>`;
  html += list(m.domains) + list([...m.limitations, ...m.gaps]) + heading('Informacje o wydaniu') + p(`Metodologia: ${m.methodology}\nOkno raportu: ${m.window}`) + p(m.windowNote);
  html += `<p>${link('Pełny raport na stronie', m.url)} · ${link('Postaw kawę', config.support_url)}</p>`;
  return { from: config.from, reply_to: config.reply_to, subject,
    html: frame(subject, html, unsubscribe),
    text: `${reportPresentationText(m)}\n\nPostaw kawę: ${config.support_url}\n\n${legalText}\nPrywatność: ${privacy}\nWypisz się: ${unsubscribe}` };
}
