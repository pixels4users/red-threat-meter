"""Bounded OSW full-text ingestion. RSS discovers URLs; it is never the article body."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup

from .collect import _feed, allowed_url, parse_published
from .common import clean_text, digest, instant, now
from .extract import make_candidate


def pending_backlog(materials, resolutions, source_id):
    """Only known, unresolved documents; no URL discovery or historical crawl."""
    return sorted((m for m in materials if m["source_id"] == source_id and
                   make_candidate(m)["candidate_id"] not in resolutions),
                  key=lambda m: (m.get("published_at") or "", m["url"]))


def article_text(body: bytes) -> str:
    soup = BeautifulSoup(body, "html.parser")
    content = soup.select_one("article.publikacje .field--name-body")
    if content is None:
        raise ValueError("OSW article body selector missing")
    for el in content.select("script,style,nav,form,iframe"):
        el.decompose()
    text = clean_text(content.get_text(" ", strip=True))
    if len(text) < 200 or text.casefold().startswith("spis treści"):
        raise ValueError("OSW article has only a teaser or table of contents")
    return text


def report_link(body: bytes, final_url: str, source: dict) -> str:
    soup = BeautifulSoup(body, "html.parser")
    links = set()
    for el in soup.select("article.publikacje .field--name-upload a[href], a[href]"):
        href = urljoin(final_url, el["href"])
        if urlsplit(href).path.lower().endswith(".pdf"):
            # A report link is deliberately narrower than all PDFs on the page.
            if el.find_parent(class_="field--name-upload") or "raport pdf" in el.get_text(" ", strip=True).casefold():
                links.add(allowed_url(href, source))
    if len(links) != 1:
        raise ValueError("OSW report needs one unambiguous publisher PDF")
    return links.pop()


def pdf_text(body: bytes) -> tuple[str, dict]:
    if not body.startswith(b"%PDF-"):
        raise ValueError("OSW report response is not a PDF")
    info, extractor = shutil.which("pdfinfo"), shutil.which("pdftotext")
    if not info or not extractor:
        raise RuntimeError("Poppler pdfinfo and pdftotext are required for OSW reports")
    with tempfile.TemporaryDirectory(prefix="rtb-osw-") as tmp:
        pdf, txt = Path(tmp) / "report.pdf", Path(tmp) / "report.txt"
        pdf.write_bytes(body)
        result = subprocess.run([info, str(pdf)], capture_output=True, timeout=15, check=True)
        match = re.search(rb"^Pages:\s+(\d+)", result.stdout, re.MULTILINE)
        pages = int(match[1]) if match else 0
        if not 1 <= pages <= 250:
            raise ValueError("OSW report page count missing or over 250")
        result = subprocess.run([extractor, "-layout", "-enc", "UTF-8", str(pdf), str(txt)],
                                capture_output=True, timeout=30, check=True)
        if result.stderr.strip():
            raise ValueError("PDF extraction warnings require manual inspection")
        if txt.stat().st_size > 1_000_000:
            raise ValueError("OSW extracted text exceeds 1 MB")
        extracted = txt.read_text(encoding="utf-8")
        if extracted.count("\f") != pages:
            raise ValueError("OSW PDF page extraction incomplete")
        text = clean_text(extracted)
        if len(text) < 500:
            raise ValueError("OSW PDF has insufficient readable text; OCR required")
        version = subprocess.run([extractor, "-v"], capture_output=True, timeout=5, check=True)
    return text, {"method": "pdftotext-layout-v1", "tool_version": version.stderr.decode().splitlines()[0],
                  "pages": pages, "text_only": True}


def full_article(item, source, fetcher):
    body, content_type, final, raw_ref = fetcher.get(item["url"])
    provenance = [{"url": final, "raw_ref": raw_ref, "content_type": content_type}]
    is_report = "/raport-osw/" in urlsplit(item["url"]).path
    if is_report:
        url = report_link(body, final, source)
        body, content_type, final, raw_ref = fetcher.get(url)
        provenance.append({"url": final, "raw_ref": raw_ref, "content_type": content_type})
        text, extraction = pdf_text(body)
        kind = "pdf_text"
    else:
        text, extraction, kind = article_text(body), {"method": "osw-drupal-body-v1"}, "article_body"
    return {**item, "text": text, "text_kind": kind, "raw_ref": raw_ref,
            "content_provenance": {"responses": provenance, "extraction": extraction}}


def archive_page(body, url, source):
    """The publisher's dated, descending listing, not dates inferred from URLs."""
    soup = BeautifulSoup(body, "html.parser")
    rows = soup.select(".view-content .views-row")
    if not rows:
        raise ValueError("OSW archive listing missing")
    entries = []
    for row in rows:
        link, stamp = row.select_one("h3 a[href]"), row.select_one("time[datetime]")
        if not link or not stamp:
            raise ValueError("OSW archive entry without title or timestamp")
        published = parse_published(stamp["datetime"])
        if not published or instant(published) > instant(now()) + timedelta(minutes=5):
            raise ValueError("OSW archive invalid or future publication date")
        entries.append({"url": allowed_url(urljoin(url, link["href"]), source),
                        "title": clean_text(link.get_text(" ", strip=True)),
                        "published_at": published, "text": "", "text_kind": "listing_summary"})
    dates = [instant(row["published_at"]) for row in entries]
    if dates != sorted(dates, reverse=True):
        raise ValueError("OSW archive publication order changed")
    next_link = soup.select_one('li.pager__item--next a[rel~="next"][href]')
    next_url = allowed_url(urljoin(url, next_link["href"]), source) if next_link else None
    if next_url:
        current, following = urlsplit(url), urlsplit(next_url)
        expected = int(parse_qs(current.query).get("page", ["0"])[0]) + 1
        if following.path != urlsplit(source["archive_url"]).path or parse_qs(following.query) != {"page": [str(expected)]}:
            raise ValueError("OSW archive pagination is not sequential")
    return entries, next_url


def collect_archive(source, window_start, fetcher, outcome):
    entries, url, previous_oldest = [], source["archive_url"], None
    outcome["archive_pages"] = 0
    # RSS alone is not a proof of a complete archive (or of event history).
    outcome["window_complete"] = False
    for _ in range(source["max_pages"]):
        body, _, final, raw_ref = fetcher.get(url)
        rows, next_url = archive_page(body, final, source)
        newest, oldest = instant(rows[0]["published_at"]), instant(rows[-1]["published_at"])
        if previous_oldest and newest > previous_oldest:
            raise ValueError("OSW archive changed while paginating; repeat in next cycle")
        previous_oldest = oldest
        outcome["archive_pages"] += 1
        entries.extend({**row, "discovery_raw_ref": raw_ref, "raw_ref": raw_ref} for row in rows)
        if oldest < window_start:
            outcome["window_complete"] = True
            outcome["archive_oldest_publication"] = rows[-1]["published_at"]
            return entries
        if not next_url:
            break
        url = next_url
    outcome["errors"].append("OSW archive did not reach requested publication window within page limit")
    return entries


def collect_osw(source, window_start, fetcher, backlog=(), known_full_urls=()):
    outcome = {"source_id": source["id"], "publisher": source["publisher"], "required": source["required"],
               "status": "error", "checked_at": now(), "items": [], "errors": [], "window_complete": False,
               "scope": "rss_full_articles_and_known_unresolved", "raw_refs": [],
               "source_definition_hash": digest(source), "backfill_count": 0}
    entries, seen = [], set()
    try:
        body, content_type, _, feed_ref = fetcher.get(source["url"])
        feed = _feed.parse_feed(body, content_type)
        if not feed["entries"]:
            raise ValueError("OSW feed empty or structure changed")
        for row in feed["entries"]:
            try:
                url = allowed_url(row.get("link") or "", source)
            except ValueError:
                outcome["errors"].append("OSW feed entry outside configured URL scope")
                continue
            if url in seen:
                continue
            seen.add(url)
            published = parse_published(row.get("published"))
            # Historical backlog must never stand in for current feed coverage.
            if published and instant(published) < window_start:
                outcome["window_complete"] = True
            entries.append({"url": url, "title": row.get("title", ""), "published_at": published,
                            "discovery_raw_ref": feed_ref, "raw_ref": feed_ref,
                            "text": row.get("summary", ""), "text_kind": "feed_summary"})
    except Exception as exc:
        outcome["errors"].append(f"OSW feed unavailable ({type(exc).__name__}): {str(exc)[:200]}")
    if source.get("archive_url"):
        outcome["scope"] = "publisher_archive_full_articles_and_known_unresolved"
        try:
            for item in collect_archive(source, window_start, fetcher, outcome):
                if item["url"] not in seen:
                    entries.append(item)
                    seen.add(item["url"])
        except Exception as exc:
            outcome["window_complete"] = False
            outcome["errors"].append(f"OSW archive unavailable ({type(exc).__name__}): {str(exc)[:200]}")
    missing = [m for m in backlog if m["url"] not in seen]
    limit = source["max_backfill_items"]
    if len(missing) > limit:
        outcome["errors"].append("OSW unresolved backlog exceeds configured limit")
    for old in missing[:limit]:
        if old["url"] in seen:
            continue
        seen.add(old["url"])
        entries.append({k: old[k] for k in ("url", "title", "published_at")} |
                       {"discovery_material_id": old["material_id"]})
        outcome["backfill_count"] += 1
    if len(entries) > source["max_items"]:
        outcome["errors"].append("OSW publication limit reached")
        outcome["window_complete"] = False
    for item in entries[:source["max_items"]]:
        try:
            item["url"] = allowed_url(item["url"], source)
            published = item["published_at"]
            if not published or instant(published) > instant(now()) + timedelta(minutes=5):
                outcome["errors"].append("OSW invalid or future publication date: " + item["url"])
            outcome["items"].append(full_article(item, source, fetcher))
        except Exception as exc:
            # Do not observe a teaser as the latest version of a previously full article.
            outcome["errors"].append(f"OSW full text unavailable ({type(exc).__name__}): {item['url']}; {str(exc)[:160]}")
            # Keep a new URL in the review queue even if it disappears from the next feed.
            if item["url"] not in known_full_urls and item.get("text_kind") in ("feed_summary", "listing_summary"):
                outcome["items"].append(item)
    outcome["raw_refs"] = list(dict.fromkeys(fetcher.raw_refs))
    outcome["checked_at"] = now()
    outcome["request_count"] = getattr(fetcher, "request_count", None)
    outcome["retry_at"] = getattr(fetcher, "retry_at", None)
    outcome["status"] = ("partial" if outcome["items"] else "error") if outcome["errors"] else "ok"
    return outcome
