import config from '../config/newsletter.json' with { type: 'json' };
import dashboard from '../config/dashboard.json' with { type: 'json' };
import { checked } from './worker.mjs';
import { confirmationEmail, reportEmail } from './newsletter-email.mjs';
import { newsletterJSON as json, boundedJSON } from './newsletter-http.mjs';
import { dateKey } from '../web/data.js';

const ORIGIN = `https://${dashboard.supabase_project_ref}.supabase.co`;
const UUID = /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/;
const REPORT_ID = /^rpt_[a-f0-9]{64}$/;
const HEX = /^[a-f0-9]{64}$/;
const encoder = new TextEncoder();
const hex = bytes => [...new Uint8Array(bytes)].map(b => b.toString(16).padStart(2,'0')).join('');
export const sha256 = async value => hex(await crypto.subtle.digest('SHA-256', encoder.encode(value)));
const randomToken = () => hex(crypto.getRandomValues(new Uint8Array(32)));
async function privateHash(value, key) {
  const k = await crypto.subtle.importKey('raw', encoder.encode(key), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return hex(await crypto.subtle.sign('HMAC', k, encoder.encode(value)));
}
async function sameSecret(left, right) {
  if (typeof left !== 'string' || typeof right !== 'string' || right.length < 24) return false;
  const a = await sha256(left), b = await sha256(right);
  let diff = 0; for (let i=0; i<a.length; i++) diff |= a.charCodeAt(i)^b.charCodeAt(i);
  return diff === 0;
}
export function normalizedEmail(value) {
  if (typeof value !== 'string') return null;
  const email = value.trim().toLowerCase();
  return email.length <= 254 && /^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$/.test(email) ? email : null;
}
export function equivalent(a, b) {
  if (a === b) return true;
  if (a === null || b === null || typeof a !== 'object' || typeof b !== 'object' || Array.isArray(a) !== Array.isArray(b)) return false;
  const keys = Object.keys(a);
  return keys.length === Object.keys(b).length && keys.every(k => Object.hasOwn(b,k) && equivalent(a[k],b[k]));
}
class UpstreamError extends Error { constructor(status) { super('upstream'); this.status = status; } }

export function newsletterClients(env, fetcher) {
  const key = env.RTA_GATEWAY_KEY;
  if (env.SUPABASE_URL !== ORIGIN || !/^(sb_secret_|eyJ)/.test(key ?? '') || !/^re_[\w-]+$/.test(env.RESEND_API_KEY ?? '')) throw new Error('configuration');
  async function db(path, body) {
    const headers = { apikey: key, 'Content-Type': 'application/json' };
    if (key.startsWith('eyJ')) headers.Authorization = `Bearer ${key}`;
    const response = await fetcher(`${ORIGIN}/rest/v1/${path}`, { method: body === undefined ? 'GET' : 'POST', headers,
      body: body === undefined ? undefined : JSON.stringify(body), redirect:'manual', signal:AbortSignal.timeout(10_000) });
    if (!response.ok) throw new UpstreamError(response.status);
    return response.status === 204 ? null : boundedJSON(response,12_000_000);
  }
  let nextCall = 0;
  async function resend(path, method = 'GET', body, idempotency) {
    // Resend's request limit applies even to contact + segment operations in one flow.
    if (nextCall > Date.now()) await new Promise(resolve => setTimeout(resolve, nextCall-Date.now()));
    nextCall = Date.now()+600;
    const headers = { Authorization:`Bearer ${env.RESEND_API_KEY}`, 'Content-Type':'application/json', 'User-Agent':'RedThreatAlert/1.0' };
    if (idempotency) headers['Idempotency-Key'] = idempotency;
    const response = await fetcher(`https://api.resend.com/${path}`, { method, headers, body:body === undefined ? undefined : JSON.stringify(body),
      redirect:'manual', signal:AbortSignal.timeout(12_000) });
    if (!response.ok) throw new UpstreamError(response.status);
    return response.status === 204 ? null : boundedJSON(response,1_000_000);
  }
  return { db, rpc:(name,body) => db(`rpc/newsletter_${name}`,body), resend };
}

// This Edge Function is private. Only the site's server and the authorized
// publisher possess RTA_GATEWAY_KEY; the public browser never receives it.
export async function handleNewsletter(request, env, fetcher = (...args) => globalThis.fetch(...args), clients = null) {
  if (!await sameSecret(request.headers.get('apikey'),env.RTA_GATEWAY_KEY)) return json({ error:'unauthorized' },401);
  const action = new URL(request.url).pathname.split('/').at(-1);
  if (!['status','subscribe','confirm','dispatch'].includes(action)) return json({error:'not_found'},404);
  if (request.method !== (action === 'status' ? 'GET' : 'POST')) return json({error:'method_not_allowed'},405);
  let body;
  try { if (action !== 'status') body = await boundedJSON(request,2048); }
  catch { return json({error:'invalid_request'},400); }
  try {
    const api = clients ?? newsletterClients(env,fetcher);
    await api.rpc('maintain',{});
    const rows = await api.db('newsletter_settings?select=enabled,segment_id,enabled_at&id=eq.true');
    const setting = rows[0];
    if (!setting?.enabled || !UUID.test(setting.segment_id ?? '')) return json({status:'disabled'},action === 'status' ? 200 : 503);
    if (action === 'status') return json({status:'enabled'});
    if (action === 'subscribe') return await subscribe(body,request,env,api);
    if (action === 'confirm') return await confirm(body,setting,api);
    return await dispatch(body,setting,api,fetcher);
  } catch (error) {
    console.error('newsletter_operation_failed',error instanceof UpstreamError ? `upstream_${error.status}` : 'operation');
    return json({error:'temporarily_unavailable'},503);
  }
}

async function subscribe(body,request,env,api) {
  const email = normalizedEmail(body?.email);
  if (!email || body.consent !== true || body.consent_version !== config.consent_version) return json({error:'invalid_request'},400);
  if (body.website) return json({status:'accepted'},202);
  const token = randomToken(), tokenHash = await sha256(token);
  const result = await api.rpc('request',{ p_email:email, p_email_hash:await privateHash(`email:${email}`,env.RTA_GATEWAY_KEY),
    p_token_hash:tokenHash,p_ip_hash:await privateHash(`ip:${request.headers.get('X-RTA-Client-IP') ?? 'unknown'}`,env.RTA_GATEWAY_KEY),p_consent_version:config.consent_version });
  if (result.status === 'disabled') return json({status:'disabled'},503);
  if (result.status === 'limited') return json({error:'limited'},429);
  if (result.send) await api.resend('emails','POST',{ ...confirmationEmail(token),to:[email] },`rta-confirm-${tokenHash}`);
  return json({status:'accepted'},202);
}

async function confirm(body,setting,api) {
  if (!HEX.test(body?.token ?? '')) return json({error:'invalid_request'},400);
  const tokenHash = await sha256(body.token), owner = crypto.randomUUID();
  const args = { p_token_hash:tokenHash,p_owner:owner };
  const claim = await api.rpc('claim_confirmation',args);
  if (claim.status !== 'claimed') return json({status:claim.status},claim.status === 'confirmed' ? 200 : claim.status === 'expired' ? 410 : 409);
  try {
    let contact;
    try { contact = await api.resend(`contacts/${encodeURIComponent(claim.email)}`); }
    catch (error) { if (!(error instanceof UpstreamError) || error.status !== 404) throw error; }
    if (!contact) contact = await api.resend('contacts','POST',{email:claim.email,unsubscribed:false,segments:[{id:setting.segment_id}]});
    else {
      if (!UUID.test(contact.id ?? '')) throw new Error('invalid_contact');
      // Opt-out is changed only after a new, valid double opt-in confirmation.
      await api.resend(`contacts/${contact.id}`,'PATCH',{unsubscribed:false});
      await api.resend(`contacts/${contact.id}/segments/${setting.segment_id}`,'POST');
    }
    if (!UUID.test(contact.id ?? '')) throw new Error('invalid_contact');
    await api.rpc('finish_confirmation',{...args,p_contact_id:contact.id});
    return json({status:'confirmed'});
  } catch (error) {
    await api.rpc('finish_confirmation',{...args,p_contact_id:null}).catch(()=>{});
    throw error;
  }
}

async function dispatch(body,setting,api,fetcher) {
  const id = body?.report_id;
  if (!REPORT_ID.test(id ?? '')) return json({error:'invalid_request'},400);
  const rows = await api.db(`dashboard_reports?select=report_id,payload,published_at&report_id=eq.${id}&limit=1`);
  if (!rows.length) return json({status:'ineligible'});
  const envelope = checked(rows[0]), report = envelope.report;
  if (report.report_type !== 'daily' || dateKey(report.as_of) !== dateKey(new Date()) ||
      Date.parse(report.as_of)>Date.now()+300_000 || Date.parse(envelope.published_at)<Date.parse(setting.enabled_at)) return json({status:'ineligible'});
  // The public website must actually expose this exact frozen publication.
  const publicResponse = await fetcher(new URL(`api/reports/${id}`,config.site_url).href,{redirect:'manual',signal:AbortSignal.timeout(15_000),headers:{Accept:'application/json'}});
  if (!publicResponse.ok) throw new Error('publication_unavailable');
  const publicEnvelope = await boundedJSON(publicResponse,12_000_000);
  if (!equivalent(envelope,publicEnvelope)) throw new Error('publication_mismatch');
  let reference = null;
  if (REPORT_ID.test(report.rtb.trend?.reference_report_id ?? '')) {
    const previous = await api.db(`dashboard_reports?select=report_id,payload,published_at&report_id=eq.${report.rtb.trend.reference_report_id}&limit=1`);
    if (previous.length) reference = checked(previous[0]).report;
  }
  const mail = reportEmail(report,{reference});
  if (encoder.encode(JSON.stringify(mail)).length>2_000_000) throw new Error('email_size_limit');
  const owner = crypto.randomUUID(), args = {p_report_id:id,p_owner:owner};
  const job = await api.rpc('claim_delivery',{...args,p_mail:mail});
  if (!['creating','ready','sending'].includes(job.status)) return json({status:job.status, ...(job.delivery_status ? {delivery_status:job.delivery_status} : {})});
  let broadcastId = job.broadcast_id;
  try {
    if (job.status === 'creating') {
      const draft = await api.resend('broadcasts','POST',{...job.mail,segment_id:setting.segment_id,name:`rta-${job.report_day}-${id}`,send:false});
      if (!UUID.test(draft.id ?? '')) throw new Error('invalid_broadcast');
      broadcastId = draft.id;
      await api.rpc('save_broadcast',{...args,p_broadcast_id:broadcastId});
    }
    if (job.status === 'sending') {
      const existing = await api.resend(`broadcasts/${broadcastId}`);
      const sent = ['sent','queued','sending','scheduled'].includes(existing.status);
      await api.rpc('finish_delivery',{...args,p_status:sent?'sent':'needs_review',p_reason:sent?null:'send_outcome_unknown'});
      return json({status:sent?'sent':'needs_review'});
    }
    if (!await api.rpc('begin_send',args)) return json({status:'busy'});
    // Broadcast endpoints do not support email idempotency keys. Persist this
    // attempt BEFORE calling Resend and never blindly repeat a send after timeout.
    await api.resend(`broadcasts/${broadcastId}/send`,'POST',{});
    await api.rpc('finish_delivery',{...args,p_status:'sent',p_reason:null});
    return json({status:'sent',report_id:id});
  } catch (error) {
    await api.rpc('finish_delivery',{...args,p_status:'needs_review',p_reason:broadcastId?'send_outcome_unknown':'draft_outcome_unknown'}).catch(()=>{});
    throw error;
  }
}
