import json
import sqlite3

import pytest

from osint_dashboard.common import read_json, write_json
from osint_dashboard.pipeline import locked, replay, run
from osint_dashboard.review import import_review
from osint_dashboard.store import Store
from conftest import batch, decision_for


def test_end_to_end_rerun_replay_and_geojson(tmp_path, fixture_file):
    folder=tmp_path/'demo'
    first=run(folder,fixture=fixture_file)
    second=run(folder,fixture=fixture_file)
    assert first['new_materials']==4
    assert second['new_materials']==0
    assert second['counts']['materials']==4
    assert first['rtb'] is None
    assert replay(folder,second['run_id'])['identical']
    snapshot=read_json(folder/read_json(folder/'latest.json')['snapshot'])
    assert snapshot['mode']=='fixture'
    assert snapshot['rtb']['score'] is None
    geo=read_json(folder/read_json(folder/'latest.json')['geojson'])
    assert geo['type']=='FeatureCollection'
    assert geo['run_id']==second['run_id']


def test_reviewed_evidence_produces_number_and_trace(tmp_path, fixture_file):
    folder=tmp_path/'demo'
    result=run(folder,fixture=fixture_file)
    queue=read_json(__import__('pathlib').Path(result['review_queue']))
    materials={m['material_id']:m for m in queue['materials']}
    decisions=[]
    for c in queue['candidates']:
        if c['source_id']=='rcb':decisions.append(decision_for(materials[c['material_id']],c))
        else:decisions.append({'kind':'exclude','candidate_ids':[c['candidate_id']],'reason':'Syntetyczny kontekst poza punktacją, świadomie wykluczony w teście.'})
    review_path=tmp_path/'review.json';write_json(review_path,batch(*decisions))
    scored=run(folder,fixture=fixture_file,review_path=review_path)
    assert scored['rtb']==15
    snap=read_json(__import__('pathlib').Path(scored['snapshot']))
    assert len(snap['rtb']['contributions'])==1
    assert snap['incidents'][0]['reviewer']['type']=='agent'
    assert replay(folder,scored['run_id'])['identical']


def test_interrupted_export_leaves_last_complete_release(tmp_path,fixture_file,monkeypatch):
    import osint_dashboard.pipeline as pipeline
    folder=tmp_path/'demo'
    result=run(folder,fixture=fixture_file)
    last=(folder/'latest.json').read_bytes()
    def fail(*args):raise RuntimeError('synthetic export interruption')
    monkeypatch.setattr(pipeline,'geojson',fail)
    with pytest.raises(RuntimeError,match='interruption'):
        run(folder,fixture=fixture_file)
    assert (folder/'latest.json').read_bytes()==last
    assert not list((folder/'snapshots').glob('.staging-*'))
    with Store(folder) as store:
        assert store.counts()['snapshots']==1
        assert store.db.execute("SELECT count(*) FROM runs WHERE status='failed'").fetchone()[0]==1


def test_fixture_and_live_data_cannot_mix(tmp_path,fixture_file):
    folder=tmp_path/'demo'
    run(folder,fixture=fixture_file)
    with pytest.raises(ValueError,match='separate'):
        run(folder,offline=True)


def test_tampered_snapshot_detected(tmp_path,fixture_file):
    folder=tmp_path/'demo'
    result=run(folder,fixture=fixture_file)
    report=__import__('pathlib').Path(result['report'])
    report.write_text('tampered')
    with pytest.raises(ValueError,match='integrity'):
        replay(folder,result['run_id'])


def test_concurrent_run_is_rejected(tmp_path):
    folder=tmp_path/'data'
    with locked(folder):
        with pytest.raises(RuntimeError,match='Another process'):
            with locked(folder):pass
