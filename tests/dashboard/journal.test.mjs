import { test } from 'node:test';
import assert from 'node:assert/strict';
import { journalDays, journalClock, journalCaution } from '../../web/journal.js';

const event = (id, published_at, extra = {}) => ({ id, published_at, occurred_on:null, sources:[], status:'confirmed_primary', review_current:true, ...extra });

test('journal groups Warsaw publication dates, preserves every record and does not mutate input', () => {
  const a = event('late','2026-10-03T22:15:00Z'), b = event('early','2026-10-03T21:59:00Z');
  const c = event('same-day','2026-10-04T07:00:00Z');
  const records = Object.freeze([Object.freeze(b),Object.freeze(a),Object.freeze(c)]);
  const groups = journalDays(records);
  assert.deepEqual(groups.map(g=>g.day),['2026-10-04','2026-10-03']);
  assert.deepEqual(groups[0].events.map(e=>e.id),['late','same-day']);
  assert.equal(groups[0].label,'4 października 2026');
  assert.equal(groups.flatMap(g=>g.events).length,3);
  assert.equal(records[0],b); assert.equal(journalClock(a),'00:15');
});

test('daily measurements keep their observed UTC day and never invent a publication hour', () => {
  const measurement = event('gps','2026-10-04T07:00:00Z',{occurred_on:'2026-10-03',presentation:{kind:'measurement'}});
  assert.equal(journalDays([measurement])[0].day,'2026-10-03');
  assert.equal(journalClock(measurement),'Pomiar');
  for (const time of ['2026-10-25T00:30:00Z','2026-10-25T01:30:00Z']) {
    assert.equal(journalDays([event('dst',time)])[0].day,'2026-10-25');
    assert.equal(journalClock(event('dst',time)),'02:30');
  }
});

test('undated publications form a final group; occurrence and recorded_at cannot substitute for publication', () => {
  const unknown = event('unknown',null,{occurred_on:'2026-10-02',recorded_at:'2026-10-03T10:00:00Z'});
  const invalid = event('invalid','not-a-date');
  const groups=journalDays([unknown,event('dated','2026-10-01T09:00:00Z'),invalid]);
  assert.deepEqual(groups.map(g=>g.day),['2026-10-01','']);
  assert.equal(groups[1].label,'Bez ustalonej daty'); assert.equal(groups[1].events.length,2);
  assert.equal(journalClock(unknown),'—'); assert.equal(journalClock(invalid),'—');
});

test('uncertainty, refutations and superseded material remain visible before expansion', () => {
  assert.equal(journalCaution(event('verified',null)),'');
  assert.equal(journalCaution(event('multi',null,{status:'corroborated'})),'');
  assert.match(journalCaution(event('single',null,{status:'unverified'})),/Pojedyncze doniesienie/);
  assert.match(journalCaution(event('conflict',null,{status:'disputed'})),/Sprzeczne informacje/);
  assert.match(journalCaution(event('refuted',null,{status:'refuted'})),/Informacja obalona/);
  assert.match(journalCaution(event('newer',null,{review_current:false})),/nowsza wersja materiału/);
});
