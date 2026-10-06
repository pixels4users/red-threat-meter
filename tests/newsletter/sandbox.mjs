import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { PGlite } from '@electric-sql/pglite';
import { handleNewsletter } from '../../hosting/newsletter.mjs';

export const fixture=JSON.parse(execFileSync('.venv/bin/python',['tests/dashboard/make_fixture.py'],{encoding:'utf8'}));
export const env={SUPABASE_URL:'https://dubhsimiblpfcaudbvjb.supabase.co',RTA_GATEWAY_KEY:'sb_secret_test_only_never_live_123456789',RESEND_API_KEY:'re_test_only'};
export const segment='11111111-1111-4111-8111-111111111111',contact='22222222-2222-4222-8222-222222222222',broadcast='33333333-3333-4333-8333-333333333333';
export const response=data=>new Response(JSON.stringify(data),{headers:{'Content-Type':'application/json'}});
export const req=(action,body,headers={})=>new Request(`https://newsletter.example/${action}`,{method:body===undefined?'GET':'POST',headers:{apikey:env.RTA_GATEWAY_KEY,'Content-Type':'application/json',...headers},body:body===undefined?undefined:JSON.stringify(body)});

export async function setup() {
  const db=new PGlite();
  await db.exec(`create role anon;create role authenticated;create role service_role bypassrls;create schema auth;create table auth.users(id uuid primary key);create function auth.uid() returns uuid language sql stable as $$select null::uuid$$;grant usage on schema public,auth to anon,authenticated,service_role;`);
  for(const file of ['20260927170000_dashboard_publications.sql','20260929190000_rtb_v03_numeric_score.sql','20260930110000_rtb_v04_confidence.sql','20261005150000_newsletter.sql'])await db.exec(readFileSync(`supabase/migrations/${file}`,'utf8'));
  await db.query('update newsletter_settings set enabled=true,enabled_at=now()-interval \'1 hour\',segment_id=$1',[segment]);
  const calls=[];let failSend=false;
  const api={
    async db(path) {
      if(path.startsWith('newsletter_settings'))return (await db.query('select * from newsletter_settings')).rows;
      const id=new URL(`https://db.example/${path}`).searchParams.get('report_id').slice(3);
      return (await db.query('select report_id,payload,published_at from dashboard_reports where report_id=$1',[id])).rows.map(row=>({...row,published_at:new Date(row.published_at).toISOString()}));
    },
    async rpc(name,args) {
      assert.match(name,/^[a-z_]+$/);const keys=Object.keys(args);keys.forEach(k=>assert.match(k,/^p_[a-z_]+$/));
      return (await db.query(`select newsletter_${name}(${keys.map((k,i)=>`${k}=>$${i+1}`).join(',')}) as result`,Object.values(args))).rows[0].result;
    },
    async resend(path,method='GET',body,key) {
      calls.push({path,method,body,key});
      if(path==='emails')return{id:'confirmation'};
      if(path.startsWith('contacts/')&&method==='GET')return null;
      if(path==='contacts')return{id:contact};
      if(path==='broadcasts')return{id:broadcast};
      if(path.endsWith('/send')){if(failSend)throw new Error('network_timeout');return{id:broadcast};}
      if(path===`broadcasts/${broadcast}`)return{id:broadcast,status:'sent'};
      throw new Error(`Unexpected provider operation: ${path}`);
    }
  };
  const fetcher=async url=>{
    const id=new URL(url).pathname.split('/').at(-1);
    const row=(await api.db(`dashboard_reports?report_id=eq.${id}`))[0];
    return response({report:row.payload,published_at:row.published_at});
  };
  const invoke=async(action,body)=>handleNewsletter(req(action,body),env,fetcher,api);
  const saveReport=async(id='rpt_'+'a'.repeat(64),asOf=new Date().toISOString())=>{
    const report=structuredClone(fixture.complete);report.mode='live';report.report_id=id;
    report.as_of=asOf;report.window.end=report.as_of;
    report.incidents=report.incidents.filter(event=>!event.published_at||Date.parse(event.published_at)<=Date.parse(asOf));
    report.geojson.features=report.geojson.features.filter(feature=>report.incidents.some(event=>event.id===feature.id));
    await db.query(`insert into dashboard_reports(report_id,report_type,as_of,methodology_version,config_hash,source_config_hash,code_hash,score,payload) values($1,'daily',$2,'rtb-v0.2',$3,$3,$3,$4,$5)`,[id,report.as_of,'a'.repeat(64),report.rtb.score,report]);return report;
  };
  return{db,api,calls,invoke,saveReport,fetcher,setFailSend:()=>{failSend=true;}};
}
