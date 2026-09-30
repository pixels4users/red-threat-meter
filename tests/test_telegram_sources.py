import pytest
from osint_dashboard.telegram_sources import parse_air_force, collect_air_force, previous_page
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
    source={**source,'max_pages':1,'max_requests':1,'max_items':20}
    source.pop('summary_query',None)
    fetch=Fetch();r=collect_air_force(source,fetch)
    assert r['status']=='partial' and r['window_complete'] is False and fetch.request_count==1
    assert len(r['items'])==1


def test_recent_pages_and_summaries_share_identity_and_keep_partial_coverage():
    source=next(s for s in read_json(ROOT/'config/sources.json')['sources'] if s['id']=='ua_air_force_public')
    class Fetch:
        raw_refs=['raw/synthetic'];request_count=0
        def get(self,url):
            self.request_count+=1
            if '?before=' in url: body=post('kpszsu/122')
            elif '?q=' in url: body=post('kpszsu/120','Synthetic dated attack summary')+post()
            else: body=post()+'<a class="tme_messages_more" data-before="123" href="/s/kpszsu?before=123">Older</a>'
            return body.encode(),'text/html',url,self.raw_refs[0]
    f=Fetch();r=collect_air_force(source,f)
    assert f.request_count==3 and len(r['items'])==3 and r['summary_pages_read']==1
    assert r['status']=='partial' and not r['window_complete']
    assert len({i['url'] for i in r['items']})==3
    assert any(i['content_provenance']['extraction']['discovery']=='summary_search' for i in r['items'])


def test_invalid_cursor_or_foreign_pagination_is_rejected():
    source=next(s for s in read_json(ROOT/'config/sources.json')['sources'] if s['id']=='ua_air_force_public')
    for cursor,href in [('124','/s/kpszsu?before=124'),('123','https://evil.example/s/kpszsu?before=123'),('123','/s/kpszsu?before=123&extra=1')]:
        body=post()+f'<a class="tme_messages_more" data-before="{cursor}" href="{href}">Older</a>'
        with pytest.raises(ValueError):previous_page(body,source['url'],source)


def test_summary_failure_does_not_erase_recent_posts():
    source=next(s for s in read_json(ROOT/'config/sources.json')['sources'] if s['id']=='ua_air_force_public')
    class Fetch:
        raw_refs=['raw/synthetic'];request_count=0
        def get(self,url):
            self.request_count+=1
            if '?q=' in url:raise TimeoutError('Synthetic outage')
            return post().encode(),'text/html',url,self.raw_refs[0]
    r=collect_air_force(source,Fetch())
    assert len(r['items'])==1 and r['status']=='partial' and r['errors']
