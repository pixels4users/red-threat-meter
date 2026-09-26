from __future__ import annotations

from datetime import datetime
from math import asin, cos, radians, sin, sqrt

from jsonschema import Draft202012Validator, FormatChecker

from ..common import ROOT, UTC, digest, instant, read_json


def now():
    return datetime.now(UTC).isoformat(timespec="microseconds")


def validate(name, payload):
    Draft202012Validator(read_json(ROOT / f"schemas/aviation/{name}.schema.json"),
                         format_checker=FormatChecker()).validate(payload)


def distance_bound_nm(lat, lon, box):
    """Conservative spherical bound for EVERY point in a small WGS84 rectangle."""
    west, south, east, north = box
    dlat = max(abs(lat - south), abs(lat - north))
    dlon = max(abs(lon - west), abs(lon - east))
    nearest_equator = 0 if south <= 0 <= north else min(abs(south), abs(north))
    a = sin(radians(dlat) / 2) ** 2 + cos(radians(lat)) * cos(radians(nearest_equator)) * sin(radians(dlon) / 2) ** 2
    return 2 * 6371008.8 / 1852 * asin(sqrt(min(1, a)))


def queries(cfg):
    w, s, e, n = cfg["region"]["bbox"]
    x, y = (w + e) / 2, (s + n) / 2
    boxes = [(w, s, x, y), (x, s, e, y), (w, y, x, n), (x, y, e, n)]
    names = ["południowy zachód", "południowy wschód", "północny zachód", "północny wschód"]
    result = []
    for i, (a, b, c, d) in enumerate(boxes):
        lat, lon = (b + d) / 2, (a + c) / 2
        if distance_bound_nm(lat, lon, (a, b, c, d)) > 249:
            raise ValueError("Region exceeds the four-query footprint")
        result.append({"id": f"q{i+1}", "label": names[i], "lat": lat, "lon": lon, "radius_nm": 250,
                       "assigned_bbox": [a, b, c, d],
                       "url": cfg["source"]["base_url"] + f"{lat:g}/{lon:g}/250"})
    return result


def config(path=None):
    cfg = read_json(path or ROOT / "config/aviation.json")
    validate_config(cfg)
    return cfg


def validate_config(cfg):
    validate("config", cfg)
    w, s, e, n = cfg["region"]["bbox"]
    if not (-180 <= w < e <= 180 and -80 <= s < n <= 80 and (e-w)*(n-s) <= 200):
        raise ValueError("Invalid or excessive regional scope")
    queries(cfg)


def identity(sample):
    return "avs_" + digest({k: v for k, v in sample.items() if k != "sample_id"})[:24]


def validate_sample(sample):
    validate("sample", sample)
    validate_config(sample["config"])
    if sample["sample_id"] != identity(sample):
        raise ValueError("Sample identity does not match its content")
    planned = queries(sample["config"])
    if [r["query"] for r in sample["requests"]] != planned:
        raise ValueError("Incomplete or changed query plan")
    start, end = instant(sample["started_at"]), instant(sample["finished_at"])
    if end < start:
        raise ValueError("Collection ends before it starts")
    for r in sample["requests"]:
        if not start <= instant(r["requested_at"]) <= instant(r["received_at"]) <= end:
            raise ValueError("Request outside collection interval")
        if r["http_status"] == 200 and not r["error"] and not r["raw_ref"]:
            raise ValueError("Successful request lacks raw evidence")
