"""One bounded public page of an allowlisted primary channel, never telemetry."""
import re

from bs4 import BeautifulSoup

from .common import clean_text, digest, instant, now


def parse_air_force(body, limit=20):
    soup = BeautifulSoup(body, 'html.parser')
    nodes = soup.select('.tgme_widget_message[data-post]')
    if not nodes:
        raise ValueError('Public channel preview is unavailable or changed')
    items, seen = [], set()
    for node in nodes[-limit:]:
        identity = node['data-post']
        if not re.fullmatch(r'kpszsu/[0-9]+', identity) or identity in seen:
            raise ValueError('Unexpected or duplicate public post identity')
        seen.add(identity)
        content = node.select_one('.tgme_widget_message_text')
        stamp = node.select_one('.tgme_widget_message_date time[datetime]')
        # Image-only/video-only messages are not readable evidence.
        if content is None or stamp is None:
            continue
        text = clean_text(content.get_text(' ', strip=True))
        if not text:
            continue
        forwarded = node.select_one('.tgme_widget_message_forwarded_from')
        replies = [a['href'] for a in node.select('.tgme_widget_message_reply[href]')]
        items.append({'url': 'https://t.me/' + identity,
                      'title': 'Siły Powietrzne Ukrainy — komunikat ' + identity.split('/')[1],
                      'published_at': instant(stamp['datetime']).isoformat(), 'text': text,
                      'text_kind': 'social_post',
                      'source_record': {'post_id': identity, 'channel': 'kpszsu',
                                        'forwarded_from': clean_text(forwarded.get_text(' ', strip=True)) if forwarded else None,
                                        'reply_urls': replies, 'occurrence_time': None,
                                        'coverage': 'bounded_public_text_preview'}})
    if not items:
        raise ValueError('No readable dated text posts in public preview')
    return items


def collect_air_force(source, fetcher):
    outcome = {'source_id': source['id'], 'publisher': source['publisher'], 'required': source['required'],
               'status': 'error', 'checked_at': now(), 'items': [], 'errors': [], 'window_complete': False,
               'scope': 'bounded_public_channel_preview', 'raw_refs': [], 'source_definition_hash': digest(source)}
    try:
        body, content_type, url, ref = fetcher.get(source['url'])
        if 'text/html' not in content_type:
            raise ValueError('Expected public channel HTML')
        items = parse_air_force(body, source['max_items'])
        for item in items:
            item.update(raw_ref=ref, content_provenance={
                'responses': [{'url': url, 'raw_ref': ref, 'content_type': content_type}],
                'extraction': {'method': 'ua-air-force-public-v1', 'coverage': 'one_page_no_history_guarantee'}})
        outcome.update(items=items, status='partial')
    except Exception as exc:
        outcome['errors'] = ['ua_air_force_public: ' + type(exc).__name__]
    outcome.update(checked_at=now(), raw_refs=fetcher.raw_refs, request_count=fetcher.request_count)
    return outcome
