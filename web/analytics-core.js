// No DOM, network, or storage effects on import. Only approved vocabulary leaves this module.
export const CONSENT_KEY = 'rta-analytics-consent';
const views = { overview: ['przeglad', 'Przegląd'], map: ['mapa', 'Mapa Operacyjna'], journal: ['dziennik', 'Dziennik Sygnałów'], reports: ['raporty', 'Raporty'] };
export function analyticsView(page, hash = '') {
  if (hash.startsWith('#newsletter/')) {
    const section = hash === '#newsletter/prywatnosc' ? 'prywatnosc' : hash === '#newsletter/potwierdzono' ? 'potwierdzono' : 'potwierdzenie';
    return { path: `/newsletter/${section}`, title: 'Newsletter — RedThreatAlert', view: 'newsletter' };
  }
  const report = /^#raport\/(rpt_[a-f0-9]{64})(?:\/(druk)|\/obszar\/[a-z]+)?$/.exec(hash);
  if (page === 'reports' && report) return { path: `/raport/${report[1]}${report[2] ? '/druk' : ''}`, title: `${report[2] ? 'Druk raportu' : 'Raport'} — RedThreatAlert`, view: 'reports' };
  const key = Object.hasOwn(views, page) ? page : 'overview';
  return { path: `/${views[key][0]}`, title: `${views[key][1]} — RedThreatAlert`, view: key };
}
export function readConsent(raw, config, now) {
  try {
    const value = JSON.parse(raw);
    if (value?.version === config.consent_version && typeof value.analytics === 'boolean' &&
      Number.isFinite(value.at) && value.at <= now && now - value.at < config.consent_days * 86400000) return value;
  } catch {}
  return null;
}
export function cleanEvent(name, input, vocabulary) {
  const pick = (value, allowed) => typeof value === 'string' && allowed.includes(value) ? value : null;
  if (['newsletter_view', 'newsletter_submit', 'newsletter_confirmed'].includes(name)) return {};
  if (name === 'support_click') {
    const placement = pick(input.placement, ['navigation', 'footer']);
    return placement ? { placement } : null;
  }
  if (name === 'select_content') {
    const view = pick(input.view, Object.keys(views));
    return view ? { view, content_type: 'signal' } : null;
  }
  if (name === 'filter_change') {
    const view = pick(input.view, Object.keys(views));
    const filter_name = pick(input.filter_name, Object.keys(vocabulary));
    const filter_value = filter_name && pick(input.filter_value, vocabulary[filter_name]);
    return view && filter_value ? { view, filter_name, filter_value } : null;
  }
  return null;
}
export function createAnalytics({ config, origin, storage, transport, vocabulary, now = Date.now, onChange = () => {} }) {
  const allowed = config.production_origins.includes(origin) && /^G-[A-Z0-9]+$/.test(config.measurement_id);
  let consent = null, active = false, current = analyticsView('overview'), last = null, seenNewsletter = false;
  try { consent = readConsent(storage.getItem(CONSENT_KEY), config, now()); } catch {}
  function stop() { if (active) { active = false; last = null; transport.stop(); } }
  function permitted() {
    if (consent && !readConsent(JSON.stringify(consent), config, now())) { consent = null; stop(); onChange(null); }
    return allowed && consent?.analytics === true;
  }
  function page() {
    if (!permitted()) return;
    if (!active) { active = true; transport.start(current); }
    if (last === current.path) return;
    transport.event('page_view', { page_location: origin + current.path, page_title: current.title, view: current.view,
      page_referrer: last ? origin + last : transport.referrer });
    last = current.path;
  }
  return {
    get consent() { permitted(); return consent; },
    get enabled() { return permitted(); },
    setView(pageName, hash) { current = analyticsView(pageName, hash); page(); },
    choose(value) {
      consent = { version: config.consent_version, analytics: value === true, at: now() };
      try { storage.setItem(CONSENT_KEY, JSON.stringify(consent)); } catch {}
      if (!consent.analytics) stop(); else page();
      onChange(consent);
    },
    sync(raw) {
      consent = readConsent(raw, config, now());
      if (!consent?.analytics) stop(); else page();
      onChange(consent);
    },
    check() { permitted(); },
    track(name, input = {}) {
      if (!permitted()) return false;
      const params = cleanEvent(name, input, vocabulary);
      if (!params || (name === 'newsletter_view' && seenNewsletter)) return false;
      page();
      transport.event(name, { ...params, page_location: origin + current.path, page_title: current.title });
      if (name === 'newsletter_view') seenNewsletter = true;
      return true;
    },
  };
}
