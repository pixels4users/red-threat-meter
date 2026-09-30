import copy
import base64
import json
import threading
from datetime import timedelta
from pathlib import Path
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

pytestmark = pytest.mark.usefixtures("legacy_engine")

from osint_dashboard.common import digest, instant, read_json
from osint_dashboard.dashboard.contract import build_report, load_snapshot, validate_report
from osint_dashboard.dashboard.publication import LocalPublications, PublicationError, SupabasePublications
from osint_dashboard.dashboard.server import create_server
from osint_dashboard.pipeline import run
from conftest import batch, decision_for


@pytest.fixture
def package(tmp_path, fixture_file):
    output = run(tmp_path / 'analysis', fixture=fixture_file)
    return Path(output['snapshot']).parent


def rehash(report):
    report['report_id'] = 'rpt_' + digest({k:v for k,v in report.items() if k != 'report_id'})
    return report


def test_export_is_allowlisted_and_keeps_incomplete_state(package):
    snapshot, config = load_snapshot(package)
    snapshot['sources'][0]['errors'] = ['secret backend log with private path /Users/operator']
    report = build_report(snapshot, config)
    assert report['rtb']['score'] is None
    assert report['rtb']['status'] == 'insufficient_data'
    assert report['rtb']['confidence']['percent'] is None
    assert report['provenance']['methodology_version'] == 'rtb-v0.2'
    assert report['commentary']['text'] is None
    assert 'secret backend' not in json.dumps(report)
    assert 'raw_refs' not in json.dumps(report)
    assert 'materials' not in report


def test_tampered_package_rejected(package):
    (package / 'snapshot.json').write_text('{}')
    with pytest.raises(ValueError, match='integrity'):
        load_snapshot(package)


def test_wrong_frozen_source_config_rejected(package):
    snapshot, config = load_snapshot(package)
    config['sources'][0]['url'] = 'https://other.example'
    with pytest.raises(ValueError, match='frozen'):
        build_report(snapshot, config)


def test_snapshot_cannot_relabel_methodology_even_with_consistent_file_hashes(package):
    snapshot = read_json(package / 'snapshot.json')
    snapshot['methodology_version'] = 'rtb-v0.3'
    (package / 'snapshot.json').write_text(json.dumps(snapshot))
    manifest = read_json(package / 'manifest.json')
    manifest['files']['snapshot.json'] = digest((package / 'snapshot.json').read_bytes())
    (package / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='methodology'):
        load_snapshot(package)


def test_export_rejects_credential_parameters_in_external_packages(package):
    snapshot, config = load_snapshot(package)
    report = build_report(snapshot, config)
    report['sources'][0]['url'] += '?access_token=synthetic-placeholder'
    with pytest.raises(ValueError, match='sanitized'):
        validate_report(rehash(report))


def test_actual_analysis_review_export_publish_read(tmp_path, fixture_file):
    folder = tmp_path / 'analysis'
    first = run(folder, fixture=fixture_file)
    snapshot, config = load_snapshot(Path(first['snapshot']).parent)
    repo = LocalPublications(tmp_path / 'publication.sqlite')
    old = build_report(snapshot, config); repo.publish(old)
    queue = read_json(Path(first['review_queue']))
    materials = {m['material_id']: m for m in queue['materials']}
    decisions = [decision_for(materials[c['material_id']], c) if c['source_id'] == 'rcb' else
                 {'kind':'exclude','candidate_ids':[c['candidate_id']], 'reason':'Syntetyczny kontekst do testowania publikacji.'} for c in queue['candidates']]
    review = tmp_path / 'review.json'; review.write_text(json.dumps(batch(*decisions)))
    second = run(folder, fixture=fixture_file, review_path=review)
    snapshot, config = load_snapshot(Path(second['snapshot']).parent)
    current = build_report(snapshot, config, previous=old)
    assert current['rtb']['score'] == 15
    assert current['rtb']['trend']['delta_points'] is None
    assert len(current['incidents']) == 1
    assert current['incidents'][0]['location']['geometry'] is None
    assert current['geojson']['features'] == []  # capital is a UI anchor, not an invented incident location
    assert repo.publish(current)['created'] is True
    assert repo.publish(current)['created'] is False
    assert len(repo.history()['items']) == 2
    assert repo.latest()['report']['report_id'] == current['report_id']


def test_numeric_trend_requires_comparable_complete_reports(package):
    snapshot, config = load_snapshot(package)
    snapshot['rtb'].update(score=15,status='experimental',blockers=[])
    a = build_report(snapshot, config)
    snapshot['as_of'] = (instant(snapshot['as_of']) + timedelta(days=1)).isoformat()
    snapshot['window']['end'] = snapshot['as_of']
    snapshot['rtb']['score'] = 20
    b = build_report(snapshot, config, previous=a)
    assert b['rtb']['trend']['delta_points'] == 5
    assert b['rtb']['trend']['percent'] == 33.3
    snapshot['methodology_version'] = 'synthetic-other-methodology'
    c = build_report(snapshot, config, previous=a)
    assert c['rtb']['trend']['direction'] == 'unavailable'


def test_old_arrival_does_not_become_latest(package, tmp_path):
    snap, cfg = load_snapshot(package)
    old = build_report(snap, cfg)
    snap['as_of'] = (instant(snap['as_of']) + timedelta(days=1)).isoformat(); snap['window']['end'] = snap['as_of']
    latest = build_report(snap, cfg)
    repo = LocalPublications(tmp_path / 'published.sqlite')
    repo.publish(latest); repo.publish(old)
    assert repo.latest()['report']['report_id'] == latest['report_id']


def test_incomplete_new_report_replaces_valid_score(package, tmp_path):
    snap, cfg = load_snapshot(package)
    old = build_report(snap, cfg); old['rtb'].update(score=15,status='available'); rehash(old)
    snap['as_of'] = (instant(snap['as_of']) + timedelta(hours=1)).isoformat(); snap['window']['end'] = snap['as_of']
    latest = build_report(snap, cfg)
    repo = LocalPublications(tmp_path / 'published.sqlite'); repo.publish(old); repo.publish(latest)
    assert repo.latest()['report']['rtb']['score'] is None


def test_live_publication_never_accepts_fixture(package):
    snap, cfg = load_snapshot(package)
    repo = SupabasePublications('https://dubhsimiblpfcaudbvjb.supabase.co', 'sb_secret_synthetic_not_a_real_key')
    repo._request = lambda *a: pytest.fail('Must not perform a network request')
    with pytest.raises(PublicationError, match='Synthetic'):
        repo.publish(build_report(snap, cfg))


def test_anonymous_key_is_rejected_before_network_use():
    claims = base64.urlsafe_b64encode(b'{"role":"anon"}').decode().rstrip('=')
    with pytest.raises(PublicationError, match='anonymous'):
        SupabasePublications('https://dubhsimiblpfcaudbvjb.supabase.co', 'eyJhbGciOiJIUzI1NiJ9.' + claims + '.synthetic')


def test_history_includes_fresh_publication_despite_local_clock_rounding(monkeypatch):
    stamp = '2026-09-27T18:20:42.116795+00:00'
    row = {'report_id': 'rpt_' + 'a' * 64, 'published_at': stamp}
    monkeypatch.setattr('osint_dashboard.dashboard.publication.now', lambda: '2026-09-27T18:20:42+00:00')
    repo = SupabasePublications('https://dubhsimiblpfcaudbvjb.supabase.co', 'sb_secret_synthetic_not_a_real_key')

    def remote_read(path):
        params = parse_qs(urlsplit(path).query)
        if params['select'] == ['published_at']:
            return [{'published_at': stamp}]
        cutoff = params['published_at'][0].removeprefix('lte.')
        return [row] if instant(stamp) <= instant(cutoff) else []

    repo._request = remote_read
    assert repo.history()['items'] == [row]


def test_conflicting_state_and_arbitrary_llm_text_rejected(package):
    snap, cfg = load_snapshot(package); report = build_report(snap, cfg)
    report['rtb']['score'] = 58
    with pytest.raises(Exception): validate_report(rehash(report))
    report = build_report(snap, cfg); report['commentary']['text'] = 'Jako AI nie mogę ocenić sytuacji.'
    with pytest.raises(ValueError, match='review registry'): validate_report(rehash(report))


def test_reference_dates_cannot_be_fabricated_and_no_duplicate_events(package):
    snap, cfg = load_snapshot(package); report = build_report(snap, cfg)
    report['window']['end'] = '2020-01-01T00:00:00Z'
    with pytest.raises(ValueError, match='cutoff'): validate_report(rehash(report))


def test_private_read_api_and_download_use_same_release(package, tmp_path):
    snap, cfg = load_snapshot(package); report = build_report(snap, cfg)
    repo = LocalPublications(tmp_path / 'publication.sqlite'); repo.publish(report)
    server = create_server(repo, 0, tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        with urlopen(base + '/api/latest') as r:
            assert r.headers['Cache-Control'] == 'no-store'
            assert json.load(r)['report'] == report
        with urlopen(base + '/api/reports/' + report['report_id'] + '/geojson') as r:
            assert r.headers['Content-Disposition'].startswith('attachment')
            assert json.load(r) == report['geojson']
        for headers in ({'Host':'attacker.example'}, {'Sec-Fetch-Site':'cross-site'}):
            with pytest.raises(HTTPError) as failure:
                urlopen(Request(base + '/api/latest', headers=headers))
            assert failure.value.code == 403
    finally:
        server.shutdown(); server.server_close(); thread.join()
