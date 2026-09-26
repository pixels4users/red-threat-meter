from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from functools import lru_cache

import h3
from jsonschema import Draft202012Validator, FormatChecker

from ..collect import allowed_url
from ..common import ROOT, digest, instant, read_json


def validate(name: str, payload: dict) -> None:
    schema = read_json(ROOT / f"schemas/early-warning/{name}.schema.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)


def config(path=None) -> dict:
    result = read_json(path or ROOT / "config/early-warning.json")
    if result["role"] != "observations_only" or result["version"] != "early-warning-1":
        raise ValueError("Unsupported observation configuration")
    if not 1 <= result["refresh_days"] <= result["history_days"] <= 90:
        raise ValueError("History must be bounded to 1–90 days")
    if not 1 <= result["check_max_age_hours"] <= 168:
        raise ValueError("Invalid check freshness limit")
    region = result["region"]
    west, south, east, north = region["bbox"]
    if not (-180 <= west < east <= 180 and -85 <= south < north <= 85):
        raise ValueError("Invalid research bbox")
    if region["h3_resolution"] != 4 or region["selection"] != "h3_cell_center_in_bbox":
        raise ValueError("Pilot supports H3 resolution 4 and center selection only")
    if not 1 <= region["min_cell_sample"] <= 10000:
        raise ValueError("Invalid sample floor")
    # Bound the area before allocating a possibly enormous grid.
    if (east - west) * (north - south) > 1000:
        raise ValueError("Research bbox too large for the local pilot")
    ids = [s["id"] for s in result["sources"]]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("Duplicate or empty source definitions")
    expected = {
        "gpsjam": ("gpsjam_manifest_csv_v1", "gpsjam.org", "/data/", "https://gpsjam.org/data/manifest.csv"),
        "belzhd_public": ("belzhd_rss_content_v1", "belzhd.info", "/", "https://belzhd.info/feed/"),
    }
    for source in result["sources"]:
        if source["id"] not in expected:
            raise ValueError("Unknown early-warning source")
        adapter, host, prefix, url = expected[source["id"]]
        if (source["adapter"], source["allowed_hosts"], source["path_prefix"], source["url"]) != (adapter, [host], prefix, url):
            raise ValueError("Source definition differs from the supported public adapter")
        allowed_url(source["url"], source)
    return result


def source_hash(source: dict, cfg: dict) -> str:
    return digest({"source": source, "region": cfg["region"] if source["id"] == "gpsjam" else None})


@lru_cache(maxsize=8)
def region_cells(bbox: tuple) -> tuple[str, ...]:
    west, south, east, north = bbox
    polygon = {"type": "Polygon", "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]]}
    return tuple(sorted(h3.geo_to_cells(polygon, 4)))


def identity(observation: dict) -> str:
    semantic = deepcopy(observation)
    for key in ("observation_id", "raw_refs"):
        semantic.pop(key, None)
    # Fetching a changed RSS envelope or updated manifest is a new receipt, not
    # necessarily a new version of this article or regional measurement.
    for key in ("first_seen_at", "fetched_at"):
        semantic["times"].pop(key, None)
    return "ewo_" + digest(semantic)[:24]


def validate_observation(obs: dict) -> None:
    validate("observation", obs)
    if identity(obs) != obs["observation_id"]:
        raise ValueError("Observation identity differs from its content")
    times = obs["times"]
    acquired = instant(times["fetched_at"])
    if instant(times["first_seen_at"]) > acquired:
        raise ValueError("First observation cannot follow its fetch")
    if times["published_at"] and instant(times["published_at"]) > acquired:
        raise ValueError("Publication is dated in the future")
    data = obs["data"]
    if data["type"] == "publication":
        if obs["source_id"] != "belzhd_public" or times["observed_start"] or times["observed_end"] or times["observed_precision"] != "unknown":
            raise ValueError("Publication date must not become an event date")
        if obs["location"]["bbox"] is not None or obs["location"]["precision"] != "unknown":
            raise ValueError("Publication locations require a separate evidence review")
        if obs["dependency_groups"] != ["publisher:belzhd"]:
            raise ValueError("Website and channel share one publisher")
    else:
        if obs["source_id"] != "gpsjam" or times["published_at"] is not None:
            raise ValueError("CSV observation is not an article publication")
        start, end = instant(times["observed_start"]), instant(times["observed_end"])
        if start.hour or start.minute or start.second or end - start != timedelta(days=1) or end > acquired:
            raise ValueError("GNSS interval must be a completed UTC day")
        if start.date() != date.fromisoformat(data["day"]) or times["observed_precision"] != "utc_day":
            raise ValueError("Incorrect daily interval")
        expected = region_cells(tuple(obs["location"]["bbox"]))
        if obs["location"]["precision"] != "h3_grid_bbox" or list(expected) != data["expected_cells"]:
            raise ValueError("Grid coverage does not match the declared region")
        origins = {"adsbexchange": ["adsb:adsbexchange"], "airplaneslive": ["adsb:airplaneslive"],
                   "merged": ["adsb:adsbexchange", "adsb:airplaneslive"]}
        if obs["dependency_groups"] != origins[data["provider"]]:
            raise ValueError("Incorrect measurement lineage")
        seen = set()
        for cell in data["cells"]:
            if cell["h3"] not in expected or cell["h3"] in seen:
                raise ValueError("Duplicate or out-of-region H3 cell")
            seen.add(cell["h3"])
            sample = cell["good"] + cell["bad"]
            if sample != cell["sample"] or cell["source_adjusted_pct"] != round(100 * (cell["bad"] - 1) / sample, 6):
                raise ValueError("Incorrect sample or GPSJAM formula")
