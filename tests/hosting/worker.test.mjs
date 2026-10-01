import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { handle } from '../../hosting/worker.mjs';

// Generated in a temporary store; these rows never reach live Supabase.
const fixtures = JSON.parse(execFileSync('.venv/bin/python', ['tests/dashboard/make_fixture.py'], { encoding: 'utf8' }));
const env = { SUPABASE_URL: 'https://dubhsimiblpfcaudbvjb.supabase.co', SUPABASE_SECRET_KEY: 'sb_secret_test_only' };
const stamp = '2026-10-01T12:00:00.123456+00:00';
const request = (path, init) => new Request(`https://dashboard.example${path}`, init);
const reply = data => new Response(JSON.stringify(data), { headers: { 'Content-Type': 'application/json' } });
const row = (payload = { ...fixtures.complete, mode: 'live' }) => ({ report_id: payload.report_id, payload, published_at: stamp });
const blockedFetch = async () => { assert.fail('No upstream request is permitted'); };
const history = index => ({ report_id: 'rpt_' + index.toString(16).padStart(64, '0'), report_type: 'daily',
  as_of: '2026-10-01T11:00:00+00:00', published_at: stamp, methodology_version: 'rtb-v0.4',
  config_hash: 'a'.repeat(64), source_config_hash: 'b'.repeat(64), code_hash: 'c'.repeat(64),
  score: 0, supersedes: null, confidence_key: 'd'.repeat(64) });

test('latest returns the existing envelope and sends the key only to the pinned table', async () => {
  const current = row(); let calls = 0;
  const result = await handle(request('/api/latest'), env, async (url, init) => {
    calls++;
    const u = new URL(url);
    assert.equal(u.origin, env.SUPABASE_URL);
    assert.equal(u.pathname, '/rest/v1/dashboard_reports');
    assert.equal(u.searchParams.get('report_type'), 'eq.daily');
    assert.equal(u.searchParams.get('limit'), '1');
    assert.equal(init.method, 'GET'); assert.equal(init.redirect, 'error');
    assert.equal(init.headers.apikey, env.SUPABASE_SECRET_KEY);
    return reply([current]);
  });
  assert.equal(calls, 1); assert.equal(result.status, 200);
  assert.equal(result.headers.get('cache-control'), 'no-store');
  const body = await result.text(); assert.ok(!body.includes(env.SUPABASE_SECRET_KEY));
  assert.deepEqual(JSON.parse(body), { report: current.payload, published_at: stamp });
});

test('configuration has no secrets or project identifiers', async () => {
  const result = await handle(request('/api/config'), env, blockedFetch);
  assert.deepEqual(await result.json(), { refresh_seconds: 30, stale_after_hours: 30 });
});

test('no write proxy, arbitrary query, duplicate parameter or cross-origin read', async () => {
  for (const path of ['/api/latest?type=other', '/api/latest?type=daily&type=weekly', '/api/latest?select=*',
    '/api/reports?offset=-1', '/api/reports?offset=100001', '/api/reports?anchor=not-a-date']) {
    assert.equal((await handle(request(path), env, blockedFetch)).status, 400, path);
  }
  for (const method of ['POST', 'DELETE', 'PUT', 'OPTIONS']) {
    assert.equal((await handle(request('/api/latest', { method }), env, blockedFetch)).status, 405);
  }
  assert.equal((await handle(request('/api/latest', { headers: { Origin: 'https://other.example' } }), env, blockedFetch)).status, 403);
  assert.equal((await handle(request('/api/latest', { headers: { 'Sec-Fetch-Site': 'cross-site' } }), env, blockedFetch)).status, 403);
});

test('raw files, unknown paths, RPC and arbitrary report ids stay unavailable', async () => {
  for (const path of ['/.env.dashboard', '/data/database/osint.sqlite3', '/server/index.js', '/api/rpc/dashboard_publish', '/api/reports/nope', '/assets/../../.env']) {
    assert.equal((await handle(request(path), env, blockedFetch)).status, 404, path);
  }
});

test('wrong project configuration never sends credentials', async () => {
  assert.equal((await handle(request('/api/latest'), { ...env, SUPABASE_URL: 'https://wrong.example' }, blockedFetch)).status, 503);
});

test('fixture, extra private fields and mismatched row identity are rejected', async () => {
  const bad = [row(fixtures.complete), row({ ...fixtures.complete, mode: 'live', raw_materials: ['private'] }),
    { ...row(), report_id: 'rpt_' + 'f'.repeat(64) }];
  for (const value of bad) assert.equal((await handle(request('/api/latest'), env, async () => reply([value]))).status, 503);
});

test('legacy incomplete score remains null while v0.4 zero remains numeric', async () => {
  const incomplete = { ...fixtures.incomplete, mode: 'live' };
  const zero = structuredClone({ ...fixtures.complete, mode: 'live' });
  zero.provenance.methodology_version = 'rtb-v0.4'; zero.rtb.score = 0; zero.rtb.status = 'provisional';
  zero.rtb.confidence = { percent: 0, method: 'coverage-review-history-v1', calibrated: false,
    coverage_percent: 0, review_percent: 0, history_percent: 0, comparison_key: 'a'.repeat(64),
    domains: [{ id: 'gnss', label: 'Zakłócenia nawigacji', percent: 0 }] };
  for (const report of [incomplete, zero]) {
    const result = await handle(request('/api/latest'), env, async () => reply([row(report)]));
    assert.equal(result.status, 200);
    assert.equal((await result.json()).report.rtb.score, report.rtb.score);
  }
});

test('unavailable upstream does not pretend the database is empty and does not leak errors', async () => {
  for (const fetcher of [async () => new Response('sensitive upstream body', { status: 401 }), async () => { throw new Error('secret in network error'); }, async () => new Response('{broken')]) {
    const result = await handle(request('/api/latest'), env, fetcher);
    assert.equal(result.status, 503);
    assert.deepEqual(await result.json(), { error: 'temporarily_unavailable' });
  }
  assert.deepEqual(await (await handle(request('/api/latest'), env, async () => reply([]))).json(), null);
});

test('response size limit rejects declared and streamed oversized upstream data', async () => {
  for (const response of [new Response('[]', { headers: { 'content-length': '12000001' } }), new Response(' '.repeat(12_000_001))]) {
    assert.equal((await handle(request('/api/latest'), env, async () => response)).status, 503);
  }
});

test('history uses the database clock and stable pagination without forwarding extra fields', async () => {
  let calls = 0;
  const result = await handle(request('/api/reports'), env, async url => {
    const u = new URL(url); calls++;
    if (calls === 1) return reply([{ published_at: stamp }]);
    assert.equal(u.searchParams.get('published_at'), `lte.${stamp}`);
    assert.equal(u.searchParams.get('order'), 'as_of.desc,published_at.desc,report_id.desc');
    return reply(Array.from({ length: 31 }, (_, i) => ({ ...history(i), unexpected: 'do not export' })));
  });
  const body = await result.json(); assert.equal(result.status, 200);
  assert.equal(calls, 2); assert.equal(body.anchor, stamp); assert.equal(body.next_offset, 30);
  assert.equal(body.items.length, 30); assert.ok(!('unexpected' in body.items[0]));
});

test('report view and both downloads use the identical published report', async () => {
  const current = row();
  for (const suffix of ['', '/json', '/geojson']) {
    const result = await handle(request(`/api/reports/${current.report_id}${suffix}`), env, async url => {
      assert.equal(new URL(url).searchParams.get('report_id'), `eq.${current.report_id}`);
      return reply([current]);
    });
    assert.equal(result.status, 200);
    assert.deepEqual(await result.json(), suffix === '/json' ? current.payload : suffix === '/geojson' ? current.payload.geojson : { report: current.payload, published_at: stamp });
    if (suffix) assert.ok(result.headers.get('content-disposition').startsWith('attachment;'));
  }
});

test('static assets are served only from the build binding', async () => {
  let calls = 0;
  const result = await handle(request('/assets/app-123.js'), { ASSETS: { fetch: async req => { calls++; return new Response(req.url); } } }, blockedFetch);
  assert.equal(result.status, 200); assert.equal(calls, 1);
});
