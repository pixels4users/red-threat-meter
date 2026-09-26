from __future__ import annotations

import time
import urllib.error
import urllib.request
from datetime import timedelta
from email.utils import parsedate_to_datetime

from ..common import atomic_write, digest, instant, read_json, write_json
from .contracts import identity, now, queries, validate_sample


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def cooldown(headers, received_at):
    value = headers.get("retry-after", "")
    try:
        seconds = max(0, int(value))
    except ValueError:
        try:
            seconds = max(0, (parsedate_to_datetime(value) - instant(received_at)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            seconds = 300
    return (instant(received_at) + timedelta(seconds=max(300, seconds))).isoformat()


class Fetcher:
    """Exactly one request per tile; rate-limit and access errors are not retried."""
    def __init__(self, folder, cfg):
        self.folder, self.cfg = folder, cfg
        self.opener = urllib.request.build_opener(NoRedirect())

    def get(self, query):
        if query not in queries(self.cfg):
            raise ValueError("Request outside the configured query plan")
        start = now()
        receipt = {"query": query, "requested_at": start, "received_at": start, "http_status": None,
                   "raw_ref": None, "bytes": 0, "headers": {}, "error": None}
        try:
            request = urllib.request.Request(query["url"], headers={"User-Agent": "OSINT-Dashboard/0.2 (local research pilot)",
                                                                   "Accept": "application/json"})
            try:
                response = self.opener.open(request, timeout=self.cfg["timeout_seconds"])
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                receipt["http_status"] = response.code
                receipt["headers"] = {k.lower(): v for k, v in response.headers.items()
                                      if k.lower() in ("date", "content-type", "cache-control", "age", "retry-after")}
                body = response.read(self.cfg["max_response_bytes"] + 1)
                receipt["bytes"] = len(body)
            if len(body) > self.cfg["max_response_bytes"]:
                receipt["error"] = "response_too_large"
            else:
                ref = f"raw/adsblol/{digest(body)}.bin"
                if not (self.folder / ref).exists():
                    atomic_write(self.folder / ref, body)
                receipt["raw_ref"] = ref
                if receipt["http_status"] != 200:
                    receipt["error"] = "http_error"
        except (OSError, TimeoutError):
            receipt["error"] = "network_error"
        receipt["received_at"] = now()
        return receipt


def collect(folder, cfg, mode, fetcher=None, progress=lambda msg: None):
    fetcher = fetcher or Fetcher(folder, cfg)
    gate_path = folder / "request-state.json"
    if gate_path.exists():
        gate = read_json(gate_path)
        if instant(gate["next_collection_at"]) > instant(now()):
            raise ValueError("Kolejne pobranie najwcześniej: " + gate["next_collection_at"])
    started = now()
    # Reserve before the first request: restarts do not bypass the local limit.
    gate = {"next_collection_at": (instant(started) + timedelta(seconds=cfg["collection_interval_seconds"])).isoformat()}
    write_json(gate_path, gate)
    receipts, stopped = [], False
    last_start = None
    for query in queries(cfg):
        if stopped:
            stamp = now()
            receipts.append({"query": query, "requested_at": stamp, "received_at": stamp, "http_status": None,
                             "raw_ref": None, "bytes": 0, "headers": {}, "error": "not_requested_after_http_error"})
            continue
        if last_start is not None:
            time.sleep(max(0, cfg["request_interval_seconds"] - (time.monotonic() - last_start)))
        last_start = time.monotonic()
        receipt = fetcher.get(query)
        receipts.append(receipt)
        status = receipt["http_status"]
        progress(f"ADSB.lol — {query['label']}: " + (f"HTTP {status}" if status else "brak odpowiedzi"))
        if status is not None and 300 <= status < 500:
            stopped = True
            # Even manual restarts respect Retry-After; unknown limits use 5 minutes.
            until = cooldown(receipt["headers"], receipt["received_at"])
            gate["next_collection_at"] = max(instant(gate["next_collection_at"]), instant(until)).isoformat()
            write_json(gate_path, gate)
    finished = now()
    gate["next_collection_at"] = max(instant(gate["next_collection_at"]),
                                     instant(finished) + timedelta(seconds=cfg["collection_interval_seconds"])).isoformat()
    write_json(gate_path, gate)
    sample = {"schema_version": "aviation-sample-1", "mode": mode, "started_at": started,
              "finished_at": finished, "config": cfg, "requests": receipts}
    sample["sample_id"] = identity(sample)
    validate_sample(sample)
    return sample
