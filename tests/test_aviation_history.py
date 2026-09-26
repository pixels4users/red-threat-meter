from copy import deepcopy
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
import gzip
import struct

import pytest

from osint_dashboard.common import ROOT, atomic_write, digest, instant, read_json, write_json
from osint_dashboard.aviation.history import contracts, fetch, pipeline
from osint_dashboard.aviation.history.decode import MAGIC, decode, position
from osint_dashboard.aviation.history.report import build_report, compare_live, make_snapshot


def record(identifier=1, lat=52, lon=21, alt=400, gs=2000, source=0, nonicao=False):
    return struct.pack('<IiiI', identifier | (source << 27) | (0x1000000 if nonicao else 0),
                       round(lat*1e6), round(lon*1e6), ((gs & 65535) << 16) | (alt & 65535))


def chunk(window, rows=None, indices=None):
    indices = list(range(180)) if indices is None else indices
    offset = len(indices)
    index, payload = [], []
    start = int(instant(window['start']).timestamp()*1000)
    for i in indices:
        records = [record()] if rows is None else rows.get(i, [])
        index.append(struct.pack('<4I', offset, 0, 0, 0))
        stamp = start + i*10000
        payload.append(struct.pack('<4I', MAGIC, stamp >> 32, stamp & 0xffffffff, 10000))
        payload.extend(records)
        offset += 1 + len(records)
    return gzip.compress(b''.join(index+payload), mtime=0)


@pytest.fixture
def env(tmp_path, monkeypatch):
    class Environment:
        def __init__(self):
            self.folder = tmp_path/'history'
            self.cfg = contracts.config()
            self.cfg['live_releases'] = []
            self.path = tmp_path/'config.json'
            write_json(self.path,self.cfg)
            self.responses = {}
            self.calls = []
            self.clock = datetime(2026,9,24,18,tzinfo=timezone.utc)

        def now(self):
            return self.clock.isoformat(timespec='microseconds')

        def factory(self,folder,cfg):
            parent = self
            class Fake:
                def get(self,window):
                    parent.calls.append(window['date'])
                    response = parent.responses.get(window['date'],chunk(window))
                    if isinstance(response, tuple):
                        status, headers = response
                        body = b'Synthetic error'
                    else:
                        status, headers, body = 200, {}, response
                    ref = f'raw/{digest(body)}.bin'
                    atomic_write(folder/ref,body)
                    return {'window':window,'requested_at':parent.now(),'received_at':parent.now(),'http_status':status,
                            'headers':headers,'bytes':len(body),'raw_ref':ref,'error':None if status==200 else 'http_error'}
            return Fake()

        def collect(self):
            return fetch.collect(self.folder,self.path,'fixture',self.factory)

        def report(self):
            result = pipeline.report(self.folder)
            return result, read_json(self.folder/'snapshots'/result['run_id']/'snapshot.json')
    e = Environment()
    for mod in (contracts,fetch,pipeline):
        monkeypatch.setattr(mod,'now',e.now)
    monkeypatch.setattr(fetch.time,'sleep',lambda n: None)
    return e


def test_history_units_and_namespace_do_not_invent_missing_metadata():
    p = position(struct.unpack('<IiiI',record(nonicao=True,alt=-40,gs=1234)))
    assert p['identifier']=='~000001' and p['altitude_ft']==-1000 and p['ground_speed_knots']==123.4
    assert p['altitude_reference']=='barometric_or_geometric_unspecified'
    assert p['position_at'] is None and p['military_flag'] is None and p['aircraft_type'] is None
    ground=position(struct.unpack('<IiiI',record(alt=-123,gs=-1)))
    assert ground['on_ground'] is True and ground['altitude_ft'] is None and ground['ground_speed_knots'] is None
    assert position(struct.unpack('<IiiI',record(alt=-124)))['on_ground'] is None


def test_empty_valid_intervals_remain_distinct_from_missing_files(env):
    plan=contracts.windows(env.cfg)
    env.responses[plan[0]['date']]=chunk(plan[0],{})
    env.responses[plan[1]['date']]=(404,{})
    env.collect()
    _,s=env.report()
    assert s['windows'][0]['unique_identifiers_in_window']==0
    assert s['windows'][0]['empty_region_intervals']==180
    assert s['windows'][1]['status']=='unavailable'
    assert 'unique_identifiers_in_window' not in s['windows'][1]
    assert len(env.calls)==3  # a missing day does not cancel other dates
    assert s['comparability']['baseline_eligible'] is False


def test_deduplication_conflicts_and_invalid_rows_have_raw_record_evidence(env):
    w=contracts.windows(env.cfg)[0]
    metadata=struct.pack('<4I',5,1<<30,0,0)
    rows={0:[record(),record(),record(identifier=2),record(identifier=2,lon=30),
             record(identifier=3,lat=100),record(identifier=1,nonicao=True),metadata]}
    data=decode(chunk(w,rows),w,env.cfg)
    assert data['status']=='partial'
    assert data['unique_identifiers_in_window']==2
    assert data['quality']['duplicate_rows']==2 and data['quality']['conflicting_identifiers']==1
    assert data['quality']['metadata_rows']==1 and data['quality']['invalid_rows']==1
    assert data['rejected_record_examples'][0]['record_index']==185
    assert data['frames'][0]['identifiers']==['000001','~000001']
    assert len(data['cells'])==165


def test_missing_intervals_are_audited_without_inserting_zero_observations(env):
    w=contracts.windows(env.cfg)[0]
    data=decode(chunk(w,indices=[0,2]),w,env.cfg)
    assert data['intervals']==2 and data['expected_intervals']==180 and len(data['missing_intervals'])==178
    assert data['empty_region_intervals']==0
    assert data['status']=='partial'
    assert data['identifiers_per_interval']['median']==1


@pytest.mark.parametrize('damage',['truncated_gzip','invalid_index','wrong_date','duplicate_time','unindexed_marker','bad_alignment'])
def test_bad_binary_contract_is_not_reported_as_empty_traffic(env,damage):
    w=contracts.windows(env.cfg)[0]
    body=chunk(w)
    raw=bytearray(gzip.decompress(body))
    if damage=='truncated_gzip':
        damaged=body[:-8]
    else:
        if damage=='invalid_index': struct.pack_into('<I',raw,16,180)
        if damage=='wrong_date': struct.pack_into('<I',raw,180*16+4,0)
        if damage=='duplicate_time': raw[182*16+4:182*16+12]=raw[180*16+4:180*16+12]
        if damage=='unindexed_marker': struct.pack_into('<I',raw,181*16,MAGIC)
        if damage=='bad_alignment': raw=raw[:-1]
        damaged=gzip.compress(raw)
    env.responses[w['date']]=damaged
    env.collect()
    _,s=env.report()
    assert s['windows'][0]['status']=='unavailable' and s['windows'][0]['error']=='invalid_format'
    assert 'unique_identifiers_in_window' not in s['windows'][0]


def test_decompression_limit_and_source_scope_are_enforced(env):
    w=contracts.windows(env.cfg)[0]
    cfg=deepcopy(env.cfg); cfg['max_decoded_bytes']=1024
    with pytest.raises(ValueError,match='decoded_size_limit'):
        decode(chunk(w),w,cfg)
    cfg=deepcopy(env.cfg); cfg['source']='https://example.com/'
    with pytest.raises(Exception): contracts.validate_config(cfg)
    cfg=deepcopy(env.cfg); cfg['max_total_bytes']=32000000
    with pytest.raises(ValueError,match='budżet'): contracts.validate_config(cfg)


def test_live_comparison_never_uses_future_or_distant_interval(env):
    w=contracts.windows(env.cfg)[-1]
    d=decode(chunk(w),w,env.cfg)
    reference={'run_id':'test','started_at':'2026-09-24T16:45:04+00:00','finished_at':'2026-09-24T16:45:10+00:00',
               'status':'ok','identifiers':['000001','000002']}
    r=compare_live(reference,[d])
    assert r['historical_interval_start']=='2026-09-24T16:44:50.000+00:00'
    assert r['seconds_before_live_start']==4 and r['common_identifiers']==1 and r['only_live']==1
    assert r['freshness_equivalent'] is False and r['independent_sources'] is False
    reference['started_at']='2026-09-24T16:30:04+00:00'
    assert compare_live(reference,[d])['status']=='no_matching_interval'
    reference['started_at']='2026-09-24T17:00:11+00:00'
    assert compare_live(reference,[d])['status']=='no_matching_interval'


def test_replay_checks_error_body_integrity_and_needs_no_network(env,monkeypatch):
    env.responses['2026-09-23']=(503,{})
    acq=env.collect()
    result,s=env.report()
    monkeypatch.setattr(fetch.Fetcher,'get',lambda *a: pytest.fail('Replay used network'))
    assert pipeline.replay(env.folder,result['run_id'])['identical']
    geo=read_json(env.folder/'snapshots'/result['run_id']/'coverage.geojson')
    assert len(geo['features'])==330
    assert all('identifiers' not in f['properties'] for f in geo['features'])
    (env.folder/acq['requests'][1]['raw_ref']).write_bytes(b'tampered error')
    with pytest.raises(ValueError,match='Zmieniona surowa'):
        pipeline.replay(env.folder,result['run_id'])


def test_rate_limit_stops_plan_and_persists_retry_after(env):
    env.responses['2026-09-22']=(429,{'retry-after':'7200'})
    env.collect()
    assert len(env.calls)==1
    _,s=env.report()
    assert s['counts']['unavailable_windows']==3
    assert 'Brak poprawnie odczytanych okien' in build_report(s)
    env.clock+=timedelta(seconds=4000)
    with pytest.raises(ValueError,match='najwcześniej'): env.collect()
    assert len(env.calls)==1


def test_collection_size_guard_does_not_read_or_archive_large_response(tmp_path):
    cfg=contracts.config(); cfg['max_response_bytes']=1024
    class Response(BytesIO):
        code=200
        headers={'Content-Length':'2000'}
        def read(self,*args): pytest.fail('Oversized response was read')
    class Opener:
        def open(self,*args,**kwargs): return Response(b'')
    f=fetch.Fetcher(tmp_path,cfg); f.opener=Opener()
    r=f.get(contracts.windows(cfg)[0])
    assert r['error']=='response_too_large_or_invalid_length' and r['raw_ref'] is None
    assert not (tmp_path/'raw').exists()


def test_time_cutoff_fixture_mode_and_failed_export_preserve_history(env,monkeypatch):
    acq=env.collect()
    result,_=env.report()
    old=read_json(env.folder/'latest.json')
    inputs=read_json(env.folder/'snapshots'/result['run_id']/'replay-input.json')
    inputs['as_of']='2026-09-24T17:00:00+00:00'
    with pytest.raises(ValueError,match='wyprzedza'): make_snapshot(inputs,env.folder)
    with pytest.raises(ValueError): fetch.collect(ROOT/'data/aviation_history',mode='fixture',fetcher_factory=env.factory)
    def fail(*args): raise OSError('disk full')
    monkeypatch.setattr(pipeline,'build_report',fail)
    with pytest.raises(OSError): env.report()
    assert read_json(env.folder/'latest.json')==old
    assert (env.folder/'snapshots'/result['run_id']/'report.md').exists()
