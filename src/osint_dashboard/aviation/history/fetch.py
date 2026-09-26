from __future__ import annotations

import http.client
import time
import urllib.error
import urllib.request
import uuid
from datetime import timedelta

from ...common import ROOT, atomic_write, digest, instant, read_json, write_json
from ...pipeline import check_mode, locked
from ..collector import NoRedirect, cooldown
from .contracts import config, now, validate_acquisition, windows


class Fetcher:
    def __init__(self, folder, cfg):
        self.folder, self.cfg = folder, cfg
        self.opener = urllib.request.build_opener(NoRedirect())

    def get(self, window):
        if window not in windows(self.cfg):
            raise ValueError("Żądanie poza planem historii")
        stamp = now()
        receipt = {"window": window, "requested_at": stamp, "received_at": stamp, "http_status": None,
                   "headers": {}, "bytes": 0, "raw_ref": None, "error": None}
        started = time.monotonic()
        limit = self.cfg["max_response_bytes"]
        try:
            req = urllib.request.Request(window["url"], headers={"User-Agent": "OSINT-Dashboard/0.2 (bounded history audit)",
                                                               "Accept-Encoding": "identity"})
            try:
                response = self.opener.open(req, timeout=self.cfg["timeout_seconds"])
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                receipt["http_status"] = response.code
                receipt["headers"] = {k.lower(): v for k, v in response.headers.items()
                                      if k.lower() in ("date", "content-type", "content-encoding", "content-length", "last-modified", "etag", "retry-after")}
                expected = response.headers.get("Content-Length")
                if expected is not None and (not expected.isdigit() or int(expected) > limit):
                    receipt["error"] = "response_too_large_or_invalid_length"
                else:
                    parts, size = [], 0
                    while size < limit:
                        if time.monotonic() - started > 90:
                            raise TimeoutError("History transfer deadline")
                        block = response.read(min(65536, limit - size))
                        if not block:
                            break
                        parts.append(block)
                        size += len(block)
                    receipt["bytes"] = size
                    if size == limit or expected is not None and size != int(expected):
                        receipt["error"] = "truncated_or_oversized_response"
                    else:
                        body = b"".join(parts)
                        ref = f"raw/{digest(body)}.bin"
                        if not (self.folder / ref).exists():
                            atomic_write(self.folder / ref, body)
                        receipt["raw_ref"] = ref
                        if response.code != 200:
                            receipt["error"] = "http_error"
        except (OSError, TimeoutError, http.client.HTTPException):
            receipt["error"] = "network_error"
            if "size" in locals():
                receipt["bytes"] = size
        receipt["received_at"] = now()
        return receipt


def collect(folder, config_path=None, mode="live", fetcher_factory=None, progress=lambda s: None):
    folder = folder.resolve()
    if folder in [ROOT / "data", ROOT / "data/aviation", ROOT / "data/early_warning"]:
        raise ValueError("Historia wymaga osobnego katalogu danych")
    if mode not in ("live", "fixture") or fetcher_factory and mode != "fixture":
        raise ValueError("Fetcher testowy wymaga trybu fixture")
    if mode == "fixture" and folder.is_relative_to(ROOT / "data") and not folder.is_relative_to(ROOT / "data/demo"):
        raise ValueError("Dane testowe nie mogą trafić do archiwum rzeczywistego")
    cfg = config(config_path)
    with locked(folder):
        check_mode(folder, mode)
        started = now()
        if any(instant(w["end"]) + timedelta(minutes=2) > instant(started) for w in windows(cfg)):
            raise ValueError("Poczekaj na zamknięcie wybranych okien historii")
        gate_path = folder / "request-state.json"
        if gate_path.exists() and instant(read_json(gate_path)["next_collection_at"]) > instant(started):
            raise ValueError("Kolejne pobranie najwcześniej: " + read_json(gate_path)["next_collection_at"])
        gate = {"next_collection_at": (instant(started) + timedelta(seconds=cfg["collection_interval_seconds"])).isoformat()}
        write_json(gate_path, gate)
        fetcher = fetcher_factory(folder, cfg) if fetcher_factory else Fetcher(folder, cfg)
        requests, stopped, last_start = [], False, None
        for window in windows(cfg):
            if stopped:
                stamp = now()
                requests.append({"window": window, "requested_at": stamp, "received_at": stamp, "http_status": None,
                                 "headers": {}, "bytes": 0, "raw_ref": None, "error": "not_requested_after_access_error"})
                continue
            if last_start is not None:
                time.sleep(max(0, cfg["request_interval_seconds"] - (time.monotonic() - last_start)))
            last_start = time.monotonic()
            r = fetcher.get(window)
            requests.append(r)
            progress(f"Historia {window['date']} / {window['chunk']:02d}: HTTP {r['http_status'] or 'brak'}; {r['bytes']} bajtów")
            if r["http_status"] is not None and 300 <= r["http_status"] < 500 and r["http_status"] != 404:
                stopped = True
                gate["next_collection_at"] = max(instant(gate["next_collection_at"]), instant(cooldown(r["headers"], r["received_at"]))).isoformat()
                write_json(gate_path, gate)
        finished = now()
        gate["next_collection_at"] = max(instant(gate["next_collection_at"]), instant(finished) + timedelta(seconds=cfg["collection_interval_seconds"])).isoformat()
        write_json(gate_path, gate)
        ident = "ahc-" + instant(finished).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        acq = {"version": "history-acquisition-1", "id": ident, "mode": mode, "started_at": started, "finished_at": finished,
               "config": cfg, "requests": requests}
        validate_acquisition(acq)
        target = folder / "collections" / (ident + ".json")
        if target.exists():
            raise ValueError("Pobranie już istnieje")
        write_json(target, acq)
        write_json(folder / "latest-collection.json", {"id": ident, "path": str(target.relative_to(folder)), "sha256": digest(acq)})
        return acq
