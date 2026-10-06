import config from '../config/dashboard.json' with { type: 'json' };
import { newsletterJSON as json, boundedJSON } from './newsletter-http.mjs';

export async function proxyNewsletter(request, env, fetcher) {
  const url = new URL(request.url), action = url.pathname.slice('/api/newsletter/'.length);
  if (!['status','subscribe','confirm'].includes(action) || url.search) return json({ error: 'not_found' }, 404);
  if (request.method !== (action === 'status' ? 'GET' : 'POST')) return json({ error: 'method_not_allowed' }, 405);
  if (request.headers.get('Sec-Fetch-Site') === 'cross-site' ||
    request.headers.has('Origin') && request.headers.get('Origin') !== url.origin) return json({ error: 'forbidden' }, 403);
  if (request.method === 'POST' && request.headers.get('Origin') !== url.origin) return json({ error: 'forbidden' }, 403);
  if (request.method === 'POST' && !/^application\/json(?:;|$)/i.test(request.headers.get('Content-Type') ?? '')) return json({ error: 'invalid_request' }, 415);
  const origin = `https://${config.supabase_project_ref}.supabase.co`;
  if (env.SUPABASE_URL !== origin || !/^(sb_secret_|eyJ)/.test(env.SUPABASE_SECRET_KEY ?? '')) return json({ error: 'temporarily_unavailable' }, 503);
  let body;
  try { if (request.method === 'POST') body = JSON.stringify(await boundedJSON(request, 2048)); }
  catch { return json({ error: 'invalid_request' }, 400); }
  try {
    const response = await fetcher(`${origin}/functions/v1/rta-newsletter/${action}`, {
      method: request.method, redirect: 'manual', signal: AbortSignal.timeout(25_000),
      headers: { apikey: env.SUPABASE_SECRET_KEY, 'Content-Type': 'application/json',
        // The public client cannot choose a different caller IP.
        'X-RTA-Client-IP': request.headers.get('CF-Connecting-IP') ?? 'unknown' }, body });
    if (![200,202,400,409,410,429,503].includes(response.status)) throw new Error('upstream');
    const value = await boundedJSON(response);
    // Only a fixed result vocabulary crosses the public gateway.
    const allowed = ['enabled','disabled','accepted','confirmed','expired','busy','invalid_request','temporarily_unavailable','limited'];
    const status = value.status ?? value.error;
    if (!allowed.includes(status)) throw new Error('upstream');
    return json(value.error ? { error: status } : { status }, response.status);
  } catch { return json({ error: 'temporarily_unavailable' }, 503); }
}
