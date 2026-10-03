"""Small, manual source trials. No database, scoring, publication or secret access."""
from __future__ import annotations

import fcntl
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from jsonschema import Draft202012Validator, FormatChecker

from .collect import _feed
from .common import ROOT, UTC, atomic_write, canonical_url, clean_text, digest, instant, now, read_json, write_json

PILOT_ROOT = ROOT / "data/source_pilots"
PARSER_VERSION = "source-pilot-parser-1"


def settings() -> dict:
    result = read_json(ROOT / "config/source-pilots.json")
    # These are upper bounds, not a general-purpose crawler configuration.
    if result["max_requests_per_source_per_day"] != 1:
        raise ValueError("Pilot supports one request per source per day")
    if not 1 <= result["max_response_bytes"] <= 1_500_000:
        raise ValueError("Invalid response limit")
    if not 1 <= result["timeout_seconds"] <= 25:
        raise ValueError("Invalid timeout")
    return result


def _once(path: Path, value: dict) -> None:
    if path.exists():
        if read_json(path) != value:
            raise ValueError("Existing pilot record differs; preserve the original")
    else:
        write_json(path, value)


@contextmanager
def _lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".pilot.lock").open("a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _date(stamp: str) -> str:
    return instant(stamp).astimezone(ZoneInfo("Europe/Warsaw")).date().isoformat()


def _retry_at(stamp: str, value: str | None) -> str:
    target = instant(stamp) + timedelta(minutes=5)
    try:
        requested = (instant(stamp) + timedelta(seconds=int(value)) if str(value).isdigit()
                     else parsedate_to_datetime(value))
        target = max(target, requested)
    except (ValueError, TypeError, OverflowError):
        pass
    return target.isoformat()


def _record(source_id: str, identity: str, title: str, body: str, url: str,
            time_raw: str | None, published_at: str | None, areas: list[str]) -> dict:
    return {
        "record_id": f"{source_id}:{identity}", "title_original": title,
        "content_original": body, "url": url, "source_time_raw": time_raw,
        "published_at": published_at, "observed_at": None,
        "valid_from": None, "valid_until": None,
        "validity_note": "Obowiązywanie i odwołania wymagają przeglądu treści.",
        "areas_original": areas,
        "content_sha256": digest({"title": title, "body": body, "time": time_raw}),
        "translation_status": "pending", "review_status": "not_reviewed",
        "origin_status": "not_established", "priority_hint": "scope_review",
    }


def parse_warnings(raw: bytes, url: str) -> tuple[list[dict], dict]:
    soup = BeautifulSoup(raw, "html.parser")
    areas = soup.select("#warnings_by_area .nav-area-div")
    if not areas:
        raise ValueError("Missing warning list; this is not an empty observation")
    records, empty, rows = {}, [], 0
    for block in areas:
        heading = block.find("h5")
        if heading is None:
            raise ValueError("Warning area has no heading")
        area = clean_text(heading.get_text(" ", strip=True))
        paragraphs = block.find_all("p", recursive=False)
        if not paragraphs:
            raise ValueError("Missing area content")
        for paragraph in paragraphs:
            label, content = paragraph.find("b"), paragraph.find("span")
            if label is None:
                if clean_text(paragraph.get_text(" ", strip=True)) == "No current warnings in the area":
                    empty.append(area)
                    continue
                raise ValueError("Unrecognised warning entry")
            title = clean_text(label.get_text(" ", strip=True))
            if not re.fullmatch(r"(?:SWEDISH|BALTIC SEA) NAV WARN \d+/\d{2}", title) or content is None:
                raise ValueError("Unrecognised warning identity or body")
            body = clean_text(content.get_text(" ", strip=True))
            prefix = " ".join(str(x) for x in label.previous_siblings if isinstance(x, str))
            time_raw = clean_text(prefix) or None
            if not body:
                raise ValueError("Empty warning body")
            key = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            item = _record("sjofartsverket", key, title, body, url, time_raw, None, [area])
            # A two-digit notice suffix is not a complete publication timestamp.
            item["validity_note"] = "Obecny na liście ostrzeżeń; data pobrania nie ustala początku ani końca zdarzenia."
            if re.search(r"Baltic|Åland|Bothnia|Quark", area, re.I) and re.search(
                r"INTERFERENCE|EXERCISE|CABLE|PIPELINE|EXPLOSION|SABOTAGE", body, re.I
            ):
                item["priority_hint"] = "context_review"
            rows += 1
            if key in records:
                if records[key]["content_sha256"] != item["content_sha256"]:
                    raise ValueError("Conflicting copies of one warning")
                records[key]["areas_original"] = sorted(set(records[key]["areas_original"] + [area]))
                if item["priority_hint"] == "context_review":
                    records[key]["priority_hint"] = "context_review"
            else:
                records[key] = item
    update = next((clean_text(b.get_text(" ", strip=True)) for b in soup.find_all("b")
                   if "Latest Update of Navigational Warnings:" in b.get_text()), None)
    return list(records.values()), {
        "page_update_raw": update, "page_update_timezone": None,
        "page_kind": "swedish_warnings_in_force", "area_rows": rows,
        "duplicate_area_rows": rows - len(records), "explicit_empty_areas": sorted(set(empty)),
        "history_complete": False, "absence_means_cancelled": False,
    }


def _strict_rss_time(value: str | None) -> str | None:
    if not value:
        return None
    try:
        stamp = parsedate_to_datetime(value)
        return stamp.astimezone(UTC).isoformat() if stamp.tzinfo else None
    except (ValueError, TypeError, OverflowError):
        return None


def parse_rss(raw: bytes, url: str) -> tuple[list[dict], dict]:
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("RSS document declarations are not supported")
    xml = ET.fromstring(raw)
    items = xml.findall("./channel/item")
    if xml.tag != "rss" or not items:
        raise ValueError("Missing RSS items; completeness is unknown")
    parsed = _feed.parse_feed(raw, "application/rss+xml")
    if len(items) != len(parsed["entries"]):
        raise ValueError("RSS parser item mismatch")
    records = {}
    for item, entry in zip(items, parsed["entries"]):
        link = canonical_url(entry["link"])
        if urlsplit(link).hostname != "meduza.io" or not entry["title"]:
            raise ValueError("Unexpected article host or missing title")
        time_raw = item.findtext("pubDate")
        record = _record("meduza", digest(link), entry["title"], entry.get("summary") or "",
                         link, time_raw, _strict_rss_time(time_raw), [])
        text = record["title_original"] + " " + record["content_original"]
        geography = re.search(r"\b(Russia\w*|Belarus\w*|Poland|Polish|Ukraine|Ukrainian|Baltic|NATO|Kaliningrad|Lithuania\w*|Latvia\w*|Estonia\w*)\b", text, re.I)
        topic = re.search(r"\b(milit\w*|mobiliz\w*|mobilis\w*|drone\w*|missile\w*|sabotage|cyber\w*|logistic\w*|war|troop\w*|defen[cs]\w*|infrastructure|airspace|naval)\b", text, re.I)
        if geography and topic:
            record["priority_hint"] = "context_review"
        key = record["record_id"]
        if key in records and records[key]["content_sha256"] != record["content_sha256"]:
            raise ValueError("Conflicting RSS copies")
        records[key] = record
    return list(records.values()), {"history_complete": False, "full_articles": False,
                                    "excerpt_max_chars": 2000, "feed_rows": len(items)}


def parse_capture(folder: Path, source_id: str, config: dict | None = None) -> dict:
    config = config or settings()
    source = config["sources"][source_id]
    meta = read_json(folder / "fetch.json")
    raw_path = folder / ("source.html" if source["parser"] == "swedish_warnings" else "source.xml")
    if raw_path.stat().st_size > config["max_response_bytes"]:
        raise ValueError("Capture exceeds byte limit")
    raw = raw_path.read_bytes()
    if meta["requested_url"] != source["url"] or meta["final_url"] != source["url"] or meta["http_status"] != 200:
        raise ValueError("Capture URL/status mismatch")
    instant(meta["fetched_at"])
    if meta["bytes"] != len(raw) or meta["sha256"] != digest(raw):
        raise ValueError("Capture integrity mismatch")
    parser = parse_warnings if source["parser"] == "swedish_warnings" else parse_rss
    records, coverage = parser(raw, source["url"])
    result = {"version": "source-pilot-1", "parser_version": PARSER_VERSION,
              "source_id": source_id, "publisher": source["publisher"], "role": source["role"],
              "fetched_at": meta["fetched_at"], "capture_sha256": meta["sha256"],
              "transport_status": "ok", "content_freshness": "not_assessed",
              "runtime_enabled": False, "coverage": coverage, "records": records}
    Draft202012Validator(read_json(ROOT / "schemas/source-pilot.schema.json"), format_checker=FormatChecker()).validate(result)
    _once(folder / "parsed-v1.json", result)
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def collect(source_id: str, root: Path = PILOT_ROOT, *, opener=None, stamp: str | None = None) -> dict:
    config = settings()
    source = config["sources"][source_id]
    stamp = stamp or now()
    root = root / source_id
    with _lock(root):
        state_path = root / "attempts.json"
        attempts = read_json(state_path) if state_path.exists() else []
        # Captures made before this collector existed also consume today's budget.
        captures = [read_json(path) for path in root.glob("*/fetch.json")]
        prior = [*attempts, *captures]
        if any(_date(row["fetched_at"]) == _date(stamp) for row in prior):
            raise ValueError("Pilot request already attempted today; parse the saved capture")
        if any(row.get("retry_at") and instant(row["retry_at"]) > instant(stamp) for row in attempts):
            raise ValueError("Source Retry-After is still active")
        attempt = {"fetched_at": stamp, "status": "started", "retry_at": None}
        attempts.append(attempt)
        write_json(state_path, attempts)  # Reserve before I/O, including failed/crashed attempts.
        folder = root / _date(stamp)
        folder.mkdir(exist_ok=True)
        request = urllib.request.Request(source["url"], headers={
            "User-Agent": "RedThreatAlert/0.1 (manual source evaluation)",
            "Accept": "application/rss+xml, text/html", "Accept-Encoding": "identity",
        })
        opener = opener or urllib.request.build_opener(NoRedirect())
        try:
            with opener.open(request, timeout=config["timeout_seconds"]) as response:
                if response.status != 200 or response.url != source["url"]:
                    raise ValueError("Unexpected response or redirect")
                raw = response.read(config["max_response_bytes"] + 1)
                if len(raw) > config["max_response_bytes"]:
                    raise ValueError("Source response exceeds byte limit")
                meta = {"requested_url": source["url"], "final_url": response.url,
                        "http_status": response.status, "fetched_at": stamp,
                        "sha256": digest(raw), "bytes": len(raw),
                        "content_type": response.headers.get("Content-Type"),
                        "retry_after": response.headers.get("Retry-After")}
                if meta["retry_after"]:
                    attempt["retry_at"] = _retry_at(stamp, meta["retry_after"])
            raw_path = folder / ("source.html" if source["parser"] == "swedish_warnings" else "source.xml")
            if raw_path.exists():
                raise ValueError("Existing capture must not be replaced")
            atomic_write(raw_path, raw)
            _once(folder / "fetch.json", meta)
            result = parse_capture(folder, source_id, config)
            attempt["status"] = "ok"
            return result
        except Exception as exc:
            attempt["status"] = "error"
            attempt["error_type"] = type(exc).__name__
            if isinstance(exc, urllib.error.HTTPError):
                attempt["http_status"] = exc.code
                value = (exc.headers or {}).get("Retry-After")
                if value or exc.code == 429:
                    attempt["retry_at"] = _retry_at(stamp, value)
            raise
        finally:
            write_json(state_path, attempts)
