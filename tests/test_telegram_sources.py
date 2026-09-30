import pytest
from osint_dashboard.telegram_sources import parse_air_force, collect_air_force
from osint_dashboard.common import ROOT, read_json


def post(ident='kpszsu/123', text='БпЛА на Рівненщині', extra=''):
    return f'<div class="tgme_widget_message" data-post="{ident}"><div class="tgme_widget_message_text">{text}</div><a class="tgme_widget_message_date"><time datetime="2026-09-30T09:00:00+00:00"></time></a>{extra}</div>'


def test_extracts_only_public_text_keeps_provenance_and_no_inferred_occurrence_date():
    p=parse_air_force(post(extra='<div class="tgme_widget_message_forwarded_from">Another authority</div><a class="tgme_widget_message_reply" href="https://t.me/kpszsu/122">quoted text</a>'))[0]
    assert p['text']=='БпЛА на Рівненщині' and 'quoted text' not in p['text']
    assert p['url']=='https://t.me/kpszsu/123' and p['published_at'].startswith('2026-09-30T09:00')
    assert p['source_record']['occurrence_time'] is None
    assert p['source_record']['forwarded_from']=='Another authority'
    assert p['source_record']['reply_urls']==['https://t.me/kpszsu/122']


def test_identity_missing_preview_and_duplicate_fail_closed():
    for body in ['<html>Login</html>',post('other/12'),post()+post()]:
        with pytest.raises(ValueError):parse_air_force(body)
    assert len(parse_air_force(''.join(post(f'kpszsu/{i}') for i in range(25))))==20


def test_single_request_bounded_success_never_claims_complete_history():
    class Fetch:
        raw_refs=['raw/test.bin'];request_count=0
        def get(self,url):
            self.request_count+=1
            return post().encode(),'text/html',url,self.raw_refs[0]
    source=next(s for s in read_json(ROOT/'config/sources.json')['sources'] if s['id']=='ua_air_force_public')
    fetch=Fetch();r=collect_air_force(source,fetch)
    assert r['status']=='partial' and r['window_complete'] is False and fetch.request_count==1
    assert len(r['items'])==1
