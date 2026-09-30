"""Offline import of frozen browser/API captures; this module never calls X."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

from .common import ROOT, canonical_url, clean_text, digest, instant, now, read_json, write_json


def post_url(value, account):
    parts = urlsplit(canonical_url(value))
    match = re.fullmatch(r"/([A-Za-z0-9_]+)/status/([0-9]{1,25})/?", parts.path)
    if (parts.scheme != "https" or parts.hostname not in ("x.com", "www.x.com", "twitter.com")
            or parts.port is not None or not match or match[1].lower() != account):
        raise ValueError("Post URL does not belong to configured account")
    return f"https://x.com/{account}/status/{match[2]}"


def validate_capture(capture, source):
    api = capture.get("schema_version") == "x-api-v1"
    if api:
        from .x_api import validate_api_capture
        validate_api_capture(capture)
    else:
        Draft202012Validator(read_json(ROOT / "schemas/x-capture.schema.json"),
                             format_checker=FormatChecker()).validate(capture)
    if source["adapter"] not in ("x_browser_import", "x_api_import") or capture["account"] != source["account"]:
        raise ValueError("Capture account mismatch")
    if instant(capture["captured_at"]) > instant(now()):
        raise ValueError("Capture cannot come from the future")
    if capture["access_status"] == "unavailable" and capture["posts"]:
        raise ValueError("Unavailable capture cannot contain posts")
    seen = set()
    for row in capture["posts"]:
        url = post_url(row["url"], source["account"])
        if url in seen:
            raise ValueError("Duplicate post in capture")
        seen.add(url)
        if row["published_at"] and instant(row["published_at"]) > instant(capture["captured_at"]):
            raise ValueError("Post published after its capture")
        if not api and clean_text(row["text"]) not in clean_text(capture["page_text"]):
            raise ValueError("Post text is absent from archived page transcript")
        for ref in row["referenced_urls"]:
            canonical_url(ref)


def import_capture(data_dir: Path, source: dict, capture: dict):
    from .pipeline import check_mode, locked
    validate_capture(capture, source)
    mode = "fixture" if capture["synthetic"] else "live"
    with locked(data_dir):
        check_mode(data_dir, mode)
        path = data_dir / "social" / source["id"] / (digest(capture) + ".json")
        if path.exists():
            if read_json(path) != capture:
                raise ValueError("Capture hash collision")
        else:
            write_json(path, capture)
    return {"path": str(path), "posts": len(capture["posts"]), "captured_at": capture["captured_at"]}


def classify_post(text, rules):
    """High-recall triage. Keywords never establish location, intent or attribution."""
    def hits(field):
        return sorted(key for key, terms in rules[field].items()
                      if any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.I) for term in terms))
    regions, broad, outside, topics = (hits(key) for key in
                                     ("regions", "broad_context", "outside_locations", "topics"))
    if regions:
        decision = "candidate" if topics else "review_topic"
    elif broad and not outside:
        decision = "review_geography"
    else:
        decision = "outside_region"
    return {"decision": decision, "region_matches": regions, "topic_matches": topics,
            "broad_matches": broad, "outside_matches": outside}


def collect_captures(source, data_dir):
    result = {"source_id": source["id"], "publisher": source["publisher"], "required": False,
              "checked_at": now(), "status": "error", "items": [], "errors": [],
              "window_complete": False, "scope": "partial_browser_observations",
              "source_definition_hash": digest(source), "raw_refs": [], "triage": [],
              "request_count": 0}
    paths = list((data_dir / "social" / source["id"]).glob("*.json"))
    if not paths:
        result["errors"] = ["Brak zapisanego odczytu profilu X."]
        return result
    if len(paths) > 200:
        result["errors"] = ["Limit paczek X przekroczony; wymagane uporządkowanie archiwum."]
        return result
    captures = []
    try:
        mode_path = data_dir / ".mode.json"
        mode = read_json(mode_path)["mode"] if mode_path.exists() else "live"
        for path in paths:
            # API envelopes include the original response and its normalized text.
            if path.stat().st_size > 1_500_000:
                raise ValueError("Capture file exceeds size limit")
            capture = read_json(path)
            if capture.get("schema_version") != "x-api-v1" and path.stat().st_size > 500_000:
                raise ValueError("Browser capture exceeds size limit")
            validate_capture(capture, source)
            if path.stem != digest(capture) or capture["synthetic"] != (mode == "fixture"):
                raise ValueError("Capture integrity or data mode mismatch")
            if capture.get("raw_ref"):
                if (data_dir / capture["raw_ref"]).stat().st_size > 1_000_000:
                    raise ValueError("API archive exceeds size limit")
                raw = read_json(data_dir / capture["raw_ref"])
                if digest(raw) != Path(capture["raw_ref"]).stem or raw["response"] != capture["response"]:
                    raise ValueError("API response archive mismatch")
                if (raw["status"] != 200 or raw["path"] != f"/2/users/{capture['user_id']}/tweets" or
                        raw["params"] != capture["request_params"] or raw["synthetic"] != capture["synthetic"]):
                    raise ValueError("API request archive mismatch")
            captures.append((capture, path))
        captures.sort(key=lambda pair: (instant(pair[0]["captured_at"]),
                                       pair[0]["access_status"] == "unavailable", pair[1].name))
        latest, latest_path = captures[-1]
        result["checked_at"] = latest["captured_at"]  # Reading a file cannot refresh a source.
        result["raw_refs"] = [str(latest_path.relative_to(data_dir))]
        result["coverage_note"] = latest["coverage_note"]
        if latest["schema_version"] == "x-api-v1":
            result["scope"] = "bounded_api_timeline"
            result["pagination_pending"] = latest["pagination_pending"]
        if latest["access_status"] == "unavailable":
            result["errors"] = ["Ostatnia próba odczytu profilu X była niedostępna."]
            return result
        if (instant(now()) - instant(latest["captured_at"])).total_seconds() > source["max_capture_age_hours"] * 3600:
            result["errors"] = ["Odczyt profilu X jest nieaktualny."]
            return result
        # Each capture is imported on the next cycle. Also keep intermediate
        # captures since the last run; newest observation wins for the same URL.
        selected, previously_selected = {}, set()
        for capture, path in captures:
            if (instant(latest["captured_at"]) - instant(capture["captured_at"])).total_seconds() > 216 * 3600:
                continue
            for row in capture["posts"]:
                url = post_url(row["url"], source["account"])
                if row.get("edit_history_ids"):
                    url = f"https://x.com/{source['account']}/status/{row['edit_history_ids'][0]}"
                if classify_post(row["text"], source["filter"])["decision"] != "outside_region":
                    previously_selected.add(url)
                selected[url] = (row, capture, path)
        if len(selected) > source["max_items"]:
            raise ValueError("Post limit exceeded; no silent truncation")
        for url, (row, capture, path) in selected.items():
            triage = classify_post(row["text"], source["filter"])
            if triage["decision"] == "outside_region" and url in previously_selected:
                triage["decision"] = "review_revision"
            result["triage"].append({"url": url, **triage})
            if triage["decision"] == "outside_region":
                continue
            raw_ref = str(path.relative_to(data_dir))
            result["raw_refs"].append(raw_ref)
            if capture.get("raw_ref"):
                result["raw_refs"].append(capture["raw_ref"])
            result["items"].append({"url": url, "title": f"Wpis {source['publisher']} · {url.rsplit('/', 1)[-1]}",
                                    "published_at": row["published_at"], "text": clean_text(row["text"]),
                                    "text_kind": "social_post" if row["text_complete"] else "social_post_excerpt",
                                    "raw_ref": raw_ref, "source_record": {
                                        "account": source["account"], "post_kind": row["post_kind"],
                                        "referenced_urls": row["referenced_urls"], "text_complete": row["text_complete"]},
                                    "content_provenance": {"capture_at": capture["captured_at"],
                                                           "access_method": capture["schema_version"],
                                                           "observed_url": row["url"],
                                                           "published_label": row["published_label"], "raw_ref": raw_ref},
                                    "triage": triage})
            if row.get("edit_history_ids"):
                result["items"][-1]["source_record"]["edit_history_ids"] = row["edit_history_ids"]
        result["raw_refs"] = list(dict.fromkeys(result["raw_refs"]))
        result["status"] = "partial"
        result["errors"] = ["Ograniczony odczyt X nie potwierdza kompletności historii ani dostępności wszystkich wpisów."]
    except Exception as exc:
        result["items"] = []
        result["status"] = "error"
        result["errors"] = [f"Niepoprawna paczka X ({type(exc).__name__})."]
    return result
