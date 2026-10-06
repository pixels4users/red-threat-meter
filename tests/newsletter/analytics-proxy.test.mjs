import { test } from 'node:test';
import assert from 'node:assert/strict';
import { proxyNewsletter } from '../../hosting/newsletter-proxy.mjs';
import config from '../../config/dashboard.json' with { type: 'json' };
const env = { SUPABASE_URL: `https://${config.supabase_project_ref}.supabase.co`, SUPABASE_SECRET_KEY: 'sb_secret_test_only' };
const request = action => new Request(`https://redthreatalert.pl/api/newsletter/${action}`, {method:'POST', headers:{Origin:'https://redthreatalert.pl','Content-Type':'application/json'},body:'{}'});
test('public confirmation passes only the trusted boolean and strips subscriber data', async () => {
  for (const newly_confirmed of [true, false, 'true', null]) {
    const response = await proxyNewsletter(request('confirm'), env, async () => Response.json({status:'confirmed',newly_confirmed,email:'private@example.test',token:'secret'}));
    assert.deepEqual(await response.json(), {status:'confirmed',...(typeof newly_confirmed === 'boolean' ? {newly_confirmed} : {})});
  }
});
test('older Edge response and subscribe cannot fabricate confirmation conversion', async () => {
  const old = await proxyNewsletter(request('confirm'), env, async () => Response.json({status:'confirmed'}));
  assert.deepEqual(await old.json(), {status:'confirmed'});
  const subscribe = await proxyNewsletter(request('subscribe'), env, async () => Response.json({status:'accepted',newly_confirmed:true}, {status:202}));
  assert.deepEqual(await subscribe.json(), {status:'accepted'});
});
