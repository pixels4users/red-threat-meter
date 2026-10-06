import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import Ajv2020 from 'ajv/dist/2020.js';
import { createAnalytics, analyticsView, readConsent, CONSENT_KEY } from '../../web/analytics-core.js';
import config from '../../config/analytics.json' with { type: 'json' };
const vocabulary = { area: ['macro', 'PL'], source: ['all', 'rcb'], topic: ['all', 'aviation'] };
function fixture(options = {}) {
  let time = 100000, raw = options.raw ?? null;
  const events = [], starts = [], stops = [];
  const analytics = createAnalytics({ config, origin: options.origin ?? 'https://redthreatalert.pl', vocabulary,
    now: () => time, storage: options.storage ?? { getItem: () => raw, setItem: (key, value) => { assert.equal(key, CONSENT_KEY); raw = value; } },
    transport: { referrer: '', start: view => starts.push(view), stop: () => stops.push(true), event: (name, params) => events.push({ name, params }) } });
  return { analytics, events, starts, stops, advance: ms => { time += ms; }, raw: () => raw };
}
test('analytics config validates against JSON Schema 2020-12', () => {
  const ajv = new Ajv2020({ allErrors: true });
  const validate = ajv.compile(JSON.parse(readFileSync('schemas/analytics.schema.json')));
  assert.ok(validate(config), JSON.stringify(validate.errors));
  assert.equal(validate({ ...config, production_origins: ['http://localhost:8769'] }), false);
});
test('no load, events, replay or newsletter impression before consent or after refusal', () => {
  const f = fixture(); f.analytics.setView('map'); f.analytics.track('newsletter_view'); f.analytics.choose(false);
  assert.equal(f.starts.length, 0); assert.equal(f.events.length, 0);
  f.analytics.choose(true);
  assert.equal(f.events.length, 1); assert.equal(f.events[0].params.page_location, 'https://redthreatalert.pl/mapa');
  assert.equal(f.analytics.track('newsletter_view'), true);
  assert.equal(f.analytics.track('newsletter_view'), false);
});
test('localhost, HTTP and preview origins never start the production tag', () => {
  for (const origin of ['http://127.0.0.1:8769', 'https://preview.example', 'http://redthreatalert.pl', 'https://redthreatalert.pl.evil.test']) {
    const f = fixture({ origin }); f.analytics.choose(true); f.analytics.setView('map'); f.analytics.track('newsletter_confirmed');
    assert.equal(f.starts.length, 0); assert.equal(f.events.length, 0);
  }
});
test('page views deduplicate renders and repeated choices, retain actual returns and clean referrers', () => {
  const f = fixture(); f.analytics.choose(true); f.analytics.choose(true);
  f.analytics.setView('overview'); f.analytics.setView('map'); f.analytics.setView('map'); f.analytics.setView('overview');
  assert.equal(f.starts.length, 1); assert.equal(f.events.length, 3);
  assert.equal(f.events[2].params.page_referrer, 'https://redthreatalert.pl/mapa');
});
test('newsletter secrets never enter views, invalid routes or event parameters', () => {
  const f = fixture(); const token = 'e'.repeat(64);
  f.analytics.setView('overview', '#newsletter/potwierdz/' + token); f.analytics.choose(true);
  f.analytics.track('newsletter_confirmed', { email: 'secret@example.test', token });
  f.analytics.track('select_content', { view: 'map', content_id: token });
  assert.equal(f.analytics.track('filter_change', { view: 'journal', filter_name: 'source', filter_value: 'secret@example.test' }), false);
  assert.equal(f.analytics.track('arbitrary', { email: 'secret@example.test' }), false);
  assert.doesNotMatch(JSON.stringify(f.events), /secret@|eeeeeeee|content_id/);
  assert.equal(f.events[0].params.page_location, 'https://redthreatalert.pl/newsletter/potwierdzenie');
  assert.equal(analyticsView('reports', '#raport/secret@example.test').path, '/raporty');
});
test('report deep links and print are distinct, category anchor is not another page', () => {
  const id = 'rpt_' + 'a'.repeat(64), f = fixture();
  f.analytics.setView('reports', '#raport/' + id); f.analytics.choose(true);
  f.analytics.setView('reports', '#raport/' + id + '/obszar/aviation');
  assert.equal(f.events.length, 1);
  f.analytics.setView('reports', '#raport/' + id + '/druk'); f.analytics.setView('reports', '#raporty');
  assert.equal(f.events.length, 3);
});
test('withdrawal and cross-tab revocation stop further collection', () => {
  const f = fixture(); f.analytics.choose(true); f.analytics.choose(false);
  const count = f.events.length; f.analytics.setView('map'); f.analytics.track('newsletter_confirmed');
  assert.equal(f.stops.length, 1); assert.equal(f.events.length, count);
  f.analytics.choose(true); f.analytics.sync(null); f.analytics.track('support_click', { placement: 'footer' });
  assert.equal(f.stops.length, 2); assert.equal(f.analytics.enabled, false);
});
test('version, future dates and expiration invalidate persisted consent; runtime expiry stops tag', () => {
  for (const value of [null, '{}', 'bad', JSON.stringify({ version: 'old', analytics: true, at: 0 }), JSON.stringify({ version: config.consent_version, analytics: true, at: 200000 })]) assert.equal(readConsent(value, config, 100000), null);
  const f = fixture(); f.analytics.choose(true); f.advance(config.consent_days * 86400000); f.analytics.check();
  assert.equal(f.stops.length, 1); assert.equal(f.analytics.consent, null); assert.equal(f.analytics.enabled, false);
  assert.equal(fixture({ raw: JSON.stringify({ version: config.consent_version, analytics: true, at: 100000 }) }).analytics.enabled, true);
});
test('unavailable storage does not break dashboard; consent remains memory-only', () => {
  const f = fixture({ storage: { getItem() { throw Error(); }, setItem() { throw Error(); } } });
  f.analytics.setView('overview'); assert.equal(f.events.length, 0); f.analytics.choose(true); assert.equal(f.events.length, 1);
});
test('only allowlisted filter values and support placements are sent', () => {
  const f = fixture(); f.analytics.choose(true);
  assert.equal(f.analytics.track('support_click', { placement: 'footer', email: 'secret@example.test' }), true);
  assert.equal(f.analytics.track('filter_change', { view: 'map', filter_name: 'area', filter_value: 'PL', token: 'secret' }), true);
  assert.equal(f.analytics.track('filter_change', { view: 'map', filter_name: 'token', filter_value: 'PL' }), false);
  assert.doesNotMatch(JSON.stringify(f.events), /secret/);
});
