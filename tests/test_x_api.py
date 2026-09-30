from copy import deepcopy
from datetime import timedelta
import json
import urllib.error

import pytest

from osint_dashboard import x_api
from osint_dashboard.common import digest, instant, load_config, read_json, write_json
from osint_dashboard.collect import collect_source
from osint_dashboard.store import Store
from osint_dashboard.x_sources import collect_captures


STAMP = '2026-09-30T12:00:00+00:00'


@pytest.fixture
def clock(monkeypatch):
    time = [STAMP]
    monkeypatch.setattr(x_api, 'now', lambda: time[0])
    # Capture validator also checks the actual observation clock.
    monkeypatch.setattr('osint_dashboard.x_sources.now', lambda: time[0])
    return time


def sources():
    return [s for s in load_config()['sources'] if s['id'].startswith('x_')]


def page(ids=range(100, 110), next_token=None):
    data = [{'id':str(i), 'text':'SYNTHETIC: German military exercise in Latvia.',
             'created_at':'2026-09-30T10:00:00Z'} for i in ids]
    return {'data':data, 'meta':{'result_count':len(data), **({'next_token':next_token} if next_token else {})}}


class Fake:
    def __init__(self, pages=None):
        self.calls = []
        self.pages = pages or [page(), page(range(200, 210))]

    def __call__(self, path, params):
        self.calls.append((path, deepcopy(params)))
        if '/by/username/' in path:
            account = path.rsplit('/', 1)[1]
            return 200, {'data':{'id':'1' if account == 'sentdefender' else '2', 'username':account}}, {}
        return 200, self.pages.pop(0), {}


def test_live_sample_ceiling_and_offline_pipeline_import(tmp_path, clock):
    fake = Fake()
    result = x_api.collect(tmp_path, transport=fake, synthetic=True)
    assert result['requests'] == 4 and result['posts_read'] == 20
    assert result['accounted_mill_usd'] == 120
    assert result['budget']['total_accounted_mill_usd'] == 120
    assert all(call[1].get('max_results') == 10 and 'expansions' not in call[1]
               for call in fake.calls if call[0].endswith('/tweets'))
    for source in sources():
        result = collect_source(source, tmp_path, instant(STAMP))
        assert result['status'] == 'partial' and len(result['items']) == 10
        assert result['scope'] == 'bounded_api_timeline' and not result['window_complete']
        assert result['checked_at'] == STAMP and result['request_count'] == 0
        with Store(tmp_path) as store, store.db:
            first = result['items'][0]
            _, added = store.add_material(source, first, first['raw_ref'], STAMP)
            assert added
            _, added = store.add_material(source, first, first['raw_ref'], STAMP)
            assert not added


def test_interval_daily_and_total_budget_survive_restarts(tmp_path, clock):
    first = x_api.collect(tmp_path, transport=Fake(), synthetic=True)
    fake = Fake()
    assert x_api.collect(tmp_path, transport=fake, synthetic=True)['reason'] == 'minimum_interval'
    assert not fake.calls
    clock[0] = '2026-09-30T14:00:00+00:00'
    blocked = x_api.collect(tmp_path, transport=fake, synthetic=True)
    assert blocked['requests'] == 0 and all(s['error'] == 'budget_limit' for s in blocked['sources'])
    assert not fake.calls
    for source in sources():
        cached = collect_captures(source, tmp_path)
        assert cached['status'] == 'partial' and cached['checked_at'] == STAMP
        assert len(cached['items']) == 10
    assert len(list((tmp_path / 'social').glob('*/*.json'))) == 2
    clock[0] = '2026-10-01T14:00:00+00:00'
    config = x_api.load_settings(); config['total_limit_mill_usd'] = 120
    assert x_api.collect(tmp_path, config=config, transport=fake, synthetic=True)['requests'] == 0
    assert not fake.calls
    assert first['budget']['total_accounted_mill_usd'] == 120


def test_legacy_budget_only_capture_cannot_replace_real_observation(tmp_path, clock):
    x_api.collect(tmp_path, transport=Fake(), synthetic=True)
    source = sources()[0]
    clock[0] = '2026-09-30T14:00:00+00:00'
    skipped = {'schema_version':'x-api-v1','synthetic':True,'account':source['account'],
        'captured_at':clock[0],'access_status':'unavailable','user_id':'1',
        'coverage_note':'Nie wykonano pełnego odczytu API X: budget_limit',
        'posts':[],'response':None,'raw_ref':None,'request_params':{},'pagination_pending':False}
    folder = tmp_path / 'social' / source['id']
    write_json(folder / (digest(skipped)+'.json'), skipped)
    cached = collect_captures(source,tmp_path)
    assert cached['status']=='partial' and cached['checked_at']==STAMP and len(cached['items'])==10
    assert cached['local_skip_at']==clock[0]
    assert (folder / (digest(skipped)+'.json')).exists()
    failed = {**skipped,'captured_at':'2026-09-30T14:01:00+00:00','coverage_note':'Nie wykonano pełnego odczytu API X: http_403'}
    clock[0] = failed['captured_at']; write_json(folder / (digest(failed)+'.json'),failed)
    assert collect_captures(source,tmp_path)['status']=='error'


def test_incremental_cursor_and_cached_user_ids(tmp_path, clock):
    x_api.collect(tmp_path, transport=Fake(), synthetic=True)
    clock[0] = '2026-10-01T12:00:00+00:00'
    fake = Fake([page(range(110, 112)), page(range(210, 211))])
    result = x_api.collect(tmp_path, transport=fake, synthetic=True)
    assert result['requests'] == 2 and result['posts_read'] == 3 and result['accounted_mill_usd'] == 15
    assert [c[1]['since_id'] for c in fake.calls] == ['109', '209']
    assert all('/by/' not in c[0] for c in fake.calls)


def test_pagination_never_skips_unread_interval(tmp_path, clock):
    fake = Fake([page(range(110, 120), 'NEXT'), page(range(210, 220), 'MORE')])
    x_api.collect(tmp_path, transport=fake, synthetic=True)
    state = read_json(tmp_path / 'x-api/state.json')
    assert 'since_id' not in state['accounts']['sentdefender']
    start_params = fake.calls[1][1]
    clock[0] = '2026-10-01T12:00:00+00:00'
    fake = Fake([page(range(100, 110)), page(range(200, 210))])
    x_api.collect(tmp_path, transport=fake, synthetic=True)
    assert fake.calls[0][1]['pagination_token'] == 'NEXT'
    assert fake.calls[0][1]['end_time'] == start_params['end_time']
    assert fake.calls[0][1]['start_time'] == start_params['start_time']
    state = read_json(tmp_path / 'x-api/state.json')
    assert state['accounts']['sentdefender']['since_id'] == '119'
    assert 'pending_params' not in state['accounts']['sentdefender']


def test_empty_page_is_real_zero_posts_without_fabricated_freshness(tmp_path, clock):
    result = x_api.collect(tmp_path, transport=Fake([{'meta':{'result_count':0}}, page([])]), synthetic=True)
    assert result['posts_read'] == 0 and result['accounted_mill_usd'] == 20
    clock[0] = '2026-10-02T12:00:00+00:00'
    stale = collect_captures(sources()[0], tmp_path)
    assert stale['status'] == 'error' and stale['checked_at'] == STAMP


def test_crash_reservation_is_not_refunded_or_ignored(tmp_path, clock):
    def crash(*_):
        raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        x_api.collect(tmp_path, transport=crash, synthetic=True)
    assert x_api.budget_status(tmp_path / 'x-api', x_api.load_settings())['total_accounted_mill_usd'] == 10
    clock[0] = '2026-09-30T14:00:00+00:00'
    fake = Fake()
    result = x_api.collect(tmp_path, transport=fake, synthetic=True)
    assert result['accounted_mill_usd'] == 70 and result['posts_read'] == 10
    assert result['sources'][-1]['error'] == 'budget_limit'


@pytest.mark.parametrize('status', [401, 403, 402, 429, 500])
def test_http_failure_never_retries_or_leaks_payload(tmp_path, clock, status):
    calls = []
    def failure(path, params):
        calls.append(path)
        return status, {'detail':'UNTRUSTED_PROVIDER_ERROR'}, {'retry-after':'90000'} if status == 429 else {}
    result = x_api.collect(tmp_path, transport=failure, synthetic=True)
    assert len(calls) == 1 and result['requests'] == 1
    assert result['accounted_mill_usd'] == 10
    assert 'UNTRUSTED_PROVIDER_ERROR' not in json.dumps(result)
    assert collect_captures(sources()[0], tmp_path)['status'] == 'error'
    if status == 429:
        clock[0] = '2026-10-01T12:00:00+00:00'
        assert x_api.collect(tmp_path, transport=failure, synthetic=True)['reason'] == 'retry_after'
        assert len(calls) == 1


def test_raw_response_integrity_and_normalized_post_cannot_be_forged(tmp_path, clock):
    result = x_api.collect(tmp_path, transport=Fake(), synthetic=True)
    path = next((tmp_path / 'social/x_sentdefender').glob('*.json'))
    capture = read_json(path)
    capture['posts'][0]['text'] = 'FORGED'
    with pytest.raises(x_api.XError, match='posts_differ'):
        x_api.validate_api_capture(capture)
    capture = read_json(path)
    raw = read_json(tmp_path / capture['raw_ref']); raw['params']['max_results'] = 100
    write_json(tmp_path / capture['raw_ref'], raw)
    assert collect_captures(sources()[0], tmp_path)['status'] == 'error'


def test_long_post_quote_provenance_and_edit_chain(tmp_path, clock):
    response = page([123])
    row = response['data'][0]
    row.update(text='short…', note_post={'text':'SYNTHETIC: German military exercise in Latvia. Full text.'},
               referenced_posts=[{'type':'quoted','id':'456'}], edit_history_post_ids=['100','123'],
               entities={'urls':[{'expanded_url':'https://example.org/primary'}]})
    x_api.collect(tmp_path, transport=Fake([response, page([])]), synthetic=True)
    item = collect_captures(sources()[0], tmp_path)['items'][0]
    assert item['text'].endswith('Full text.') and item['text_kind'] == 'social_post'
    assert item['source_record']['post_kind'] == 'quote'
    assert item['url'].endswith('/100') and item['content_provenance']['observed_url'].endswith('/123')
    assert 'https://x.com/i/status/456' in item['source_record']['referenced_urls']


def test_large_valid_capture_can_be_imported(tmp_path, clock):
    response = page()
    for row in response['data']:
        row['note_post'] = {'text':row['text'] + ' Long text.' * 2700}
    x_api.collect(tmp_path, transport=Fake([response,page([])]), synthetic=True)
    path = next((tmp_path / 'social/x_sentdefender').glob('*.json'))
    assert path.stat().st_size > 500000
    assert len(collect_captures(sources()[0],tmp_path)['items']) == 10


@pytest.mark.parametrize('field,value', [('created_at',None),('created_at','2026-10-01T00:00:00Z'),
                                        ('author_id','OTHER'),('id','broken')])
def test_bad_post_data_does_not_advance_cursor(tmp_path, clock, field, value):
    response = page([123]); response['data'][0][field] = value
    result = x_api.collect(tmp_path, transport=Fake([response]), synthetic=True)
    assert result['status'] == 'incomplete'
    state = read_json(tmp_path / 'x-api/state.json')
    assert 'since_id' not in state['accounts']['sentdefender']


def test_out_of_window_posts_fail_closed(tmp_path, clock):
    response = page([123]); response['data'][0]['created_at'] = '2026-09-28T12:00:00Z'
    result = x_api.collect(tmp_path, transport=Fake([response]), synthetic=True)
    assert result['sources'][0]['error'] == 'post_outside_requested_interval'
    assert result['posts_read'] == 1
    assert 'since_id' not in read_json(tmp_path / 'x-api/state.json')['accounts']['sentdefender']


def test_global_data_lock_prevents_parallel_charges(tmp_path, clock):
    from osint_dashboard.pipeline import locked
    fake = Fake()
    with locked(tmp_path), pytest.raises(RuntimeError, match='Another process'):
        x_api.collect(tmp_path, transport=fake, synthetic=True)
    assert not fake.calls


def test_new_token_is_not_needed_for_offline_import_or_status(tmp_path, clock, monkeypatch):
    x_api.collect(tmp_path, transport=Fake(), synthetic=True)
    monkeypatch.setattr(x_api, 'load_token', lambda *a: pytest.fail('Offline operation opened a secret'))
    assert x_api.budget_status(tmp_path / 'x-api', x_api.load_settings())['total_accounted_mill_usd'] == 120
    assert collect_captures(sources()[0], tmp_path)['status'] == 'partial'


def test_token_private_file_and_redirect_are_fail_closed(tmp_path, monkeypatch):
    monkeypatch.delenv('X_BEARER_TOKEN', raising=False)
    path = tmp_path / '.env.x'; path.write_text('X_BEARER_TOKEN=' + 'A'*40)
    path.chmod(0o644)
    with pytest.raises(x_api.XError, match='permissions'): x_api.load_token(path)
    path.chmod(0o600)
    assert x_api.load_token(path) == 'A'*40
    assert x_api.NoRedirect().redirect_request(None,None,302,'',{},'https://evil.example') is None
    with pytest.raises(x_api.XError, match='endpoint_not_allowed'):
        x_api.Transport('A'*40, x_api.load_settings())('/2/users/by/username/unconfigured', {})


def test_separate_live_budget_directories_and_modes_are_rejected(tmp_path, clock):
    with pytest.raises(x_api.XError, match='shared_live_budget'):
        x_api.collect(tmp_path, transport=Fake())
    write_json(tmp_path / '.mode.json', {'mode':'live'})
    with pytest.raises(ValueError, match='separate'):
        x_api.collect(tmp_path, transport=Fake(), synthetic=True)
