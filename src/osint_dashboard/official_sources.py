"""Direct PAŻP plan and RSO XML snapshots, without automatic threat attribution."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from .common import UTC, canonical_json, clean_text, digest, now


def local_timestamp(text):
    dt = datetime.strptime(text, '%Y-%m-%d %H:%M:%S')
    zone = ZoneInfo('Europe/Warsaw')
    a,b=dt.replace(tzinfo=zone,fold=0),dt.replace(tzinfo=zone,fold=1)
    if a.utcoffset()!=b.utcoffset() or a.astimezone(UTC).astimezone(zone).replace(tzinfo=None)!=dt:
        raise ValueError('RSO local timestamp ambiguous or nonexistent')
    return a.astimezone(UTC).isoformat()


def parse_rso(body):
    if b'<!DOCTYPE' in body.upper() or b'<!ENTITY' in body.upper():
        raise ValueError('RSO XML declarations are not accepted')
    root=ET.fromstring(body)
    meta=root.find('pagination_info')
    if root.tag!='newses' or meta is None:
        raise ValueError('RSO XML structure changed')
    nodes=root.findall('news'); expected=int(meta.attrib['totalItems'])
    if expected != len(nodes) or len(nodes)>500:
        raise ValueError('RSO export incomplete or exceeds 500 warnings')
    records=[];seen=set()
    for node in nodes:
        def field(name): return (node.findtext(name) or '').strip()
        ident=field('id')
        if not ident.isdigit() or ident in seen or not field('title') or not field('content'):
            raise ValueError('RSO warning missing identity/content or duplicated')
        seen.add(ident)
        records.append({'id':ident,'title':clean_text(field('title')),'text':clean_text(BeautifulSoup(field('content'),'html.parser').get_text(' ',strip=True)),
                        'published_at':local_timestamp(field('created_at')),'updated_at':local_timestamp(field('updated_at')),
                        'valid_from_raw':field('valid_from'),'valid_to_raw':field('valid_to'),
                        'province_slugs':sorted(p.get('slug','') for p in node.findall('./provinces/province')),
                        'rso_alarm_raw':field('rso_alarm'),'rso_type_raw':field('type'),
                        'classification':'not_reviewed','origin':'requires_authority_review'})
    return sorted(records,key=lambda r:r['id'])


def parse_pansa(body):
    soup=BeautifulSoup(body,'html.parser')
    update=soup.select_one('[data-i18n="usePlan.lastUpdate"]')
    validity=soup.select_one('[data-i18n="validity"]')
    if not update or not validity: raise ValueError('PAŻP plan metadata missing')
    date_pattern=r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}'
    stamps=re.findall(date_pattern,validity.parent.get_text(' ',strip=True))
    stamp=re.findall(date_pattern,update.parent.get_text(' ',strip=True))
    if len(stamps)!=2 or len(stamp)!=1: raise ValueError('PAŻP plan validity invalid')
    def utc(s): return datetime.strptime(s,'%Y-%m-%d %H:%M').replace(tzinfo=UTC).isoformat()
    records=[]
    tables=soup.select('table[data-table][data-view="aup"]')
    if not tables or not soup.select_one('table[data-table="bravo"]'): raise ValueError('PAŻP plan tables missing')
    for table in tables:
        for row in table.select('tbody tr'):
            cells=[clean_text(c.get_text(' ',strip=True)) for c in row.find_all('td',recursive=False)]
            if row.select_one('[data-i18n="usePlan.nil"]'): continue
            if len(cells)<2 or not cells[0].isdigit(): raise ValueError('PAŻP plan row structure changed')
            designator=cells[1]
            kind=next((name for name,pat in [('ADHOC',r'AD\s?HOC'),('NPZ',r'NPZ'),('R',r'^EPR\d'),('D',r'^EPD\d')] if re.search(pat,designator,re.I)), 'other')
            records.append({'section':table['data-table'],'row':int(cells[0]),'designator':designator,'zone_type':kind,'fields':cells[2:],
                            'state':'planned','activation_confirmed':False})
    if len(records)>1500: raise ValueError('PAŻP plan exceeds 1500 rows')
    return {'updated_at':utc(stamp[0]),'valid_from':utc(stamps[0]),'valid_until':utc(stamps[1]),'timezone':'UTC',
            'plan':'AUP/current','activation_status':'not_observed','zones':records}


def collect_official(source,fetcher):
    outcome={'source_id':source['id'],'publisher':source['publisher'],'required':source['required'],'status':'error',
             'checked_at':now(),'items':[],'errors':[],'window_complete':False,'scope':'current_official_state_only',
             'raw_refs':[],'source_definition_hash':digest(source)}
    try:
        body,ct,final,ref=fetcher.get(source['url'])
        if source['adapter']=='pansa':
            dataset=parse_pansa(body);title='PAŻP: bieżący plan wykorzystania przestrzeni powietrznej'
            published=dataset['updated_at'];count=len(dataset['zones'])
        else:
            rows=parse_rso(body);dataset={'warnings':rows,'timezone_assumption':'Europe/Warsaw','scope':'ogólne','status':'published_list_not_cancellation_register'}
            title='RSO: ogólne komunikaty i ostrzeżenia';published=max((r['updated_at'] for r in rows),default=None);count=len(rows)
        # Stable URL identifies the versioned dataset. Individual alert IDs stay in
        # the full text and allow reviews to join the same authority alert across RCB/RSO.
        outcome['items']=[{'url':source['url'],'title':title,'published_at':published,'text':canonical_json(dataset),
                           'text_kind':'official_dataset','raw_ref':ref,'content_provenance':{'responses':[{'url':final,'raw_ref':ref,'content_type':ct}],
                           'extraction':{'method':source['adapter']+'-public-v1','record_count':count}}}]
        outcome.update(status='ok',current_state_complete=True,record_count=count,
                       activation_observed=False if source['adapter']=='pansa' else None)
    except Exception as exc:
        outcome['errors']=[f'{source["id"]}: {type(exc).__name__}; {str(exc)[:180]}']
    outcome.update(checked_at=now(),raw_refs=fetcher.raw_refs,request_count=fetcher.request_count)
    return outcome
