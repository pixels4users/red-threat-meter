import validateReport from './.generated/validate-report.cjs';
import config from '../config/dashboard.json' with { type: 'json' };

const ORIGIN = `https://${config.supabase_project_ref}.supabase.co`;
const REPORT_ID = /^rpt_[a-f0-9]{64}$/;
const HASH = /^[a-f0-9]{64}$/;
const MAX_BYTES = 12_000_000;
const HISTORY_FIELDS = ['report_id', 'report_type', 'as_of', 'published_at', 'methodology_version',
  'config_hash', 'source_config_hash', 'code_hash', 'score', 'supersedes', 'confidence_key'];
const ORDER = 'as_of.desc,published_at.desc,report_id.desc';

class InvalidRequest extends Error {}
const timestamp = value => typeof value === 'string' && value.length <= 40 &&
  /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,9})?(?:Z|[+-]\d\d:\d\d)$/.test(value) && Number.isFinite(Date.parse(value));
const unique = rows => new Set(rows.map(x => x.id)).size === rows.length;

function json(data, status = 200, filename) {
  const headers = { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer' };
  if (filename) headers['Content-Disposition'] = `attachment; filename="${filename}"`;
  return new Response(JSON.stringify(data), { status, headers });
}

function sourceURL(value) {
  const url = new URL(value);
  if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password ||
      ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)) throw new Error('invalid_source');
  for (const key of url.searchParams.keys()) {
    if (/^(token|access_token|key|api_key|apikey|signature|password|secret|auth)$/i.test(key)) throw new Error('invalid_source');
  }
}

function checked(row) {
  const r = row?.payload;
  // Publication's Python writer verifies the content hash and editorial receipt.
  // At the HTTP boundary, enforce the same closed schema and row identity without
  // reserializing Python floating point numbers into a different hash in JS.
  if (!validateReport(r) || r.mode !== 'live' || row.report_id !== r.report_id ||
      !timestamp(row.published_at) || !unique(r.incidents) || !unique(r.sources) ||
      Date.parse(r.window.end) !== Date.parse(r.as_of) || Date.parse(r.window.start) > Date.parse(r.as_of)) {
    throw new Error('invalid_report');
  }
  for (const s of r.sources) sourceURL(s.url);
  for (const i of r.incidents) {
    for (const s of i.sources) sourceURL(s.url);
    if (i.published_at && Date.parse(i.published_at) > Date.parse(r.as_of)) throw new Error('invalid_report');
  }
  const expected = new Map(r.incidents.filter(i => i.location.geometry).map(i => [i.id, i.location.geometry]));
  if (expected.size !== r.geojson.features.length || !unique(r.geojson.features) ||
      r.geojson.features.some(f => JSON.stringify(f.geometry) !== JSON.stringify(expected.get(f.id)))) throw new Error('invalid_map');
  if (r.commentary.text !== null && (!r.commentary.review ||
      r.commentary.review.snapshot_sha256 !== r.provenance.snapshot_sha256 || r.rtb.score === null)) throw new Error('invalid_commentary');
  if (r.commentary.text === null && r.commentary.review) throw new Error('invalid_commentary');
  if (r.commentary.sections && (!r.commentary.text || !r.commentary.review?.sections_sha256 || Object.values(r.commentary.sections).some(t => !r.commentary.text.includes(t)))) throw new Error('invalid_commentary');
  return { report: r, published_at: row.published_at };
}

function historyRow(row) {
  if (!REPORT_ID.test(row.report_id) || !['daily', 'weekly'].includes(row.report_type) ||
      !timestamp(row.as_of) || !timestamp(row.published_at) ||
      typeof row.methodology_version !== 'string' || !/^[\w.:-]{1,150}$/.test(row.methodology_version) ||
      ['config_hash', 'source_config_hash', 'code_hash'].some(k => !HASH.test(row[k])) ||
      !(row.score === null || Number.isFinite(row.score) && row.score >= 0 && row.score <= 100) ||
      !(row.supersedes === null || REPORT_ID.test(row.supersedes)) ||
      !(row.confidence_key === null || HASH.test(row.confidence_key))) throw new Error('invalid_history');
  return Object.fromEntries(HISTORY_FIELDS.map(k => [k, row[k]]));
}

function query(url, allowed) {
  for (const key of url.searchParams.keys()) {
    if (!allowed.includes(key) || url.searchParams.getAll(key).length !== 1) throw new InvalidRequest();
  }
  const kind = url.searchParams.get('type') ?? config.report_type;
  if (!['daily', 'weekly'].includes(kind)) throw new InvalidRequest();
  return kind;
}

async function readRows(env, params, fetcher) {
  const key = env.SUPABASE_SECRET_KEY;
  if (env.SUPABASE_URL !== ORIGIN || typeof key !== 'string' || !/^(sb_secret_|eyJ)/.test(key)) throw new Error('configuration');
  const headers = { apikey: key, Accept: 'application/json' };
  if (key.startsWith('eyJ')) headers.Authorization = `Bearer ${key}`;
  // No request URL, user headers, table name or SQL is forwarded to Supabase.
  const response = await fetcher(`${ORIGIN}/rest/v1/dashboard_reports?${new URLSearchParams(params)}`,
    // This hosting runtime rejects redirect:'error'. Manual mode never forwards
    // credentials to a redirect destination; all 3xx responses fail below.
    { method: 'GET', headers, redirect: 'manual', signal: AbortSignal.timeout(10_000) });
  if (!response.ok || Number(response.headers.get('content-length')) > MAX_BYTES) throw new Error('upstream');
  const reader = response.body?.getReader();
  if (!reader) throw new Error('upstream');
  const chunks = []; let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_BYTES) { await reader.cancel(); throw new Error('size_limit'); }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const bytes = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  const rows = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
  if (!Array.isArray(rows) || rows.length > 31) throw new Error('upstream');
  return rows;
}

// Preserve the receiver for runtimes whose native fetch requires it.
export async function handle(request, env, fetcher = (...args) => globalThis.fetch(...args)) {
  const url = new URL(request.url);
  if (!['GET', 'HEAD'].includes(request.method)) return json({ error: 'method_not_allowed' }, 405);
  if (!url.pathname.startsWith('/api/')) {
    // The asset binding contains only the built frontend, never the repository.
    if (!(url.pathname === '/' || url.pathname === '/index.html' || url.pathname === '/favicon.svg' ||
        /^\/assets\/[a-zA-Z0-9_.-]+$/.test(url.pathname))) return json({ error: 'not_found' }, 404);
    if (!env.ASSETS) return json({ error: 'temporarily_unavailable' }, 503);
    return env.ASSETS.fetch(request);
  }
  if (request.method !== 'GET') return json({ error: 'method_not_allowed' }, 405);
  if (request.headers.get('Sec-Fetch-Site') === 'cross-site') return json({ error: 'forbidden' }, 403);
  const origin = request.headers.get('Origin');
  if (origin && origin !== url.origin) return json({ error: 'forbidden' }, 403);
  try {
    if (url.pathname === '/api/config') {
      query(url, []);
      return json({ refresh_seconds: config.refresh_seconds, stale_after_hours: config.stale_after_hours });
    }
    if (url.pathname === '/api/latest') {
      const kind = query(url, ['type']);
      const rows = await readRows(env, { select: 'report_id,payload,published_at', report_type: `eq.${kind}`, order: ORDER, limit: '1' }, fetcher);
      const result = rows.length ? checked(rows[0]) : null;
      if (result && result.report.report_type !== kind) throw new Error('invalid_type');
      return json(result);
    }
    if (url.pathname === '/api/reports') {
      const kind = query(url, ['type', 'offset', 'anchor']);
      const offset = url.searchParams.get('offset') ?? '0';
      if (!/^(0|[1-9]\d{0,5})$/.test(offset) || Number(offset) > 100000) throw new InvalidRequest();
      let anchor = url.searchParams.get('anchor');
      if (anchor !== null && !timestamp(anchor)) throw new InvalidRequest();
      if (anchor === null) {
        const newest = await readRows(env, { select: 'published_at', order: 'published_at.desc', limit: '1' }, fetcher);
        if (!newest.length) return json({ items: [], anchor: new Date().toISOString(), next_offset: null });
        anchor = newest[0].published_at;
        if (!timestamp(anchor)) throw new Error('invalid_anchor');
      }
      const rows = await readRows(env, { select: HISTORY_FIELDS.join(','), report_type: `eq.${kind}`, published_at: `lte.${anchor}`, order: ORDER, limit: '31', offset }, fetcher);
      const items = rows.slice(0, 30).map(historyRow);
      if (items.some(r => r.report_type !== kind || Date.parse(r.published_at) > Date.parse(anchor))) throw new Error('invalid_history');
      return json({ items, anchor, next_offset: rows.length > 30 ? Number(offset) + 30 : null });
    }
    const match = /^\/api\/reports\/(rpt_[a-f0-9]{64})(?:\/(json|geojson))?$/.exec(url.pathname);
    if (!match) return json({ error: 'not_found' }, 404);
    query(url, []);
    const rows = await readRows(env, { select: 'report_id,payload,published_at', report_id: `eq.${match[1]}`, limit: '1' }, fetcher);
    if (!rows.length) return json({ error: 'not_found' }, 404);
    const result = checked(rows[0]);
    if (result.report.report_id !== match[1]) throw new Error('invalid_identity');
    return match[2] ? json(match[2] === 'json' ? result.report : result.report.geojson, 200, `${match[1]}.${match[2]}`) : json(result);
  } catch (error) {
    if (error instanceof InvalidRequest) return json({ error: 'invalid_request' }, 400);
    // Deliberately exclude exception bodies, source text and credentials.
    const reasons = ['configuration', 'upstream', 'size_limit', 'invalid_report', 'invalid_source',
      'invalid_map', 'invalid_commentary', 'invalid_history', 'invalid_anchor', 'invalid_identity', 'invalid_type'];
    console.error('dashboard_read_failed', JSON.stringify({
      reason: reasons.includes(error.message) ? error.message : 'runtime',
      error_type: error instanceof TypeError ? 'TypeError' : 'Error',
      runtime_detail: /redirect/i.test(error.message) ? 'redirect_mode' :
        /header/i.test(error.message) ? 'header_format' :
        /invocation|this reference/i.test(error.message) ? 'native_receiver' :
        /decod|encoding|fatal/i.test(error.message) ? 'decoder' :
        /fetch|network/i.test(error.message) ? 'network' : 'other',
      key_has_whitespace: /\s/.test(env?.SUPABASE_SECRET_KEY ?? ''),
      url_configured: typeof env?.SUPABASE_URL === 'string',
      url_matches: env?.SUPABASE_URL === ORIGIN,
      key_configured: typeof env?.SUPABASE_SECRET_KEY === 'string',
      key_supported: /^(sb_secret_|eyJ)/.test(env?.SUPABASE_SECRET_KEY ?? ''),
      timeout_supported: typeof AbortSignal.timeout === 'function'
    }));
    return json({ error: 'temporarily_unavailable' }, 503);
  }
}

export default { fetch: (request, env) => handle(request, env) };
