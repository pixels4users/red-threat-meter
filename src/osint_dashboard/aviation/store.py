from __future__ import annotations

import json
import re
import sqlite3
from datetime import timedelta

from ..common import ROOT, canonical_json, digest, instant
from .contracts import validate_sample


def raw_bytes(folder, ref):
    if not re.fullmatch(r"raw/adsblol/[0-9a-f]{64}\.bin", ref):
        raise ValueError("Invalid aviation raw reference")
    path = folder / ref
    if not path.resolve().is_relative_to((folder / "raw").resolve()):
        raise ValueError("Raw evidence outside archive")
    body = path.read_bytes()
    if digest(body) != path.stem:
        raise ValueError("Raw evidence integrity failure")
    return body


class Store:
    def __init__(self, folder):
        self.folder = folder
        path = folder / "database/aviation.sqlite3"
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            self.db.executescript((ROOT / "migrations/aviation/001_initial.sql").read_text())
        elif version != 1:
            raise ValueError("Unsupported aviation database version")
        for table in ("samples", "releases"):
            for action in ("UPDATE", "DELETE"):
                self.db.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_no_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'Append-only audit table'); END")
        self.db.commit()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.db.close()

    def add(self, sample):
        validate_sample(sample)
        for r in sample["requests"]:
            if r["raw_ref"]:
                raw_bytes(self.folder, r["raw_ref"])
        with self.db:
            self.db.execute("INSERT INTO samples VALUES (?,?,?,?,?)", (sample["sample_id"], instant(sample["started_at"]).isoformat(timespec="microseconds"),
                            instant(sample["finished_at"]).isoformat(timespec="microseconds"), digest(sample["config"]), canonical_json(sample)))

    def samples(self, as_of, hours):
        end = instant(as_of)
        start = end - timedelta(hours=hours)
        rows = self.db.execute("SELECT payload FROM samples WHERE finished_at>=? AND finished_at<=? ORDER BY finished_at,sample_id",
                               (start.isoformat(timespec="microseconds"), end.isoformat(timespec="microseconds")))
        return [json.loads(r[0]) for r in rows]

    def last(self):
        row = self.db.execute("SELECT payload FROM samples ORDER BY finished_at DESC,sample_id DESC LIMIT 1").fetchone()
        return json.loads(row[0]) if row else None

    def counts(self):
        return {t: self.db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("samples", "releases")}

    def doctor(self):
        if self.db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Aviation database integrity failure")
        refs = set()
        for row in self.db.execute("SELECT payload FROM samples"):
            sample = json.loads(row[0])
            validate_sample(sample)
            refs.update(r["raw_ref"] for r in sample["requests"] if r["raw_ref"])
        for ref in refs:
            raw_bytes(self.folder, ref)
        return {"integrity": "ok", "raw_files_checked": len(refs), "counts": self.counts()}
