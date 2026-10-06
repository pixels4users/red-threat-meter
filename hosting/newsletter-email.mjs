import { buildReportPresentation, reportPresentationText } from '../web/report-presentation.js';
import config from '../config/newsletter.json' with { type: 'json' };
import { emailFrame, emailInset, escapeHTML } from '../ui/email/layout.mjs';

export { escapeHTML };
const p = (value, meta = false) => value ? `<p${meta ? ' class="r-email-meta"' : ''}>${escapeHTML(value).replace(/\n/g, '<br>')}</p>` : '';
const heading = (value, level = 2) => `<h${level}>${escapeHTML(value)}</h${level}>`;
const link = (label, url) => `<a href="${escapeHTML(url)}">${escapeHTML(label)}</a>`;
const list = rows => rows.length ? `<ul>${rows.map(value => `<li>${escapeHTML(value)}</li>`).join('')}</ul>` : '';
const privacy = new URL('#newsletter/prywatnosc', config.site_url).href;
const legalText = `${config.operator.name}\n${config.operator.address}\nNIP: ${config.operator.nip}\n${config.reply_to}`;
function frame(title, content, unsubscribe = null, masthead = {}) {
  return emailFrame({ title, content, siteUrl:config.site_url, eyebrow:'NEWSLETTER', headline:title, ...masthead,
    footer:`${p('RedThreatAlert by Pixels4Users')}${p(legalText)}${link('Informacja o prywatności', privacy)}${unsubscribe ? `<p style="margin:16px 0 0">${link('Wypisz się z newslettera', unsubscribe)}</p>` : ''}` });
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
// The email links to full event groups in this exact edition. The approved
// summary, warnings, uncertainty and source status remain in the message.
export function reportEmail(report, options = {}) {
  const m = buildReportPresentation(report, { ...options, baseUrl: config.site_url });
  const subject = `RedThreatAlert — raport dzienny · ${m.date}`;
  const unsubscribe = '{{{RESEND_UNSUBSCRIBE_URL}}}';
  let html = `<p class="r-email-meta" style="margin:0 0 28px">${link('Otwórz ten raport na stronie', m.url)} · ${link('Postaw kawę', config.support_url)} · ${link('Wypisz się',unsubscribe)}</p>`;
  html += `<h2 style="border:0;padding:0;margin:0 0 12px;font-size:14px">Indeks RTA</h2><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td width="40%" style="vertical-align:top"><p class="r-email-score" style="font-size:60px;line-height:1.15;font-weight:bold;margin:0 12px 16px 0">${escapeHTML(m.metric.score)}${m.metric.hasScore ? '<span style="font-size:18px;color:#626262;font-weight:400"> /100</span>' : ''}</p></td><td style="vertical-align:middle;font-size:14px;line-height:1.6">${p(m.metric.level)}${p(`Pewność danych: ${m.metric.confidence}`)}</td></tr></table>`;
  html += p(m.metric.delta) + p(m.metric.note) + p(m.explanation, true) + p(m.snapshotNote, true);
  if (m.previous) html += p('Korekta wcześniejszego wydania.') + `<p>${link('Poprzednia wersja', new URL(`#raport/${m.previous}`, config.site_url).href)}</p>`;
  if (m.summary.length) html += emailInset(heading('Najważniejsze ustalenia') + m.summary.map(row => (row.label ? heading(row.label, 3) : '') + p(row.text)).join(''));
  if (m.warnings.length) html += heading('Oficjalne ostrzeżenia') + p('Status i instrukcje zapisane w chwili wydania raportu. Niski indeks nie odwołuje zaleceń służb.') + m.warnings.map(w => heading(`${w.authority} · ${w.area}`, 3) + p(w.status) + p(w.instruction) + p([w.from && `Od: ${w.from}`, w.until && `Do: ${w.until}`].filter(Boolean).join(' · '))).join('');
  html += heading('Wydarzenia i kontekst');
  if (!m.count) html += p('Brak wydarzeń ujętych w tym wydaniu');
  else html += p('Pełne wpisy otworzysz w wybranej kategorii na stronie raportu.', true);
  for (const group of m.groups) {
    html += `<p style="margin:0 0 8px"><a href="${escapeHTML(group.url)}" class="r-email-topic-link" style="display:block;padding:16px;background:#f6f6f6;color:#171717;font-size:16px;line-height:24px;text-decoration:none"><strong>${escapeHTML(group.label)}</strong> · ${group.events.length}<span aria-hidden="true"> &nbsp;→</span></a></p>`;
  }
  html += heading('Źródła i zakres obserwacji') + heading('Wydawcy materiałów wykorzystanych w raporcie', 3) + p(m.usedPublishers.join(' · '));
  html += heading('Monitorowani wydawcy — dostępność w chwili wydania', 3) + `<ul>${m.sources.map(s => `<li>${s.url ? link(s.name, s.url) : escapeHTML(s.name)}: ${escapeHTML(s.status)}${s.incompleteWindow ? ' · niepełne okno obserwacji' : ''}${s.checked ? ` · sprawdzono ${escapeHTML(s.checked)}` : ''}</li>`).join('')}</ul>`;
  html += list(m.domains) + list([...m.limitations, ...m.gaps]) + heading('Informacje o wydaniu') + p(`Metodologia: ${m.methodology}\nOkno raportu: ${m.window}`) + p(m.windowNote);
  html += `<p>${link('Pełny raport na stronie', m.url)} · ${link('Postaw kawę', config.support_url)}</p>`;
  return { from: config.from, reply_to: config.reply_to, subject,
    html: frame(subject, html, unsubscribe, { eyebrow:'RAPORT DZIENNY', headline:m.date, dateline:m.asOf }),
    text: `${reportPresentationText(m, { eventDetails:false })}\n\nPostaw kawę: ${config.support_url}\n\n${legalText}\nPrywatność: ${privacy}\nWypisz się: ${unsubscribe}` };
}
