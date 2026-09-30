import json
import shutil
import urllib.error
from datetime import datetime
from types import SimpleNamespace

import pytest
from jsonschema import ValidationError

from osint_dashboard import collect, osw
from osint_dashboard.common import UTC, load_config, now, write_json
from osint_dashboard.extract import extract_candidates, make_candidate
from osint_dashboard.review import import_review


HOST = "https://www.osw.waw.pl"
TEXT = "TEST SYNTHETYCZNY. Treść pełnego artykułu o współpracy i planach obronnych. " * 6
HTML = ('<div class="field--name-body">Menu</div><article class="publikacje">'
        '<div class="field--name-body"><p>' + TEXT + '</p><p>Sprostowanie: ćwiczenia odwołano.</p>'
        '<script>DO NOT EXECUTE</script></div></article>').encode()
START = datetime(2026, 9, 23, tzinfo=UTC)


@pytest.fixture
def osw_source(source_config):
    return next(s for s in source_config["sources"] if s["id"] == "osw")


class FakeFetcher:
    def __init__(self, rows, pages=None):
        self.rows, self.pages = rows, pages or {}
        self.calls, self.raw_refs = [], []

    def get(self, url):
        self.calls.append(url)
        raw = f"raw/osw/{len(self.calls)}.bin"
        self.raw_refs.append(raw)
        if url.endswith("rss.xml"):
            entries = [{"id": row[0], "url": HOST + row[0], "title": "TEST SYNTHETYCZNY", "date_published": row[1], "content_text": "Skrót"} for row in self.rows]
            return json.dumps({"version": "https://jsonfeed.org/version/1.1", "title": "Test", "items": entries}).encode(), "application/feed+json", url, raw
        value = self.pages.get(url, HTML)
        if isinstance(value, Exception):
            raise value
        return value, "text/html", url, raw


def test_article_keeps_body_correction_and_omits_surrounding_page():
    text = osw.article_text(HTML)
    assert "Sprostowanie: ćwiczenia odwołano." in text
    assert "Menu" not in text and "DO NOT EXECUTE" not in text
    with pytest.raises(ValueError):
        osw.article_text(b'<div class="field--name-body">Wrong section</div>')
    with pytest.raises(ValueError):
        osw.article_text('<article class="publikacje"><div class="field--name-body">Spis treści '.encode() + b'x' * 300 + b'</div></article>')


def test_pending_articles_outside_feed_are_fetched_once(osw_source, tmp_path):
    current, old = HOST + "/pl/current", HOST + "/pl/old"
    fetcher = FakeFetcher([("/pl/current", "2026-09-29T12:00:00Z")])
    backlog = [{"url": url, "title": "Stored title", "published_at": "2026-09-15T12:00:00+00:00", "material_id": "mat_old"} for url in (current, old)]
    result = collect.collect_source(osw_source, tmp_path, START, fetcher, backlog=backlog)
    assert result["status"] == "ok" and len(result["items"]) == 2
    assert fetcher.calls.count(current) == fetcher.calls.count(old) == 1
    assert result["backfill_count"] == 1
    assert result["items"][1]["published_at"] == backlog[1]["published_at"]
    assert result["items"][1]["discovery_material_id"] == "mat_old"
    assert not result["window_complete"]  # Old backlog does not prove RSS coverage.


def test_new_failed_article_stays_pending_but_full_version_is_never_downgraded(osw_source, tmp_path):
    url = HOST + "/pl/current"
    def fetcher():
        return FakeFetcher([("/pl/current", "2026-09-29T12:00:00Z")], {url: TimeoutError("Test")})
    result = collect.collect_source(osw_source, tmp_path, START, fetcher())
    assert result["status"] == "partial" and result["items"][0]["text_kind"] == "feed_summary"
    result = collect.collect_source(osw_source, tmp_path, START, fetcher(), known_full_urls={url})
    assert result["status"] == "error" and result["items"] == []
    assert result["errors"]


def test_backlog_and_total_limits_are_visible(osw_source, tmp_path):
    backlog = [{"url": HOST + f"/pl/old-{i}", "title": "Stored", "published_at": "2026-09-15T12:00:00Z", "material_id": "mat_old"} for i in range(3)]
    fetcher = FakeFetcher([("/pl/current", "2026-09-22T12:00:00Z")])
    result = collect.collect_source({**osw_source, "max_backfill_items": 2, "max_items": 2}, tmp_path, START, fetcher, backlog=backlog)
    assert result["status"] == "partial" and len(result["items"]) == 2
    assert len(fetcher.calls) == 3 and not result["window_complete"]
    assert len(result["errors"]) == 2


def test_pdf_uses_publisher_link_and_keeps_original_document_identity(osw_source, monkeypatch):
    url = HOST + "/pl/publikacje/raport-osw/2026-09-18/test"
    report = HOST + "/sites/default/files/report.pdf"
    class Fetcher:
        def get(self, target):
            if target == url:
                return f'<a href="{report}">Raport PDF</a>'.encode(), "text/html", HOST + "/transformacja-bundeswehry/", "raw/landing.bin"
            assert target == report
            return b"%PDF-TEST", "application/pdf", report, "raw/report.bin"
    monkeypatch.setattr(osw, "pdf_text", lambda body: (TEXT, {"method": "test", "pages": 2, "text_only": True}))
    result = osw.full_article({"url": url, "published_at": "2026-09-18T12:00:00Z"}, osw_source, Fetcher())
    assert result["url"] == url and result["text_kind"] == "pdf_text"
    assert result["raw_ref"] == "raw/report.bin"
    assert len(result["content_provenance"]["responses"]) == 2
    for body in (b'<a href="https://evil.example/report.pdf">Raport PDF</a>', b'<p>Interactive summary without report</p>'):
        with pytest.raises(ValueError):
            osw.report_link(body, url, osw_source)
    with pytest.raises(ValueError):
        collect.allowed_url(HOST + "/pl/%2e%2e/admin", osw_source)
    with pytest.raises(ValueError):
        collect.allowed_url(HOST + "/arbitrary-microsite/", osw_source)


def test_full_text_versions_require_review_and_repeated_fetch_is_idempotent(osw_source, store):
    item = {"url": HOST + "/pl/test", "title": "TEST SYNTHETYCZNY", "published_at": now(), "text": "Skrót", "text_kind": "feed_summary"}
    with store.db:
        summary, _ = store.add_material(osw_source, item, "raw/rss", now())
    first = extract_candidates(store, [summary])[0]
    import_review(store, {"schema_version": "1", "reviewer": {"type": "agent", "name": "Test"}, "decisions": [{"kind": "exclude", "candidate_ids": [first["candidate_id"]], "reason": "Syntetyczny kontekst do sprawdzenia historii wersji."}]})
    with store.db:
        full, added = store.add_material(osw_source, {**item, "text": TEXT, "text_kind": "pdf_text"}, "raw/pdf", now())
        again, repeated = store.add_material(osw_source, {**item, "text": TEXT, "text_kind": "pdf_text"}, "raw/pdf", now())
    second = extract_candidates(store, [full])[0]
    assert added and not repeated and again["material_id"] == full["material_id"]
    assert summary["document_id"] == full["document_id"] and summary["material_id"] != full["material_id"]
    assert "summary_only" not in second["flags"]
    assert first["candidate_id"] in store.resolutions(now()) and second["candidate_id"] not in store.resolutions(now())
    assert osw.pending_backlog([full], store.resolutions(now()), "osw") == [full]
    assert store.material(summary["material_id"])["text"] == "Skrót"


def test_retry_after_stops_requests_and_survives_new_fetcher(osw_source, tmp_path):
    fetcher = collect.Fetcher(tmp_path, osw_source)
    calls = []
    def blocked(*args, **kwargs):
        calls.append(1)
        raise urllib.error.HTTPError(osw_source["url"], 429, "Rate limited", {"Retry-After": "900"}, None)
    fetcher.opener = SimpleNamespace(open=blocked)
    with pytest.raises(urllib.error.HTTPError):
        fetcher.get(osw_source["url"])
    fresh = collect.Fetcher(tmp_path, osw_source)
    fresh.opener = SimpleNamespace(open=blocked)
    with pytest.raises(RuntimeError, match="cooldown"):
        fresh.get(osw_source["url"])
    assert len(calls) == 1 and fresh.request_count == 0


def test_redirects_count_towards_request_limit_and_cannot_escape(osw_source, tmp_path, monkeypatch):
    monkeypatch.setattr(collect.time, "sleep", lambda _: None)
    fetcher = collect.Fetcher(tmp_path, {**osw_source, "max_requests": 2})
    fetcher.before_request()
    handler = collect.RestrictedRedirect(osw_source, fetcher.before_request)
    req = collect.urllib.request.Request(HOST + "/pl/test")
    handler.redirect_request(req, None, 302, "", {}, HOST + "/transformacja-bundeswehry/")
    with pytest.raises(RuntimeError, match="budget"):
        handler.redirect_request(req, None, 302, "", {}, HOST + "/pl/other")
    with pytest.raises(ValueError):
        handler.redirect_request(req, None, 302, "", {}, "https://evil.example/pl/test")
    assert fetcher.request_count == 2


def test_source_config_rejects_unbounded_osw_requests(osw_source, tmp_path):
    path = tmp_path / "sources.json"
    write_json(path, {"version": "test", "sources": [{**osw_source, "max_requests": 100}]})
    with pytest.raises(ValidationError):
        load_config(path)


def synthetic_pdf():
    # A small self-contained text PDF; never written to live data.
    text = "SYNTHETIC OSW TEST. This is a test document without real-world claims."
    stream = ("BT /F1 10 Tf 10 270 Td 14 TL " + " ".join(f"({text}) Tj T*" for _ in range(15)) + " ET").encode()
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 2000 300] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"]
    body, offsets = b"%PDF-1.4\n", [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(body)); body += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(body)
    body += b"xref\n0 6\n0000000000 65535 f \n" + b"".join(f"{n:010d} 00000 n \n".encode() for n in offsets[1:])
    return body + f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


@pytest.mark.skipif(not shutil.which("pdftotext"), reason="Poppler unavailable")
def test_actual_pdf_extraction_and_corrupt_pdf():
    text, meta = osw.pdf_text(synthetic_pdf())
    assert text.startswith("SYNTHETIC OSW TEST") and meta["pages"] == 1
    assert meta["text_only"] is True
    with pytest.raises(ValueError, match="not a PDF"):
        osw.pdf_text(b"<html>Service unavailable</html>")
