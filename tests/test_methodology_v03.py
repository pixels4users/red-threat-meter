import copy
from datetime import timedelta

import pytest

from osint_dashboard.common import ROOT, digest, instant, now, read_json
from osint_dashboard.pipeline import create_inputs, make_snapshot
from osint_dashboard.review import import_review, validate_evidence
from osint_dashboard.scoring import score, window_for
from osint_dashboard.scoring_v03 import decay, propagation
from osint_dashboard.dashboard.contract import build_report
from conftest import batch, decision_for, seed, source_checks


@pytest.fixture
def case(store,source,source_config):
    material,candidate=seed(store,source)
    d=decision_for(material,candidate)
    ev=copy.deepcopy(d['incident']['evidence'][0]);ev.update(id='place',claim='location')
    d['incident']['evidence'].append(ev);d['incident']['location']['evidence_ids']=['place']
    import_review(store,batch(d))
    config=read_json(ROOT/'config/scoring-v0.3.json')
    inputs=create_inputs(store,source_config,config,source_checks(source_config),now(),'fixture','synthetic-v03')
    e=inputs['incidents'][0];stamp=inputs['as_of']
    e['assessment_v03']={'version':'rtb-v0.3','profile':'tactical','time':{'earliest':stamp,'latest':stamp,'evidence_ids':['timing']},
        'episode_key':'synthetic-episode','components':[],'direct_kinetic':True,'kinetic_evidence_ids':['occurrence'],
        'region_ids':['PL-06'],'region_evidence_ids':['place'],'regional_scope_known':True,'active_until':None,'end_evidence_ids':[],'correlation':None}
    certify(inputs)
    return inputs


def certify(i):
    i['history_review']={'inputs_sha256':digest({'latest_material_ids':sorted(i['latest_material_ids']),'resolutions':i['resolutions'],'source_config':i['source_config'],'source_checks':i['source_checks']}),
         'from':(instant(i['as_of'])-timedelta(days=10)).isoformat(),'until':i['as_of'],'reviewed_at':i['as_of'],
         'event_and_revision_history_reviewed':True,'reviewer':{'type':'agent','name':'Synthetic fixture'},'reason':'SYNTHETIC: isolated history coverage for mathematical tests only.'}


def age(i,seconds,profile='tactical'):
    a=i['incidents'][0]['assessment_v03'];a['profile']=profile
    stamp=(instant(i['as_of'])-timedelta(seconds=seconds)).isoformat()
    a['time']={'earliest':stamp,'latest':stamp,'evidence_ids':['timing']}


def clone(i,n,category=None):
    e=copy.deepcopy(i['incidents'][0]);e.update(incident_id=f'evt_{n}',revision_id=f'rev_{n}',event_key=f'event-{n}')
    e['assessment_v03']['episode_key']=f'episode-{n}'
    if category:
        e['category']=category;e['criteria']={k:['criterion'] for k in i['scoring']['categories'][category]['criteria']}
    i['resolutions'][e['candidate_ids'][0]]['revision_ids'][e['incident_id']]=e['revision_id']
    i['incidents'].append(e);certify(i)
    return e


@pytest.mark.parametrize('minutes,value',[(0,1),(30,1),(45,.5),(60,0),(61,0),(-1,0)])
def test_tactical_decay_boundaries(minutes,value):
    assert decay(minutes*60,{'hold_seconds':1800,'fade_seconds':1800})==value


@pytest.mark.parametrize('hours,value',[(48,1),(132,.5),(216,0)])
def test_structural_decay_boundaries(hours,value):
    assert decay(hours*3600,{'hold_seconds':172800,'fade_seconds':604800})==value


def test_fractional_score_and_regional_projection(case):
    age(case,45*60)
    r,_=score(case)
    assert r['score']==12.5 and r['contributions'][0]['points']==2.5
    assert r['regions']['PL-14']['score']==11
    assert r['regions']['PL-10']['score']==10.4
    assert r['regions']['PL-10']['propagated_points']==.4
    snap=make_snapshot(case);report=build_report(snap,case['source_config'])
    assert report['rtb']['score']==12.5 and report['rtb']['regions']['PL-10']['score']==10.4
    assert 'evidence_ids' not in str(report['rtb']['regions'])


def test_real_prg_graph_and_multiple_paths_count_once(case):
    graph=case['scoring']['spatial']['graph'];f=[1,.4,.16]
    assert len(graph['nodes'])==16 and len(graph['edges'])==34
    assert propagation(['PL-06','PL-20'],'PL-14',True,graph,f)==.4
    assert propagation(['PL-06','PL-20'],'PL-10',True,graph,f)==.16
    assert propagation(['PL-10'],'PL-10',True,graph,f)==1
    assert propagation(['PL-06'],'PL-10',False,graph,f)==0


def test_missing_history_and_source_error_keep_null(case):
    case.pop('history_review');r,_=score(case)
    assert r['score'] is None and 'event_history_unverified' in r['blockers']
    certify(case);case['source_checks'][0]['status']='error';certify(case)
    assert score(case)[0]['score'] is None


def test_old_publication_boundary_is_not_history_proof(case):
    case['history_review']['from']=(instant(case['as_of'])-timedelta(days=7)).isoformat()
    assert score(case)[0]['score'] is None


def test_date_only_full_plateau_or_expired_is_unambiguous(case):
    a=case['incidents'][0]['assessment_v03'];a['time']=None;a['profile']='structural'
    case['incidents'][0]['occurred_on']=(instant(case['as_of'])-timedelta(days=1)).date().isoformat()
    assert score(case)[0]['score']==15
    case['incidents'][0]['occurred_on']=(instant(case['as_of'])-timedelta(days=5)).date().isoformat()
    assert score(case)[0]['score'] is None
    case['incidents'][0]['occurred_on']='2020-01-01'
    assert score(case)[0]['score']==10


def test_tactical_unknown_time_future_and_cancellation(case):
    case['incidents'][0]['assessment_v03']['time']=None
    assert score(case)[0]['score'] is None
    age(case,-60);assert score(case)[0]['score'] is None
    age(case,300);a=case['incidents'][0]['assessment_v03'];a.update(active_until=case['as_of'],end_evidence_ids=['timing'])
    assert score(case)[0]['score']==10


def test_republication_does_not_refresh_age_and_future_review_cannot_hide_old(case):
    age(case,3600)
    for m in case['materials']:m['published_at']=case['as_of']
    future=copy.deepcopy(case['incidents'][0]);future.update(revision=99,recorded_at=(instant(case['as_of'])+timedelta(days=1)).isoformat())
    case['incidents'].append(future)
    r,_=score(case);assert r['score']==10 and r['exclusions'][0]['reason']=='expired_weight'


def test_same_episode_is_one_contribution(case):
    e=clone(case,2);e['assessment_v03']=copy.deepcopy(case['incidents'][0]['assessment_v03'])
    assert score(case)[0]['score']==15
    e['assessment_v03']['profile']='structural'
    assert score(case)[0]['score'] is None


def test_campaign_chooses_largest_decayed_weight_before_regions(case):
    age(case,2700);e=clone(case,2)
    for event in case['incidents']:event['campaign_id']='same'
    e['assessment_v03']['time'].update(earliest=case['as_of'],latest=case['as_of'])
    e['assessment_v03']['region_ids']=['PL-10']
    r,_=score(case);assert r['score']==15 and r['contributions'][0]['incident_id']=='evt_2'
    assert r['regions']['PL-10']['direct_points']==5


def test_unknown_region_gates_regional_only(case):
    a=case['incidents'][0]['assessment_v03'];a.update(region_ids=[],region_evidence_ids=[],regional_scope_known=False)
    r,_=score(case);assert r['score']==15 and r['regions']['PL-14']['score'] is None


def wave(i,offsets):
    a=i['incidents'][0]['assessment_v03']
    a['components']=[{'key':f'physical-{n}','status':'confirmed_primary','evidence_ids':['occurrence'],
                       'time':{'earliest':(instant(i['as_of'])-timedelta(seconds=x)).isoformat(),
                               'latest':(instant(i['as_of'])-timedelta(seconds=x)).isoformat(),'evidence_ids':['timing']}}
                      for n,x in enumerate(offsets)]


def test_wave_requires_physical_components_in_15_minutes_and_uses_oldest(case):
    wave(case,[2700,2400,2100]);r,_=score(case)
    assert r['score']==13.125 and r['contributions'][0]['synergy']==1.25
    wave(case,[900,450,0]);assert score(case)[0]['score']==16.25
    wave(case,[901,450,0]);assert score(case)[0]['score']==15
    wave(case,[10,0]);assert score(case)[0]['score']==15


def test_component_cannot_belong_to_two_episodes(case):
    wave(case,[5,3,0]);clone(case,2)
    assert score(case)[0]['score'] is None
    a=case['incidents'][0]['assessment_v03'];a['components'][1]['key']=a['components'][0]['key']
    assert score(case)[0]['score'] is None


def triad(i):
    a=i['incidents'][0]['assessment_v03'];e=i['incidents'][0]
    for n,family in enumerate(['gnss','pansa','osint']):
        material=copy.deepcopy(i['materials'][0]);material.update(material_id='signal-'+family,source_id=family)
        i['materials'].append(material);i['latest_material_ids'].append(material['material_id'])
        ev=copy.deepcopy(e['evidence'][0]);ev.update(id=family,claim='criterion',origin_id=family,material_id=material['material_id'])
        e['evidence'].append(ev)
    a['correlation']={'signals':[{'family':f,'time':copy.deepcopy(a['time']),'region_ids':['PL-06'],'evidence_ids':[f],
                                  'valid_until':(instant(i['as_of'])+timedelta(hours=1)).isoformat() if f=='pansa' else None} for f in ['gnss','pansa','osint']],
                      'gnss_method':'synthetic-minute-detector','baseline_sha256':'a'*64,'link_reason':'SYNTHETIC explicit same episode and shared area for testing.', 'nonroutine_evidence_ids':['criterion']}
    for sid in ['pansa_airspace','rso_public']:
        definition=next(s for s in read_json(ROOT/'config/sources.json')['sources'] if s['id']==sid)
        i['source_config']['sources'].append(definition)
        i['source_checks'].append({'source_id':sid,'checked_at':i['as_of'],'status':'ok','activation_observed':True,'source_definition_hash':digest(definition)})
    certify(i)


def test_daily_gnss_cannot_activate_bonus_even_with_pansa_osint(case):
    triad(case);r,_=score(case)
    assert r['score']==15 and r['contributions'][0]['correlation_status']=='not_assessed'


def test_qualified_triad_and_wave_bound_and_reused_origin(case):
    age(case,2700);triad(case);case['scoring']['correlation']['approved_gnss_methods']=['synthetic-minute-detector']
    wave(case,[2700,2400,2100])
    r,_=score(case);assert r['score']==14.375 and r['contributions'][0]['synergy']==1.75
    next(e for e in case['incidents'][0]['evidence'] if e['id']=='osint')['origin_id']='gnss'
    assert score(case)[0]['contributions'][0]['synergy']==1.25


def test_triad_rejects_day_resolution_stale_control_and_plan_only(case):
    triad(case);case['scoring']['correlation']['approved_gnss_methods']=['synthetic-minute-detector']
    a=case['incidents'][0]['assessment_v03'];a['correlation']['signals'][0]['time']['earliest']=(instant(case['as_of'])-timedelta(days=1)).isoformat()
    assert score(case)[0]['contributions'][0]['synergy']==1
    a['correlation']['signals'][0]['time']['earliest']=case['as_of']
    case['source_checks'][-2]['activation_observed']=False
    assert score(case)[0]['contributions'][0]['correlation_reason']=='pansa_plan_only'
    case['source_checks'][-2]['activation_observed']=True
    case['source_checks'][-1]['checked_at']=(instant(case['as_of'])-timedelta(minutes=6)).isoformat();certify(case)
    assert score(case)[0]['contributions'][0]['correlation_reason']=='tactical_source_not_fresh'


def test_caps_keep_direct_and_propagated_proportionate(case):
    for n in range(8):clone(case,n+2)
    case['incidents'][0]['assessment_v03']['region_ids']=['PL-14']
    r,_=score(case);assert r['score']==35
    regional=r['regions']['PL-06']
    assert regional['direct_points']+regional['propagated_points']==pytest.approx(25)
    assert len(r['contributions'])==9


def test_one_origin_and_propagation_cannot_open_red(case):
    for n in range(4):clone(case,2+n,'sabotage')
    for n in range(5):clone(case,10+n,'arms_explosion')
    r,_=score(case);assert r['score']>60 and not r['red_priority']['eligible']
    assert not r['regions']['PL-14']['red_priority']['eligible']
    second=copy.deepcopy(case['materials'][0]);second.update(material_id='m-second',source_id='different-primary')
    case['materials'].append(second);case['latest_material_ids'].append('m-second')
    e=case['incidents'][0];ev=copy.deepcopy(e['evidence'][0]);ev.update(id='second',material_id='m-second',origin_id='independent-primary');e['evidence'].append(ev);e['status']='corroborated';certify(case)
    assert score(case)[0]['red_priority']['eligible']


def test_official_warning_survives_null_and_deduplicates_by_authority_key(case):
    e=case['incidents'][0];e['category']='context';e.pop('assessment_v03')
    e['official_warning']={'alert_key':'rcb-example','authority':'synthetic-authority','level':'L3_shelter','status':'active','effective_at':case['as_of'],
                         'valid_until':None,'area':'SYNTHETIC region','instruction_pl':'TEST: schroń się w budynku.','evidence_ids':['occurrence']}
    second=copy.deepcopy(e);second.update(incident_id='other',revision_id='other-rev')
    case['resolutions'][e['candidate_ids'][0]]['revision_ids']['other']='other-rev';case['incidents'].append(second)
    case.pop('history_review');r,_=score(case)
    assert r['score'] is None and len(r['official_warnings'])==1
    second['official_warning']['status']='cancelled'
    second['official_warning']['effective_at']=(instant(case['as_of'])+timedelta(seconds=1)).isoformat()
    assert score(case)[0]['official_warnings'][0]['status']=='active'


def test_utc_window_does_not_gain_hour_on_dst(case):
    w=window_for('2026-10-26T12:00:00+00:00',case['scoring'])
    assert (instant(w['end'])-instant(w['start'])).total_seconds()==216*3600


def test_future_component_cannot_supply_wave_bonus(case):
    wave(case,[600,300,-1])
    assert score(case)[0]['score'] is None


def test_v03_frozen_export_publication_and_replay(case, store, tmp_path):
    from osint_dashboard.pipeline import publish, replay
    from osint_dashboard.dashboard.contract import load_snapshot
    from osint_dashboard.dashboard.publication import LocalPublications
    age(case,2700)
    # The run and the report remain explicitly synthetic, in a temporary store.
    store.start_run(case['run_id'])
    folder=publish(store,case,make_snapshot(case))
    snap,cfg=load_snapshot(folder)
    report=build_report(snap,cfg)
    repo=LocalPublications(tmp_path/'published.sqlite')
    assert repo.publish(report)['created']
    assert not repo.publish(report)['created']
    assert repo.latest()['report']['rtb']['score']==12.5
    assert replay(store.data_dir,case['run_id'])['identical']


def test_active_cycle_uses_v03_without_inventing_history(tmp_path,fixture_file):
    from osint_dashboard.analysis import cycle
    from osint_dashboard.pipeline import run
    from osint_dashboard.dashboard.contract import load_snapshot
    result=run(tmp_path/'new',fixture=fixture_file)
    snap,cfg=load_snapshot(__import__('pathlib').Path(result['snapshot']).parent)
    assert snap['methodology_version']=='rtb-v0.3'
    assert 'event_history_unverified' in snap['rtb']['blockers']
    assert build_report(snap,cfg)['rtb']['score'] is None
