from __future__ import annotations

import re
from datetime import datetime, timedelta

from jsonschema import Draft202012Validator, FormatChecker

from ...common import ROOT, UTC, digest, instant, read_json


def now():
    return datetime.now(UTC).isoformat(timespec="microseconds")


def config(path=None):
    cfg = read_json(path or ROOT / "config/aviation-history.json")
    validate_config(cfg)
    return cfg


def validate(name, value):
    Draft202012Validator(read_json(ROOT / f"schemas/aviation/history/{name}.schema.json"), format_checker=FormatChecker()).validate(value)


def validate_config(cfg):
    validate("config", cfg)
    w, s, e, n = cfg["bbox"]
    if not (-180 <= w < e <= 180 and -80 <= s < n <= 80 and (e-w)*(n-s) <= 200):
        raise ValueError("Nieprawidłowy region badania historii")
    if len(cfg["windows"]) * cfg["max_response_bytes"] > cfg["max_total_bytes"]:
        raise ValueError("Plan przekracza budżet pobrania")
    dates = [datetime.fromisoformat(x["date"]) for x in cfg["windows"]]
    if max(dates) - min(dates) > timedelta(days=30):
        raise ValueError("Pilotaż obejmuje najwyżej 30 dni między wybranymi oknami")


def windows(cfg):
    result = []
    for item in sorted(cfg["windows"], key=lambda x: (x["date"], x["chunk"])):
        start = datetime.fromisoformat(item["date"]).replace(tzinfo=UTC) + timedelta(minutes=30 * item["chunk"])
        result.append({**item, "start": start.isoformat(), "end": (start + timedelta(minutes=30)).isoformat(),
                       "url": cfg["source"] + item["date"].replace("-", "/") + f"/heatmap/{item['chunk']:02d}.bin.ttf"})
    return result


def raw_bytes(folder, ref):
    if not isinstance(ref, str) or not re.fullmatch(r"raw/[0-9a-f]{64}\.bin", ref):
        raise ValueError("Nieprawidłowa ścieżka dowodu")
    path = folder / ref
    if not path.resolve().is_relative_to((folder / "raw").resolve()):
        raise ValueError("Dowód poza archiwum")
    body = path.read_bytes()
    if digest(body) != path.stem:
        raise ValueError("Zmieniona surowa odpowiedź")
    return body


def validate_acquisition(acq):
    validate("acquisition", acq)
    validate_config(acq["config"])
    if acq["version"] != "history-acquisition-1" or acq["mode"] not in ("live", "fixture"):
        raise ValueError("Nieprawidłowy tryb archiwum")
    if not re.fullmatch(r"ahc-\d{8}T\d{6}Z-[0-9a-f]{8}", acq["id"]):
        raise ValueError("Nieprawidłowy identyfikator pobrania")
    if [r["window"] for r in acq["requests"]] != windows(acq["config"]):
        raise ValueError("Odpowiedzi nie pasują do zamrożonego planu")
    start, end = instant(acq["started_at"]), instant(acq["finished_at"])
    if start > end:
        raise ValueError("Nieprawidłowy czas pobrania")
    total = 0
    for r in acq["requests"]:
        if not start <= instant(r["requested_at"]) <= instant(r["received_at"]) <= end:
            raise ValueError("Odczyt poza czasem pobrania")
        if instant(r["window"]["end"]) + timedelta(minutes=2) > start:
            raise ValueError("Okno jeszcze nie było zamknięte w chwili pobierania")
        if type(r["bytes"]) is not int or not 0 <= r["bytes"] <= acq["config"]["max_response_bytes"]:
            raise ValueError("Nieprawidłowy rozmiar odpowiedzi")
        total += r["bytes"]
        if r["http_status"] == 200 and not r["error"] and not r["raw_ref"]:
            raise ValueError("Brak źródła dla poprawnej odpowiedzi")
    if total > acq["config"]["max_total_bytes"]:
        raise ValueError("Przekroczony budżet archiwum")
