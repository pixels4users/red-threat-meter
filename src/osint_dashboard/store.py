from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .common import ROOT, canonical_json, digest, now


class Store:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir.resolve()
        path = self.data_dir / "database/osint.sqlite3"
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=15)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.execute("PRAGMA journal_mode = WAL")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version > 1:
            raise ValueError("Database schema is newer than this application")
        if version == 0:
            sql = (ROOT / "migrations/001_initial.sql").read_text()
            triggers = ""
            for table in ("materials", "observations", "candidates", "incident_revisions", "resolutions", "snapshots", "source_checks"):
                for operation in ("UPDATE", "DELETE"):
                    triggers += (f"CREATE TRIGGER {table}_no_{operation.lower()} BEFORE {operation} ON {table} "
                                 "BEGIN SELECT RAISE(ABORT, 'Append-only audit history'); END;\n")
            self.db.executescript("BEGIN IMMEDIATE;\n" + sql + "\n" + triggers + "\nCOMMIT;")

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def add_material(self, source: dict, item: dict, raw_ref: str, fetched_at: str) -> tuple[dict, bool]:
        document_id = "doc_" + digest([source["id"], item["url"]])[:24]
        identity = {k: item.get(k) for k in ("url", "title", "published_at", "text", "text_kind")}
        if "source_record" in item:
            identity["source_record"] = item["source_record"]
        content_hash = digest(identity)
        material_id = "mat_" + digest([document_id, content_hash])[:24]
        existing = self.db.execute("SELECT payload FROM materials WHERE material_id=?", (material_id,)).fetchone()
        if existing:
            self.db.execute("INSERT OR IGNORE INTO observations VALUES (?,?,?)", (document_id, material_id, fetched_at))
            return json.loads(existing[0]), False
        payload = {**item, "material_id": material_id, "document_id": document_id,
                   "source_id": source["id"], "publisher": source["publisher"],
                   "source_kind": source["kind"], "content_hash": content_hash,
                   "fetched_at": fetched_at, "raw_ref": raw_ref}
        self.db.execute("INSERT INTO materials VALUES (?,?,?,?,?,?)",
                        (material_id, document_id, source["id"], content_hash, fetched_at, canonical_json(payload)))
        self.db.execute("INSERT OR IGNORE INTO observations VALUES (?,?,?)", (document_id, material_id, fetched_at))
        return payload, True

    def material(self, material_id: str) -> dict:
        row = self.db.execute("SELECT payload FROM materials WHERE material_id=?", (material_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown material: {material_id}")
        return json.loads(row[0])

    def latest_materials(self, as_of: str) -> list[dict]:
        rows = self.db.execute("""SELECT payload FROM (
            SELECT m.payload, ROW_NUMBER() OVER (PARTITION BY o.document_id ORDER BY o.observed_at DESC, o.rowid DESC) AS n
            FROM observations o JOIN materials m USING(material_id) WHERE o.observed_at <= ?) WHERE n=1""", (as_of,)).fetchall()
        return [json.loads(r[0]) for r in rows]

    def latest_incidents(self, as_of: str) -> list[dict]:
        rows = self.db.execute("""SELECT payload FROM (
            SELECT payload, ROW_NUMBER() OVER (PARTITION BY incident_id ORDER BY revision DESC) AS n
            FROM incident_revisions WHERE recorded_at <= ?) WHERE n=1""", (as_of,)).fetchall()
        return [json.loads(r[0]) for r in rows]

    def resolutions(self, as_of: str) -> dict[str, dict]:
        rows = self.db.execute("""SELECT candidate_id,payload FROM (
            SELECT candidate_id,payload, ROW_NUMBER() OVER
            (PARTITION BY candidate_id ORDER BY recorded_at DESC,rowid DESC) AS n
            FROM resolutions WHERE recorded_at <= ?) WHERE n=1""", (as_of,)).fetchall()
        return {r[0]: json.loads(r[1]) for r in rows}

    def start_run(self, run_id: str) -> None:
        with self.db:
            self.db.execute("INSERT INTO runs(run_id,started_at,status) VALUES (?,?,?)", (run_id, now(), "running"))

    def finish_run(self, run_id: str, status: str, error: str | None = None) -> None:
        with self.db:
            self.db.execute("UPDATE runs SET finished_at=?,status=?,error=? WHERE run_id=?", (now(), status, error, run_id))

    def counts(self) -> dict:
        return {name: self.db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                for name in ("materials", "candidates", "incident_revisions", "resolutions", "runs", "snapshots")}

    def backup(self, destination: Path) -> None:
        if destination.exists():
            raise ValueError("Backup destination already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(destination) as target:
            self.db.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Backup integrity check failed")
