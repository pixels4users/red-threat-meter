"""Read-only connectivity and publication check; never calls the paid X API."""
from __future__ import annotations

import argparse
import json
import socket
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from jsonschema.exceptions import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from osint_dashboard.common import ROOT, now, read_json
from osint_dashboard.review import validate_schema
from osint_dashboard.dashboard.publication import (
    PublicationError, SupabasePublications, load_environment,
)


def check(expected_report_id: str | None = None) -> dict:
    config = read_json(ROOT / "config/dashboard.json")
    result = {"checked_at": now(), "dns": {}, "supabase": {}, "website": {},
              "paid_requests": 0, "ready": False}
    hosts = ("redthreatalert.pl", "gpsjam.org", config["supabase_project_ref"] + ".supabase.co")
    for host in hosts:
        try:
            socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
            result["dns"][host] = "ok"
        except OSError:
            result["dns"][host] = "dns_unavailable_in_this_execution"
    if any(value != "ok" for value in result["dns"].values()):
        return result

    try:
        load_environment()  # Existing private credentials; never printed.
        stored = SupabasePublications().latest("daily")
        result["supabase"] = {"status": "ok"}
    except PublicationError as exc:
        # PublicationError contains fixed, redacted messages only.
        result["supabase"] = {"status": "failed", "reason": str(exc)}
        return result
    except (OSError, ValueError, KeyError, TypeError, ValidationError):
        result["supabase"] = {"status": "failed", "reason": "stored_readback_unavailable_or_invalid"}
        return result

    request = Request("https://redthreatalert.pl/api/latest", headers={
        "User-Agent": "Mozilla/5.0 (compatible; RedThreatAlert/1.0; +https://redthreatalert.pl)",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
    })
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read(12_000_001)
            if len(raw) > 12_000_000:
                raise ValueError("response_too_large")
            public = json.loads(raw)
            if public is not None:
                # The website serializes JSON in JavaScript (0.0 becomes 0).
                # SupabasePublications validates the original content hash;
                # here require the schema and equality of the entire payload.
                validate_schema("dashboard/report", public["report"])
            result["website"] = {"status": "ok", "http_status": response.status}
    except HTTPError as exc:
        result["website"] = {"status": "failed", "http_status": exc.code}
        return result
    except (OSError, URLError, TimeoutError, ValueError, KeyError, TypeError, ValidationError):
        result["website"] = {"status": "failed", "reason": "public_readback_unavailable_or_invalid"}
        return result

    stored_report = stored["report"] if stored else None
    public_report = public["report"] if public else None
    matches = stored_report == public_report
    result["readback_matches"] = matches
    if stored_report:
        result["latest"] = {key: stored_report[key] for key in ("report_id", "as_of", "report_type")}
        result["latest"]["warsaw_date"] = datetime.fromisoformat(stored_report["as_of"]).astimezone(ZoneInfo("Europe/Warsaw")).date().isoformat()
    if expected_report_id:
        result["expected_report_matches"] = bool(stored_report and stored_report["report_id"] == expected_report_id)
    result["ready"] = matches and (not expected_report_id or result["expected_report_matches"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-report-id")
    args = parser.parse_args()
    result = check(args.expected_report_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ready"] else 1)
