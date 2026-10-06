import config from '../config/analytics.json' with { type: 'json' };
import newsletter from '../config/newsletter.json' with { type: 'json' };
import presentation from '../config/signal-presentation.json' with { type: 'json' };
import { CONSENT_KEY, createAnalytics } from './analytics-core.js';

const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text) n.textContent = text; return n; };
const action = (text, fn, cls = 'r-button') => { const n = el('button', cls, text); n.type = 'button'; n.addEventListener('click', fn); return n; };
const link = (text, href) => { const n = el('a', 'r-link', text); n.href = href; n.rel = 'noopener noreferrer'; return n; };

function clearAnalyticsCookies() {
  const host = location.hostname.split('.');
  const domains = ['', ...host.map((_, i) => host.slice(i).join('.')).flatMap(d => [d, `.${d}`])];
  for (const entry of document.cookie.split(';')) {
    const name = entry.trim().split('=')[0];
    if (!/^_ga(?:_|$)/.test(name)) continue;
    for (const domain of domains) document.cookie = `${name}=; Max-Age=0; Path=/;${domain ? ` Domain=${domain};` : ''} SameSite=Lax`;
  }
}

export function initializeAnalytics(root, getView) {
  let storage;
  try { storage = window.localStorage; } catch { storage = { getItem: () => null, setItem: () => {} }; }
  let referrer = '';
  try { const url = new URL(document.referrer); if (['https:', 'http:'].includes(url.protocol) && url.origin !== location.origin) referrer = url.origin + '/'; } catch {}
  let script, gtag, tagReady = false;
  const disableKey = `ga-disable-${config.measurement_id}`;
  window[disableKey] = true;
  const transport = {
    referrer,
    start(view) {
      window[disableKey] = false;
      window.dataLayer = [];
      gtag = window.gtag = function () { window.dataLayer.push(arguments); };
      gtag('consent', 'default', { analytics_storage: 'denied', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied' });
      gtag('consent', 'update', { analytics_storage: 'granted' });
      gtag('set', 'ads_data_redaction', true);
      gtag('js', new Date());
      gtag('config', config.measurement_id, { send_page_view: false, allow_google_signals: false, allow_ad_personalization_signals: false,
        cookie_expires: config.cookie_days * 86400, cookie_update: false, cookie_flags: 'SameSite=Lax;Secure',
        page_location: location.origin + view.path, page_title: view.title, page_referrer: referrer });
      script = document.createElement('script'); script.async = true; script.dataset.rtaAnalytics = '';
      script.src = `https://www.googletagmanager.com/gtag/js?id=${config.measurement_id}`;
      // A blocked tag must never affect the dashboard or retry requests.
      script.onerror = () => { window.dataLayer.length = 0; };
      script.onload = () => { tagReady = true; };
      document.head.append(script);
    },
    event(name, params) {
      if (window[disableKey]) return;
      if (name === 'page_view') gtag('set', { page_location: params.page_location, page_title: params.page_title, page_referrer: params.page_referrer });
      // Bound the queue if a blocker prevents the library from loading.
      if (tagReady || window.dataLayer.length < 200) gtag('event', name, { ...params, send_to: config.measurement_id });
    },
    stop() {
      // Disable first, then unload the library. Do not send a denied-consent ping.
      window[disableKey] = true;
      if (window.dataLayer) window.dataLayer.length = 0;
      script?.remove(); clearAnalyticsCookies();
      window.location.reload();
    },
  };
  let refreshUI = () => {};
  const analytics = createAnalytics({ config, origin: location.origin, storage, transport,
    vocabulary: {
      area: ['macro', 'PL', ...Object.keys(presentation.regions)],
      period: ['day', 'week', 'month', 'quarter', 'year', 'all', 'undated', 'current7', 'previous7'],
      topic: ['all', ...Object.keys(presentation.topics)], source: ['all', ...config.source_ids],
      report_type: ['all', 'daily', 'weekly', 'monthly'],
    }, onChange: () => { refreshUI(); updateExposure(); },
  });
  if (!analytics.consent?.analytics) clearAnalyticsCookies();

  const banner = el('section', 'r-cookie-banner'); banner.setAttribute('aria-labelledby', 'cookie-title');
  const text = el('div', 'r-cookie-copy'), title = el('h2', '', 'Pliki cookie'); title.id = 'cookie-title';
  text.append(title, el('p', '', 'Za Twoją zgodą używamy Google Analytics, aby sprawdzać, które raporty i funkcje są przydatne, i ulepszać RedThreatAlert. Możesz zaakceptować dodatkowe pliki cookie lub pozostać przy niezbędnych. Swój wybór zmienisz w ustawieniach prywatności.'));
  const buttons = el('div', 'r-cookie-actions');
  function choose(value) {
    const returnFocus = banner.contains(document.activeElement);
    analytics.choose(value); if (dialog.open) dialog.close();
    if (returnFocus) focusContent();
  }
  buttons.append(action('Tylko niezbędne', () => choose(false)), action('Akceptuj', () => choose(true), 'r-button r-cookie-accept'));
  const links = el('div', 'r-cookie-links');
  links.append(action('Ustawienia', () => openSettings(false), 'r-link'), action('Polityka prywatności', () => openSettings(true), 'r-link'));
  const controls = el('div', 'r-cookie-controls'); controls.append(buttons, links); banner.append(text, controls);
  // Fixed bottom layer; mobile offset leaves the navigation accessible.
  root.querySelector('.r-main').prepend(banner);

  const dialog = el('dialog', 'r-dialog r-cookie-dialog'); dialog.setAttribute('aria-labelledby', 'cookie-settings-title');
  const header = el('div', 'r-cookie-header'), heading = el('h2', '', 'Ustawienia prywatności'); heading.id = 'cookie-settings-title';
  header.append(heading, action('Zamknij', () => dialog.close()));
  const intro = el('p', '', 'Wybierz, czy chcesz udostępniać statystyki korzystania ze strony. Odmowa nie ogranicza dostępu do raportów.');
  const required = el('div', 'r-cookie-option'); required.append(el('strong', '', 'Niezbędne — zawsze aktywne'), el('p', '', 'Zapamiętanie wyboru prywatności i ustawień strony.'));
  const option = el('label', 'r-cookie-option'), checkbox = el('input'); checkbox.type = 'checkbox'; checkbox.id = 'cookie-analytics';
  const optionText = el('span'); optionText.append(el('strong', '', 'Statystyki — Google Analytics'), el('span', '', 'Pomiar odwiedzin, korzystania z raportów, newslettera i przycisku wsparcia.'));
  option.append(checkbox, optionText);
  const details = el('details', 'r-cookie-policy'); details.append(el('summary', '', 'Polityka prywatności — statystyki strony'));
  function paragraph(text) { details.append(el('p', '', text)); }
  paragraph(`Administratorem jest ${newsletter.operator.name}, ${newsletter.operator.address}, NIP ${newsletter.operator.nip}. Kontakt: ${newsletter.reply_to}.`);
  paragraph('Po Twojej zgodzie korzystamy z Google Analytics 4 (Google Ireland Limited) do analizy odwiedzin i ulepszania strony. Podstawą przetwarzania jest zgoda (art. 6 ust. 1 lit. a RODO). Jest dobrowolna i niezależna od zapisu do newslettera.');
  paragraph('Google otrzymuje informacje o odwiedzanych widokach i działaniach, identyfikatory cookies oraz dane techniczne przeglądarki i urządzenia. Połączenie z Google obejmuje adres IP. Nie wysyłamy do statystyk adresu e-mail, tokenu potwierdzenia zapisu ani zawartości formularza. Nie włączamy Google Signals ani personalizacji reklam.');
  paragraph('Wybór prywatności zapamiętujemy lokalnie przez 180 dni. Cookies _ga i _ga_* mają okres ważności do 60 dni, bez przedłużania przy każdej wizycie. Dla danych użytkowników i zdarzeń wybieramy retencję 2 miesięcy w GA4; zbiorcze raporty mogą być przechowywane dłużej.');
  paragraph('Możesz wycofać zgodę przez „Ustawienia prywatności” w stopce. Zatrzymamy pomiar, usuniemy dostępne cookies GA i odświeżymy stronę. Nie cofa to wcześniejszego przetwarzania ani automatycznie nie usuwa danych już przekazanych Google.');
  paragraph('Usługa Google może przetwarzać dane poza EOG, w tym w USA. Informacje o warunkach przetwarzania i zabezpieczeniach transferu znajdziesz w dokumentach Google; możesz też skontaktować się z administratorem.');
  details.append(link('Warunki przetwarzania Google', 'https://business.safety.google/adsprocessorterms/'), document.createTextNode(' · '), link('Polityka prywatności Google', 'https://policies.google.com/privacy'));
  paragraph('Możesz żądać dostępu do danych, sprostowania, usunięcia, ograniczenia przetwarzania oraz — w przypadkach przewidzianych prawem — przeniesienia danych. Możesz złożyć skargę do Prezesa UODO. Nie podejmujemy na tej podstawie zautomatyzowanych decyzji wywołujących skutki prawne lub podobnie istotne.');
  details.append(link('Prywatność newslettera', '#newsletter/prywatnosc'));
  details.lastChild.addEventListener('click', () => dialog.close());
  paragraph(`Wersja informacji: ${config.consent_version}.`);
  const save = action('Zapisz ustawienia', () => choose(checkbox.checked));
  dialog.append(header, intro, required, option, save, details); root.append(dialog);
  let opener;
  function focusContent() { const heading = root.querySelector('[data-page-title]'); heading.tabIndex = -1; heading.focus({ preventScroll: true }); }
  function openSettings(policy) {
    opener = document.activeElement; checkbox.checked = analytics.consent?.analytics === true; details.open = policy;
    dialog.showModal(); (policy ? details.querySelector('summary') : checkbox).focus();
  }
  dialog.addEventListener('close', () => {
    if (opener?.isConnected && !opener.closest('[hidden]')) opener.focus({ preventScroll: true }); else focusContent();
  });
  dialog.addEventListener('keydown', event => {
    if (event.key !== 'Tab') return;
    const controls = [...dialog.querySelectorAll('button:not(:disabled),input:not(:disabled),a[href],summary')]
      .filter(n => n.getClientRects().length && (!n.closest('details:not([open])') || n.tagName === 'SUMMARY'));
    const first = controls[0], last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
  const footerSettings = action('Ustawienia prywatności', () => openSettings(false), 'r-link');
  root.querySelector('.r-footer-info').append(footerSettings);
  refreshUI = () => { banner.hidden = analytics.consent !== null; };
  refreshUI();

  let visible = false, timer = null, observer;
  function updateExposure() {
    clearTimeout(timer); timer = null;
    const section = root.querySelector('#newsletter');
    if (!visible || document.hidden || !section || section.hidden || !analytics.enabled) return;
    timer = setTimeout(() => { if (visible && !document.hidden && !section.hidden) analytics.track('newsletter_view'); }, 1000);
  }
  queueMicrotask(() => {
    const section = root.querySelector('#newsletter');
    if (section && 'IntersectionObserver' in window) {
      observer = new IntersectionObserver(entries => { visible = entries[0].isIntersecting && entries[0].intersectionRatio >= 0.5; updateExposure(); }, { threshold: [0, 0.5] });
      observer.observe(section);
    }
    syncView();
  });
  function syncView() { const view = getView(); analytics.setView(view.page, view.hash); }
  window.addEventListener('rta:view-change', syncView);
  window.addEventListener('hashchange', syncView);
  window.addEventListener('storage', event => { if (event.key === CONSENT_KEY || event.key === null) analytics.sync(event.newValue); });
  document.addEventListener('visibilitychange', () => { analytics.check(); updateExposure(); });
  setInterval(() => analytics.check(), 60000);
  root.addEventListener('click', event => {
    const coffee = event.target.closest('.r-coffee-link');
    if (coffee) analytics.track('support_click', { placement: coffee.closest('.r-nav') ? 'navigation' : 'footer' });
  });
  root.addEventListener('change', event => {
    const control = event.target;
    const names = { region: 'area', mapArea: 'area', journalArea: 'area', mapPeriod: 'period', journalPeriod: 'period', mapTopic: 'topic', category: 'topic', source: 'source', reportType: 'report_type' };
    for (const [key, name] of Object.entries(names)) if (Object.hasOwn(control.dataset, key)) {
      analytics.track('filter_change', { view: getView().page, filter_name: name, filter_value: control.value }); break;
    }
  });
  return { track: (name, params) => analytics.track(name, params), get enabled() { return analytics.enabled; }, syncView };
}
