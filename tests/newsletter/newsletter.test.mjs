import { test } from 'node:test';
import assert from 'node:assert/strict';
import { handleNewsletter, equivalent, normalizedEmail } from '../../hosting/newsletter.mjs';
import { reportEmail } from '../../hosting/newsletter-email.mjs';
import { handle } from '../../hosting/worker.mjs';

import { setup, env, segment, contact, fixture, response, req } from './sandbox.mjs';

test('private Edge endpoint and public gateway cannot be used as an open relay',async()=>{
  const blocked=async()=>assert.fail('Unexpected upstream request');
  assert.equal((await handleNewsletter(req('subscribe',{}, {apikey:'wrong'}),env,blocked)).status,401);
  const gateway={SUPABASE_URL:env.SUPABASE_URL,SUPABASE_SECRET_KEY:env.RTA_GATEWAY_KEY};
  const request=(path,init={})=>new Request(`https://redthreatalert.pl${path}`,init);
  assert.equal((await handle(request('/api/newsletter/dispatch',{method:'POST'}),gateway,blocked)).status,404);
  for(const headers of [{},{Origin:'https://evil.example'},{Origin:'https://redthreatalert.pl','Sec-Fetch-Site':'cross-site'}])
    assert.equal((await handle(request('/api/newsletter/subscribe',{method:'POST',headers}),gateway,blocked)).status,403);
  assert.equal((await handle(request('/api/newsletter/confirm',{method:'GET'}),gateway,blocked)).status,405);
  const result=await handle(request('/api/newsletter/subscribe',{method:'POST',headers:{Origin:'https://redthreatalert.pl','Content-Type':'application/json','X-RTA-Client-IP':'forged'},body:'{}'}),gateway,async(url,init)=>{
    assert.equal(url,env.SUPABASE_URL+'/functions/v1/rta-newsletter/subscribe');assert.equal(init.redirect,'manual');
    assert.equal(init.headers['X-RTA-Client-IP'],'unknown');return response({status:'accepted',email:'private@example.test'});
  });
  assert.deepEqual(await result.json(),{status:'accepted'});
});

test('double opt-in: pending, no GET activation, confirm, replay, consent receipt and erased pending email',async()=>{
  const s=await setup();try{
    const data={email:'Reader@Example.test',consent:true,consent_version:'2026-10-05'};
    assert.equal((await s.invoke('subscribe',{...data,consent:false})).status,400);
    assert.equal((await s.invoke('subscribe',data)).status,202);
    const sent=s.calls.find(x=>x.path==='emails');assert.deepEqual(sent.body.to,['reader@example.test']);
    assert.match(sent.key,/^rta-confirm-[a-f0-9]{64}$/);assert.equal(s.calls.some(x=>x.path==='contacts'),false);
    const token=/potwierdz\/([a-f0-9]{64})/.exec(sent.body.html)[1];
    assert.equal((await handleNewsletter(req('confirm'),env,s.fetcher,s.api)).status,405);
    assert.equal((await s.invoke('confirm',{token:'f'.repeat(64)})).status,410);
    assert.equal((await s.invoke('confirm',{token})).status,200);
    assert.equal((await s.invoke('confirm',{token})).status,200);
    assert.equal(s.calls.filter(x=>x.path==='contacts').length,1);
    assert.deepEqual(s.calls.find(x=>x.path==='contacts').body.segments,[{id:segment}]);
    const row=(await s.db.query('select * from newsletter_requests')).rows[0];assert.equal(row.email,null);assert.ok(row.confirmed_at);
    assert.notEqual(row.token_hash,token);assert.equal((await s.db.query('select count(*)::int as n from newsletter_consents')).rows[0].n,1);
  }finally{await s.db.close();}
});

test('cooldown, honeypot and durable limits prevent repeated confirmation mail',async()=>{
  const s=await setup();try{
    const data={email:'reader@example.test',consent:true,consent_version:'2026-10-05'};
    await s.invoke('subscribe',{...data,website:'bot'});assert.equal(s.calls.length,0);
    await s.invoke('subscribe',data);await s.invoke('subscribe',data);assert.equal(s.calls.length,1);
    for(let i=0;i<6;i++)await s.invoke('subscribe',{...data,email:`reader${i}@example.test`});
    assert.equal(s.calls.filter(x=>x.path==='emails').length,5);
    assert.equal(normalizedEmail('a@example.test\nBcc: victim@example.test'),null);
  }finally{await s.db.close();}
});

test('database denies anonymous access to subscriptions, receipts and delivery operations',async()=>{
  const s=await setup();try{
    await s.db.exec('set role anon');
    for(const table of ['newsletter_requests','newsletter_consents','newsletter_deliveries','newsletter_settings'])await assert.rejects(s.db.query(`select * from ${table}`),/permission denied/);
    await assert.rejects(s.db.query("select newsletter_claim_confirmation($1,$2)",['a'.repeat(64),contact]),/permission denied/);
  }finally{await s.db.close();}
});

test('dispatch verifies public readback and sends one immutable broadcast despite repeat or concurrency',async()=>{
  const s=await setup();try{
    const report=await s.saveReport();
    const replies=await Promise.all([s.invoke('dispatch',{report_id:report.report_id}),s.invoke('dispatch',{report_id:report.report_id})]);
    assert.ok(replies.every(x=>x.status===200));
    await s.invoke('dispatch',{report_id:report.report_id});
    assert.equal(s.calls.filter(x=>x.path==='broadcasts').length,1);
    assert.equal(s.calls.filter(x=>x.path.endsWith('/send')).length,1);
    assert.equal(s.calls.find(x=>x.path==='broadcasts').body.send,false);
    assert.equal((await s.db.query('select status from newsletter_deliveries')).rows[0].status,'sent');
    assert.ok(equivalent({a:0,b:null},{b:null,a:0}));assert.ok(!equivalent({a:0},{a:null}));
  }finally{await s.db.close();}
});

test('publication mismatch and unknown send outcomes fail closed without duplicate send',async()=>{
  const s=await setup();try{
    const report=await s.saveReport();
    assert.equal((await handleNewsletter(req('dispatch',{report_id:report.report_id}),env,async()=>response({report:{}}),s.api)).status,503);
    assert.equal(s.calls.length,0);
    s.setFailSend();assert.equal((await s.invoke('dispatch',{report_id:report.report_id})).status,503);
    assert.equal((await s.db.query('select status from newsletter_deliveries')).rows[0].status,'needs_review');
    await s.invoke('dispatch',{report_id:report.report_id});assert.equal(s.calls.filter(x=>x.path.endsWith('/send')).length,1);
  }finally{await s.db.close();}
});

test('HTML and TXT preserve null, zero, every event and frozen uncertainty; content is escaped',()=>{
  for(const source of [fixture.incomplete,fixture.complete]){
    const report=structuredClone(source);report.incidents=[{id:'newsletter-test-event',title:'<img src=x onerror=alert(1)>',summary:'Treść zamrożonego wydarzenia.',category:'context',country:'PL',location:{precision:'unknown',label:null},published_at:null,occurred_on:null,status:'unverified',sources:[{source_id:'cert_pl',publisher:'CERT',url:'https://cert.pl/test'}]}];
    const mail=reportEmail(report);
    assert.ok(mail.html.includes('&lt;img'));assert.ok(!mail.html.includes('<img src=x'));
    for(const event of report.incidents)assert.ok(mail.text.includes(event.summary));
    assert.ok(mail.html.includes('{{{RESEND_UNSUBSCRIBE_URL}}}'));
    if(report.rtb.score===null)assert.ok(mail.text.includes('Indeks RTA: niewyliczony'));
  }
  const zero=structuredClone(fixture.complete);zero.rtb.score=0;
  assert.ok(reportEmail(zero).html.includes('Zero nie potwierdza bezpieczeństwa'));
});

test('expired confirmations do not create contacts and maintenance removes obsolete personal data',async()=>{
  const s=await setup();try{
    await s.invoke('subscribe',{email:'reader@example.test',consent:true,consent_version:'2026-10-05'});
    const token=/potwierdz\/([a-f0-9]{64})/.exec(s.calls[0].body.html)[1];
    await s.db.query("update newsletter_requests set expires_at=now()-interval '1 minute'");
    assert.equal((await s.invoke('confirm',{token})).status,410);
    assert.equal(s.calls.some(x=>x.path==='contacts'),false);
    await s.db.query("update newsletter_requests set expires_at=now()-interval '7 days'");
    await s.db.query("update newsletter_rate_limits set expires_at=now()-interval '1 day'");
    await s.invoke('status');
    for(const table of ['newsletter_requests','newsletter_rate_limits'])assert.equal((await s.db.query(`select count(*)::int as n from ${table}`)).rows[0].n,0);
  }finally{await s.db.close();}
});

test('an opted-out contact is reactivated only after a new valid confirmation',async()=>{
  const s=await setup();try{
    const original=s.api.resend;s.api.resend=async(path,method,body,key)=>{
      if(path.startsWith('contacts/')&&method===undefined)return {id:contact,unsubscribed:true};
      if(path.startsWith('contacts/')&&['PATCH','POST'].includes(method)){s.calls.push({path,method,body});return {id:contact};}
      return original(path,method,body,key);
    };
    await s.invoke('subscribe',{email:'reader@example.test',consent:true,consent_version:'2026-10-05'});
    assert.equal(s.calls.some(x=>x.path.startsWith('contacts')),false);
    const token=/potwierdz\/([a-f0-9]{64})/.exec(s.calls[0].body.html)[1];
    await s.invoke('confirm',{token});
    assert.equal(s.calls.filter(x=>x.method==='PATCH').length,1);
    assert.equal(s.calls.find(x=>x.method==='PATCH').body.unsubscribed,false);
  }finally{await s.db.close();}
});

test('stale, pre-activation, superseded and same-day correction reports do not generate extra mail',async()=>{
  const s=await setup();try{
    const first=await s.saveReport();
    await s.db.query("update newsletter_settings set enabled_at=now()+interval '1 minute'");
    assert.equal((await (await s.invoke('dispatch',{report_id:first.report_id})).json()).status,'ineligible');
    await s.db.query("update newsletter_settings set enabled_at=now()-interval '1 hour'");
    const yesterday=await s.saveReport('rpt_'+'d'.repeat(64),new Date(Date.now()-86400_000).toISOString());
    assert.equal((await (await s.invoke('dispatch',{report_id:yesterday.report_id})).json()).status,'ineligible');
    const second=await s.saveReport('rpt_'+'b'.repeat(64));
    assert.equal((await (await s.invoke('dispatch',{report_id:first.report_id})).json()).status,'superseded');
    await s.invoke('dispatch',{report_id:second.report_id});
    const correction=await s.saveReport('rpt_'+'c'.repeat(64));
    assert.equal((await (await s.invoke('dispatch',{report_id:correction.report_id})).json()).status,'already_handled');
    assert.equal(s.calls.filter(x=>x.path.endsWith('/send')).length,1);
  }finally{await s.db.close();}
});
