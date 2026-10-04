"""Preflight must fail before paid collection and preserve existing data."""
import fcntl
import importlib.util
from pathlib import Path

from osint_dashboard.common import ROOT

spec = importlib.util.spec_from_file_location("rta_project_access", ROOT / "scripts/check_project_access.py")
access = importlib.util.module_from_spec(spec)
spec.loader.exec_module(access)


def test_success_preserves_existing_files_and_cleans_probes(tmp_path):
    data = tmp_path / "data"
    (data / "database").mkdir(parents=True)
    (data / "early_warning").mkdir()
    sentinel = data / "database/sentinel"
    sentinel.write_bytes(b"existing-content")
    result = access.check(tmp_path)
    assert result["ready"]
    assert sentinel.read_bytes() == b"existing-content"
    assert not list(data.rglob(".rta-access-check-*"))
    assert result["network_requests"] == 0
    assert not result["live_records_changed"]


def test_permission_denial_is_not_reported_as_ready(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()

    def blocked(directory):
        raise PermissionError(1, "sandbox denies writes")

    monkeypatch.setattr(access, "probe_directory", blocked)
    result = access.check(tmp_path)
    assert not result["ready"]
    assert result["error"] == {"check": "create_replace_read_delete", "path": str(data),
                               "type": "PermissionError", "errno": 1}
    assert result["network_requests"] == 0


def test_busy_pipeline_is_not_touched(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    with (data / ".pipeline.lock").open("a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = access.check(tmp_path)
        assert not result["ready"]
        assert result["error"]["type"] == "BlockingIOError"
        assert result["error"]["check"] == "pipeline_lock"
    assert access.check(tmp_path)["ready"]


def test_wrong_project_does_not_create_a_new_data_directory(tmp_path):
    result = access.check(tmp_path)
    assert not result["ready"]
    assert result["error"]["type"] == "FileNotFoundError"
    assert not (tmp_path / "data").exists()
