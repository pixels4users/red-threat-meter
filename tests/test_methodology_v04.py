import copy
from datetime import timedelta

import pytest
from jsonschema import ValidationError

from osint_dashboard.common import ROOT, digest, instant, read_json
from osint_dashboard.dashboard.contract import build_report
from osint_dashboard.pipeline import make_snapshot
from osint_dashboard.review import validate_schema
from osint_dashboard.scoring import score
from test_methodology_v03 import case as legacy_case, certify, clone


@pytest.fixture
def case(legacy_case):
    legacy_case['scoring'] = read_json(ROOT / 'config/scoring-v0.4.json')
    return legacy_case


def test_pending_material_and_missing_history_cannot_erase_confirmed_event(case):
    case.pop('history_review')
    case['candidates'].append({'candidate_id':'pending'})
    r,_ = score(case)
    assert r['score'] == 5 and r['blockers'] == []
    assert {'event_history_unverified','unreviewed_candidates:1'} <= set(r['quality_issues'])
    assert 0 < r['confidence']['percent'] < 50
    assert r['regions']['PL-14']['score'] == 2
    assert r['regions']['PL-10']['score'] == .8
    report = build_report(make_snapshot(case), case['source_config'])
    assert report['rtb']['status'] == 'provisional' and report['rtb']['score'] == 5
    assert report['rtb']['confidence'] == r['confidence']


def test_no_signals_returns_zero_without_constant_base(case):
    case['incidents'] = []
    r,_ = score(case)
    assert r['score'] == 0 and r['contributions'] == []
    assert r['confidence']['percent'] > 0
    assert not r['red_priority']['eligible']
    report = build_report(make_snapshot(case), case['source_config'])
    assert report['rtb']['score'] == 0


def test_no_sources_returns_zero_confidence_not_false_safety(case):
    case['source_checks'] = []
    case['incidents'] = []
    r,_ = score(case)
    assert r['score'] == 0 and r['confidence']['percent'] == 0
    assert r['status'] == 'provisional' and r['blockers'] == []
    assert all(d['percent'] == 0 for d in r['confidence']['domains'])


def test_missing_feed_does_not_erase_still_qualified_evidence(case):
    case['source_checks'] = []
    r,_ = score(case)
    assert r['score'] == 5 and r['confidence']['percent'] == 0


def test_unconfigured_capabilities_never_count_as_complete(case):
    r,_ = score(case)
    domains = {d['id']:d['percent'] for d in r['confidence']['domains']}
    assert domains['gnss'] == domains['border'] == 0
    assert r['confidence']['coverage_percent'] < 100
    original = r['confidence']['percent']
    case.pop('history_review')
    assert score(case)[0]['confidence']['percent'] <= round(original / 2) + 1


def test_stale_or_changed_source_lowers_confidence(case):
    before = score(case)[0]['confidence']
    for check in case['source_checks']:
        check['checked_at'] = (instant(case['as_of'])-timedelta(hours=9)).isoformat()
    after = score(case)[0]['confidence']
    assert after['percent'] == 0 and after['comparison_key'] != before['comparison_key']
    for check in case['source_checks']:
        check['checked_at'] = case['as_of']; check['source_definition_hash'] = 'wrong'
    assert score(case)[0]['confidence']['percent'] == 0


def test_conflicting_episode_is_excluded_without_global_null(case):
    e = clone(case,2)
    e['assessment_v03']['episode_key'] = case['incidents'][0]['assessment_v03']['episode_key']
    e['assessment_v03']['profile'] = 'structural'
    r,_ = score(case)
    assert r['score'] == 0 and r['blockers'] == []
    assert any(e['reason']=='episode_conflict' for e in r['exclusions'])
    assert r['confidence']['review_percent'] == 0


def test_invalid_quote_is_excluded_and_reduces_review_confidence(case):
    case['incidents'][0]['evidence'][0]['quote'] = 'invented quotation'
    r,_ = score(case)
    assert r['score'] == 0 and r['confidence']['review_percent'] == 0
    assert r['exclusions'][0]['reason'] == 'evidence_validation_failed'


def test_v04_temporal_assessment_and_ukraine_scope(case):
    e=case['incidents'][0]
    e['assessment_v04']=e.pop('assessment_v03');e['assessment_v04']['version']='rtb-v0.4'
    e.update(country='UA',category='cross_border_air_pressure',criteria={'air_attack':['criterion'],'western_ukraine':['criterion']})
    e['assessment_v04'].update(region_ids=[],region_evidence_ids=[],direct_kinetic=False,kinetic_evidence_ids=[])
    assert score(case)[0]['score']==3
    e['attribution']['actor']='unknown'
    assert score(case)[0]['score']==0
    e['attribution']['actor']='RU';e['country']='PL'
    assert score(case)[0]['score']==0


def test_zero_comparison_never_divides_by_zero_and_coverage_changes_hide_trend(case):
    old=copy.deepcopy(case);old['incidents']=[]
    previous=build_report(make_snapshot(old),old['source_config'])
    case['as_of']=(instant(case['as_of'])+timedelta(seconds=1)).isoformat()
    current=build_report(make_snapshot(case),case['source_config'],previous=previous)
    assert current['rtb']['trend']['delta_points']==5
    assert current['rtb']['trend']['percent'] is None
    case['source_checks'][0]['status']='error'
    current=build_report(make_snapshot(case),case['source_config'],previous=previous)
    assert current['rtb']['trend']['direction']=='unavailable'


def test_v04_contract_rejects_null_negative_and_fake_confidence(case):
    report=build_report(make_snapshot(case),case['source_config'])
    for field,value in [('score',None),('score',-1),('confidence',{'percent':None,'method':'not_calibrated'})]:
        bad=copy.deepcopy(report);bad['rtb'][field]=value
        with pytest.raises(ValidationError):validate_schema('dashboard/report',bad)


def test_new_default_cycle_is_numeric_and_replayable(tmp_path, fixture_file):
    from osint_dashboard.pipeline import run, replay
    from osint_dashboard.dashboard.contract import load_snapshot
    from pathlib import Path
    result=run(tmp_path/'new',fixture=fixture_file)
    snap,cfg=load_snapshot(Path(result['snapshot']).parent)
    assert snap['methodology_version']=='rtb-v0.4'
    assert snap['rtb']['score']==0 and not snap['rtb']['blockers']
    assert 'event_history_unverified' in snap['rtb']['quality_issues']
    assert replay(tmp_path/'new',snap['run_id'])['identical']


def test_imprecise_proven_day_uses_conservative_bound_without_inventing_time(case):
    e=case['incidents'][0];a=e['assessment_v03'];a.update(profile='structural',time=None)
    # Timing evidence fixture is explicitly replaced with a dated synthetic text.
    day=(instant(case['as_of'])-timedelta(days=5)).date().isoformat()
    e['occurred_on']=day
    e['evidence'][2]['quote']='Dnia '+day
    for m in case['materials']:m['text'] += ' Dnia '+day
    r,_=score(case)
    assert 0<r['score']<5
    c=r['contributions'][0]
    assert c['decay']==c['decay_bounds'][0]<c['decay_bounds'][1]
    assert 'time_interval' in c
    assert any(q.startswith('time_precision_limited:') for q in r['quality_issues'])


def test_official_instruction_survives_zero_confidence_and_duplicate_sources(case):
    e=case['incidents'][0];e['category']='context';e.pop('assessment_v03')
    e['official_warning']={'alert_key':'synthetic-alert','authority':'synthetic-authority','level':'L3_shelter','status':'active',
        'effective_at':case['as_of'],'valid_until':(instant(case['as_of'])+timedelta(minutes=30)).isoformat(),
        'area':'SYNTHETIC region','instruction_pl':'TEST SYNTHETYCZNY: schroń się w budynku.','evidence_ids':['occurrence']}
    second=copy.deepcopy(e);second.update(incident_id='other',revision_id='other-rev')
    case['resolutions'][e['candidate_ids'][0]]['revision_ids']['other']='other-rev';case['incidents'].append(second)
    case['source_checks']=[];case.pop('history_review')
    r,_=score(case)
    assert r['score']==0 and r['confidence']['percent']==0
    assert len(r['official_warnings'])==1 and r['official_warnings'][0]['status']=='active'
    report=build_report(make_snapshot(case),case['source_config'])
    assert report['rtb']['official_warnings'][0]['instruction_pl'].startswith('TEST SYNTHETYCZNY')
    case['as_of']=(instant(case['as_of'])+timedelta(hours=1)).isoformat()
    assert score(case)[0]['official_warnings'][0]['status']=='expired'


def test_high_qualified_score_retains_independent_red_gate_despite_quality_gaps(case):
    clone(case,2)
    for n in range(4):clone(case,10+n,'sabotage')
    for n in range(5):clone(case,20+n,'arms_explosion')
    case.pop('history_review')
    assert score(case)[0]['score']>60 and not score(case)[0]['red_priority']['eligible']
    second=copy.deepcopy(case['materials'][0]);second.update(material_id='m-second',source_id='different-primary')
    case['materials'].append(second);case['latest_material_ids'].append('m-second')
    e=case['incidents'][0];ev=copy.deepcopy(e['evidence'][0]);ev.update(id='second',material_id='m-second',origin_id='independent-primary')
    e['evidence'].append(ev);e['status']='corroborated'
    r,_=score(case)
    assert r['red_priority']['eligible'] and r['alert']['status']=='analyst_review_required'
