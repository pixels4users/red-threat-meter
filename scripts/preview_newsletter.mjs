// Entirely local: no credentials are loaded and every upstream is simulated.
import { createServer } from 'node:http';
import { readFile, readdir } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
import { setup, env as privateEnv, response as json } from '../tests/newsletter/sandbox.mjs';
import { handle, checked } from '../hosting/worker.mjs';
import { handleNewsletter } from '../hosting/newsletter.mjs';
import { reportEmail } from '../hosting/newsletter-email.mjs';

const origin='http://127.0.0.1:8771', sandbox=await setup(), rows=[];
for (const cycle of await readdir('data/analysis/cycles')) {
  try {
    const report=JSON.parse(await readFile(`data/analysis/cycles/${cycle}/publication-daily.json`,'utf8'));
    const verify=JSON.parse(await readFile(`data/analysis/cycles/${cycle}/verification.json`,'utf8'));
    if (verify.report_id!==report.report_id)continue;
    const row={report_id:report.report_id,payload:report,published_at:verify.publication?.published_at ?? verify.verified_at,
      report_type:report.report_type,as_of:report.as_of,...report.provenance,score:report.rtb.score,
      supersedes:report.supersedes ?? null,confidence_key:report.rtb.confidence?.key ?? null};
    checked(row); rows.push(row);
  } catch { /* Ignore unfinished local cycles. */ }
}
rows.sort((a,b)=>b.as_of.localeCompare(a.as_of)||b.published_at.localeCompare(a.published_at));
if(!rows.length)throw new Error('A verified local publication is required for the preview');
const latest=rows[0], reference=rows.find(r=>r.report_id===latest.payload.rtb.trend?.reference_report_id)?.payload;
const reportMail=reportEmail(latest.payload,{reference});
console.log(`Report preview: ${Buffer.byteLength(reportMail.html)} HTML bytes, ${latest.payload.incidents.length} events`);
const client=resolve('build/hosted/dist/client'), mime={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.json':'application/json'};
const html=text=>new Response(text,{headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'}});
const localEmailLinks=text=>text.replaceAll('https://redthreatalert.pl/', origin+'/');
const marker='<div style="padding:10px 16px;background:#f3efe2;color:#171717;font:14px/1.5 Arial">Podgląd lokalny newslettera — wiadomości nie są wysyłane. <a href="/__newsletter_preview">Podgląd wiadomości</a></div>';
const env={SUPABASE_URL:privateEnv.SUPABASE_URL,SUPABASE_SECRET_KEY:privateEnv.RTA_GATEWAY_KEY,ASSETS:{async fetch(request){
  const url=new URL(request.url),pathname=url.pathname;
  const target=resolve(client,pathname==='/'?'index.html':'.'+pathname);
  if(!target.startsWith(client+sep))return new Response(null,{status:404});
  try {
    const data=await readFile(target);
    const appearance=url.searchParams.get('appearance')==='dark'?'dark':'auto';
    return extname(target)==='.html'?html(data.toString().replace('<body>','<body>'+marker).replace('data-appearance="auto"',`data-appearance="${appearance}"`)):new Response(data,{headers:{'Content-Type':mime[extname(target)]??'application/octet-stream'}});
  }catch{return new Response(null,{status:404});}
}}};
async function upstream(url,init){
  const u=new URL(url);
  if(u.origin===privateEnv.SUPABASE_URL && u.pathname.startsWith('/functions/v1/rta-newsletter/'))return handleNewsletter(new Request(url,init),privateEnv,()=>{throw new Error('External fetch forbidden in preview');},sandbox.api);
  if(u.origin===privateEnv.SUPABASE_URL && u.pathname==='/rest/v1/dashboard_reports'){
    let found=rows.filter(r=>!u.searchParams.has('report_type')||r.report_type===u.searchParams.get('report_type').slice(3));
    if(u.searchParams.has('report_id'))found=found.filter(r=>r.report_id===u.searchParams.get('report_id').slice(3));
    if(u.searchParams.has('published_at'))found=found.filter(r=>Date.parse(r.published_at)<=Date.parse(u.searchParams.get('published_at').slice(4)));
    const start=Number(u.searchParams.get('offset')??0),limit=Number(u.searchParams.get('limit')??31);
    return json(found.slice(start,start+limit));
  }
  throw new Error('External fetch forbidden in preview');
}
createServer(async(req,res)=>{
  if(!['127.0.0.1:8771','localhost:8771'].includes(req.headers.host)){res.writeHead(403).end();return;}
  try{
    const url=new URL(req.url,origin);let result;
    if(url.pathname.startsWith('/__newsletter_preview')){
      if(req.method!=='GET'){res.writeHead(405).end();return;}
      if(url.pathname==='/__newsletter_preview/report')result=html(localEmailLinks(reportMail.html).replace(/(<body[^>]*>)/,'$1'+marker).replace(/\{\{\{RESEND_UNSUBSCRIBE_URL\}\}\}/g,'/__newsletter_preview/unsubscribe'));
      else if(url.pathname==='/__newsletter_preview/confirmation'){
        const last=sandbox.calls.filter(x=>x.path==='emails').at(-1);
        result=html(last?last.body.html.replaceAll('https://redthreatalert.pl/',origin+'/'):'<p>Najpierw wypełnij lokalny formularz zapisu.</p>');
      }else if(url.pathname==='/__newsletter_preview/unsubscribe')result=html('<p>To podgląd. Wysłane wiadomości użyją linku wypisu udostępnianego przez Resend.</p>');
      else result=html('<!doctype html><html lang="pl"><meta name="viewport" content="width=device-width"><title>Podgląd newslettera</title><body style="font:18px/1.6 Arial;padding:24px">'+marker+'<h1>Newsletter — podgląd lokalny</h1><p><a href="/">Formularz na stronie</a></p><p><a href="/__newsletter_preview/report">Mail z ostatnim opublikowanym raportem</a></p><p><a href="/__newsletter_preview/confirmation">Ostatnia wiadomość z potwierdzeniem adresu</a></p><p>Zapisy są przechowywane tylko w pamięci tego serwera. Możesz użyć adresu reader@example.test.</p></body></html>');
    }else{
      const init={method:req.method,headers:req.headers};
      if(!['GET','HEAD'].includes(req.method)){init.body=req;init.duplex='half';}
      result=await handle(new Request(`http://${req.headers.host}${req.url}`,init),env,upstream);
    }
    res.writeHead(result.status,Object.fromEntries(result.headers));res.end(Buffer.from(await result.arrayBuffer()));
  }catch{res.writeHead(503).end('local_preview_unavailable');}
}).listen(8771,'127.0.0.1',()=>console.log(`Newsletter preview: ${origin}/`));
