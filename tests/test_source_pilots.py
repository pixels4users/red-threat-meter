import io
import urllib.error

import pytest

from osint_dashboard.common import digest, read_json, write_json
from osint_dashboard.source_pilots import collect, parse_capture, parse_rss, parse_warnings, settings

URL = settings()["sources"]["sjofartsverket"]["url"]
RSS_URL = settings()["sources"]["meduza"]["url"]
STAMP = "2026-10-03T10:58:56+00:00"


def warning_page(body="GNSS INTERFERENCE OBSERVED IN AREA.", areas=("Southern Baltic",)):
    sections = "".join(f'<div class="nav-area-div"><h5>{area}</h5><p>021100 UTC JUL<br>'
                       '<b>BALTIC SEA NAV WARN 026/25</b>'
                       f'<span>{body}</span></p></div>' for area in areas)
    return ('<b>Latest Update of Navigational Warnings: 2026-10-03 12:15</b>'
            f'<div id="warnings_by_area">{sections}</div>').encode()


def rss(date="Sat, 03 Oct 2026 09:00:00 +0000", link="https://meduza.io/en/news/one"):
    return (f'<rss><channel><item><title>Russia announces military exercises</title>'
            f'<link>{link}</link><pubDate>{date}</pubDate>'
            '<description>Exercises in Belarus. A report citing a ministry.</description>'
            '</item></channel></rss>').encode()


def capture(folder, raw, source="sjofartsverket"):
    folder.mkdir(parents=True, exist_ok=True)
    url = settings()["sources"][source]["url"]
    (folder / ("source.html" if source == "sjofartsverket" else "source.xml")).write_bytes(raw)
    write_json(folder / "fetch.json", {"requested_url": url, "final_url": url,
               "http_status": 200, "fetched_at": STAMP, "sha256": digest(raw), "bytes": len(raw)})


def test_repeated_areas_are_one_notice_without_invented_time():
    records, coverage = parse_warnings(warning_page(areas=("Western Baltic", "Southern Baltic", "Northern Baltic")), URL)
    assert len(records) == 1
    item = records[0]
    assert len(item["areas_original"]) == 3
    assert item["source_time_raw"] == "021100 UTC JUL"
    assert item["published_at"] is None and item["observed_at"] is None
    assert item["valid_until"] is None
    assert coverage["duplicate_area_rows"] == 2
    assert coverage["page_update_timezone"] is None
    assert coverage["absence_means_cancelled"] is False
    assert item["priority_hint"] == "context_review"


def test_same_notice_new_content_preserves_identity_and_changes_version():
    first, _ = parse_warnings(warning_page(), URL)
    changed, _ = parse_warnings(warning_page("INTERFERENCE CEASED."), URL)
    assert first[0]["record_id"] == changed[0]["record_id"]
    assert first[0]["content_sha256"] != changed[0]["content_sha256"]


def test_conflicting_copies_are_not_silently_merged():
    raw = warning_page(areas=("Western Baltic", "Southern Baltic"))
    raw = raw.replace(b"GNSS INTERFERENCE", b"NO INTERFERENCE", 1)
    with pytest.raises(ValueError, match="Conflicting"):
        parse_warnings(raw, URL)


@pytest.mark.parametrize("raw", [b"<html>maintenance</html>", b'<div id="warnings_by_area"><div class="nav-area-div"><h5>Baltic</h5><p>Changed layout</p></div></div>'])
def test_unrecognised_pages_are_not_zero(raw):
    with pytest.raises(ValueError):
        parse_warnings(raw, URL)


def test_explicit_empty_is_a_page_observation_not_full_history():
    records, coverage = parse_warnings(b'<div id="warnings_by_area"><div class="nav-area-div"><h5>The Sound</h5><p>No current warnings in the area</p></div></div>', URL)
    assert records == []
    assert coverage["history_complete"] is False
    assert coverage["explicit_empty_areas"] == ["The Sound"]


def test_rss_preserves_dates_and_does_not_claim_full_text_or_verified_origin():
    records, coverage = parse_rss(rss(), RSS_URL)
    assert records[0]["published_at"] == "2026-10-03T09:00:00+00:00"
    assert records[0]["origin_status"] == "not_established"
    assert records[0]["priority_hint"] == "context_review"
    assert records[0]["translation_status"] == "pending"
    assert coverage["full_articles"] is False
    assert coverage["history_complete"] is False


def test_rss_timezone_missing_is_not_filled_with_fetch_time():
    records, _ = parse_rss(rss(date="Sat, 03 Oct 2026 09:00:00"), RSS_URL)
    assert records[0]["published_at"] is None


@pytest.mark.parametrize("raw", [rss(link="https://other.example/item"), b'<!DOCTYPE rss [<!ENTITY x "text">]><rss/>'])
def test_rss_rejects_wrong_hosts_and_document_entities(raw):
    with pytest.raises(ValueError):
        parse_rss(raw, RSS_URL)


def test_capture_replay_is_identical_and_tampering_fails(tmp_path):
    capture(tmp_path, warning_page())
    original = parse_capture(tmp_path, "sjofartsverket")
    assert parse_capture(tmp_path, "sjofartsverket") == original
    assert original["runtime_enabled"] is False
    (tmp_path / "source.html").write_bytes(warning_page("Changed"))
    with pytest.raises(ValueError, match="integrity"):
        parse_capture(tmp_path, "sjofartsverket")


class Response(io.BytesIO):
    status = 200
    url = RSS_URL
    headers = {"Content-Type": "application/rss+xml"}


class Opener:
    def __init__(self, error=None, raw=None):
        self.calls = 0
        self.error = error
        self.raw = rss() if raw is None else raw

    def open(self, request, timeout):
        self.calls += 1
        if self.error:
            raise self.error
        return Response(self.raw)


def test_collect_once_saves_raw_and_second_call_does_no_network(tmp_path):
    opener = Opener()
    result = collect("meduza", tmp_path, opener=opener, stamp=STAMP)
    assert len(result["records"]) == 1
    with pytest.raises(ValueError, match="already attempted"):
        collect("meduza", tmp_path, opener=opener, stamp=STAMP)
    assert opener.calls == 1
    assert read_json(tmp_path / "meduza/attempts.json")[0]["status"] == "ok"


def test_failed_requests_consume_budget_and_persist_retry_after(tmp_path):
    opener = Opener(error=urllib.error.HTTPError(RSS_URL, 429, "limit", {"Retry-After": "172800"}, None))
    with pytest.raises(urllib.error.HTTPError):
        collect("meduza", tmp_path, opener=opener, stamp=STAMP)
    for stamp in [STAMP, "2026-10-04T10:58:56+00:00"]:
        with pytest.raises(ValueError):
            collect("meduza", tmp_path, opener=opener, stamp=stamp)
    assert opener.calls == 1
    attempt = read_json(tmp_path / "meduza/attempts.json")[0]
    assert attempt["status"] == "error" and attempt["http_status"] == 429


def test_manual_capture_counts_toward_budget(tmp_path):
    capture(tmp_path / "sjofartsverket/2026-10-03", warning_page())
    opener = Opener()
    with pytest.raises(ValueError, match="already attempted"):
        collect("sjofartsverket", tmp_path, opener=opener, stamp=STAMP)
    assert opener.calls == 0


def test_response_limit_is_not_retried(tmp_path):
    opener = Opener(raw=b"x" * 1_500_001)
    with pytest.raises(ValueError, match="byte limit"):
        collect("meduza", tmp_path, opener=opener, stamp=STAMP)
    assert opener.calls == 1
    assert not (tmp_path / "meduza/2026-10-03/source.xml").exists()


def test_redirect_is_rejected_without_following():
    from osint_dashboard.source_pilots import NoRedirect
    assert NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://other.example") is None


def test_retry_after_http_date_and_success_response_are_respected(tmp_path, monkeypatch):
    monkeypatch.setattr(Response, "headers", {"Retry-After": "Mon, 05 Oct 2026 12:00:00 GMT"})
    opener = Opener()
    collect("meduza", tmp_path, opener=opener, stamp=STAMP)
    with pytest.raises(ValueError, match="Retry-After"):
        collect("meduza", tmp_path, opener=opener, stamp="2026-10-04T10:58:56+00:00")
    assert opener.calls == 1
