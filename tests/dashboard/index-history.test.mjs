import { test } from 'node:test';
import assert from 'node:assert/strict';
import { historyDays, historyRow, canJoinDays, ReportHistory, SnapshotSelection } from '../../web/index-history.js';
import { SignalArchive, filterSignals, topicCounts, mapReport, WEEK } from '../../web/signals.js';
import { commentaryRows } from '../../web/commentary.js';

const id = n => 'rpt_' + n.toString(16).padStart(64, '0');
const env = (n, asOf, score = 3, extra = {}) => ({ published_at: new Date(Date.parse(asOf) + 60000).toISOString(), report: {
  report_id: id(n), report_type: 'daily', contract_version: 'dashboard-v1', mode: 'fixture', as_of: asOf,
  incidents: [], sources: [], commentary: { text: `Komentarz ${n}` },
  provenance: { methodology_version: 'rtb-v0.4', config_hash: 'rules', code_hash: 'code', source_config_hash: 'sources' },
  rtb: { score, status: 'provisional', confidence: { comparison_key: 'coverage' }, regions: { 'PL-10': { score: n / 10 } } }, ...extra,
} });
const slot = (days, day) => days.find(d => d.day === day);

test('calendar history selects the last daily edition and correction, preserving gaps and nulls', () => {
  const a = env(1, '2026-10-02T07:00:00Z'), b = env(2, '2026-10-02T11:00:00Z', 0), c = env(3, '2026-10-02T11:00:00Z', 2);
  c.published_at = '2026-10-02T12:00:00Z';
  const legacy = env(4, '2026-09-30T07:00:00Z', null), weekly = env(5, '2026-10-01T07:00:00Z', 9, { report_type: 'weekly' });
  const days = historyDays([a,b,c,legacy,weekly].map(historyRow), '2026-10-03T07:00:00Z');
  assert.equal(days.length, 14); assert.equal(days[0].day, '2026-09-20');
  assert.equal(slot(days, '2026-10-02').row.report_id, id(3));
  assert.equal(slot(days, '2026-09-30').score, null); assert.ok(slot(days, '2026-09-30').row);
  assert.equal(slot(days, '2026-10-01').row, null); assert.equal(slot(days, '2026-10-01').score, null);
  assert.equal(slot(historyDays([historyRow(b)], b.report.as_of), '2026-10-02').score, 0);
});

test('calendar uses Warsaw dates through midnight and DST; weekly/future reports never enter the chart', () => {
  const at = '2026-10-25T23:10:00Z', a = env(1, '2026-10-25T00:30:00Z'), b = env(2, '2026-10-25T01:30:00Z'), c = env(3, at), future = env(4, '2026-10-26T01:00:00Z');
  const days = historyDays([a,b,c,future].map(historyRow), at);
  assert.equal(days.at(-1).day, '2026-10-26'); assert.equal(days.at(-1).row.report_id, id(3));
  assert.equal(slot(days,'2026-10-25').row.report_id, id(2));
});

test('regional history reads the region in each frozen report, never substitutes a national number', () => {
  const a = env(1,'2026-10-02T07:00:00Z',8), b = env(2,'2026-10-03T07:00:00Z',9);
  delete a.report.rtb.regions;
  const rows=[a,b].map(historyRow), cache=new Map([[id(1),a],[id(2),b]]);
  const days=historyDays(rows,b.report.as_of,cache,'PL-10');
  assert.equal(days.at(-2).score,null); assert.equal(days.at(-1).score,.2);
  assert.equal(historyDays(rows,b.report.as_of,new Map(),'PL-10').at(-1).score,null);
});

test('points remain visible across methodology changes, but lines cannot bridge incompatible scores or absent days', () => {
  const a=env(1,'2026-10-01T07:00:00Z'), b=env(2,'2026-10-02T07:00:00Z'), c=env(3,'2026-10-03T07:00:00Z');
  const days=historyDays([a,b,c].map(historyRow),c.report.as_of);
  assert.ok(canJoinDays(days.at(-3),days.at(-2)));
  days.at(-1).row.config_hash='changed';
  assert.equal(canJoinDays(days.at(-2),days.at(-1)),false); assert.equal(days.at(-1).score,3);
  assert.equal(canJoinDays(days.at(-3),days.at(-1)),false);
  days.at(-2).score=null; assert.equal(canJoinDays(days.at(-3),days.at(-2)),false);
});

test('history colors use each frozen report including warnings, zero and the red eligibility gate', () => {
  const readings = [
    [null, {}, 'unknown'], [0, {}, 'unknown'], [3, {}, 'low'],
    [3, { official_warnings: [{ status: 'active' }] }, 'unknown'],
    [3, { official_warnings: [{ status: 'unknown' }] }, 'unknown'],
    [3, { official_warnings: [{ status: 'expired' }] }, 'low'],
    [45, {}, 'elevated'], [70, { red_priority: { eligible: false } }, 'elevated'],
    [70, { red_priority: { eligible: true } }, 'high'],
  ];
  const values = readings.map(([score, fields], n) => {
    const value = env(n + 1, `2026-10-${String(n + 1).padStart(2,'0')}T07:00:00Z`, score);
    Object.assign(value.report.rtb, fields); return value;
  });
  const cache = new Map(values.map(value => [value.report.report_id, value]));
  const rows = values.map(historyRow), asOf = values.at(-1).report.as_of;
  assert.deepEqual(historyDays(rows, asOf, cache).filter(day => day.row).map(day => day.tone), readings.map(r => r[2]));
  assert.ok(historyDays(rows, asOf).every(day => day.tone === 'unknown'));
  // National red evidence must never turn a low regional score red.
  assert.equal(historyDays(rows, asOf, cache, 'PL-10').at(-1).tone, 'low');
  values.at(-1).report.rtb.regions['PL-10'] = { score: 80, red_priority: { eligible: false } };
  assert.equal(historyDays(rows, asOf, cache, 'PL-10').at(-1).tone, 'elevated');
  values.at(-1).report.rtb.regions['PL-10'].red_priority.eligible = true;
  assert.equal(historyDays(rows, asOf, cache, 'PL-10').at(-1).tone, 'high');
  assert.equal(historyDays(rows, asOf, cache, 'PL-02').at(-1).tone, 'unknown');
});

test('history pins pagination and caches reports; many editions cannot crowd an older day out of the window', async () => {
  const latest=env(40,'2026-10-03T12:00:00Z'), older=env(1,'2026-09-21T07:00:00Z');
  const editions=Array.from({length:31},(_,n)=>env(n+2,`2026-10-03T11:${String(n).padStart(2,'0')}:00Z`));
  const values=[latest,older,...editions], calls=[];
  const model=new ReportHistory(async path=>{
    calls.push(path);
    if(path.startsWith('/api/reports?')){
      const q=new URL(path,'http://local').searchParams;
      assert.equal(q.get('anchor'),latest.published_at);
      return q.get('offset')==='0'?{items:[historyRow(latest),...editions.slice(1).map(historyRow)],next_offset:31}:{items:[historyRow(editions[0]),historyRow(older)],next_offset:null};
    }
    return values.find(e=>path.endsWith(e.report.report_id));
  });
  await model.load(latest);
  assert.equal(model.failed,false);
  assert.equal(slot(historyDays(model.rows,latest.report.as_of),'2026-09-21').row.report_id,id(1));
  assert.equal(calls.filter(p=>!p.includes('?')).length,1);
  await model.get(id(1)); assert.equal(calls.filter(p=>!p.includes('?')).length,1);
});

test('an unavailable archive retains the real latest score instead of inventing fourteen zeroes', async () => {
  const latest=env(1,'2026-10-03T07:00:00Z',2);
  const model=new ReportHistory(async()=>{throw Error('offline');});
  await model.load(latest); assert.equal(model.failed,true);
  const days=historyDays(model.rows,latest.report.as_of);
  assert.equal(days.filter(d=>d.score!==null).length,1); assert.equal(days.at(-1).score,2);
});

test('the last click wins, and failed selection preserves the currently displayed snapshot', async () => {
  const resolves=new Map(); let displayed='current';
  const choose=new SnapshotSelection(key=>new Promise((resolve,reject)=>resolves.set(key,{resolve,reject})),value=>{displayed=value;});
  const first=choose.choose('old'), second=choose.choose('new');
  resolves.get('new').resolve('new'); await second;
  resolves.get('old').resolve('old'); await first;
  assert.equal(displayed,'new');
  const failed=choose.choose('missing'); resolves.get('missing').reject(Error('offline')); await failed;
  assert.equal(displayed,'new'); assert.equal(choose.failed,true); assert.equal(choose.pending,null);
});

test('malformed/mismatched report responses never enter the cache or selected view', async () => {
  const model=new ReportHistory(async()=>env(2,'2026-10-03T07:00:00Z'));
  await assert.rejects(model.get(id(1))); assert.equal(model.cache.size,0);
  await assert.rejects(model.get('../latest'));
});

test('opening the past excludes later corrections from commentary, counts and map even when their occurrence is older', async () => {
  const time='2026-10-01T07:00:00Z';
  const event=(revision,title)=>({id:'incident',revision,recorded_at:revision===1?'2026-09-30T08:00:00Z':'2026-10-02T08:00:00Z',published_at:'2026-09-30T06:00:00Z',title,summary:title,country:'PL',category:'context',status:'confirmed_primary',review_current:true,sources:[{source_id:'cert_pl',publisher:'CERT'}],location:{precision:'country',label:'Polska',geometry:{type:'Point',coordinates:[21,52]}}});
  const old=env(1,time,2,{incidents:[event(1,'Pierwotny opis')]}), current=env(2,'2026-10-03T07:00:00Z',3,{incidents:[event(2,'Późniejsza korekta')]});
  const model=new ReportHistory(async path=>path.includes('?')?{items:[historyRow(current),historyRow(old)],next_offset:null}:current);
  model.remember(old); model.remember(current);
  const archive=new SignalArchive(old,path=>model.read(path));
  await archive.loadThrough(Date.parse(time)-2*WEEK);
  assert.equal(archive.failed,false); assert.equal(archive.records[0].title,'Pierwotny opis');
  assert.equal(commentaryRows(old.report,'macro',archive.records)[0][1],'Komentarz 1');
  assert.equal(filterSignals(archive.records,{asOf:time,period:'current7'}).length,1);
  assert.equal(topicCounts(archive.records,[...archive.reports.values()],time,'macro',archive)[1].current.length,1);
  assert.equal(mapReport(old.report,archive.records).incidents[0].title,'Pierwotny opis');
});
