"""Bounded public text pages and dated summaries from one primary channel."""
import re
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

from bs4 import BeautifulSoup

from .common import clean_text, digest, instant, now
from .collect import allowed_url


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
               'scope': 'bounded_public_channel_and_summaries', 'raw_refs': [], 'source_definition_hash': digest(source),
               'pages_read': 0, 'summary_pages_read': 0}
    seen = {}
    def page(target, discovery):
        body, content_type, url, ref = fetcher.get(target)
        if 'text/html' not in content_type:
            raise ValueError('Expected public channel HTML')
        items = parse_air_force(body, 20)
        outcome['pages_read'] += 1
        outcome['summary_pages_read'] += int(discovery == 'summary_search')
        for item in items:
            if item['url'] in seen:
                if seen[item['url']]['text'] != item['text']:
                    outcome['errors'].append('Post changed between pages: ' + item['url'])
                continue
            if len(seen) >= source['max_items']:
                outcome['errors'].append('Text post limit reached')
                break
            item.update(raw_ref=ref, content_provenance={
                'responses': [{'url': url, 'raw_ref': ref, 'content_type': content_type}],
                'extraction': {'method': 'ua-air-force-public-v2', 'discovery': discovery,
                               'coverage': 'bounded_text_pages_no_history_guarantee'}})
            seen[item['url']] = item
        return body, url
    url = source['url']
    recent_pages = source['max_pages'] - int(bool(source.get('summary_query')))
    for index in range(recent_pages):
        try:
            body, final = page(url, 'recent_posts')
            if index + 1 == recent_pages:
                break
            next_url = previous_page(body, final, source)
            if next_url is None:
                break
            url = next_url
        except Exception as exc:
            outcome['errors'].append('recent_posts: ' + type(exc).__name__)
            break
    if source.get('summary_query') and len(seen) < source['max_items']:
        try:
            page(source['url'] + '?' + urlencode({'q': source['summary_query']}), 'summary_search')
        except Exception as exc:
            outcome['errors'].append('summary_search: ' + type(exc).__name__)
    outcome.update(items=sorted(seen.values(), key=lambda p: (p['published_at'], p['url'])),
                   status='partial' if seen else 'error')
    outcome.update(checked_at=now(), raw_refs=fetcher.raw_refs, request_count=fetcher.request_count)
    return outcome


def previous_page(body, url, source):
    soup = BeautifulSoup(body, 'html.parser')
    link = soup.select_one('a.tme_messages_more[data-before][href]')
    if link is None:
        return None
    cursor = link['data-before']
    target = allowed_url(urljoin(url, link['href']), source)
    query = parse_qs(urlsplit(target).query)
    current = parse_qs(urlsplit(url).query).get('before', [None])[0]
    ids = [int(n['data-post'].split('/')[1]) for n in soup.select('.tgme_widget_message[data-post]')
           if re.fullmatch(r'kpszsu/[0-9]+', n['data-post'])]
    if (not cursor.isdigit() or not ids or int(cursor) != min(ids) or
            urlsplit(target).path != '/s/kpszsu' or query != {'before': [cursor]} or
            (current is not None and int(cursor) >= int(current))):
        raise ValueError('Invalid public channel pagination')
    return target
