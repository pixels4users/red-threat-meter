import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildReportPresentation, reportPresentationText, reportHref, reportTopicHref, reportRoute } from '../../web/report-presentation.js';
import { reportText } from '../../web/data.js';

const id = char => 'rpt_' + char.repeat(64);
const make = () => ({ report_id:id('a'), report_type:'daily', as_of:'2026-10-03T22:30:00Z', window:{start:'2026-09-25T12:00:00Z',end:'2026-10-03T22:30:00Z',definition:'Jawne okno.'},
  rtb:{score:2,status:'provisional',confidence:{percent:null},trend:{direction:'unavailable',delta_points:null,reference_report_id:null}},
  commentary:{text:'Starszy zatwierdzony komentarz.'}, incidents:[],sources:[],limitations:['Ograniczona obserwacja.'],gaps:[],
  provenance:{methodology_version:'rtb-v0.4',config_hash:'config',source_config_hash:'sources',code_hash:'code'},supersedes:null });
const event = (extra={}) => ({id:'e',title:'Zapisany tytuł',summary:'Zapisane podsumowanie',category:'context',country:'PL',location:{precision:'unknown',label:null},published_at:null,occurred_on:null,status:'unverified',sources:[{source_id:'cert_pl',publisher:'CERT',url:'https://cert.pl/test'}],...extra});

test('summary keeps sections once, legacy prose once, and omits missing content',()=>{
 const r=make();let m=buildReportPresentation(r);assert.equal(m.date,'4 października 2026');assert.equal(m.asOf,'Stan na godz. 00:30 czasu polskiego');
 assert.deepEqual(m.summary,[{label:null,text:r.commentary.text}]);
 r.commentary.sections={situation:'Sytuacja zapisana.',recommendation:'Zalecenie zapisane.'};m=buildReportPresentation(r);
 assert.deepEqual(m.summary.map(s=>s.label),['Sytuacja','Zalecenia']);assert.ok(!reportPresentationText(m).includes(r.commentary.text));
 r.commentary={text:null};assert.deepEqual(buildReportPresentation(r).summary,[]);
});
test('zero and historical null stay distinct and missing confidence is not zero',()=>{
 const r=make();r.rtb.score=0;let m=buildReportPresentation(r);assert.equal(m.metric.score,'0');assert.equal(m.metric.tone,'unknown');assert.match(m.metric.note,/nie potwierdza/);
 r.rtb.score=null;r.rtb.status='insufficient_data';r.provenance.methodology_version='rtb-v0.2';m=buildReportPresentation(r);
 assert.equal(m.metric.hasScore,false);assert.equal(m.metric.confidence,'Nieokreślona');assert.match(m.methodologyUrl,/methodology-v0.2.md$/);
});
test('warnings preserve authority, instruction, historical status and dates without invented URLs',()=>{
 const r=make();r.commentary={text:null};r.rtb.official_warnings=['active','expired','unknown','cancelled'].map(status=>({status,authority:'RCB',area:'Obszar',instruction_pl:'Zapisana instrukcja.',effective_at:'2026-10-01T10:00:00Z',valid_until:null}));
 const m=buildReportPresentation(r);assert.equal(m.summary.length,0);assert.equal(m.warnings.length,4);assert.equal(m.metric.tone,'unknown');
 assert.match(m.warnings[0].status,/Aktywne w chwili wydania/);assert.match(m.warnings[1].status,/Wygasłe/);assert.match(m.warnings[2].status,/nieustalony/);assert.match(m.warnings[3].status,/Odwołane/);
 assert.ok(m.warnings.every(w=>w.instruction==='Zapisana instrukcja.' && !w.url && w.until===null));
});
test('multi-topic events occur once with all labels, missing dates and safe links',()=>{
 const r=make();r.incidents=[event({presentation:{version:'signals-v1',topics:['cyber','aviation'],kind:'context',scope:'unknown',region_ids:[]},sources:[{source_id:'cert_pl',publisher:'CERT',url:'javascript:alert(1)'},{source_id:'cert_pl',publisher:'CERT',url:'https://cert.pl/test'}]})];
 const before=JSON.stringify(r),m=buildReportPresentation(r);assert.equal(m.count,1);assert.equal(m.groups.length,1);const e=m.groups[0].events[0];
 assert.deepEqual(e.topics,['Cyber','Lotnictwo']);assert.equal(e.publication,'Nieustalona');assert.equal(e.occurred,'Nieustalona');assert.equal(e.sources.length,1);assert.equal(JSON.stringify(r),before);
 assert.equal(reportText(r),reportPresentationText(m));assert.match(reportText(r),/Starszy zatwierdzony komentarz/);
});
test('delta requires the exact older comparable reference and preserves its date',()=>{
 const r=make(),ref=make();ref.report_id=id('b');ref.as_of='2026-10-02T10:00:00Z';r.rtb.trend={reference_report_id:ref.report_id,delta_points:-1,direction:'down'};
 assert.equal(buildReportPresentation(r).metric.delta,null);assert.match(buildReportPresentation(r,{reference:ref}).metric.delta,/-1 pkt względem 02.10.2026/);
 ref.provenance={...ref.provenance,code_hash:'other'};assert.equal(buildReportPresentation(r,{reference:ref}).metric.delta,null);
 delete r.provenance.code_hash;delete ref.provenance.code_hash;assert.equal(buildReportPresentation(r,{reference:ref}).metric.delta,null);
});
test('corrections and print links identify the exact edition without exposing private fields',()=>{
 const r=make();r.supersedes=id('b');r.private_snapshot='SECRET';r.sources=[{name:'Źródło',status:'partial',url:'https://example.org',diagnostics:'TRACEBACK'}];
 const m=buildReportPresentation(r,{newerId:id('c')});assert.equal(m.previous,id('b'));assert.equal(m.newer,id('c'));
 assert.deepEqual(reportRoute(reportHref(r.report_id,true)),{id:r.report_id,print:true});assert.equal(reportRoute('#raport/../../secret'),null);
 assert.ok(!reportPresentationText(m).includes('SECRET'));assert.ok(!reportPresentationText(m).includes('TRACEBACK'));assert.match(reportPresentationText(m),/Niepełne/);
 assert.match(reportPresentationText(m),/Brak wydarzeń ujętych w tym wydaniu/);
});

test('category links keep edition identity while full TXT remains complete',()=>{
 const r=make();r.incidents=[event()];const m=buildReportPresentation(r),g=m.groups[0];
 assert.deepEqual(reportRoute(new URL(g.url).hash),{id:r.report_id,print:false,topic:g.key});
 assert.equal(new URL(g.url).origin,'https://redthreatalert.pl');
 assert.ok(reportPresentationText(m).includes(r.incidents[0].summary));
 const compact=reportPresentationText(m,{eventDetails:false});assert.ok(!compact.includes(r.incidents[0].summary));assert.ok(compact.includes(g.url));
 assert.equal(reportTopicHref('bad','aviation'),null);assert.equal(reportTopicHref(r.report_id,'unknown'),null);
 assert.equal(reportRoute(`#raport/${r.report_id}/obszar/unknown`),null);
 assert.equal(reportRoute(`#raport/${r.report_id}/obszar/constructor`),null);
 assert.equal(reportRoute(`#raport/${r.report_id}/druk/obszar/cyber`),null);
 assert.deepEqual(reportRoute(reportHref(r.report_id)),{id:r.report_id,print:false});
});
