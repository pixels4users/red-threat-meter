"""Bounded, explicitly invoked X reads. Report preparation only imports captures."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
import uuid
from datetime import timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode

from jsonschema import Draft202012Validator, FormatChecker

from .common import ROOT, canonical_url, digest, instant, load_config, now, read_json, write_json


class XError(ValueError):
    """Messages are fixed error codes, never provider bodies or credentials."""


def load_settings():
    config = read_json(ROOT / "config/x-api.json")
    Draft202012Validator(read_json(ROOT / "schemas/x-api-config.schema.json")).validate(config)
    return config


def load_token(path=ROOT / ".env.x"):
    token = os.environ.get("X_BEARER_TOKEN", "").strip()
    if not token and path.is_file():
        if path.stat().st_mode & 0o077:
            raise XError("token_file_permissions_require_0600")
        rows = [line.split("=", 1)[1].strip().strip("\"'")
                for line in path.read_text().splitlines()
                if line.strip().startswith("X_BEARER_TOKEN=")]
        if len(rows) != 1:
            raise XError("token_missing_or_ambiguous")
        token = rows[0]
    if not re.fullmatch(r"[A-Za-z0-9%._~+/=-]{20,2048}", token):
        raise XError("token_missing_or_invalid")
    return token


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward Authorization, including to another X host.


class Transport:
    def __init__(self, token, config):
        self.token, self.config = token, config
        self.opener = urllib.request.build_opener(NoRedirect())

    def __call__(self, path, params):
        if not re.fullmatch(r"/2/users/(?:by/username/(?:sentdefender|osinttechnical)|[0-9]{1,19}/tweets)", path):
            raise XError("endpoint_not_allowed")
        request = urllib.request.Request("https://api.x.com" + path + ("?" + urlencode(params) if params else ""),
                                        headers={"Authorization": "Bearer " + self.token,
                                                 "Accept": "application/json", "User-Agent": "RTB/0.3"})
        try:
            response = self.opener.open(request, timeout=self.config["timeout_seconds"])
        except urllib.error.HTTPError as exc:
            response = exc
        except (urllib.error.URLError, TimeoutError, OSError):
            raise XError("network_failure_no_retry") from None
        with response:
            body = response.read(self.config["max_response_bytes"] + 1)
            if len(body) > self.config["max_response_bytes"]:
                raise XError("response_size_limit")
            try:
                payload = json.loads(body)
            except (ValueError, UnicodeError):
                raise XError("response_not_json") from None
            headers = {k.lower(): v for k, v in response.headers.items()
                       if k.lower() in ("retry-after", "x-rate-limit-reset")}
            return response.code, payload, headers


def valid_id(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9]{1,19}", value))


def normalize_posts(payload, account, user_id, captured_at):
    """No expansions: quoted posts, media and article bodies are not fetched."""
    rows = payload.get("data", [])
    if not isinstance(rows, list) or len(rows) > 10 or not isinstance(payload.get("meta"), dict):
        raise XError("invalid_timeline_response")
    if payload["meta"].get("result_count") != len(rows) or payload.get("errors") or payload.get("includes"):
        raise XError("incomplete_or_unexpected_response")
    seen, posts = set(), []
    for row in rows:
        post_id = row.get("id")
        if not valid_id(post_id) or post_id in seen or row.get("author_id", user_id) != user_id:
            raise XError("invalid_post_identity")
        seen.add(post_id)
        published = row.get("created_at")
        if not published or instant(published) > instant(captured_at):
            raise XError("invalid_post_timestamp")
        # Current API names and older exports are supported without another request.
        note = row.get("note_post") or row.get("note_tweet") or {}
        text = note.get("text") or row.get("text")
        if not isinstance(text, str) or not text.strip() or len(text) > 30000:
            raise XError("invalid_post_text")
        refs = row.get("referenced_posts", row.get("referenced_tweets", []))
        urls = []
        for entity in (row.get("entities", {}), note.get("entities", {})):
            for link in entity.get("urls", []):
                url = link.get("unwound_url") or link.get("expanded_url") or link.get("url")
                if url:
                    urls.append(canonical_url(url))
        for ref in refs:
            if not valid_id(ref.get("id")):
                raise XError("invalid_reference")
            urls.append("https://x.com/i/status/" + ref["id"])
        kind = "repost" if any(r.get("type") == "retweeted" for r in refs) else (
            "quote" if any(r.get("type") == "quoted" for r in refs) else "post")
        edit_ids = row.get("edit_history_post_ids", row.get("edit_history_tweet_ids", [post_id]))
        if not isinstance(edit_ids, list) or not edit_ids or not all(valid_id(i) for i in edit_ids) or post_id not in edit_ids:
            raise XError("invalid_edit_history")
        posts.append({"url": f"https://x.com/{account}/status/{post_id}", "text": text,
                      "published_at": published, "published_label": published, "post_kind": kind,
                      "text_complete": not bool(row.get("withheld") or row.get("article") or
                                                 row.get("truncated") or kind == "repost") and not text.rstrip().endswith(("…", "...")),
                      "referenced_urls": sorted(set(urls)), "edit_history_ids": edit_ids})
    token = payload["meta"].get("next_token")
    if token is not None and (not isinstance(token, str) or not 1 <= len(token) <= 2048):
        raise XError("invalid_pagination_token")
    return posts


def validate_api_capture(capture):
    schema = read_json(ROOT / "schemas/x-api-capture.schema.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(capture)
    if capture["access_status"] == "partial":
        if not capture["raw_ref"] or not valid_id(capture["user_id"]):
            raise XError("api_capture_requires_response_provenance")
        expected = normalize_posts(capture["response"], capture["account"], capture["user_id"], capture["captured_at"])
        if expected != capture["posts"]:
            raise XError("posts_differ_from_original_response")
        query = capture["request_params"]
        if len(expected) > query.get("max_results", 0):
            raise XError("response_exceeds_requested_post_limit")
        if capture["pagination_pending"] != bool(capture["response"]["meta"].get("next_token")):
            raise XError("pagination_state_mismatch")
        for row in expected:
            published = instant(row["published_at"])
            if ((query.get("start_time") and published < instant(query["start_time"])) or
                    (query.get("end_time") and published >= instant(query["end_time"])) or
                    (query.get("since_id") and int(row["url"].rsplit("/", 1)[1]) <= int(query["since_id"]))):
                raise XError("post_outside_requested_interval")
    elif capture["posts"]:
        raise XError("unavailable_capture_contains_posts")


def budget_status(folder, config, at=None):
    """Unsettled reservations count in full, including a crash during HTTP."""
    day = instant(at or now()).date().isoformat()
    daily = total = 0
    for path in (folder / "requests").glob("*.reservation.json"):
        reserved = read_json(path)
        settled = path.with_name(path.name.replace(".reservation.json", ".result.json"))
        amount = read_json(settled)["accounted_mill_usd"] if settled.exists() else reserved["reserved_mill_usd"]
        if not isinstance(amount, int) or amount < 0:
            raise XError("invalid_budget_ledger")
        total += amount
        if instant(reserved["at"]).date().isoformat() == day:
            daily += amount
    return {"daily_accounted_mill_usd": daily, "total_accounted_mill_usd": total,
            "daily_limit_mill_usd": config["daily_limit_mill_usd"],
            "total_limit_mill_usd": config["total_limit_mill_usd"]}


def cooldown(headers, at):
    stamp = instant(at)
    until = stamp + timedelta(minutes=15)
    try:
        value = headers.get("retry-after", "")
        until = max(until, stamp + timedelta(seconds=int(value)) if value.isdigit() else parsedate_to_datetime(value))
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        until = max(until, stamp.fromtimestamp(int(headers["x-rate-limit-reset"]), stamp.tzinfo))
    except (KeyError, TypeError, ValueError, OverflowError, OSError):
        pass
    return until.isoformat()


def collect(data_dir=ROOT / "data", *, config=None, transport=None, synthetic=False):
    from .pipeline import check_mode, locked
    from .x_sources import classify_post, validate_capture

    config = config or load_settings()
    Draft202012Validator(read_json(ROOT / "schemas/x-api-config.schema.json")).validate(config)
    if synthetic and transport is None:
        raise XError("synthetic_collection_requires_test_transport")
    if not synthetic and Path(data_dir).resolve() != (ROOT / "data").resolve():
        raise XError("paid_collection_requires_shared_live_budget_directory")
    data_dir = Path(data_dir)
    sources = [s for s in load_config()["sources"] if s["id"] in config["source_ids"] and s["enabled"]]
    if {s["id"] for s in sources} != set(config["source_ids"]):
        raise XError("configured_source_missing")
    folder = data_dir / "x-api"
    with locked(data_dir):
        check_mode(data_dir, "fixture" if synthetic else "live")
        state_path = folder / "state.json"
        state = read_json(state_path) if state_path.exists() else {"accounts": {}}
        stamp = now()
        if state.get("retry_at") and instant(stamp) < instant(state["retry_at"]):
            return {"status": "skipped", "reason": "retry_after", "retry_at": state["retry_at"], "requests": 0}
        if state.get("last_attempt_at") and (instant(stamp) - instant(state["last_attempt_at"])).total_seconds() < config["minimum_interval_seconds"]:
            return {"status": "skipped", "reason": "minimum_interval", "requests": 0}
        # Do not open the secret file for status/import/report operations.
        transport = transport or Transport(load_token(), config)
        run_id = uuid.uuid4().hex
        summary = {"run_id": run_id, "status": "partial", "started_at": stamp,
                   "requests": 0, "posts_read": 0, "accounted_mill_usd": 0, "sources": []}

        def request(path, params, resource, maximum):
            reserved = maximum * config[resource + "_mill_usd"]
            usage = budget_status(folder, config)
            if (summary["requests"] >= config["max_requests_per_run"] or
                    summary["accounted_mill_usd"] + reserved > config["run_limit_mill_usd"] or
                    usage["daily_accounted_mill_usd"] + reserved > config["daily_limit_mill_usd"] or
                    usage["total_accounted_mill_usd"] + reserved > config["total_limit_mill_usd"]):
                raise XError("budget_limit")
            rid = uuid.uuid4().hex
            entry = {"at": now(), "run_id": run_id, "path": path, "params": params,
                     "resource": resource, "reserved_mill_usd": reserved, "synthetic": synthetic}
            write_json(folder / "requests" / (rid + ".reservation.json"), entry)
            state["last_attempt_at"] = now()
            write_json(state_path, state)
            summary["requests"] += 1
            summary["accounted_mill_usd"] += reserved
            status, payload, headers = transport(path, params)  # One attempt; no automatic retry.
            record = {**entry, "received_at": now(), "status": status, "response": payload,
                      "headers": headers}
            raw_ref = f"raw/x-api/{digest(record)}.json"
            if not (data_dir / raw_ref).exists():
                write_json(data_dir / raw_ref, record)
            # Only a successful, structurally bounded response releases unused reservation.
            data = payload.get("data") if isinstance(payload, dict) else None
            bounded = (isinstance(data, list) and len(data) <= maximum) if resource == "post" else isinstance(data, dict)
            if resource == "post" and isinstance(payload, dict) and data is None and payload.get("meta", {}).get("result_count") == 0:
                data, bounded = [], True
            amount = reserved
            if status == 200 and bounded and not payload.get("includes") and not payload.get("errors"):
                amount = (len(data) if isinstance(data, list) else 1) * config[resource + "_mill_usd"]
            write_json(folder / "requests" / (rid + ".result.json"),
                       {"accounted_mill_usd": amount, "http_status": status, "raw_ref": raw_ref})
            summary["accounted_mill_usd"] += amount - reserved
            if status == 429 or headers.get("retry-after"):
                state["retry_at"] = cooldown(headers, now())
                write_json(state_path, state)
            if status != 200:
                raise XError(f"http_{status}_no_retry")
            if not bounded or payload.get("includes"):
                raise XError("unexpected_billable_resources")
            if resource == "post":
                summary["posts_read"] += len(data)
            return payload, raw_ref

        for source in sources:
            account = source["account"]
            current = state["accounts"].setdefault(account, {})
            try:
                if not current.get("user_id"):
                    user, user_ref = request("/2/users/by/username/" + account, {}, "user", 1)
                    identity = user["data"]
                    if identity.get("username", "").lower() != account or not valid_id(identity.get("id")) or user.get("errors"):
                        raise XError("account_identity_mismatch")
                    current.update(user_id=identity["id"], identity_raw_ref=user_ref)
                    write_json(state_path, state)
                user_id = current["user_id"]
                if not valid_id(user_id):
                    raise XError("invalid_cached_user_id")
                # A pending page retains the original since_id/end_time. Advancing
                # the high-water mark before the final page would silently lose posts.
                params = current.get("pending_params")
                if params is None:
                    params = {"end_time": (instant(now()) - timedelta(seconds=30)).isoformat()}
                    if current.get("since_id"):
                        params["since_id"] = current["since_id"]
                    else:
                        params["start_time"] = current.get("completed_until") or (
                            instant(now()) - timedelta(hours=config["initial_lookback_hours"])).isoformat()
                params = dict(params)
                if set(params) - {"start_time", "end_time", "since_id", "pagination_token"}:
                    raise XError("invalid_cursor_parameters")
                for key in ("start_time", "end_time"):
                    if key in params:
                        instant(params[key])
                if "since_id" in params and not valid_id(params["since_id"]):
                    raise XError("invalid_cursor_id")
                query = {**params, "max_results": config["posts_per_account"], "exclude": "retweets",
                         "post.fields": "created_at,entities,note_post"}
                payload, raw_ref = request(f"/2/users/{user_id}/tweets", query, "post", config["posts_per_account"])
                captured_at = now()
                posts = normalize_posts(payload, account, user_id, captured_at)
                next_token = payload["meta"].get("next_token")
                capture = {"schema_version": "x-api-v1", "synthetic": synthetic, "account": account,
                           "captured_at": captured_at, "access_status": "partial", "user_id": user_id,
                           "coverage_note": "Ograniczony odczyt API X; pominięto reposty. " + (
                               "Dalsze wpisy oczekują na pobranie w limicie budżetu." if next_token else
                               "Odczytano dostępne wpisy w przedziale zapytania; nie poświadcza to pełnej historii konta."),
                           "posts": posts, "response": payload, "raw_ref": raw_ref,
                           "request_params": query, "pagination_pending": bool(next_token)}
                validate_capture(capture, source)
                capture_path = data_dir / "social" / source["id"] / (digest(capture) + ".json")
                if not capture_path.exists():
                    write_json(capture_path, capture)
                ids = [int(p["url"].rsplit("/", 1)[1]) for p in posts]
                newest = max([int(current.get("pending_newest_id", current.get("since_id", "0"))), *ids])
                if next_token:
                    current.update(pending_params={**params, "pagination_token": next_token}, pending_newest_id=str(newest))
                else:
                    if newest:
                        current["since_id"] = str(newest)
                    current["completed_until"] = params["end_time"]
                    current.pop("pending_params", None)
                    current.pop("pending_newest_id", None)
                write_json(state_path, state)
                selected = sum(classify_post(p["text"], source["filter"])["decision"] != "outside_region" for p in posts)
                summary["sources"].append({"source_id": source["id"], "posts": len(posts), "selected": selected,
                                           "pagination_pending": bool(next_token), "capture": str(capture_path)})
            except (ValueError, TypeError, KeyError, IndexError) as exc:
                # A failed paid read is not a successful refresh. Preserve the
                # previous material but expose the latest failed access to import.
                code = str(exc) if isinstance(exc, XError) else "invalid_api_data"
                if code == "budget_limit":
                    # No request was made: this is a local scheduling decision,
                    # not a new observation of an unavailable remote source.
                    summary["status"] = "incomplete"
                    summary["sources"].append({"source_id": source["id"], "error": code})
                    continue
                capture = {"schema_version": "x-api-v1", "synthetic": synthetic, "account": account,
                           "captured_at": now(), "access_status": "unavailable", "user_id": current.get("user_id"),
                           "coverage_note": "Nie wykonano pełnego odczytu API X: " + code,
                           "posts": [], "response": None, "raw_ref": None, "request_params": {},
                           "pagination_pending": bool(current.get("pending_params"))}
                validate_capture(capture, source)
                write_json(data_dir / "social" / source["id"] / (digest(capture) + ".json"), capture)
                summary["status"] = "incomplete"
                summary["sources"].append({"source_id": source["id"], "error": code})
                break  # Auth, rate or parser failure: never probe another account.
        summary["budget"] = budget_status(folder, config)
        write_json(folder / "runs" / (run_id + ".json"), summary)
        return summary
