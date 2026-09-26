from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from statistics import median

from ..common import UTC, digest, instant
from .contracts import distance_bound_nm
from .store import raw_bytes


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def stamp(seconds):
    return datetime.fromtimestamp(seconds, UTC).isoformat(timespec="microseconds")


def strict_json(body):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("Non-finite JSON number")
    return json.loads(body, object_pairs_hook=pairs, parse_constant=invalid)


def parse_record(row, source_seconds, query_id, index):
    if not isinstance(row, dict) or not isinstance(row.get("hex"), str) or not re.fullmatch(r"~?[0-9a-fA-F]{6}", row["hex"]):
        raise ValueError("invalid_identifier")
    seen, seen_pos = row.get("seen"), row.get("seen_pos")
    if not number(seen) or seen < 0 or seen_pos is not None and (not number(seen_pos) or seen_pos < 0):
        raise ValueError("invalid_age")
    lat, lon = row.get("lat"), row.get("lon")
    if lat is not None and (not number(lat) or not -90 <= lat <= 90) or lon is not None and (not number(lon) or not -180 <= lon <= 180):
        raise ValueError("invalid_coordinates")
    position = [lon, lat] if lat is not None and lon is not None else None
    for field in ("alt_geom", "gs"):
        if row.get(field) is not None and not number(row[field]):
            raise ValueError("invalid_optional_number")
    alt = row.get("alt_baro")
    if alt is not None and alt != "ground" and not number(alt):
        raise ValueError("invalid_altitude")
    flags = row.get("dbFlags")
    if flags is not None and (type(flags) is not int or flags < 0):
        raise ValueError("invalid_database_flags")
    aircraft_type = row.get("t") or None
    if aircraft_type is not None and (not isinstance(aircraft_type, str) or not re.fullmatch(r"[A-Z0-9-]{1,8}", aircraft_type)):
        raise ValueError("invalid_type_code")
    position_source = row.get("type")
    if not isinstance(position_source, str) or not re.fullmatch(r"[a-z_]{1,32}", position_source):
        raise ValueError("invalid_position_source")
    return {"identifier": row["hex"].lower(), "position": position,
            "position_at": stamp(source_seconds - seen_pos) if position is not None and seen_pos is not None else None,
            "message_at": stamp(source_seconds - seen), "position_source": position_source,
            "barometric_altitude_ft": alt if number(alt) else None,
            "geometric_altitude_ft": row.get("alt_geom"), "ground_speed_knots": row.get("gs"),
            "on_ground": True if alt == "ground" else False if number(alt) else None,
            "aircraft_type_reported": aircraft_type, "military_flag_reported": bool(flags & 1) if flags is not None else None,
            "classification_source": "adsb:adsblol", "classification_status": "provider_reported_unverified",
            "operator": None, "operator_status": "not_established", "intent": None,
            "evidence": {"query_id": query_id, "row_index": index}}


def parse_response(body, receipt, cfg):
    data = strict_json(body)
    if not isinstance(data, dict) or not isinstance(data.get("ac"), list) or len(data["ac"]) > 20000:
        raise ValueError("invalid_envelope")
    if type(data.get("total")) is not int or data["total"] != len(data["ac"]) or data.get("msg") != "No error":
        raise ValueError("invalid_count_or_message")
    ts = data.get("now")
    if not number(ts) or not 946684800000 <= ts <= 4102444800000:
        raise ValueError("invalid_millisecond_timestamp")
    age = instant(receipt["received_at"]).timestamp() - ts / 1000
    if age < -cfg["future_tolerance_seconds"]:
        raise ValueError("future_response")
    rows, rejected = [], []
    for i, row in enumerate(data["ac"]):
        try:
            rows.append(parse_record(row, ts / 1000, receipt["query"]["id"], i))
        except (ValueError, OverflowError, OSError):
            rejected.append(i)
    return {"source_at": stamp(ts / 1000), "age_at_receipt_seconds": round(age, 3), "rows": rows,
            "reported_rows": len(data["ac"]), "rejected_row_indices": rejected}


def cells_for(cfg):
    w, s, e, n = cfg["region"]["bbox"]
    return [{"id": f"{lon}:{lat}", "bbox": [lon, lat, lon+1, lat+1], "fresh_identifiers": 0}
            for lat in range(s, n) for lon in range(w, e)]


def cell_id(position, cfg):
    w, s, e, n = cfg["region"]["bbox"]
    lon, lat = position
    return f"{min(math.floor(lon), e-1)}:{min(math.floor(lat), n-1)}"


def analyze_sample(sample, folder):
    cfg = sample["config"]
    cutoff = instant(sample["finished_at"])
    requests, candidates, good_queries = [], [], []
    for receipt in sample["requests"]:
        item = {"query_id": receipt["query"]["id"], "label": receipt["query"]["label"],
                "http_status": receipt["http_status"], "error": receipt["error"], "raw_ref": receipt["raw_ref"],
                "reported_rows": None, "rejected_row_indices": [], "source_at": None,
                "age_at_receipt_seconds": None, "age_at_sample_seconds": None, "usable_response": False}
        if receipt["http_status"] == 200 and not receipt["error"]:
            body = raw_bytes(folder, receipt["raw_ref"])
            try:
                parsed = parse_response(body, receipt, cfg)
            except (ValueError, TypeError, OverflowError) as exc:
                item["error"] = "invalid_contract"
            else:
                item.update({k: v for k, v in parsed.items() if k != "rows"})
                age = (cutoff - instant(parsed["source_at"])).total_seconds()
                item["age_at_sample_seconds"] = round(age, 3)
                item["usable_response"] = 0 <= age <= cfg["response_max_age_seconds"]
                if item["usable_response"]:
                    good_queries.append(receipt["query"])
                else:
                    item["error"] = "stale_or_future_response"
                for row in parsed["rows"]:
                    row["response_usable"] = item["usable_response"]
                    candidates.append(row)
        requests.append(item)
    grouped = defaultdict(list)
    for row in candidates:
        grouped[row["identifier"]].append(row)
    w, s, e, n = cfg["region"]["bbox"]
    cells = cells_for(cfg)
    by_cell = {c["id"]: c for c in cells}
    selected, quality = [], Counter()
    for ident in sorted(grouped):
        # Select globally BEFORE filtering to bbox: do not resurrect an older
        # in-region position when the latest known position is outside it.
        rows = grouped[ident]
        row = max(rows, key=lambda r: (r["position_at"] or "", r["message_at"], r["evidence"]["query_id"], -r["evidence"]["row_index"]))
        row = {**row, "occurrences": len(rows), "position_age_seconds": None}
        position = row["position"]
        if position is None:
            status = "missing_position"
        elif not (w <= position[0] <= e and s <= position[1] <= n):
            status = "outside_region"
        elif row["position_at"] is None:
            status = "unknown_position_age"
        else:
            age = (cutoff - instant(row["position_at"])).total_seconds()
            row["position_age_seconds"] = round(age, 3)
            status = "fresh" if row["response_usable"] and 0 <= age <= cfg["position_max_age_seconds"] else "stale_or_future_position"
        row["quality"] = status
        quality[status] += 1
        if status == "fresh":
            by_cell[cell_id(position, cfg)]["fresh_identifiers"] += 1
        selected.append(row)
    for cell in cells:
        cell["query_scope_available"] = any(distance_bound_nm(q["lat"], q["lon"], cell["bbox"]) <= q["radius_nm"] - 1 for q in good_queries)
        cell["status"] = "observed" if cell["fresh_identifiers"] else "no_observation" if cell["query_scope_available"] else "query_gap"
        if not cell["query_scope_available"] and not cell["fresh_identifiers"]:
            cell["fresh_identifiers"] = None
    valid_count = sum(r["usable_response"] for r in requests)
    rejected = sum(len(r["rejected_row_indices"]) for r in requests)
    status = "unavailable" if valid_count == 0 else "partial" if valid_count != len(requests) or rejected else "ok"
    fresh = [r for r in selected if r["quality"] == "fresh"]
    ages = sorted(r["position_age_seconds"] for r in fresh)
    return {"sample_id": sample["sample_id"], "started_at": sample["started_at"], "finished_at": sample["finished_at"],
            "status": status, "requests": requests, "records": selected, "cells": cells,
            "content_fingerprint": digest([r["raw_ref"] for r in sample["requests"]]),
            "metrics": {"usable_queries": valid_count, "planned_queries": len(requests),
                        "rows_received": sum(r["reported_rows"] or 0 for r in requests), "invalid_rows": rejected,
                        "unique_identifiers_in_responses": len(selected), "overlap_rows_removed": len(candidates) - len(selected),
                        "fresh_in_region": len(fresh) if valid_count else None,
                        "fresh_airborne_reported": sum(r["on_ground"] is False for r in fresh),
                        "fresh_on_ground_reported": sum(r["on_ground"] is True for r in fresh),
                        "ground_status_unknown": sum(r["on_ground"] is None for r in fresh),
                        "military_flag_yes": sum(r["military_flag_reported"] is True for r in fresh),
                        "military_flag_absent": sum(r["military_flag_reported"] is False for r in fresh),
                        "military_flag_unknown": sum(r["military_flag_reported"] is None for r in fresh),
                        "operator_established": 0,
                        "missing_position": quality["missing_position"], "outside_region": quality["outside_region"],
                        "unknown_position_age": quality["unknown_position_age"], "stale_or_future_position": quality["stale_or_future_position"],
                        "position_age_median_seconds": round(median(ages), 3) if ages else None,
                        "position_age_p95_seconds": ages[math.ceil(.95 * len(ages))-1] if ages else None,
                        "observed_cells": sum(c["status"] == "observed" for c in cells),
                        "empty_observed_scope_cells": sum(c["status"] == "no_observation" for c in cells),
                        "query_gap_cells": sum(c["status"] == "query_gap" for c in cells),
                        "total_cells": len(cells),
                        "reported_aircraft_types": dict(sorted(Counter(r["aircraft_type_reported"] or "unknown" for r in fresh).items()))}}
