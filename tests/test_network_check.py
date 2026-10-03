"""Preflight stays read-only, reports failures and compares the full public payload."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

from osint_dashboard.common import ROOT
from osint_dashboard.dashboard.contract import build_report, load_snapshot, validate_report
from osint_dashboard.pipeline import run


spec = importlib.util.spec_from_file_location("rta_network_check", ROOT / "scripts/check_network.py")
network = importlib.util.module_from_spec(spec)
spec.loader.exec_module(network)


def test_dns_failure_does_not_load_secrets_or_request_services(monkeypatch):
    def blocked(*args, **kwargs):
        raise OSError("execution has no network")

    def forbidden(*args, **kwargs):
        pytest.fail("Must not attempt services or load credentials after a DNS failure")

    monkeypatch.setattr(network.socket, "getaddrinfo", blocked)
    monkeypatch.setattr(network, "load_environment", forbidden)
    monkeypatch.setattr(network, "urlopen", forbidden)
    result = network.check()
    assert not result["ready"]
    assert result["paid_requests"] == 0
    assert set(result["dns"].values()) == {"dns_unavailable_in_this_execution"}


@pytest.fixture
def report(tmp_path, fixture_file, legacy_engine):
    output = run(tmp_path / "isolated-analysis", fixture=fixture_file)
    snapshot, config = load_snapshot(Path(output["snapshot"]).parent)
    return build_report(snapshot, config)


def connect(monkeypatch, stored, public):
    class Store:
        def latest(self, report_type):
            assert report_type == "daily"
            validate_report(stored)
            return {"report": stored}

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, limit):
            return json.dumps({"report": public}).encode()[:limit]

    def request(req, timeout):
        assert req.full_url == "https://redthreatalert.pl/api/latest"
        assert req.get_method() == "GET"
        assert "Authorization" not in req.headers
        return Response()

    monkeypatch.setattr(network.socket, "getaddrinfo", lambda *a, **kw: [])
    monkeypatch.setattr(network, "load_environment", lambda: None)
    monkeypatch.setattr(network, "SupabasePublications", Store)
    monkeypatch.setattr(network, "urlopen", request)


def test_equivalent_json_number_format_is_not_a_report_change(monkeypatch, report):
    public = json.loads(json.dumps(report), parse_float=lambda s: int(float(s)) if float(s).is_integer() else float(s))
    connect(monkeypatch, report, public)
    result = network.check(report["report_id"])
    assert result["ready"] and result["readback_matches"]
    assert result["expected_report_matches"]


def test_changed_public_content_is_rejected_even_with_same_id(monkeypatch, report):
    public = copy.deepcopy(report)
    public["limitations"].append("TEST SYNTHETYCZNY — zmieniona treść")
    connect(monkeypatch, report, public)
    result = network.check()
    assert not result["readback_matches"]
    assert not result["ready"]


def test_old_publication_cannot_confirm_requested_new_report(monkeypatch, report):
    connect(monkeypatch, report, report)
    result = network.check("rpt_" + "0" * 64)
    assert result["readback_matches"]
    assert not result["expected_report_matches"]
    assert not result["ready"]
