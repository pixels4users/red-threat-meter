from __future__ import annotations

import csv
import io
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime

import h3
from bs4 import BeautifulSoup

from ..collect import Fetcher, allowed_url
from ..common import UTC, clean_text, instant, now
from .contracts import identity, region_cells, source_hash, validate_observation

PROVIDERS = {
    "adsbexchange": ["adsb:adsbexchange"],
    "airplaneslive": ["adsb:airplaneslive"],
    "merged": ["adsb:adsbexchange", "adsb:airplaneslive"],
}


def base_observation(source, cfg, key, url, refs, fetched_at):
    return {
        "schema_version": "ew-observation-1", "logical_key": key,
        "source_id": source["id"], "publisher": source["publisher"], "url": url,
        "source_config_hash": source_hash(source, cfg), "adapter_version": source["adapter"],
        "times": {"observed_start": None, "observed_end": None, "observed_precision": "unknown",
                  "published_at": None, "first_available_at": None,
                  "availability_basis": "unknown; first_seen_at is a local acquisition bound",
                  "first_seen_at": fetched_at, "fetched_at": fetched_at},
        "location": {"label": "Nie ustalono lokalizacji zdarzenia", "precision": "unknown", "bbox": None},
        "raw_refs": list(dict.fromkeys(refs)),
    }


def finish(obs):
    obs["observation_id"] = identity(obs)
    validate_observation(obs)
    return obs


def parse_manifest(body: bytes) -> dict:
    rows = csv.DictReader(io.StringIO(body.decode("utf-8-sig")))
    if not {"date", "suspect", "source"} <= set(rows.fieldnames or []):
        raise ValueError("GPSJAM manifest columns changed")
    result = {}
    for row in rows:
        day = date.fromisoformat(row["date"])
        if row["suspect"] not in ("true", "false") or row["source"] not in PROVIDERS or day in result:
            raise ValueError("Invalid or duplicated GPSJAM manifest entry")
        result[day] = {"suspect": row["suspect"] == "true", "provider": row["source"]}
    if not result:
        raise ValueError("Empty GPSJAM manifest")
    return result


def parse_gnss(body, day, metadata, source, cfg, url, refs, fetched_at):
    expected = region_cells(tuple(cfg["region"]["bbox"]))
    selected = set(expected)
    reader = csv.DictReader(io.StringIO(body.decode("utf-8-sig")))
    if reader.fieldnames != ["hex", "count_good_aircraft", "count_bad_aircraft"]:
        raise ValueError("GPSJAM CSV columns changed")
    seen, cells = set(), []
    for row in reader:
        cell = row["hex"]
        if not h3.is_valid_cell(cell) or h3.get_resolution(cell) != 4 or cell in seen:
            raise ValueError("Invalid, duplicated or unexpected-resolution H3 cell")
        seen.add(cell)
        good, bad = row["count_good_aircraft"], row["count_bad_aircraft"]
        if not good or not bad or not good.isascii() or not bad.isascii() or not good.isdecimal() or not bad.isdecimal():
            raise ValueError("Aircraft category counts must be non-negative integers")
        good, bad = int(good), int(bad)
        if good + bad == 0:
            raise ValueError("Zero denominator in a reported cell")
        if cell in selected:
            cells.append({"h3": cell, "good": good, "bad": bad, "sample": good + bad,
                          "source_adjusted_pct": round(100 * (bad - 1) / (good + bad), 6)})
    if not seen:
        raise ValueError("Empty GNSS CSV")
    region = cfg["region"]
    obs = base_observation(source, cfg, f"gpsjam:{region['id']}:{day}", url, refs, fetched_at)
    obs["times"].update(observed_start=datetime.combine(day, datetime.min.time(), UTC).isoformat(),
                        observed_end=datetime.combine(day + timedelta(days=1), datetime.min.time(), UTC).isoformat(),
                        observed_precision="utc_day")
    obs["location"] = {"label": region["label"], "precision": "h3_grid_bbox", "bbox": region["bbox"]}
    obs["dependency_groups"] = PROVIDERS[metadata["provider"]]
    obs["quality"] = {"integrity": "suspect_by_publisher" if metadata["suspect"] else "not_flagged_by_publisher",
                      "limitations": ["Agregat dobowy nie dowodzi ciągłości ani sprawcy zakłóceń.",
                                      "Brak komórki oznacza brak obserwacji; suma próbek nie jest liczbą unikalnych lotów.",
                                      "Brak flagi suspect nie dowodzi pełnego pokrycia; pierwsza dostępność historyczna nieznana."]}
    obs["data"] = {"type": "gnss_daily", "day": str(day), "provider": metadata["provider"],
                   "manifest_suspect": metadata["suspect"], "cells": sorted(cells, key=lambda c: c["h3"]),
                   "expected_cells": list(expected), "global_rows": len(seen),
                   "formula": "100 * (bad - 1) / (good + bad)", "unit": "percent_per_cell",
                   "denominator": "good + bad aircraft category counts in one cell and UTC day",
                   "min_cell_sample": region["min_cell_sample"]}
    return finish(obs)


def html_text(content: str) -> str:
    soup = BeautifulSoup(content, "html.parser")
    for el in soup.select("script, style, form, nav, iframe, .essb_links, .sharedaddy"):
        el.decompose()
    return clean_text(soup.get_text(" ", strip=True))


def parse_publication(item, source, cfg, raw_ref, fetched_at):
    url = allowed_url(item.findtext("link") or "", source)
    title = clean_text(item.findtext("title") or "")
    content = item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded")
    text_kind = "rss_full_content" if content else "rss_summary"
    text = html_text(content or item.findtext("description") or "")
    if not title or len(text) < 30:
        raise ValueError("RSS publication lacks a title or usable text")
    published, date_problem = None, False
    try:
        parsed = parsedate_to_datetime(item.findtext("pubDate") or "")
        if parsed.tzinfo is None:
            raise ValueError("Publication date has no timezone")
        published = parsed.astimezone(UTC).isoformat()
        if instant(published) > instant(fetched_at):
            raise ValueError("Publication date lies in the future")
    except (ValueError, TypeError, OverflowError):
        # Keep a discovery with an explicit missing date, without inventing one.
        published, date_problem = None, True
    categories = sorted({clean_text(c.text or "") for c in item.findall("category") if clean_text(c.text or "")})
    obs = base_observation(source, cfg, "belzhd:" + url, url, [raw_ref], fetched_at)
    obs["times"]["published_at"] = published
    obs["dependency_groups"] = ["publisher:belzhd"]
    limitations = ["Pojedynczy wydawca; witryna i kanał Telegram nie są niezależnym potwierdzeniem.",
                   "Data publikacji nie jest datą zdarzenia. Nie ustalono czasu zdarzenia ani dokładnej lokalizacji.",
                   "RSS obejmuje ostatnie publikacje, nie wszystkie transporty ani pełne archiwum wydawcy."]
    if date_problem:
        limitations.append("Brak poprawnej, nieprzyszłej daty publikacji w źródle.")
    if text_kind == "rss_summary":
        limitations.append("Dostępny tylko skrót RSS, bez pełnej treści.")
    obs["quality"] = {"integrity": "unknown", "limitations": limitations}
    obs["data"] = {"type": "publication", "title": title, "text": text, "text_kind": text_kind,
                   "categories": categories, "language": "ru", "military_transport_tag": any(c.casefold() == "воинские перевозки" for c in categories)}
    return finish(obs), date_problem or text_kind == "rss_summary"


def collect(source, cfg, data_dir, days: int, end: date, fetcher=None, progress=lambda m: None):
    fetcher = fetcher or Fetcher(data_dir, source)
    start = end - timedelta(days=days - 1)
    check = {"source_id": source["id"], "source_config_hash": source_hash(source, cfg),
             "checked_at": now(), "status": "error", "errors": [], "raw_refs": [],
             "requested_start": str(start), "requested_end": str(end), "requested_days": days,
             "successful_days": [], "missing_days": [], "scope": "", "items": 0}
    observations = []
    try:
        body, _, _, raw_ref = fetcher.get(source["url"])
        fetched_at = now()
        if source["id"] == "gpsjam":
            check["scope"] = "published_daily_grids_in_research_bbox"
            manifest = parse_manifest(body)
            check["publisher_latest_day"] = str(max(manifest))
            consecutive_errors = 0
            # Recent days first so a bounded failure does not hide today's gap.
            for offset in range(days):
                day = end - timedelta(days=offset)
                try:
                    if consecutive_errors >= 5:
                        raise ValueError("Stopped after five consecutive data failures")
                    metadata = manifest.get(day)
                    if metadata is None:
                        raise ValueError("Day not listed in publisher manifest")
                    provider = metadata["provider"]
                    prefix = "data/" + (provider + "/" if provider != "adsbexchange" else "")
                    url = f"https://gpsjam.org/{prefix}{day}-h3_4.csv"
                    csv_body, _, final, csv_ref = fetcher.get(url)
                    obs = parse_gnss(csv_body, day, metadata, source, cfg, final, [raw_ref, csv_ref], now())
                    observations.append(obs)
                    check["successful_days"].append(str(day))
                    if metadata["suspect"]:
                        check["errors"].append(f"{day}: publisher marks data suspect")
                    consecutive_errors = 0
                except Exception as exc:
                    consecutive_errors += 1
                    check["missing_days"].append(str(day))
                    check["errors"].append(f"{day}: {type(exc).__name__}: {str(exc)[:180]}")
                if offset % 5 == 0 or offset == days - 1:
                    progress(f"GPSJAM: sprawdzono {offset + 1}/{days} dni.")
        else:
            check["scope"] = "latest_publisher_rss_entries_only"
            if b"<!DOCTYPE" in body.upper() or b"<!ENTITY" in body.upper():
                raise ValueError("DTD/entities are not permitted in RSS")
            root = ET.fromstring(body)
            items = root.findall("./channel/item")
            if not items or len(items) > 100:
                raise ValueError("Empty or unexpectedly large RSS feed")
            seen = set()
            for item in items:
                try:
                    obs, partial = parse_publication(item, source, cfg, raw_ref, fetched_at)
                    if obs["logical_key"] in seen:
                        raise ValueError("Duplicated RSS publication URL")
                    seen.add(obs["logical_key"])
                    observations.append(obs)
                    if partial:
                        check["errors"].append(f"Incomplete publication: {obs['url']}")
                except Exception as exc:
                    check["errors"].append(f"{type(exc).__name__}: {str(exc)[:180]}")
            dates = [o["times"]["published_at"] for o in observations if o["times"]["published_at"]]
            check["oldest_publication"] = min(dates) if dates else None
            check["latest_publication"] = max(dates) if dates else None
            check["feed_reaches_window_start"] = bool(dates and instant(min(dates)).date() <= start)
            # Reaching a date is only a publication-window property, never event completeness.
        check["status"] = "partial" if check["errors"] else "ok"
    except Exception as exc:
        check["errors"].append(f"{type(exc).__name__}: {str(exc)[:250]}")
    if not observations:
        check["status"] = "error"
    check["items"] = len(observations)
    check["raw_refs"] = list(dict.fromkeys(fetcher.raw_refs))
    check["checked_at"] = now()
    return observations, check
