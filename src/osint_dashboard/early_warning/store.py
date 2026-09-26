from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..common import ROOT, canonical_json, digest, instant, now
from .contracts import validate, validate_observation


def check_raw(data_dir: Path, refs: list[str]) -> None:
    for ref in refs:
        path = data_dir / ref
        if not path.resolve().is_relative_to((data_dir / "raw").resolve()):
            raise ValueError("Raw evidence path outside archive")
        if not path.is_file() or path.suffix != ".bin" or digest(path.read_bytes()) != path.stem:
            raise ValueError(f"Missing or changed raw evidence: {ref}")


class Store:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        path = data_dir / "database/observations.sqlite3"
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1, 2):
            raise ValueError("Unsupported observation database version")
        if version == 0:
            self.db.executescript((ROOT / "migrations/early-warning/001_initial.sql").read_text())
            version = 1
        if version == 1:
            self.db.executescript((ROOT / "migrations/early-warning/002_translations.sql").read_text())
        for table in ("observations", "fetches", "source_checks", "reviews", "releases", "translations"):
            for action in ("UPDATE", "DELETE"):
                self.db.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_no_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'Append-only audit table'); END")
        self.db.commit()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.db.close()

    def add(self, obs: dict, run_id: str) -> bool:
        validate_observation(obs)
        check_raw(self.data_dir, obs["raw_refs"])
        added = self.db.execute("INSERT OR IGNORE INTO observations VALUES (?,?,?)",
                                (obs["observation_id"], obs["logical_key"], canonical_json(obs))).rowcount == 1
        self.db.execute("INSERT INTO fetches (observation_id,fetched_at,run_id,raw_refs) VALUES (?,?,?,?)",
                        (obs["observation_id"], obs["times"]["fetched_at"], run_id, canonical_json(obs["raw_refs"])))
        return added

    def observation(self, oid):
        row = self.db.execute("SELECT payload FROM observations WHERE observation_id=?", (oid,)).fetchone()
        if not row:
            raise ValueError("Unknown observation")
        return json.loads(row[0])

    def latest(self, as_of: str) -> list[dict]:
        as_of = instant(as_of).isoformat()
        rows = self.db.execute("""
            WITH ranked AS (
                SELECT o.payload, f.fetched_at, f.raw_refs,
                       ROW_NUMBER() OVER (PARTITION BY o.logical_key ORDER BY f.fetched_at DESC, f.seq DESC) AS n
                FROM observations o JOIN fetches f USING (observation_id) WHERE f.fetched_at <= ?
            ) SELECT payload,fetched_at,raw_refs FROM ranked WHERE n=1 ORDER BY json_extract(payload,'$.logical_key')
        """, (as_of,))
        return [{"observation": json.loads(r[0]), "last_fetched_at": r[1], "last_raw_refs": json.loads(r[2])} for r in rows]

    def add_check(self, run_id, check):
        check_raw(self.data_dir, check["raw_refs"])
        self.db.execute("INSERT INTO source_checks (run_id,source_id,checked_at,payload) VALUES (?,?,?,?)",
                        (run_id, check["source_id"], check["checked_at"], canonical_json(check)))

    def checks(self, as_of):
        as_of = instant(as_of).isoformat()
        rows = self.db.execute("""
            WITH ranked AS (
                SELECT payload, ROW_NUMBER() OVER (PARTITION BY source_id ORDER BY checked_at DESC,seq DESC) AS n
                FROM source_checks WHERE checked_at <= ?
            ) SELECT payload FROM ranked WHERE n=1 ORDER BY json_extract(payload,'$.source_id')
        """, (as_of,))
        return [json.loads(r[0]) for r in rows]

    def reviews(self, as_of):
        as_of = instant(as_of).isoformat()
        rows = self.db.execute("""
            WITH ranked AS (
                SELECT payload, ROW_NUMBER() OVER (PARTITION BY observation_id ORDER BY revision DESC) AS n
                FROM reviews WHERE created_at <= ?
            ) SELECT payload FROM ranked WHERE n=1
        """, (as_of,))
        return {p["observation_id"]: p for p in (json.loads(r[0]) for r in rows)}

    def translations(self, as_of):
        as_of = instant(as_of).isoformat()
        rows = self.db.execute("""
            WITH ranked AS (
                SELECT payload, ROW_NUMBER() OVER (PARTITION BY observation_id ORDER BY revision DESC) AS n
                FROM translations WHERE created_at <= ?
            ) SELECT payload FROM ranked WHERE n=1
        """, (as_of,))
        return {p["observation_id"]: p for p in (json.loads(r[0]) for r in rows)}

    def counts(self):
        return {name: self.db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                for name in ("observations", "fetches", "source_checks", "reviews", "translations", "releases")}

    def doctor(self):
        from .translations import validate_translation
        integrity = self.db.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok" or self.db.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Observation database integrity check failed")
        for row in self.db.execute("SELECT payload FROM observations"):
            validate_observation(json.loads(row[0]))
        for row in self.db.execute("SELECT payload FROM translations"):
            translation = json.loads(row[0])
            validate_translation(translation, self.observation(translation["observation_id"]))
        refs = set()
        for row in self.db.execute("SELECT raw_refs FROM fetches"):
            refs.update(json.loads(row[0]))
        for row in self.db.execute("SELECT payload FROM source_checks"):
            refs.update(json.loads(row[0])["raw_refs"])
        check_raw(self.data_dir, sorted(refs))
        return {"integrity": integrity, "raw_files_checked": len(refs), "counts": self.counts()}


def import_reviews(store: Store, batch: dict) -> dict:
    validate("review", batch)
    created_at = now()
    latest = {r["observation"]["observation_id"] for r in store.latest(created_at)}
    previous = store.reviews(created_at)
    seen = set()
    with store.db:
        for decision in batch["decisions"]:
            oid = decision["observation_id"]
            if oid in seen or oid not in latest:
                raise ValueError("Duplicate decision or superseded observation version")
            seen.add(oid)
            revision = previous.get(oid, {}).get("revision", 0)
            if decision["previous_revision"] != revision:
                raise ValueError("Review revision conflict")
            obs = store.observation(oid)
            check_raw(store.data_dir, obs["raw_refs"])
            data = obs["data"]
            for evidence in decision["evidence"]:
                if evidence["kind"] == "quote":
                    if data["type"] != "publication" or evidence["quote"] not in data["text"]:
                        raise ValueError("Quote absent from this publication version")
                else:
                    cells = {c["h3"]: c for c in data.get("cells", [])}
                    cell = cells.get(evidence["cell"])
                    if data["type"] != "gnss_daily" or not cell or cell[evidence["field"]] != evidence["value"]:
                        raise ValueError("Measurement differs from this daily grid")
            attribution = decision["attribution"]
            if (attribution["status"] == "unknown") != (attribution["actor"] is None):
                raise ValueError("Unknown attribution requires actor=null")
            record = {**decision, "revision": revision + 1, "created_at": created_at, "reviewer": batch["reviewer"]}
            record["review_id"] = "ewr_" + digest(record)[:24]
            store.db.execute("INSERT INTO reviews VALUES (?,?,?,?,?)",
                             (record["review_id"], oid, revision + 1, created_at, canonical_json(record)))
    return {"imported": len(seen), "reviewer": batch["reviewer"], "rtb_effect": "none"}
