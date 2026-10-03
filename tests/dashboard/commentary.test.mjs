import { test } from 'node:test';
import assert from 'node:assert/strict';
import { commentaryRows } from '../../web/commentary.js';
const r = { as_of:'2026-10-03T08:00:00Z', incidents:[], commentary:{text:'Szwecja zapowiedziała udział myśliwców w ochronie polskiej przestrzeni powietrznej.'} };
test('old reviewed prose remains visible without invented impact or recommendations', () => {
 assert.deepEqual(commentaryRows(r,'macro'),[['Sytuacja',r.commentary.text]]);
 assert.deepEqual(commentaryRows({...r,commentary:{text:null}},'macro'),[]);
});
test('reviewed sections appear only when present; national advice is not relabelled as local', () => {
 const report={...r,commentary:{text:'Podsumowanie',sections:{situation:'Sytuacja',recommendation:'Instrukcja'}}};
 assert.deepEqual(commentaryRows(report,'macro'),[['Sytuacja','Sytuacja'],['Co zrobić','Instrukcja']]);
 assert.deepEqual(commentaryRows(report,'PL-10'),[['Sytuacja','Sytuacja']]);
});
