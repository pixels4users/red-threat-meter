"""Bounded, dated publisher archives. Publication coverage is not event coverage."""
import re
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urljoin, urlsplit
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from .collect import _feed, allowed_url, parse_published
from .common import clean_text, digest, instant, now


def publication_date(text, parser):
    fmt = '%d-%m-%Y' if parser == 'cert_pl' else '%d.%m.%Y'
    day = datetime.strptime(clean_text(text), fmt).replace(tzinfo=ZoneInfo('Europe/Warsaw'))
    return day.date().isoformat()


def listing(body, url, source):
    soup = BeautifulSoup(body, 'html.parser')
    parser = source['bulletin_parser']
    rows = soup.select('main .advisory-card' if parser == 'cert_pl' else 'li.news')
    if not rows:
        raise ValueError('Dated bulletin listing missing')
    entries = []
    for row in rows:
        link = row.find_parent('a', href=True) if parser == 'cert_pl' else row.select_one('a[href]')
        title = row.select_one('h3')
        stamp = row.select_one('.subtitle > div') if parser == 'cert_pl' else row.select_one('.data')
        intro = row.select_one('p')
        if not link or not title or not stamp:
            raise ValueError('Bulletin identity, title or publication date missing')
        target = allowed_url(urljoin(url, link['href'].strip()), source)
        pattern = r'/komunikaty/\d{4}/\d+/[^/]+/' if parser == 'cert_pl' else r'/pod/aktualnosci/\d+,[^/]+\.html'
        if not re.fullmatch(pattern, urlsplit(target).path):
            raise ValueError('Unexpected bulletin document path')
        published = publication_date(stamp.get_text(' ', strip=True), parser)
        if published > instant(now()).astimezone(ZoneInfo('Europe/Warsaw')).date().isoformat():
            raise ValueError('Future bulletin publication date')
        entries.append({'url': target, 'title': clean_text(title.get_text(' ', strip=True)),
                        'published_at': None, 'text': clean_text(intro.get_text(' ', strip=True)) if intro else '',
                        'text_kind': 'listing_summary',
                        'source_record': {'published_on': published, 'publication_precision': 'date', 'occurrence_time': None}})
    dates = [e['source_record']['published_on'] for e in entries]
    if dates != sorted(dates, reverse=True) or len({e['url'] for e in entries}) != len(entries):
        raise ValueError('Bulletin order or identity conflict')
    label = '›' if parser == 'cert_pl' else 'Następny'
    links = [a for a in soup.select('a[href]') if a.get_text(' ', strip=True) == label]
    if len(links) > 1:
        raise ValueError('Ambiguous archive pagination')
    following = allowed_url(urljoin(url, links[0]['href']), source) if links else None
    if following:
        default_page = '1' if parser == 'cert_pl' else '0'
        current_page = int(parse_qs(urlsplit(url).query).get('page', [default_page])[0])
        if (urlsplit(following).path != urlsplit(source['url']).path or
                parse_qs(urlsplit(following).query) != {'page': [str(current_page + 1)]}):
            raise ValueError('Archive pagination is not sequential')
    return entries, following


def article(body, parser):
    soup = BeautifulSoup(body, 'html.parser')
    if parser == 'cert_pl':
        content = soup.select_one('main div[id^="alert-advisory-"]')
        heading = content.select_one('h1[data-advisory-title]') if content else None
        if not heading:
            raise ValueError('CERT bulletin body missing')
        for node in content.select('h1,.badge,.subtitle,script,style,form,input,.d-none'):
            node.decompose()
        text = content.get_text(' ', strip=True)
    else:
        content = soup.select_one('article.txt')
        head = content.find_previous_sibling('div', class_='head') if content else None
        if not content or not head or not head.select_one('h2'):
            raise ValueError('Border Guard article body missing')
        for node in content.select('.zdjecia,figure,script,style,form,nav'):
            node.decompose()
        lead = head.select_one('h3')
        text = (lead.get_text(' ', strip=True) + ' ' if lead else '') + content.get_text(' ', strip=True)
    text = clean_text(text)
    if len(text) < 50:
        raise ValueError('Bulletin body unexpectedly short')
    return text


def collect_bulletins(source, window_start, fetcher):
    result = {'source_id': source['id'], 'publisher': source['publisher'], 'required': source['required'],
              'status': 'error', 'checked_at': now(), 'items': [], 'errors': [], 'window_complete': False,
              'scope': 'publisher_bulletins_not_all_incidents', 'source_definition_hash': digest(source)}
    seen, previous_oldest, url = set(), None, source['url']
    timestamps = {}
    if source.get('publication_feed_url'):
        try:
            feed_body, feed_type, feed_url, feed_ref = fetcher.get(source['publication_feed_url'])
            entries = _feed.parse_feed(feed_body, feed_type)['entries']
            if not entries:
                raise ValueError('Publication feed missing entries')
            for entry in entries[:source['max_items']]:
                target = allowed_url(entry.get('link') or '', source)
                stamp = parse_published(entry.get('published'))
                if stamp and instant(stamp) <= instant(now()) + timedelta(minutes=5):
                    timestamps[target] = (stamp, {'url': feed_url, 'raw_ref': feed_ref, 'content_type': feed_type})
        except Exception as exc:
            result['errors'].append('Publication feed unavailable: ' + type(exc).__name__)
    try:
        for _ in range(source['max_pages']):
            body, content_type, final, ref = fetcher.get(url)
            if 'text/html' not in content_type:
                raise ValueError('Expected bulletin archive HTML')
            entries, following = listing(body, final, source)
            if previous_oldest and entries[0]['source_record']['published_on'] > previous_oldest:
                raise ValueError('Archive changed while paginating')
            previous_oldest = entries[-1]['source_record']['published_on']
            for item in entries:
                if item['url'] in seen:
                    continue
                if len(result['items']) >= source['max_items']:
                    break
                seen.add(item['url'])
                item['raw_ref'] = ref
                responses = [{'url': final, 'raw_ref': ref, 'content_type': content_type}]
                if item['url'] in timestamps:
                    stamp, feed_response = timestamps[item['url']]
                    if instant(stamp).astimezone(ZoneInfo('Europe/Warsaw')).date().isoformat() == item['source_record']['published_on']:
                        item['published_at'] = stamp
                        item['source_record']['publication_precision'] = 'timestamp'
                        responses.append(feed_response)
                    else:
                        result['errors'].append('Publication date conflicts with feed: ' + item['url'])
                try:
                    full, kind, final_article, full_ref = fetcher.get(item['url'])
                    if 'text/html' not in kind:
                        raise ValueError('Expected bulletin HTML')
                    item.update(text=article(full, source['bulletin_parser']), text_kind='article_body', raw_ref=full_ref)
                    responses.append({'url': final_article, 'raw_ref': full_ref, 'content_type': kind})
                except Exception as exc:
                    result['errors'].append('Article unavailable (' + type(exc).__name__ + '): ' + item['url'])
                item['content_provenance'] = {'responses': responses, 'extraction': {
                    'method': source['bulletin_parser'] + '-bulletin-v1', 'occurrence_time_inferred': False}}
                result['items'].append(item)
                if item['source_record']['published_on'] < window_start.astimezone(ZoneInfo('Europe/Warsaw')).date().isoformat():
                    result['window_complete'] = True
            if result['window_complete'] or not following or len(result['items']) >= source['max_items']:
                break
            url = following
        if not result['window_complete']:
            result['errors'].append('Publication window not reached within bounded archive')
        result['status'] = 'partial' if result['errors'] else 'ok'
    except Exception as exc:
        result['errors'].append(type(exc).__name__ + ': ' + str(exc)[:200])
        result['status'] = 'partial' if result['items'] else 'error'
        result['window_complete'] = False
    result.update(checked_at=now(), raw_refs=list(dict.fromkeys(fetcher.raw_refs)), request_count=fetcher.request_count)
    return result
