"""Check local cycle writes without networking, credentials or changing live records."""
from __future__ import annotations

import fcntl
import json
import os
import sqlite3
import tempfile
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Probe every existing output directory: a writable data/ parent does not
# guarantee writable database/, snapshots/ or the collector's own directories.
OUTPUT_DIRS = (
    "", "database", "backups", "analysis", "analysis/code", "analysis/cycles",
    "raw", "runs", "snapshots", "reviews", "dashboard", "x-api", "social",
    "early_warning", "early_warning/database", "early_warning/raw",
    "early_warning/runs", "early_warning/snapshots",
)


def probe_directory(directory: Path) -> None:
    # Temporary files stay separate from the live database and are removed.
    with tempfile.TemporaryDirectory(prefix=".rta-access-check-", dir=directory) as temp:
        folder = Path(temp)
        first, final = folder / "pending", folder / "finished"
        with first.open("xb") as handle:
            handle.write(b"rta-access-check")
            handle.flush()
            os.fsync(handle.fileno())
        first.replace(final)
        if final.read_bytes() != b"rta-access-check":
            raise OSError("temporary_file_readback_failed")
        final.unlink()


def probe_sqlite(directory: Path) -> None:
    with tempfile.TemporaryDirectory(prefix=".rta-access-check-", dir=directory) as temp:
        db = sqlite3.connect(Path(temp) / "probe.sqlite3")
        try:
            if db.execute("PRAGMA journal_mode=WAL").fetchone()[0] != "wal":
                raise OSError("temporary_wal_unavailable")
            db.execute("CREATE TABLE probe (value INTEGER)")
            db.execute("INSERT INTO probe VALUES (1)")
            db.commit()
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise OSError("temporary_sqlite_integrity_failed")
        finally:
            db.close()


def check(root: Path = ROOT) -> dict:
    data = root / "data"
    result = {"checked_at": datetime.now(timezone.utc).isoformat(),
              "project_root": str(root), "ready": False, "checks": [],
              "network_requests": 0, "live_records_changed": False}
    step, target = "project_data", data
    try:
        if not data.is_dir():
            raise FileNotFoundError("project_data_missing")
        with ExitStack() as stack:
            # Same lock files and nonblocking flock as the production pipeline.
            # This detects an active operation; it is not a cycle-long reservation.
            for folder in (data, data / "early_warning"):
                if not folder.is_dir():
                    continue
                step, target = "pipeline_lock", folder / ".pipeline.lock"
                handle = stack.enter_context(target.open("a+"))
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                stack.callback(fcntl.flock, handle, fcntl.LOCK_UN)
                result["checks"].append({"check": step, "path": str(target), "status": "ok"})
            for suffix in OUTPUT_DIRS:
                target = data / suffix
                if not target.is_dir():
                    # A later mkdir is covered by the nearest existing ancestor.
                    continue
                step = "create_replace_read_delete"
                probe_directory(target)
                result["checks"].append({"check": step, "path": str(target), "status": "ok"})
            step, target = "sqlite_wal", data / "database"
            if not target.is_dir():
                target = data
            probe_sqlite(target)
            result["checks"].append({"check": step, "path": str(target), "status": "ok"})
        result["ready"] = True
    except (OSError, sqlite3.Error) as exc:
        result["error"] = {"check": step, "path": str(target),
                           "type": type(exc).__name__, "errno": getattr(exc, "errno", None)}
    return result


if __name__ == "__main__":
    result = check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ready"] else 1)
