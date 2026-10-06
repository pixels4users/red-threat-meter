import hashlib
import json

import pytest

from scripts.dispatch_newsletter import NewsletterError, verified_report


def cycle(tmp_path):
    report = {"report_id": "rpt_" + "a" * 64, "mode": "live", "report_type": "daily",
              "as_of": "2026-10-05T09:00:00+00:00", "provenance": {"run_id": "test-cycle"}}
    raw = json.dumps(report).encode()
    (tmp_path / "publication-daily.json").write_bytes(raw)
    (tmp_path / "published-daily.json").write_text(json.dumps({"report_id": report["report_id"], "verified_readback": True}))
    verification = {"report_id": report["report_id"], "cycle_id": "test-cycle",
                    "publication": {"verified_readback": True, "export_sha256": hashlib.sha256(raw).hexdigest()},
                    "public_readback": {"report_id": report["report_id"], "ready": True, "readback_matches": True, "expected_report_matches": True},
                    "replay": {"run_id": "test-cycle", "identical": True}}
    save = lambda: (tmp_path / "verification.json").write_text(json.dumps(verification))
    save()
    return report, verification, save


def test_newsletter_requires_verified_exact_publication(tmp_path):
    report, _, _ = cycle(tmp_path)
    assert verified_report(tmp_path, "2026-10-05") == report
    (tmp_path / "publication-daily.json").write_text(json.dumps({**report, "extra": "tampered"}))
    with pytest.raises(NewsletterError, match="publication_receipt_mismatch"):
        verified_report(tmp_path, "2026-10-05")


@pytest.mark.parametrize("gate,flag", [("replay", "identical"), ("public_readback", "readback_matches"), ("publication", "verified_readback")])
def test_newsletter_stops_after_incomplete_verification(tmp_path, gate, flag):
    _, verification, save = cycle(tmp_path)
    verification[gate][flag] = False
    save()
    with pytest.raises(NewsletterError):
        verified_report(tmp_path, "2026-10-05")


def test_newsletter_does_not_send_yesterdays_report(tmp_path):
    cycle(tmp_path)
    with pytest.raises(NewsletterError, match="stale_report"):
        verified_report(tmp_path, "2026-10-06")
