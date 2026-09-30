import { test } from 'node:test';
import assert from 'node:assert/strict';
import { timelineGroups, safeLink, comparable, checkEnvelope, scoreLabel, visibleWarnings } from '../../web/data.js';

test('semantic zoom uses Polish calendar boundaries, including DST and month edges', () => {
  const records = [{published_at:'2026-09-30T21:59:00Z'}, {published_at:'2026-09-30T22:01:00Z'}, {published_at:'2026-10-01T08:00:00Z'}];
  assert.equal(timelineGroups(records, '2026-10-01T09:00:00Z','day').eligible.length,2);
  assert.equal(timelineGroups(records, '2026-10-01T09:00:00Z','month').eligible.length,2);
  const dst = [{published_at:'2026-10-25T00:30:00Z'},{published_at:'2026-10-25T01:30:00Z'}];
  const groups = timelineGroups(dst, '2026-10-25T10:00:00Z','day').groups;
  assert.equal(groups.find(([key])=>key.endsWith('T02'))[1].length,2);
});
test('publication time is never filled from another timestamp', () => {
  const r=[{published_at:null,recorded_at:'2026-09-27T08:00:00Z'},{published_at:'2026-09-27T18:00:00Z'}];
  assert.equal(timelineGroups(r,'2026-09-27T08:00:00Z','week').eligible.length,0);
});
test('links and inconsistent metric states are rejected', () => {
  assert.equal(safeLink('javascript:alert(1)'),null); assert.equal(safeLink('https://u:secret@example.com'),null);
  assert.equal(safeLink('https://www.gov.pl/web/rcb'),'https://www.gov.pl/web/rcb');
  assert.throws(()=>checkEnvelope({report:{rtb:{score:58,status:'insufficient_data'}}}));
});
test('methodology changes cannot share a continuous numeric trend', () => {
  const a={methodology_version:'rtb-v0.2',config_hash:'a',source_config_hash:'b',code_hash:'c'};
  assert.ok(comparable(a,{...a})); assert.ok(!comparable(a,{...a,config_hash:'changed'}));
  assert.ok(!comparable(a,{...a,methodology_version:'rtb-v0.3'}));
});
test('fractional RTB is rounded only for display; shelter instructions survive a missing score', () => {
  assert.equal(scoreLabel(12.375), '12,4');
  const report = {contract_version:'dashboard-v1',report_id:'rpt_'+'a'.repeat(64),mode:'fixture',as_of:'2026-09-29T16:00:00Z',incidents:[],sources:[],provenance:{methodology_version:'rtb-v0.3'},rtb:{status:'available',score:12.375}};
  assert.equal(checkEnvelope({report}).report.rtb.score,12.375);
  assert.equal(visibleWarnings({score:null,official_warnings:[{status:'active',level:'L3_shelter'},{status:'cancelled'},{status:'unknown'}]}).length,2);
});
