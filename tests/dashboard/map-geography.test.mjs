import { test } from 'node:test';
import assert from 'node:assert/strict';
import { geoArea, geoContains } from 'd3';
import boundaries from '../../web/assets/admin1.json' with { type: 'json' };
import { eventAreas, mapAreas, mapPoints, mappedSignalIds, areaLocationNote } from '../../web/map-geography.js';
import { matchesArea } from '../../web/signals.js';

const event = (id, country, label, precision = 'region', extra = {}) => ({
  id, country, title: 'Sygnał testowy', sources: [], category: 'context',
  location: { label, precision, geometry: null },
  presentation: { version:'signals-v1', topics:['aviation'], kind:'context', scope:'foreign', region_ids:[], episode_id:id },
  ...extra,
});
const regional = (id, label, ids) => {
  const e = event(id, 'PL', label); e.presentation.scope = 'regional'; e.presentation.region_ids = ids; return e;
};

test('country flag is a display anchor, not a new event location', () => {
  const e = event('national', 'PL', 'Polska', 'country'); e.presentation.scope = 'national';
  const original = JSON.stringify(e), [point] = mapPoints({ incidents:[e] });
  assert.equal(point.capital, 'Warszawa'); assert.equal(point.national, true);
  assert.equal(eventAreas(e).length, 0); assert.equal(JSON.stringify(e), original);
  e.presentation.scope = 'unknown'; assert.equal(mapPoints({ incidents:[e] }).length, 0);
});

test('explicit Volyn and Rivne labels map to separate oblasts, regardless of accents/case', () => {
  for (const [label, id] of [['Obwód wołyński','UA-07'], ['OBWÓD WOŁYŃSKI','UA-07'], ['OBWOD ROWIENSKI','UA-56']]) {
    const e = event(id, 'UA', label), [area] = eventAreas(e);
    assert.equal(area.feature.properties.id, id); assert.equal(area.context, false);
    assert.equal(mapPoints({ incidents:[e] }).length, 0);
  }
});

test('several reviewed voivodeships count as one signal, and regions collect all their signals', () => {
  const a = regional('a', 'Województwa lubelskie i podkarpackie', ['PL-06','PL-18']);
  const b = regional('b', 'Województwo lubelskie', ['PL-06']);
  const report = { incidents:[a,b] };
  assert.equal(eventAreas(a).length, 2); assert.ok(eventAreas(a).every(a => !a.context));
  assert.equal(mappedSignalIds(report).size, 2); assert.equal(mapAreas(report).length, 2);
  assert.equal(mapAreas(report).find(a => a.feature.properties.id === 'PL-06').events.length, 2);
});

test('localities inside a reviewed region use contextual outlines, never whole-region claims', () => {
  const e = regional('powiat', 'Powiat wadowicki', ['PL-12']);
  assert.equal(eventAreas(e)[0].context, true); assert.match(areaLocationNote(e), /nie oznacza zasięgu zdarzenia/);
  const ua = event('crossing','UA','Rejon przejścia Jagodzin, obwód wołyński');
  assert.equal(eventAreas(ua)[0].feature.properties.id,'UA-07'); assert.equal(eventAreas(ua)[0].context,true);
  ua.location.precision = 'city'; assert.equal(eventAreas(ua)[0].context,true);
});

test('a named Polish region without an old presentation ID stays consistent in filters and on the map', () => {
  const e = event('older','PL','Województwo lubelskie');
  assert.equal(matchesArea(e,'PL-06'),true); assert.equal(eventAreas(e)[0].feature.properties.id,'PL-06');
  assert.equal(matchesArea(e,'PL-18'),false);
  e.location.label = null; e.title = 'Województwo lubelskie';
  assert.equal(matchesArea(e,'PL-06'),false);
});

test('unknown regions and title mentions cannot silently supply geography', () => {
  for (const label of [null, 'Ukraina — kilka obwodów', 'Rejon sarneński', 'Kijów i Dniepr', 'Obwód wołyńskiXYZ']) {
    const e = event('unknown','UA',label); e.title = 'Obwód wołyński: alarm';
    assert.equal(eventAreas(e).length, 0); assert.equal(mappedSignalIds({ incidents:[e] }).size, 0);
  }
  assert.equal(eventAreas(event('wrong-country','PL','Obwód wołyński')).length,0);
  assert.equal(eventAreas(event('no-country',null,'Obwód wołyński')).length,0);
});

test('reviewed city and source point take precedence over a broad regional outline', () => {
  const city = regional('city','Łowicz',['PL-10']);
  city.location.precision = 'city'; city.presentation.map_anchor = {type:'Point', coordinates:[19.93333,52.1], label:'Łowicz'};
  assert.equal(eventAreas(city).length, 0); assert.equal(mapPoints({incidents:[city]})[0].city,'Łowicz');
  const exact = regional('exact','Miejsce w źródle',['PL-10']); exact.location.geometry = {type:'Point',coordinates:[19.9,52.1]};
  assert.equal(eventAreas(exact).length, 0); assert.deepEqual(mapPoints({incidents:[exact]})[0].coordinates,[19.9,52.1]);
});

test('regional asset covers 16 PL + 27 UA units, with small correctly oriented polygons', () => {
  assert.equal(boundaries.features.length,43);
  assert.equal(new Set(boundaries.features.map(f=>f.properties.id)).size,43);
  assert.equal(boundaries.features.filter(f=>f.properties.country==='PL').length,16);
  assert.equal(boundaries.features.filter(f=>f.properties.country==='UA').length,27);
  for (const f of boundaries.features) {
    assert.ok(geoArea(f)>0 && geoArea(f)<.01, f.properties.id);
    assert.ok(geoContains(f,f.properties.label_coordinates), f.properties.id+' label inside region');
  }
});
