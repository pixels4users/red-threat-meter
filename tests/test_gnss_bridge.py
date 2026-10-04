from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import ValidationError

from osint_dashboard import gnss_bridge as bridge
from osint_dashboard.common import ROOT, digest, read_json, write_json
from osint_dashboard.early_warning import collectors, pipeline as ew, store as storage, translations
from osint_dashboard.analysis import cycle
from osint_dashboard.pipeline import replay
from osint_dashboard.review import validate_evidence
from test_early_warning import Fixtures, AS_OF
from test_analysis_cycle import audit_for


@pytest.fixture
def prepared_gnss(tmp_path, monkeypatch):
    for module in (collectors, ew, storage, translations, bridge):
        monkeypatch.setattr(module, 'now', lambda: AS_OF)
    data = tmp_path / 'main'
    write_json(data / '.mode.json', {'mode': 'fixture'})
    ew.run(data / 'early_warning', days=3, mode='fixture', fetcher_factory=Fixtures())
    source = next(s for s in read_json(ROOT / 'config/sources.json')['sources'] if s['id'] == 'gpsjam_reviewed')
    return data, source


def test_import_copies_numeric_provenance_without_network_or_clock_renewal(prepared_gnss, monkeypatch):
    data, source = prepared_gnss
    monkeypatch.setattr(collectors.Fetcher, 'get', lambda *args: pytest.fail('Duplicate network collection'))
    result = bridge.collect_verified_input(source, data)
    assert result['status'] == 'partial' and result['checked_at'] == AS_OF
    assert result['request_count'] == 0 and not result['window_complete']
    assert all((data / p).exists() for p in result['raw_refs'])
    record = result['items'][0]['source_record']
    assert bridge.numeric_values(record)['high_cells'] == 1
    assert record['comparison']['reference_days'] == ['2026-09-21']
    monkeypatch.setattr(bridge, 'now', lambda: '2026-09-23T21:00:00+00:00')
    stale = bridge.collect_verified_input(source, data)
    assert stale['status'] == 'unavailable' and stale['checked_at'] == AS_OF and not stale['items']


def test_corrupt_raw_and_synthetic_live_mismatch_fail_closed(prepared_gnss):
    data, source = prepared_gnss
    write_json(data / '.mode.json', {'mode': 'live'})
    assert not bridge.collect_verified_input(source, data)['items']
    write_json(data / '.mode.json', {'mode': 'fixture'})
    latest = read_json(data / 'early_warning/latest.json')
    inputs = read_json(data / 'early_warning/snapshots' / latest['run_id'] / 'replay-input.json')
    obs = next(r['observation'] for r in inputs['observations'] if r['observation']['source_id'] == 'gpsjam')
    (data / 'early_warning' / obs['raw_refs'][1]).write_bytes(b'corrupt fixture')
    assert not bridge.collect_verified_input(source, data)['items']


def proposal(material, candidate):
    record = material['source_record']
    values = bridge.numeric_values(record)
    origin = 'gpsjam:' + '+'.join(record['observation']['dependency_groups'])
    evidence = [{'id': claim, 'material_id': material['material_id'], 'claim': claim, 'stance': 'supports',
                 'measurement': {'observation_id': record['observation']['observation_id'], 'field': field, 'value': values[field]},
                 'origin_id': origin, 'origin_reason': 'Syntetyczny test jednej serii GPSJAM; wspólne dane ADS-B.'}
                for claim, field in [('occurrence', 'high_cells'), ('timing', 'day'), ('location', 'bbox')]]
    return {'kind': 'incident', 'candidate_ids': [candidate['candidate_id']], 'previous_revision': 0,
            'reason': 'Syntetyczny test dowodów liczbowych; bez interpretacji zagrożenia.',
            'incident': {'event_key': 'synthetic-gnss-day', 'title': 'TEST SYNTETYCZNY — dokładność nawigacji',
                'summary': 'Syntetyczny pomiar dokładności nawigacji. Nie ustala sprawcy ani ciągłości zakłóceń.',
                'category': 'context', 'status': 'confirmed_primary', 'occurred_on': values['day'],
                'date_evidence_ids': ['timing'], 'country': None,
                'attribution': {'actor': 'unknown', 'status': 'unverified', 'reason': 'Pomiar nie określa źródła sygnału.'},
                'location': {'label': 'Prostokąt badawczy', 'geometry': None, 'precision': 'region', 'evidence_ids': ['location']},
                'criteria': [], 'campaign_id': None, 'evidence': evidence,
                'security_relevance': {'classification': 'operational_context', 'reason': 'Syntetyczny pomiar nawigacji bez punktacji i atrybucji.', 'evidence_ids': ['occurrence']}}}


def test_numeric_evidence_review_confidence_publication_and_replay(prepared_gnss, monkeypatch):
    from osint_dashboard import pipeline, review
    from osint_dashboard.dashboard.contract import load_snapshot, build_report
    data, source = prepared_gnss
    for module in (pipeline, review, cycle):
        monkeypatch.setattr(module, 'now', lambda: AS_OF)
    imported = bridge.collect_verified_input(source, data)
    fixture = data / 'synthetic-import.json'
    write_json(fixture, {'synthetic': True, 'source_results': [imported]})
    run = cycle.prepare(data, fixture=fixture)
    cid = run['cycle_id']
    folder, prepared = cycle.load_cycle(data, cid)
    m = prepared['packet']['materials'][0]
    c = prepared['packet']['candidates'][0]
    d = proposal(m, c)
    from osint_dashboard.analysis.reviewer import context_material, convert_proposal, AnalysisError
    compact = context_material(m)
    assert 'source_record' not in compact and compact['review_scope'] == 'context_summary'
    assert compact['numeric_context']['values'] == bridge.numeric_values(m['source_record'])
    assert compact['numeric_context']['source_record_sha256'] == digest(m['source_record'])
    compact_packet = deepcopy(prepared['packet']); compact_packet['materials'] = [compact]
    with pytest.raises(AnalysisError, match='requires_full_material'):
        convert_proposal({'decisions': [d]}, compact_packet, {'type': 'agent', 'name': 'fixture'})
    from osint_dashboard.scoring_v04 import score_v04
    before, _ = score_v04(prepared['inputs'])
    assert next(x for x in before['confidence']['domains'] if x['id'] == 'gnss')['percent'] == 0
    bad = deepcopy(d); bad['incident']['evidence'][0]['measurement']['value'] = 999
    with pytest.raises(ValueError, match='differs'):
        cycle.check(data, cid, {'decisions': [bad]}, 'Codex — synthetic test')
    bad = deepcopy(d); bad['incident']['evidence'][0].pop('measurement');bad['incident']['evidence'][0]['quote'] = m['text'][:100]
    with pytest.raises(ValueError, match='numeric evidence'):
        cycle.check(data, cid, {'decisions': [bad]}, 'Codex — synthetic test')
    for field, value in [('country', 'PL'), ('category', 'gps_jamming')]:
        bad = deepcopy(d);bad['incident'][field] = value
        with pytest.raises(ValueError, match='context only'):
            cycle.check(data, cid, {'decisions': [bad]}, 'Codex — synthetic test')
    checked = cycle.check(data, cid, {'decisions': [d]}, 'Codex — synthetic test')
    cycle.apply(data, cid, checked['proposal_sha256'], audit_for(checked))
    assert cycle.calculate(data, cid)['score'] == 0
    draft = read_json(folder / 'draft.json')
    assert next(x for x in draft['snapshot']['rtb']['confidence']['domains'] if x['id'] == 'gnss')['percent'] == 50
    next_day = deepcopy(draft['inputs']);next_day['as_of'] = '2026-09-24T00:01:00+00:00'
    assert not bridge.reviewed_current_day(next_day, source['id'])
    cycle.finish(data, cid)
    snap, cfg = load_snapshot(data / 'snapshots' / cid)
    public = build_report(snap, cfg)
    assert public['incidents'][0]['title'] == d['incident']['title']
    assert 'observation' not in str(public)  # Private raw grid is never in the browser export.
    assert replay(data, cid)['identical']
