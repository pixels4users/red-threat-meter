"""Send a verified, already published daily report; never collect or publish data."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from osint_dashboard.common import ROOT
from osint_dashboard.dashboard.publication import load_environment


class NewsletterError(ValueError):
    """Fixed operational messages, safe for logs."""


def verified_report(folder: Path, today: str | None = None) -> dict:
    report_bytes = (folder / "publication-daily.json").read_bytes()
    report = json.loads(report_bytes)
    receipt = json.loads((folder / "published-daily.json").read_text())
    verification = json.loads((folder / "verification.json").read_text())
    report_id = report.get("report_id", "")
    cycle_id = report.get("provenance", {}).get("run_id")
    publication = verification.get("publication", {})
    public = verification.get("public_readback", {})
    replay = verification.get("replay", {})
    if not re.fullmatch(r"rpt_[a-f0-9]{64}", report_id) or report.get("mode") != "live" or report.get("report_type") != "daily":
        raise NewsletterError("ineligible_report")
    if receipt.get("report_id") != report_id or receipt.get("verified_readback") is not True:
        raise NewsletterError("publication_not_verified")
    if verification.get("report_id") != report_id or verification.get("cycle_id") != cycle_id:
        raise NewsletterError("verification_identity_mismatch")
    if publication.get("verified_readback") is not True or publication.get("export_sha256") != hashlib.sha256(report_bytes).hexdigest():
        raise NewsletterError("publication_receipt_mismatch")
    if public.get("report_id") != report_id or not all(public.get(k) is True for k in ("ready", "readback_matches", "expected_report_matches")):
        raise NewsletterError("public_readback_not_verified")
    if replay.get("run_id") != cycle_id or replay.get("identical") is not True:
        raise NewsletterError("replay_not_verified")
    today = today or datetime.now(ZoneInfo("Europe/Warsaw")).date().isoformat()
    if datetime.fromisoformat(report["as_of"]).astimezone(ZoneInfo("Europe/Warsaw")).date().isoformat() != today:
        raise NewsletterError("stale_report")
    return report


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--cycle", help="Exact verified cycle ID; no implicit latest report")
    operation.add_argument("--status", action="store_true", help="Read the private service status without sending or collecting")
    parser.add_argument("--send", action="store_true", help="Submit to the private newsletter service; default is offline verification only")
    args = parser.parse_args(argv)
    if args.status and args.send:
        parser.error("--send requires --cycle")
    try:
        if not args.status:
            if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.cycle):
                raise NewsletterError("invalid_cycle")
            report = verified_report(ROOT / "data/analysis/cycles" / args.cycle)
            if not args.send:
                print(json.dumps({"status": "verified_dry_run", "report_id": report["report_id"], "sent": False}))
                return 0
        load_environment()
        config = json.loads((ROOT / "config/dashboard.json").read_text())
        origin = f'https://{config["supabase_project_ref"]}.supabase.co'
        key = os.environ.get("SUPABASE_SECRET_KEY", "")
        if os.environ.get("SUPABASE_URL") != origin or not key.startswith(("sb_secret_", "eyJ")):
            raise NewsletterError("invalid_runtime")
        action = "status" if args.status else "dispatch"
        request = Request(origin + "/functions/v1/rta-newsletter/" + action, method="GET" if args.status else "POST",
                          data=None if args.status else json.dumps({"report_id": report["report_id"]}).encode(),
                          headers={"apikey": key, "Content-Type": "application/json", "User-Agent": "RedThreatAlert/1.0"})
        with build_opener(NoRedirect).open(request, timeout=60) as response:
            raw = response.read(16_385)
            if len(raw) > 16_384:
                raise NewsletterError("invalid_response")
            result = json.loads(raw)
        status = result.get("status")
        if args.status:
            if status not in ("enabled", "disabled"):
                raise NewsletterError("invalid_response")
            print(json.dumps({"status": status, "sent": False}))
            return 0
        if status == "already_handled" and result.get("delivery_status") != "sent":
            raise NewsletterError("delivery_needs_review")
        if status not in ("sent", "already_handled", "ineligible", "superseded", "disabled"):
            raise NewsletterError("delivery_needs_review")
        print(json.dumps({"status": status, "report_id": report["report_id"]}))
        return 0
    except Exception as exc:
        code = str(exc) if isinstance(exc, NewsletterError) else "newsletter_operation_failed"
        print(json.dumps({"error": code, "type": type(exc).__name__}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
