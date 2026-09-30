import pytest
from datetime import datetime, timedelta

from osint_dashboard.collect import allowed_url, collect_source, parse_article, parse_listing, parse_published
from osint_dashboard.common import UTC


def test_date_quarantine_preserves_good_records(source, tmp_path):
    class Fetcher:
        raw_refs = ["raw/test.xml"]
        def get(self, url):
            return (b'<rss version="2.0"><channel><title>Test</title><item><title>Valid</title>'
                    b'<link>https://www.gov.pl/web/rcb/a</link><pubDate>Mon, 21 Sep 2026 12:00:00 GMT</pubDate></item>'
                    b'<item><title>Bad date</title><link>https://www.gov.pl/web/rcb/b</link><pubDate>unknown-date</pubDate></item>'
                    b'</channel></rss>', 'application/rss+xml', url, 'raw/test.xml')
    result = collect_source({**source, 'adapter':'rss','fetch_articles':False}, tmp_path, datetime(2026,9,16,tzinfo=UTC), Fetcher())
    assert result['status'] == 'partial'
    assert len(result['items']) == 2
    assert result['items'][1]['published_at'] is None
    assert result['items'][0]['published_at'] is not None


def test_lead_and_correction_are_both_retained():
    html = '<article><p class="intro">Cywilny dron nie stanowił zagrożenia dla bazy.</p><div class="editor-content">Sprostowanie: nie operował nad bazą wojskową.</div></article>'
    result = parse_article(html.encode())
    assert 'Cywilny dron' in result
    assert 'Sprostowanie' in result


def test_listing_extracts_only_articles_and_real_next_page():
    body = b'<main><nav><a href="/admin">Ignore</a></nav><div class="art-prev"><ul><li><span class="date">21.09.2026</span><div class="title"><a href="/web/rcb/event">Title</a></div></li></ul></div><a id="js-pagination-page-next" href="?page=2&amp;size=10"></a></main>'
    items, next_page = parse_listing(body, 'https://www.gov.pl/web/rcb/komunikaty')
    assert len(items) == 1
    assert next_page.endswith('?page=2&size=10')
    assert items[0]['published_at'] == '2026-09-20T22:00:00+00:00'


@pytest.mark.parametrize('url', ['https://example.org/?tag=government','file:///etc/passwd','https://www.gov.pl@evil.example/web/rcb/post','https://www.gov.pl/','https://www.gov.pl:444/web/rcb/post'])
def test_untrusted_links_cannot_change_source_identity(source, url):
    with pytest.raises(ValueError):
        allowed_url(url, source)


def test_http_failure_is_not_empty_success(source, tmp_path):
    class Fetcher:
        raw_refs = []
        def get(self,url): raise TimeoutError('synthetic outage')
    result=collect_source(source,tmp_path,datetime.now(UTC),Fetcher())
    assert result['status']=='error'
    assert not result['window_complete']
    assert result['items']==[]


def test_future_publication_is_partial_not_a_clear_empty_window(source, tmp_path):
    class Fetcher:
        raw_refs = ['raw/future.json']
        def get(self, url):
            import json
            body = json.dumps({'version': 'https://jsonfeed.org/version/1.1', 'title': 'Test', 'items': [{
                'id': 'future', 'url': 'https://www.gov.pl/web/rcb/future', 'title': 'Synthetic future date',
                'date_published': (datetime.now(UTC) + timedelta(days=2)).isoformat(),
                'content_text': 'Synthetic record with an invalid future publication timestamp.'}]}).encode()
            return body, 'application/feed+json', url, 'raw/future.json'
    result = collect_source({**source, 'adapter': 'rss', 'fetch_articles': False}, tmp_path, datetime.now(UTC), Fetcher())
    assert result['status'] == 'partial'
    assert any('future' in error for error in result['errors'])
    assert len(result['items']) == 1


def test_connection_reset_is_retried_once_and_rate_limit_is_not(source,tmp_path,monkeypatch):
    import io
    import urllib.error
    from osint_dashboard.collect import Fetcher
    monkeypatch.setattr('osint_dashboard.collect.time.sleep',lambda _:None)
    class Response(io.BytesIO):
        url=source['url'];headers={'Content-Type':'text/html'}
    class Opener:
        calls=0
        def open(self,*args,**kwargs):
            self.calls+=1
            if self.calls==1:raise ConnectionResetError('Synthetic connection reset')
            return Response(b'Synthetic response')
    fetch=Fetcher(tmp_path,{**source,'max_requests':2});fetch.opener=Opener()
    assert fetch.get(source['url'])[0]==b'Synthetic response'
    assert fetch.opener.calls==fetch.request_count==2
    class Limited(Opener):
        def open(self,*args,**kwargs):
            self.calls+=1
            raise urllib.error.HTTPError(source['url'],429,'Synthetic limit',{'Retry-After':'600'},None)
    fetch=Fetcher(tmp_path,{**source,'max_requests':2});fetch.opener=Limited()
    with pytest.raises(urllib.error.HTTPError):fetch.get(source['url'])
    with pytest.raises(RuntimeError,match='cooldown'):fetch.get(source['url'])
    assert fetch.opener.calls==1 and fetch.retry_at
