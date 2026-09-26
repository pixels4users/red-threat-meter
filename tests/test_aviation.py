from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import sqlite3
from io import BytesIO
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from osint_dashboard.common import ROOT, atomic_write, digest, read_json, write_json
from osint_dashboard.aviation import collector, contracts, pipeline
from osint_dashboard.aviation.analysis import analyze_sample, parse_response
from osint_dashboard.aviation.contracts import config, identity, queries
from osint_dashboard.aviation.store import Store


def test_transport_limits_response_size_without_archiving_truncated_evidence(tmp_path):
    cfg = config()
    cfg['max_response_bytes'] = 1000
    transport = collector.Fetcher(tmp_path, cfg)
    class Response(BytesIO):
        code = 200
        headers = {'Content-Type': 'application/json'}
        def read(self, size):
            assert size == 1001
            return super().read(size)
    class Opener:
        def open(self, request, timeout):
            return Response(b'x' * 2000)
    transport.opener = Opener()
    receipt = transport.get(queries(cfg)[0])
    assert receipt['error'] == 'response_too_large'
    assert receipt['raw_ref'] is None and receipt['bytes'] == 1001
    assert not (tmp_path / 'raw').exists()


def test_http_error_body_is_archived_and_retry_after_date_is_respected(tmp_path):
    cfg = config()
    transport = collector.Fetcher(tmp_path, cfg)
    class Opener:
        def open(self, request, timeout):
            raise HTTPError(request.full_url, 429, 'Too Many Requests',
                            {'Retry-After': 'Thu, 24 Sep 2026 17:00:00 GMT', 'Set-Cookie': 'omit-this'}, BytesIO(b'limited'))
    transport.opener = Opener()
    receipt = transport.get(queries(cfg)[0])
    assert receipt['http_status'] == 429 and receipt['error'] == 'http_error'
    assert (tmp_path / receipt['raw_ref']).read_bytes() == b'limited'
    assert 'set-cookie' not in receipt['headers']
    assert collector.cooldown(receipt['headers'], '2026-09-24T16:00:00+00:00') == '2026-09-24T17:00:00+00:00'


def test_http_redirect_is_not_followed_to_another_host():
    handler = collector.NoRedirect()
    class Parent:
        def open(self, *args, **kwargs):
            pytest.fail('Redirect attempted another request')
    handler.parent = Parent()
    request = Request(queries(config())[0]['url'])
    # Returning None declines the redirect; urllib's default error handler then
    # supplies the original HTTP error to Fetcher instead of contacting the URL.
    assert handler.http_error_302(request, BytesIO(b''), 302, 'Found', {'location': 'https://example.com/unexpected'}) is None


def aircraft(**changes):
    return {"hex": "000001", "type": "adsb_icao", "lat": 52, "lon": 21, "seen": 0, "seen_pos": 2,
            "alt_baro": 10000, "gs": 200, "t": "A320", "dbFlags": 1, **changes}


class Environment:
    def __init__(self, folder):
        self.folder = folder
        self.clock = datetime(2026, 9, 24, 16, tzinfo=timezone.utc)
        self.responses = {}
        self.calls = []

    def now(self):
        return self.clock.isoformat(timespec="microseconds")

    def advance(self, seconds=61):
        self.clock += timedelta(seconds=seconds)

    def payload(self, rows=None, **changes):
        rows = [aircraft()] if rows is None else rows
        return {"ac": rows, "total": len(rows), "msg": "No error", "now": int(self.clock.timestamp()*1000),
                "ctime": int(self.clock.timestamp()*1000), "ptime": 0, **changes}

    def fetcher(self, folder, cfg):
        parent = self
        class Fake:
            def get(self, query):
                qid = query["id"]
                parent.calls.append(qid)
                result = parent.responses.get(qid, parent.payload())
                if isinstance(result, tuple):
                    status, headers = result
                    body = b'{"error":"synthetic HTTP error"}'
                else:
                    status, headers = 200, {}
                    body = result if isinstance(result, bytes) else json.dumps(result).encode()
                ref = f"raw/adsblol/{digest(body)}.bin"
                atomic_write(folder/ref, body)
                return {"query": query, "requested_at": parent.now(), "received_at": parent.now(), "http_status": status,
                        "headers": headers, "raw_ref": ref, "bytes": len(body), "error": None if status == 200 else "http_error"}
        return Fake()

    def run(self, **kwargs):
        return pipeline.run(self.folder, mode="fixture", fetcher_factory=self.fetcher, **kwargs)

    def snapshot(self, result):
        return read_json(self.folder / "snapshots" / result["run_id"] / "snapshot.json")

    def inputs(self, result):
        return read_json(self.folder / "snapshots" / result["run_id"] / "replay-input.json")


@pytest.fixture
def env(tmp_path, monkeypatch):
    instance = Environment(tmp_path / "aviation")
    for mod in (collector, contracts, pipeline):
        monkeypatch.setattr(mod, "now", instance.now)
    monkeypatch.setattr(collector.time, "sleep", lambda s: None)
    return instance


def test_regional_run_deduplicates_overlaps_retains_units_and_replays(env, monkeypatch):
    result = env.run()
    snap = env.snapshot(result)
    latest = snap["latest"]
    assert len(env.calls) == 4
    assert latest["metrics"]["fresh_in_region"] == 1
    assert latest["metrics"]["overlap_rows_removed"] == 3
    assert latest["metrics"]["position_age_median_seconds"] == 2
    row = latest["records"][0]
    assert row["barometric_altitude_ft"] == 10000 and row["ground_speed_knots"] == 200
    assert row["operator"] is None and row["intent"] is None
    assert row["military_flag_reported"] is True and row["classification_status"] == "provider_reported_unverified"
    assert snap["receiver_coverage"] == "unknown" and snap["rtb_effect"] == "none"
    assert len(latest["cells"]) == 165 and all(c["query_scope_available"] for c in latest["cells"])
    geo = read_json(env.folder / "snapshots" / result["run_id"] / "coverage.geojson")
    assert len(geo["features"]) == 165
    assert all("identifier" not in f["properties"] for f in geo["features"])
    monkeypatch.setattr(collector.Fetcher, "get", lambda *args: pytest.fail("Offline replay used network"))
    assert pipeline.replay(env.folder, result["run_id"])["identical"]
    with Store(env.folder) as db:
        assert db.doctor()["raw_files_checked"] == 1


def test_latest_position_is_chosen_before_region_filter(env):
    env.responses["q1"] = env.payload([aircraft(lon=21, seen_pos=10)])
    for q in ("q2", "q3", "q4"):
        env.responses[q] = env.payload([aircraft(lon=30, seen_pos=1)])
    latest = env.snapshot(env.run())["latest"]
    assert latest["metrics"]["fresh_in_region"] == 0
    assert latest["metrics"]["outside_region"] == 1
    assert latest["records"][0]["position"] == [30, 52]


def test_position_freshness_uses_response_age_and_retains_missing_values(env):
    rows = [aircraft(seen_pos=31), aircraft(hex="000002", lat=None),
            aircraft(hex="000003", seen_pos=None), aircraft(hex="000004", alt_baro="ground", dbFlags=0, seen_pos=0),
            aircraft(hex="~000004", dbFlags=None, seen_pos=0)]
    for q in queries(config()):
        env.responses[q["id"]] = env.payload(rows, now=int((env.clock.timestamp()-30)*1000))
    latest = env.snapshot(env.run())["latest"]
    m = latest["metrics"]
    assert m["stale_or_future_position"] == 1 and m["missing_position"] == 1 and m["unknown_position_age"] == 1
    assert m["fresh_in_region"] == 2 and m["fresh_on_ground_reported"] == 1
    assert m["military_flag_absent"] == 1 and m["military_flag_unknown"] == 1
    assert m["position_age_median_seconds"] == 30
    # ICAO and non-ICAO address namespaces must not be merged.
    assert {r["identifier"] for r in latest["records"]} >= {"000004", "~000004"}


@pytest.mark.parametrize("changes", [{"lat": 91}, {"hex": "not-a-hex"}, {"seen_pos": -1}, {"seen": True},
                                      {"gs": float("inf")}, {"t": "untrusted **markup**"}])
def test_malformed_rows_are_audited_and_not_silently_counted(env, changes):
    # Use a finite malformed row alongside a valid row. Infinity makes the whole
    # JSON nonstandard, which must be rejected rather than repaired.
    data = env.payload([aircraft(hex="000002"), aircraft(**changes)])
    env.responses["q1"] = data
    latest = env.snapshot(env.run())["latest"]
    assert latest["status"] == "partial"
    q1 = latest["requests"][0]
    assert q1["error"] == "invalid_contract" or q1["rejected_row_indices"] == [1]


@pytest.mark.parametrize("changed", [{"total": 99}, {"now": 1790260000}, {"msg": "upstream error"}])
def test_bad_envelopes_do_not_look_like_valid_empty_measurements(env, changed):
    for q in queries(config()):
        env.responses[q["id"]] = env.payload(**changed)
    snap = env.snapshot(env.run())
    assert snap["latest"]["status"] == "unavailable"
    assert snap["latest"]["metrics"]["fresh_in_region"] is None
    assert snap["counts"]["unavailable_sample_share_pct"] == 100
    assert all(c["fresh_identifiers"] is None for c in snap["latest"]["cells"])


def test_empty_response_distinct_from_failure_and_stale_data(env):
    for q in queries(config()):
        env.responses[q["id"]] = env.payload([])
    snap = env.snapshot(env.run())
    assert snap["latest"]["status"] == "ok" and snap["counts"]["complete_empty_samples"] == 1
    assert snap["latest"]["metrics"]["fresh_in_region"] == 0
    env.advance()
    for q in queries(config()):
        env.responses[q["id"]] = env.payload(now=int((env.clock.timestamp()-120)*1000))
    snap = env.snapshot(env.run())
    assert snap["latest"]["status"] == "unavailable" and snap["latest"]["metrics"]["fresh_in_region"] is None
    assert snap["counts"]["unavailable_samples"] == 1


def test_partial_query_failure_does_not_erase_successful_regions(env):
    env.responses["q4"] = (503, {})
    snap = env.snapshot(env.run())
    assert len(env.calls) == 4 and snap["latest"]["status"] == "partial"
    assert snap["latest"]["metrics"]["fresh_in_region"] == 1
    assert snap["latest"]["metrics"]["query_gap_cells"] > 0


def test_rate_limit_stops_remaining_queries_and_survives_restart(env):
    env.responses["q1"] = (429, {"retry-after": "600"})
    result = env.run()
    assert env.calls == ["q1"]
    assert env.snapshot(result)["latest"]["status"] == "unavailable"
    env.advance(599)
    with pytest.raises(ValueError, match="najwcześniej"):
        env.run()
    assert env.calls == ["q1"]
    env.advance(2)
    env.responses = {}
    assert env.snapshot(env.run())["latest"]["status"] == "ok"


def test_repeat_payloads_preserve_receipts_and_do_not_invent_new_flights(env):
    data = env.payload()
    env.responses = {q["id"]: data for q in queries(config())}
    first = env.run()
    with pytest.raises(ValueError, match="najwcześniej"):
        env.run()
    env.advance()
    # Cached payload becomes stale; fresh current samples are not fabricated.
    second = env.run()
    snap = env.snapshot(second)
    assert snap["counts"]["samples"] == 2 and snap["latest"]["metrics"]["fresh_in_region"] is None
    assert snap["series"][0]["content_fingerprint"] == snap["series"][1]["content_fingerprint"]
    with Store(env.folder) as db:
        assert db.doctor()["raw_files_checked"] == 1
        assert db.counts()["samples"] == 2
    assert pipeline.replay(env.folder, first["run_id"])["identical"]


def test_offline_cutoff_expiry_and_config_change(env, tmp_path):
    first = env.run()
    inputs = env.inputs(first)
    inputs["as_of"] = (env.clock - timedelta(seconds=1)).isoformat()
    with pytest.raises(ValueError, match="not known"):
        pipeline.validate_inputs(inputs)
    env.advance(901)
    snap = env.snapshot(env.run(offline=True))
    assert not snap["latest_is_current"]
    assert len(env.calls) == 4
    changed = config()
    changed["position_max_age_seconds"] = 30
    path = tmp_path / "changed.json"
    write_json(path, changed)
    snap = env.snapshot(env.run(offline=True, config_path=path))
    assert snap["latest"] is None and snap["counts"]["excluded_configuration_samples"] == 1


def test_future_measurement_does_not_become_fresh_observation(env):
    for q in queries(config()):
        env.responses[q["id"]] = env.payload(now=int((env.clock.timestamp()+20)*1000))
    snap = env.snapshot(env.run())
    assert snap["latest"]["status"] == "unavailable"
    assert all(r["error"] == "invalid_contract" for r in snap["latest"]["requests"])


def test_archives_are_append_only_and_raw_error_evidence_checked_in_replay(env):
    env.responses["q4"] = (503, {})
    result = env.run()
    with Store(env.folder) as db:
        with pytest.raises(sqlite3.IntegrityError, match="Append-only"):
            db.db.execute("DELETE FROM samples")
        db.db.rollback()
    raw = env.inputs(result)["samples"][0]["requests"][3]["raw_ref"]
    (env.folder / raw).write_text("changed error evidence")
    with pytest.raises(ValueError, match="integrity"):
        pipeline.replay(env.folder, result["run_id"])


def test_failed_export_keeps_previous_latest_and_fixture_live_separation(env, monkeypatch):
    first = env.run()
    original = pipeline.write_json
    def fail(path, data):
        if Path(path).name == "snapshot.json":
            raise OSError("synthetic disk failure")
        return original(path, data)
    monkeypatch.setattr(pipeline, "write_json", fail)
    with pytest.raises(OSError):
        env.run(offline=True)
    assert read_json(env.folder / "latest.json")["run_id"] == first["run_id"]
    assert not list((env.folder / "snapshots").glob(".staging-*"))
    with pytest.raises(ValueError, match="Fixture and live"):
        pipeline.run(env.folder, offline=True)
    with pytest.raises(ValueError, match="Synthetic"):
        pipeline.run(ROOT / "data/aviation", mode="fixture", fetcher_factory=env.fetcher)


def test_query_scope_and_contract_cannot_be_redirected_by_configuration():
    cfg = config()
    cfg["source"]["base_url"] = "https://example.test/steal/"
    with pytest.raises(Exception):
        contracts.validate_config(cfg)
    cfg = config()
    cfg["region"]["bbox"] = [0, 0, 100, 1]
    with pytest.raises(ValueError, match="footprint"):
        contracts.validate_config(cfg)


def test_duplicate_json_keys_and_old_fallback_positions_are_not_accepted_as_current(env):
    env.responses["q1"] = b'{"now":1,"now":2,"ac":[],"total":0,"msg":"No error"}'
    for q in ("q2", "q3", "q4"):
        env.responses[q] = env.payload([aircraft(lat=None, lon=None, lastPosition={"lat":52,"lon":21,"seen_pos":120}, rr_lat=52, rr_lon=21)])
    latest = env.snapshot(env.run())["latest"]
    assert latest["requests"][0]["error"] == "invalid_contract"
    assert latest["metrics"]["missing_position"] == 1 and latest["metrics"]["fresh_in_region"] == 0
