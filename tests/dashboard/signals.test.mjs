import { test } from 'node:test';
import assert from 'node:assert/strict';
import { presentation, regionLabel, matchesArea, inPeriod, filterSignals, mergeSignals, topicCounts, comparisonState, SignalArchive, WEEK } from '../../web/signals.js';
const asOf = '2026-10-03T07:00:00Z', end = Date.parse(asOf), iso = t => new Date(t).toISOString();
const event = (id, time, extra = {}) => ({ id, revision_id: id+'-1', revision: 1, title: 'Sprawdzona informacja', summary: 'Opis', published_at: time, recorded_at: '2026-09-20T08:00:00Z', country: 'PL', category: 'context', status: 'confirmed_primary', review_current: true, location: { label: 'Polska', precision: 'country', geometry: null }, sources: [{ source_id: 'cert_pl', publisher: 'CERT', url: 'https://cert.pl/' }], ...extra });
const report = (time, incidents = [], extra = {}) => ({ contract_version:'dashboard-v1', mode:'fixture', report_type:'daily', report_id:'rpt_'+'a'.repeat(64), as_of: time, incidents, sources:[{ id:'cert_pl',status:'current',window_complete:true }], rtb:{ score:2, status:'available' }, coverage:{pending_review:0}, provenance:{ methodology_version:'rtb-v0.4', source_config_hash:'same', exporter_version:'dashboard-export-v5' }, ...extra });

test('topic is separate from scoring: CERT context stays Cyber, GNSS a measurement', () => {
  const cert = event('cert', asOf);
  assert.deepEqual(presentation(cert).topics, ['cyber']); assert.equal(cert.category, 'context');
  const gnss = event('gnss', asOf, { sources: [{source_id:'gpsjam_reviewed'}] });
  assert.deepEqual(presentation(gnss).topics, ['navigation']); assert.equal(presentation(gnss).kind, 'measurement');
});
test('exact reviewed regions, national signals and unknown scope remain distinct', () => {
  const unknown = event('rso', asOf, {sources:[{source_id:'rso_public'}]});
  assert.equal(matchesArea(unknown, 'PL-10'), false); assert.equal(regionLabel(unknown), 'Obszar nieustalony');
  const national = event('cert', asOf);
  assert.equal(matchesArea(national, 'PL-10'), true); assert.equal(matchesArea(national, 'PL-10', false), false);
  const local = event('local', asOf, {presentation:{version:'signals-v1',topics:['cyber'],kind:'warning',scope:'regional',region_ids:['PL-10'],episode_id:'one'}});
  assert.equal(matchesArea(local,'PL-10',false), true); assert.equal(matchesArea(local,'PL-14'), false);
  assert.equal(regionLabel(local), 'łódzkie');
  const city = event('city', asOf, {location:{precision:'city',label:'Łowicz',geometry:null}});
  assert.equal(matchesArea(city,'PL-10'), false); // No geocoding guesses.
});
test('two 168-hour windows are disjoint; no date from recorded_at; clock pinned to report', () => {
  for (const [offset,current,previous] of [[0,false,false],[-1,true,false],[-WEEK,true,false],[-WEEK-1,false,true],[-2*WEEK,false,true],[-2*WEEK-1,false,false]]) {
    const e=event('e',iso(end+offset)); assert.equal(inPeriod(e,asOf,'current7'),current); assert.equal(inPeriod(e,asOf,'previous7'),previous);
  }
  const unknown=event('u',null); assert.equal(inPeriod(unknown,asOf,'current7'),false); assert.equal(inPeriod(unknown,asOf,'undated'),true);
});
test('calendar filters use Warsaw, Monday week, quarter/year and DST', () => {
  const at='2026-10-01T09:00:00Z';
  assert.ok(inPeriod(event('e','2026-09-30T22:00:00Z'),at,'quarter'));
  assert.ok(!inPeriod(event('e','2026-09-30T21:59:59Z'),at,'month'));
  assert.ok(inPeriod(event('e','2026-09-27T22:00:00Z'),at,'week'));
  assert.ok(!inPeriod(event('e','2026-09-27T21:59:59Z'),at,'week'));
  for (const t of ['2026-10-25T00:30:00Z','2026-10-25T01:30:00Z']) assert.ok(inPeriod(event('e',t),'2026-10-25T10:00:00Z','day'));
});
test('reports, revisions, reprints and episodes count once; future knowledge is ignored', () => {
  const a=event('a',iso(end-WEEK-1000));
  const revised={...a,revision:2,title:'Korekta',recorded_at:iso(end-1000),published_at:a.published_at};
  const sameEpisode={...revised,id:'b',presentation:{version:'signals-v1',episode_id:'episode',topics:['cyber'],kind:'context',scope:'national',region_ids:[]}};
  revised.presentation=sameEpisode.presentation;
  const future={...revised,revision:3,title:'Future',recorded_at:iso(end+1000)};
  const merged=mergeSignals([report(iso(end-WEEK),[a]),report(asOf,[revised,sameEpisode,future]),report(iso(end+1000),[future])],asOf);
  assert.equal(merged.length,1); assert.equal(merged[0].title,'Korekta'); assert.equal(merged[0].published_at,a.published_at);
  assert.equal(filterSignals(merged,{asOf,period:'current7',topic:'cyber'}).length,0);
  assert.equal(filterSignals(merged,{asOf,period:'previous7',topic:'cyber'}).length,1);
});
test('comparison needs retained daily coverage, same source scope and complete collection/review', () => {
  const history=Array.from({length:15},(_,i)=>report(iso(end-i*86400000)));
  assert.equal(comparisonState(history,asOf),'available');
  const events=[event('a',iso(end-1)),event('b',iso(end-WEEK-1))];
  const cyber=topicCounts(events,history,asOf,'macro',{})[1]; assert.equal(cyber.delta,0); assert.equal(cyber.current.length,1);
  assert.equal(comparisonState(history.slice(0,5),asOf),'unavailable');
  assert.equal(comparisonState(history.filter((_,i)=>i!==5),asOf),'unavailable');
  const changed=structuredClone(history); changed[3].provenance.source_config_hash='changed'; assert.equal(comparisonState(changed,asOf),'unavailable');
  changed[3]=structuredClone(history[3]); changed[3].sources[0].status='partial'; assert.equal(comparisonState(changed,asOf),'partial');
  assert.equal(topicCounts(events,changed,asOf,'macro',{})[1].delta,null);
  assert.equal(comparisonState(history,asOf,{failed:true}),'unavailable');
});
test('archive paginates with fixed publication anchor, uses latest corrections and caches reads', async () => {
  const latest=report(asOf,[event('a',iso(end-1))]), prior=report(iso(end-WEEK),[event('b',iso(end-WEEK-1))],{report_id:'rpt_'+'b'.repeat(64)});
  const older=report(iso(end-2*WEEK-1),[],{report_id:'rpt_'+'c'.repeat(64)});
  const published=iso(end+1000), calls=[];
  const api=async path=>{calls.push(path); if(path.startsWith('/api/reports?')) {const q=new URL(path,'http://local').searchParams;assert.equal(q.get('anchor'),published);return q.get('offset')==='0'?{items:[{...latest,published_at:published},{...prior,published_at:iso(end-WEEK+1000)}],next_offset:2}:{items:[{...older,published_at:iso(end-2*WEEK+1000)}],next_offset:null};} const r=[prior,older].find(r=>path.endsWith(r.report_id));return {report:r,published_at:published};};
  const archive=new SignalArchive({report:latest,published_at:published},api);
  await archive.loadThrough(end-2*WEEK); assert.equal(archive.failed,false);assert.equal(archive.records.length,2); assert.equal(calls.length,4);
  await archive.loadThrough(end-2*WEEK); assert.equal(calls.length,4);
});
test('history failure preserves latest report and cannot create a false decrease', async () => {
  const r=report(asOf,[event('a',iso(end-1))]); const archive=new SignalArchive({report:r,published_at:iso(end)},async()=>{throw Error('offline');});
  await archive.loadThrough(end-2*WEEK); assert.equal(archive.failed,true); assert.equal(archive.records.length,1);
  assert.equal(topicCounts(archive.records,[...archive.reports.values()],asOf,'macro',archive)[1].delta,null);
});

test('an explicit reviewed date correction wins over a superseded timestamp', () => {
  const old=event('a',iso(end-WEEK-1));
  const corrected={...old,revision:2,published_at:null,recorded_at:iso(end-1)};
  const items=mergeSignals([report(iso(end-1000),[old]),report(asOf,[corrected])],asOf);
  assert.equal(items[0].published_at,null);
  assert.equal(filterSignals(items,{asOf,period:'previous7'}).length,0);
});
