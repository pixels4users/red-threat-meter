from __future__ import annotations

import base64
import json
import os
import sqlite3
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..common import ROOT, canonical_json, instant, now, read_json
from .contract import validate_report
from ..analysis.commentary import verify_publication_record


class PublicationError(RuntimeError):
    """Fixed messages only; never expose HTTP bodies or credentials."""


def load_environment(path: Path | None = None) -> None:
    """Read a private KEY=value file as data. Never execute shell expressions."""
    path = path or ROOT / ".env.dashboard"
    if not path.exists():
        return
    allowed = {"SUPABASE_URL", "SUPABASE_SECRET_KEY"}
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if sep and key.strip() in allowed:
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class SupabasePublications:
    def __init__(self, url: str | None = None, key: str | None = None):
        config = read_json(ROOT / "config/dashboard.json")
        self.url = (url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.key = key or os.environ.get("SUPABASE_SECRET_KEY", "")
        if self.url != f"https://{config['supabase_project_ref']}.supabase.co":
            raise PublicationError("Supabase project URL is missing or differs from the configured project")
        if not self.key or not self.key.startswith(("sb_secret_", "eyJ")):
            raise PublicationError("Server-side Supabase write key is missing")
        if self.key.startswith("eyJ"):
            # Inspect the legacy key's declared role without logging the token.
            # The server still verifies its signature; this is a misconfiguration guard.
            try:
                encoded = self.key.split(".")[1]
                claims = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
                if claims.get("role") != "service_role":
                    raise ValueError()
            except (ValueError, IndexError, AttributeError):
                raise PublicationError("A server write key is required; anonymous keys are not accepted") from None

    def _request(self, path: str, payload: dict | None = None):
        headers = {"apikey": self.key, "Accept": "application/json"}
        if self.key.startswith("eyJ"):
            headers["Authorization"] = "Bearer " + self.key
        data = canonical_json(payload).encode() if payload is not None else None
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.url + "/rest/v1/" + path, data=data, headers=headers)
        try:
            with urlopen(request, timeout=20) as response:
                data = response.read(12_000_001)
                if len(data) > 12_000_000:
                    raise PublicationError("Publication response exceeds the size limit")
                return json.loads(data)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            code = exc.code if isinstance(exc, HTTPError) else "unavailable"
            raise PublicationError(f"Supabase operation failed ({code})") from None

    def publish(self, report: dict, *, commentary_record: dict | None = None) -> dict:
        validate_report(report)
        verify_publication_record(report, commentary_record)
        if report["mode"] != "live":
            raise PublicationError("Synthetic data cannot be published to live Supabase")
        return self._request("rpc/dashboard_publish", {"p_report": report})

    def latest(self, report_type="daily", before: str | None = None) -> dict | None:
        params = {"select": "payload,published_at", "report_type": "eq." + report_type,
                  "order": "as_of.desc,published_at.desc,report_id.desc", "limit": "1"}
        if before:
            instant(before)
            params["as_of"] = "lt." + before
        rows = self._request("dashboard_reports?" + urlencode(params))
        return self._checked(rows[0]) if rows else None

    @staticmethod
    def _checked(row):
        validate_report(row["payload"])
        return {"report": row["payload"], "published_at": row["published_at"]}

    def get(self, report_id: str) -> dict | None:
        rows = self._request("dashboard_reports?" + urlencode({"select": "payload,published_at", "report_id": "eq." + report_id, "limit": "1"}))
        return self._checked(rows[0]) if rows else None

    def history(self, report_type="daily", offset=0, anchor=None) -> dict:
        if anchor is None:
            # Use the database publication clock, including fractional seconds.
            # A local, second-rounded cutoff can hide the report just published.
            newest = self._request("dashboard_reports?select=published_at&order=published_at.desc&limit=1")
            if not newest:
                return {"items": [], "anchor": now(), "next_offset": None}
            anchor = newest[0]["published_at"]
        instant(anchor)
        params = {"select": "report_id,report_type,as_of,published_at,methodology_version,config_hash,source_config_hash,code_hash,score,supersedes",
                  "report_type": "eq." + report_type, "published_at": "lte." + anchor,
                  "order": "as_of.desc,published_at.desc,report_id.desc", "limit": "31", "offset": str(offset)}
        rows = self._request("dashboard_reports?" + urlencode(params))
        return {"items": rows[:30], "anchor": anchor, "next_offset": offset + 30 if len(rows) > 30 else None}


class LocalPublications:
    """Isolated release store for local end-to-end tests; never a cloud fallback."""
    def __init__(self, path: Path, mode="fixture"):
        self.path, self.mode = path, mode
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS metadata(mode TEXT NOT NULL)")
            row = db.execute("SELECT mode FROM metadata").fetchone()
            if row is None:
                db.execute("INSERT INTO metadata VALUES (?)", (mode,))
            elif row[0] != mode:
                raise PublicationError("Fixture and live publication stores must remain separate")
            db.execute("CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY, as_of TEXT NOT NULL, published_at TEXT NOT NULL, report_type TEXT NOT NULL, payload TEXT NOT NULL)")

    def connect(self):
        return sqlite3.connect(self.path)

    def publish(self, report: dict, *, commentary_record: dict | None = None) -> dict:
        validate_report(report)
        verify_publication_record(report, commentary_record)
        if report["mode"] != self.mode:
            raise PublicationError("Publication mode mismatch")
        value, stamp = canonical_json(report), now()
        with self.connect() as db:
            existing = db.execute("SELECT payload,published_at FROM reports WHERE id=?", (report["report_id"],)).fetchone()
            if existing:
                if existing[0] != value:
                    raise PublicationError("Report cannot be overwritten")
                return {"report_id": report["report_id"], "published_at": existing[1], "created": False}
            if report["supersedes"]:
                old = db.execute("SELECT payload FROM reports WHERE id=?", (report["supersedes"],)).fetchone()
                if not old or any(json.loads(old[0])[k] != report[k] for k in ("as_of", "report_type")):
                    raise PublicationError("Invalid correction reference")
            db.execute("INSERT INTO reports VALUES (?,?,?,?,?)", (report["report_id"], instant(report["as_of"]).isoformat(), stamp, report["report_type"], value))
        return {"report_id": report["report_id"], "published_at": stamp, "created": True}

    @staticmethod
    def _row(row):
        if not row:
            return None
        value = json.loads(row[0]); validate_report(value)
        return {"report": value, "published_at": row[1]}

    def latest(self, report_type="daily", before=None):
        query = "SELECT payload,published_at FROM reports WHERE report_type=?"
        args = [report_type]
        if before:
            query += " AND as_of < ?"; args.append(instant(before).isoformat())
        with self.connect() as db:
            return self._row(db.execute(query + " ORDER BY as_of DESC,published_at DESC,rowid DESC LIMIT 1", args).fetchone())

    def get(self, report_id):
        with self.connect() as db:
            return self._row(db.execute("SELECT payload,published_at FROM reports WHERE id=?", (report_id,)).fetchone())

    def history(self, report_type="daily", offset=0, anchor=None):
        anchor = anchor or now(); instant(anchor)
        with self.connect() as db:
            rows = db.execute("SELECT payload,published_at FROM reports WHERE report_type=? AND published_at<=? ORDER BY as_of DESC,published_at DESC,rowid DESC LIMIT 31 OFFSET ?", (report_type, anchor, offset)).fetchall()
        items = []
        for raw, stamp in rows[:30]:
            r = json.loads(raw)
            items.append({"report_id": r["report_id"], "report_type": r["report_type"], "as_of": r["as_of"],
                          "published_at": stamp, "methodology_version": r["provenance"]["methodology_version"],
                          "score": r["rtb"]["score"], "supersedes": r["supersedes"],
                          **{k:r["provenance"][k] for k in ("config_hash", "source_config_hash", "code_hash")}})
        return {"items": items, "anchor": anchor, "next_offset": offset + 30 if len(rows) > 30 else None}
