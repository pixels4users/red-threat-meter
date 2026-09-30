"""Generate synthetic releases in a temporary analysis store, never live data."""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
from conftest import item_for, source_checks, decision_for, batch
from osint_dashboard.common import read_json, write_json
from osint_dashboard.pipeline import run
from osint_dashboard.dashboard.contract import load_snapshot, build_report

with tempfile.TemporaryDirectory() as name:
    folder = Path(name); config = read_json(ROOT / 'config/sources.json')
    outcomes = []
    for check in source_checks(config):
        outcome = {k:v for k,v in check.items() if k != 'item_count'}
        outcome['items'] = [item_for()]; outcomes.append(outcome)
    fixture = folder / 'fixture.json'; write_json(fixture, {'synthetic':True,'source_results':outcomes})
    first = run(folder / 'analysis', fixture=fixture, methodology='rtb-v0.2')
    snap, cfg = load_snapshot(Path(first['snapshot']).parent); incomplete = build_report(snap, cfg)
    queue = read_json(Path(first['review_queue'])); materials = {m['material_id']:m for m in queue['materials']}
    decisions = [decision_for(materials[c['material_id']],c) if c['source_id']=='rcb' else {'kind':'exclude','candidate_ids':[c['candidate_id']],'reason':'Kontekst syntetyczny do testowania interfejsu.'} for c in queue['candidates']]
    review = folder / 'review.json'; write_json(review, batch(*decisions))
    second = run(folder / 'analysis', fixture=fixture, review_path=review, methodology='rtb-v0.2')
    snap, cfg = load_snapshot(Path(second['snapshot']).parent); complete = build_report(snap, cfg, previous=incomplete)
    print(json.dumps({'incomplete':incomplete,'complete':complete}, ensure_ascii=False))
