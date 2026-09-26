from __future__ import annotations

import importlib.util
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from .common import ROOT, UTC, atomic_write, canonical_url, clean_text, digest, instant, now

# Reuse the supplied skill's parser, never its unbounded URL discovery/fetch path.
_spec = importlib.util.spec_from_file_location("osint_rss_skill", ROOT / "skills/rss-feeds/scripts/feed.py")
_feed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_feed)


def parse_published(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    try:
        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", value):
            return datetime.strptime(value, "%d.%m.%Y").replace(tzinfo=ZoneInfo("Europe/Warsaw")).astimezone(UTC).isoformat()
        parsed = _feed.parse_date(value)
        return instant(parsed).isoformat() if parsed else None
    except (ValueError, TypeError, OverflowError):
        return None


def allowed_url(url: str, source: dict) -> str:
    url = canonical_url(url)
    p = urlsplit(url)
    if p.hostname not in source["allowed_hosts"] or p.port not in (None, 80, 443):
        raise ValueError("URL outside source host allowlist")
    if not p.path.startswith(source["path_prefix"]):
        raise ValueError("URL outside configured source path")
    return url


class RestrictedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, source: dict):
        self.source = source

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed_url(newurl, self.source)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Fetcher:
    def __init__(self, data_dir: Path, source: dict, timeout: float = 15):
        self.data_dir, self.source, self.timeout = data_dir, source, timeout
        self.opener = urllib.request.build_opener(RestrictedRedirect(source))
        self.raw_refs: list[str] = []
        self.last_request = 0.0

    def get(self, url: str) -> tuple[bytes, str, str, str]:
        url = allowed_url(url, self.source)
        for attempt in range(2):
            pause = max(0, 0.3 - (time.monotonic() - self.last_request))
            if pause:
                time.sleep(pause)
            self.last_request = time.monotonic()
            try:
                request = urllib.request.Request(url, headers={
                    "User-Agent": "OSINT-Dashboard/0.1 (local research pilot)",
                    "Accept": "application/rss+xml, application/atom+xml, text/html, application/json;q=0.8",
                })
                with self.opener.open(request, timeout=self.timeout) as response:
                    final = allowed_url(response.url, self.source)
                    body = response.read(3_000_001)
                    if len(body) > 3_000_000:
                        raise ValueError("Source response exceeds 3 MB limit")
                    content_type = response.headers.get("Content-Type", "")
                raw_ref = f"raw/{self.source['id']}/{digest(body)}.bin"
                if not (self.data_dir / raw_ref).exists():
                    atomic_write(self.data_dir / raw_ref, body)
                self.raw_refs.append(raw_ref)
                return body, content_type, final, raw_ref
            except urllib.error.HTTPError as exc:
                if attempt == 0 and (exc.code == 429 or exc.code >= 500):
                    time.sleep(1)
                    continue
                raise
            except (urllib.error.URLError, TimeoutError):
                if attempt == 0:
                    time.sleep(1)
                    continue
                raise
        raise RuntimeError("Fetch attempts exhausted")


def parse_listing(body: bytes, url: str) -> tuple[list[dict], str | None]:
    soup = BeautifulSoup(body, "html.parser")
    entries = []
    for item in soup.select("main .art-prev > ul > li"):
        title = item.select_one(".title a[href]")
        if title is None:
            continue
        date = item.select_one(".date")
        intro = item.select_one(".intro")
        entries.append({"url": urljoin(url, title["href"]), "title": title.get_text(" ", strip=True),
                        "published_at": parse_published(date.get_text(strip=True) if date else None),
                        "text": intro.get_text(" ", strip=True) if intro else "", "text_kind": "listing_summary"})
    next_page = soup.select_one("a#js-pagination-page-next[href]")
    return entries, urljoin(url, next_page["href"]) if next_page else None


def parse_article(body: bytes) -> str:
    soup = BeautifulSoup(body, "html.parser")
    content = soup.select_one("article .editor-content")
    if content is None:
        raise ValueError("Article body selector missing")
    for el in content.select("script,style,nav,form"):
        el.decompose()
    lead = soup.select_one("article > .intro") or soup.select_one("article .intro")
    text = ((lead.get_text(" ", strip=True) + " ") if lead else "") + content.get_text(" ", strip=True)
    if len(text) < 30:
        raise ValueError("Article body unexpectedly empty")
    return clean_text(text)


def collect_source(source: dict, data_dir: Path, window_start: datetime, fetcher=None) -> dict:
    fetcher = fetcher or Fetcher(data_dir, source)
    outcome = {"source_id": source["id"], "publisher": source["publisher"], "required": source["required"],
               "status": "error", "checked_at": now(), "items": [], "errors": [], "window_complete": False,
               "scope": "configured_publications_only", "raw_refs": [], "source_definition_hash": digest(source)}
    items, seen = [], set()
    try:
        url = source["url"]
        for page in range(source["max_pages"]):
            body, content_type, final, raw_ref = fetcher.get(url)
            if source["adapter"] == "rss":
                feed = _feed.parse_feed(body, content_type)
                entries = [{"url": e.get("link"), "title": e.get("title", ""),
                            "published_at": parse_published(e.get("published")),
                            "text": e.get("summary", ""), "text_kind": "feed_summary"}
                           for e in feed["entries"]]
                next_page = None
            elif source["adapter"] == "govpl":
                entries, next_page = parse_listing(body, final)
            else:
                raise ValueError("Unknown source adapter")
            if not entries:
                raise ValueError("No entries found; empty feed or changed page structure")
            reached_boundary = False
            for item in entries:
                if not item["url"]:
                    outcome["errors"].append("Entry without URL")
                    continue
                try:
                    item["url"] = allowed_url(item["url"], source)
                except ValueError:
                    outcome["errors"].append("Entry outside configured source URL scope")
                    continue
                if item["url"] in seen:
                    continue
                seen.add(item["url"])
                item["raw_ref"] = raw_ref
                if item["published_at"] and instant(item["published_at"]) < window_start:
                    reached_boundary = True
                if item["published_at"] is None:
                    outcome["errors"].append("Invalid or missing publication date: " + item["url"])
                elif instant(item["published_at"]) > instant(now()) + timedelta(minutes=5):
                    outcome["errors"].append("Publication date lies in the future: " + item["url"])
                # Retain a small overlap, including older entries, to detect corrections.
                if source["fetch_articles"]:
                    try:
                        article, _, _, article_ref = fetcher.get(item["url"])
                        item["text"] = parse_article(article)
                        item["text_kind"] = "article_body"
                        item["raw_ref"] = article_ref
                    except Exception as exc:
                        outcome["errors"].append(f"Article unavailable ({type(exc).__name__}): {item['url']}")
                items.append(item)
                if len(items) >= source["max_items"]:
                    break
            if reached_boundary:
                outcome["window_complete"] = True
            if reached_boundary or not next_page or len(items) >= source["max_items"]:
                break
            url = next_page
        outcome["status"] = "partial" if outcome["errors"] else "ok"
    except Exception as exc:
        outcome["errors"].append(f"{type(exc).__name__}: {str(exc)[:300]}")
        outcome["status"] = "partial" if items else "error"
    outcome["items"] = items
    outcome["raw_refs"] = list(dict.fromkeys(fetcher.raw_refs))
    outcome["checked_at"] = now()
    return outcome
