from copy import deepcopy
from datetime import timedelta
from pathlib import Path

import pytest

from osint_dashboard.common import instant, load_config, now, write_json
from osint_dashboard.extract import make_candidate
from osint_dashboard.store import Store
from osint_dashboard.x_sources import classify_post, collect_captures, import_capture, post_url


def source():
    return next(s for s in load_config()['sources'] if s['id'] == 'x_osinttechnical')


def capture(text='SYNTHETIC TEST: German military exercise in Latvia.', hours=0):
    return {'schema_version':'x-browser-v1','synthetic':True,'account':'osinttechnical',
            'captured_at':(instant(now())-timedelta(hours=hours)).isoformat(),
            'access_status':'partial','coverage_note':'Test syntetyczny ograniczonego widoku profilu.',
            'page_text':text,'posts':[{'url':'https://x.com/Osinttechnical/status/123?s=21&t=tracking',
            'text':text,'published_at':None,'published_label':'2 h',
            'post_kind':'post','text_complete':True,'referenced_urls':[]}]}


@pytest.mark.parametrize('text,decision',[
    ('German fighter jets arrive in Latvia.', 'candidate'),
    ('Russian drone crashed in Amur during training.', 'outside_region'),
    ('US fighter operations in Alaska.', 'outside_region'),
    ('Russian drone attacks Ukraine.', 'candidate'),
    ('NATO ships have deployed.', 'review_geography'),
    ('Berlin hosts a festival.', 'review_topic'),
    ('Polish Navy patrols the Baltic Sea.', 'candidate'),
    ('Iran war: Russian missiles reportedly supplied to Tehran.', 'outside_region'),
    ('Russia is moving equipment, location unknown.', 'review_geography'),
    ('The Pentagon announces a new fighter contract.', 'outside_region')])
def test_region_filter_routes_ambiguity_to_review(text,decision):
    assert classify_post(text,source()['filter'])['decision'] == decision


def test_url_strips_tracking_and_rejects_other_authors_hosts():
    assert post_url('https://x.com/Osinttechnical/status/123?s=21&t=abc','osinttechnical') == 'https://x.com/osinttechnical/status/123'
    for url in ['https://x.com/other/status/123','https://x.com.evil/Osinttechnical/status/123','https://x.com/Osinttechnical/status/123/photo/1','https://x.com:443/Osinttechnical/status/123']:
        with pytest.raises(ValueError): post_url(url,'osinttechnical')


def test_repeated_import_is_idempotent_and_does_not_refresh_date(tmp_path):
    s,c=source(),capture(hours=1)
    first=import_capture(tmp_path,s,c)
    assert import_capture(tmp_path,s,c)==first
    result=collect_captures(s,tmp_path)
    assert result['status']=='partial' and not result['window_complete'] and result['request_count']==0
    assert result['checked_at']==c['captured_at'] and len(result['items'])==1
    with Store(tmp_path) as db, db.db:
        a,_=db.add_material(s,result['items'][0],result['items'][0]['raw_ref'],result['checked_at'])
        b,added=db.add_material(s,result['items'][0],result['items'][0]['raw_ref'],result['checked_at'])
        assert not added and a['material_id']==b['material_id']
        assert 'summary_only' not in make_candidate(a)['flags']
        changed=deepcopy(result['items'][0]);changed['source_record']['referenced_urls']=['https://example.org/primary']
        updated,added=db.add_material(s,changed,changed['raw_ref'],now())
        assert added and updated['material_id']!=a['material_id']


def test_truncated_post_never_becomes_full_content(tmp_path):
    c=capture();c['posts'][0]['text_complete']=False
    import_capture(tmp_path,source(),c)
    item=collect_captures(source(),tmp_path)['items'][0]
    assert item['text_kind']=='social_post_excerpt'


def test_stale_missing_and_unavailable_captures_are_not_success(tmp_path):
    s=source();assert collect_captures(s,tmp_path)['status']=='error'
    c=capture(hours=25);import_capture(tmp_path,s,c)
    stale=collect_captures(s,tmp_path)
    assert stale['items']==[] and stale['checked_at']==c['captured_at']
    c=capture();c.update(access_status='unavailable',posts=[])
    import_capture(tmp_path,s,c)
    result=collect_captures(s,tmp_path)
    assert result['status']=='error' and result['items']==[]


def test_invalid_identity_missing_evidence_future_or_fixture_into_live_rejected(tmp_path):
    s=source()
    for mutation in ['author','text','future','duplicate']:
        c=capture()
        if mutation=='author':c['account']='sentdefender'
        if mutation=='text':c['posts'][0]['text']='This text is absent from the page.'
        if mutation=='future':c['captured_at']=(instant(now())+timedelta(days=1)).isoformat()
        if mutation=='duplicate':c['posts'].append(c['posts'][0])
        with pytest.raises(ValueError):import_capture(tmp_path,s,c)
    write_json(tmp_path/'.mode.json',{'mode':'live'})
    with pytest.raises(ValueError):import_capture(tmp_path,s,capture())


def test_newest_revision_outside_region_does_not_resurrect_old_version(tmp_path):
    # A correction removing regional relevance is still a changed document;
    # it must reach review if the prior version was selected.
    s=source();import_capture(tmp_path,s,capture(hours=1))
    c=capture('SYNTHETIC TEST: Correction: this was in Alaska.')
    import_capture(tmp_path,s,c)
    result=collect_captures(s,tmp_path)
    assert len(result['items'])==1 and 'Correction' in result['items'][0]['text']
    assert result['items'][0]['triage']['decision']=='review_revision'
