from datetime import datetime

import pytest

from osint_dashboard.bulletin_sources import article, collect_bulletins, listing
from osint_dashboard.common import ROOT, UTC, load_config


def source(name):
    return next(s for s in load_config()['sources'] if s['id'] == name)


def cert_row(number, day='29-09-2026'):
    return f'<a href=" /komunikaty/2026/{number}/test/ "><div class="advisory-card"><h3>Test syntetyczny</h3><p>Skrót</p><div class="subtitle"><div>{day}</div><div>[{number}/2026]</div></div></div></a>'


def sg_row(number, day='29.09.2026'):
    return f'<li class="news"><a href="/pod/aktualnosci/{number},Test.html"><h3>Test syntetyczny</h3><p>Skrót</p><span class="data">{day}</span></a></li>'


CERT = b'<main><div id="alert-advisory-1"><h1 data-advisory-title="1">Test</h1><div class="subtitle">29-09-2026</div><p>SYNTHETIC: initial vulnerability advisory without actor attribution.</p><p>Correction: vendor released a patch.</p><div class="d-none">private form token</div></div></main>'
SG = b'<div class="head"><h2>Test</h2><h3>SYNTHETIC: Border Guard lead contains the observation period.</h3></div><article class="txt"><p>Synthetic details for parser verification, not live data.</p><div class="zdjecia">Image caption unrelated to observation</div></article>'


def test_full_body_retains_updates_and_border_lead_without_hidden_controls():
    text = article(CERT, 'cert_pl')
    assert 'Correction: vendor released a patch.' in text and 'private form token' not in text
    assert 'Test' not in text
    text = article(SG, 'sg_podlaski')
    assert 'observation period' in text and 'Synthetic details' in text
    assert 'Image caption' not in text
    for parser in ('cert_pl', 'sg_podlaski'):
        with pytest.raises(ValueError):
            article(b'<main>Sign in</main>', parser)


@pytest.mark.parametrize('name,row,next_page', [('cert_pl', cert_row, 2), ('sg_podlaski', sg_row, 1)])
def test_listing_preserves_date_precision_and_only_sequential_pagination(name, row, next_page):
    cfg = source(name)
    label = '›' if name == 'cert_pl' else 'Następny'
    html = '<main>' + row(1) + f'<a href="?page={next_page}">{label}</a></main>'
    items, following = listing(html, cfg['url'], cfg)
    assert len(items) == 1 and items[0]['published_at'] is None
    assert items[0]['source_record']['published_on'] == '2026-09-29'
    assert items[0]['source_record']['occurrence_time'] is None
    assert following.endswith(f'?page={next_page}')
    with pytest.raises(ValueError):
        listing(html.replace(f'page={next_page}', 'page=9'), cfg['url'], cfg)
    with pytest.raises(ValueError):
        listing('<main>' + row(1) + row(1) + '</main>', cfg['url'], cfg)
    with pytest.raises(ValueError):
        listing(html.replace('href=" ', 'href="https://evil.example') if name == 'cert_pl' else html.replace('href="/pod', 'href="https://evil.example/pod'), cfg['url'], cfg)


def test_archive_boundary_is_not_claimed_for_truncated_or_unreadable_articles():
    cfg = {**source('cert_pl'), 'max_items': 1}
    cfg.pop('publication_feed_url')
    class Fetch:
        raw_refs = ['raw/synthetic']; request_count = 0
        def get(self, url):
            self.request_count += 1
            body = ('<main>'+cert_row(2)+cert_row(1,'20-09-2026')+'</main>').encode() if url == cfg['url'] else CERT
            return body, 'text/html', url, self.raw_refs[0]
    r = collect_bulletins(cfg, datetime(2026,9,21,tzinfo=UTC), Fetch())
    assert len(r['items']) == 1 and not r['window_complete'] and r['status'] == 'partial'
    cfg['max_items'] = 2
    r = collect_bulletins(cfg, datetime(2026,9,21,tzinfo=UTC), Fetch())
    assert r['status'] == 'ok' and r['window_complete']
    class Broken(Fetch):
        def get(self, url):
            if url != cfg['url']:
                raise TimeoutError('Synthetic article outage')
            return super().get(url)
    r = collect_bulletins(cfg, datetime(2026,9,21,tzinfo=UTC), Broken())
    assert r['status'] == 'partial' and all(i['text_kind'] == 'listing_summary' for i in r['items'])


def test_feed_adds_only_real_matching_publication_timestamp():
    cfg = source('cert_pl')
    target = cfg['url'] + '2026/1/test/'
    class Fetch:
        raw_refs = ['raw/synthetic']; request_count = 0
        stamp = 'Mon, 21 Sep 2026 14:00:00 GMT'
        def get(self, url):
            self.request_count += 1
            if url == cfg['publication_feed_url']:
                return f'<rss><channel><item><title>Test</title><link>{target}</link><pubDate>{self.stamp}</pubDate></item></channel></rss>'.encode(), 'application/xml', url, 'raw/feed'
            body = ('<main>'+cert_row(1,'21-09-2026')+'</main>').encode() if url == cfg['url'] else CERT
            return body, 'text/html', url, self.raw_refs[0]
    r = collect_bulletins(cfg, datetime(2026,9,22,tzinfo=UTC), Fetch())
    assert r['items'][0]['published_at'] == '2026-09-21T14:00:00+00:00'
    assert len(r['items'][0]['content_provenance']['responses']) == 3
    wrong = Fetch(); wrong.stamp = 'Sun, 20 Sep 2026 14:00:00 GMT'
    r = collect_bulletins(cfg, datetime(2026,9,22,tzinfo=UTC), wrong)
    assert r['items'][0]['published_at'] is None and r['status'] == 'partial'
