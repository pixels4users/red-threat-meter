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
const loadedHistory = { earliestLoaded: end - 2 * WEEK };
test('counts compare recorded signals despite source changes, partial feeds, review backlog and report gaps', () => {
  const history = [report(iso(end - 2 * WEEK), [], {
    provenance: { source_config_hash: 'old', exporter_version: 'old' },
    sources: [{ id: 'cert_pl', status: 'partial', window_complete: false }],
    coverage: { pending_review: 12 },
  }), report(asOf)];
  const signal = (id, time, source) => event(id, time, { sources: [{ source_id: source }] });
  const events = [
    ...Array.from({ length: 7 }, (_, i) => signal(`current-${i}`, iso(end - 1), 'pansa_airspace')),
    ...Array.from({ length: 5 }, (_, i) => signal(`previous-${i}`, iso(end - WEEK - 1), 'pansa_airspace')),
    ...Array.from({ length: 3 }, (_, i) => signal(`cyber-${i}`, iso(end - WEEK - 1), 'cert_pl')),
  ];
  assert.equal(comparisonState(history, asOf, loadedHistory), 'available');
  const counts = topicCounts(events, history, asOf, 'macro', loadedHistory);
  assert.deepEqual(counts.map(c => [c.current.length, c.previous.length, c.delta]), [[7, 5, 2], [0, 3, -3], [0, 0, 0]]);
});
test('older signals retained in newer reports provide actual comparison history', () => {
  const events = [event('current', iso(end - 1)), event('previous', iso(end - WEEK - 1))];
  const history = [report(asOf, events)];
  const cyber = topicCounts(events, history, asOf, 'macro', loadedHistory)[1];
  assert.equal(cyber.current.length, 1); assert.equal(cyber.previous.length, 1); assert.equal(cyber.delta, 0);
});
test('a known zero in an existing archive compares normally, but missing or unread history does not', () => {
  const events = [event('current', iso(end - 1))], current = report(asOf, events);
  const history = [report(iso(end - 2 * WEEK)), current];
  assert.equal(topicCounts(events, history, asOf, 'macro', loadedHistory)[1].delta, 1);
  assert.equal(topicCounts([], history, asOf, 'macro', loadedHistory)[1].delta, 0);
  assert.equal(topicCounts(events, [current], asOf, 'macro', loadedHistory)[1].delta, null);
  for (const options of [{}, { earliestLoaded: end - WEEK }, { ...loadedHistory, failed: true }, { ...loadedHistory, loading: true }]) {
    const count = topicCounts(events, history, asOf, 'macro', options)[1];
    assert.equal(count.current.length, 1); assert.equal(count.delta, null);
  }
  assert.equal(comparisonState(history, asOf, { ...loadedHistory, loading: true }), 'loading');
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

test('daily GNSS measurements count and filter by observed day without inventing a publication hour', async () => {
  const { signalTime } = await import('../../web/signal-time.js');
  const { timelineGroups, signalTimeText } = await import('../../web/data.js');
  const gnss = event('gnss-day', null, { occurred_on: '2026-10-02', sources: [{ source_id: 'gpsjam_reviewed' }] });
  assert.equal(inPeriod(gnss, asOf, 'current7'), true);
  assert.equal(inPeriod(gnss, asOf, 'undated'), false);
  assert.equal(filterSignals([gnss], { asOf, topic: 'navigation', period: 'current7' }).length, 1);
  assert.equal(topicCounts([gnss], [report(iso(end - 2 * WEEK))], asOf, 'macro', loadedHistory)[2].current.length, 1);
  const groups = timelineGroups([gnss], '2026-10-02T19:00:00Z', 'day');
  assert.deepEqual(groups.groups.filter(([, items]) => items.length).map(([key]) => key), ['2026-10-02Tdaily']);
  assert.equal(signalTime(gnss).precision, 'day');
  assert.equal(signalTimeText(gnss), 'Pomiar dobowy · 02.10.2026 (UTC)');
  assert.equal(gnss.published_at, null);
  assert.equal(inPeriod({ ...gnss, occurred_on: '2026-10-04' }, asOf, 'current7'), false);
  assert.equal(inPeriod({ ...gnss, occurred_on: '2026-02-31' }, asOf, 'undated'), true);
  const ordinary = { ...gnss, sources: [{ source_id: 'cert_pl' }] };
  assert.equal(inPeriod(ordinary, asOf, 'undated'), true);
});
