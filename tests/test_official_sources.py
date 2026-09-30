from pathlib import Path
import pytest
from osint_dashboard.official_sources import parse_pansa, parse_rso, collect_official, local_timestamp
from osint_dashboard.common import ROOT, load_config

RSO=b'''<?xml version="1.0"?><newses><pagination_info totalItems="1" itemsPerPage="20"/><news><id>1</id><title>TEST SYNTHETYCZNY</title><content>TEST: komunikat wylacznie do sprawdzenia parsera.</content><created_at>2026-09-29 10:00:00</created_at><updated_at>2026-09-29 11:00:00</updated_at><valid_from>2026-09-29 10:00:00</valid_from><valid_to>2026-09-29 12:00:00</valid_to><rso_alarm>1</rso_alarm><provinces><province slug="lubelskie">Lubelskie</province></provinces></news></newses>'''
PANSA=b'''<p><span data-i18n="usePlan.lastUpdate"></span>2026-09-29 06:01</p><p><span data-i18n="validity"></span>2026-09-29 06:00 - 2026-09-30 06:00</p><table data-table="bravo" data-view="aup"><tbody><tr><td>1</td><td>EPR1</td><td>GND</td><td>A100</td><td>06:00</td><td>00:00</td><td>TEST</td><td>Y</td><td>SYNTHETIC</td></tr></tbody></table>'''


def test_pansa_plan_never_confirms_activation_even_with_y_field():
    p=parse_pansa(PANSA)
    assert p['updated_at']=='2026-09-29T06:01:00+00:00'
    assert p['zones'][0]['zone_type']=='R'
    assert p['activation_status']=='not_observed' and not p['zones'][0]['activation_confirmed']
    assert p['zones'][0]['fields'][-2]=='Y'


def test_pansa_missing_metadata_or_changed_row_is_not_empty_success():
    with pytest.raises(ValueError):parse_pansa(b'<html>No data</html>')
    with pytest.raises(ValueError):parse_pansa(PANSA.replace(b'<td>1</td>',b'<td>new format</td>'))


def test_rso_keeps_identifiers_validity_and_does_not_infer_shelter_level():
    r=parse_rso(RSO)[0]
    assert r['id']=='1' and r['published_at']=='2026-09-29T08:00:00+00:00'
    assert r['rso_alarm_raw']=='1' and r['classification']=='not_reviewed'
    assert r['valid_to_raw']=='2026-09-29 12:00:00'


@pytest.mark.parametrize('body',[RSO.replace(b'totalItems="1"',b'totalItems="2"'),RSO.replace(b'<content>',b'<wrong>').replace(b'</content>',b'</wrong>'),b'<!DOCTYPE x [<!ENTITY x "z">]>'+RSO])
def test_rso_partial_or_changed_xml_fails_closed(body):
    with pytest.raises(ValueError):parse_rso(body)


@pytest.mark.parametrize('stamp',['2026-10-25 02:30:00','2026-03-29 02:30:00'])
def test_rso_dst_ambiguity_requires_review(stamp):
    with pytest.raises(ValueError):local_timestamp(stamp)


def test_official_source_failure_and_current_state_do_not_claim_nine_day_history():
    config=load_config()
    class Fake:
        raw_refs=['raw/synthetic.bin'];request_count=1
        def get(self,url):return RSO,'application/xml',url,self.raw_refs[0]
    source=next(s for s in config['sources'] if s['id']=='rso_public')
    result=collect_official(source,Fake())
    assert result['status']=='ok' and result['record_count']==1
    assert result['current_state_complete'] and not result['window_complete']
    assert result['items'][0]['text_kind']=='official_dataset'
    class Bad(Fake):
        def get(self,url):raise TimeoutError('test')
    failure=collect_official(source,Bad())
    assert failure['status']=='error' and not failure['items']
