from __future__ import annotations

import gzip
import io
import math
import struct
from collections import Counter
from datetime import datetime
from statistics import median

from ...common import UTC, instant

MAGIC = 0x0E7F7C9D
SOURCES = ("adsb_icao", "adsb_icao_nt", "adsr_icao", "tisb_icao", "adsc", "mlat", "other", "mode_s",
           "adsb_other", "adsr_other", "tisb_trackfile", "tisb_other", "mode_ac")
ENTRY = struct.Struct("<IiiI")
WORDS = struct.Struct("<4I")


def stamp(milliseconds):
    return datetime.fromtimestamp(milliseconds / 1000, UTC).isoformat(timespec="milliseconds")


def position(words):
    address, lat, lon, packed = words
    if lat >= 1 << 30:
        return None  # callsign/squawk metadata has no position
    if not (-90000000 <= lat <= 90000000 and -180000000 <= lon <= 180000000) or address & 0x06000000:
        raise ValueError("invalid_position_record")
    kind = (address >> 27) & 31
    identifier = ("~" if address & 0x1000000 else "") + f"{address & 0xffffff:06x}"
    altitude = packed & 65535
    altitude -= 65536 if altitude >= 32768 else 0
    speed = packed >> 16
    speed -= 65536 if speed >= 32768 else 0
    if speed < -1:
        raise ValueError("invalid_speed")
    return {"identifier": identifier, "lat": lat / 1e6, "lon": lon / 1e6,
            "altitude_ft": None if altitude in (-123, -124) else altitude * 25,
            "altitude_reference": "barometric_or_geometric_unspecified",
            "on_ground": True if altitude == -123 else None if altitude == -124 else False,
            "ground_speed_knots": None if speed == -1 else speed / 10,
            "position_source": SOURCES[kind] if kind < len(SOURCES) else "unknown",
            "position_at": None, "military_flag": None, "aircraft_type": None, "operator": None}


def decode(body, window, cfg):
    if not body.startswith(b"\x1f\x8b"):
        raise ValueError("expected_gzip")
    with gzip.GzipFile(fileobj=io.BytesIO(body)) as compressed:
        data = compressed.read(cfg["max_decoded_bytes"] + 1)
    if len(data) > cfg["max_decoded_bytes"]:
        raise ValueError("decoded_size_limit")
    if not data or len(data) % 16:
        raise ValueError("invalid_record_alignment")
    size = len(data) // 16
    count = WORDS.unpack_from(data)[0]
    if not 1 <= count <= 1800 or count >= size:
        raise ValueError("invalid_index_length")
    offsets = []
    for i in range(count):
        offset, b, c, d = WORDS.unpack_from(data, i * 16)
        if b or c or d or not count <= offset < size or offsets and offset <= offsets[-1]:
            raise ValueError("invalid_index")
        offsets.append(offset)
    if offsets[0] != count:
        raise ValueError("invalid_first_offset")
    expected_start = int(instant(window["start"]).timestamp() * 1000)
    expected_end = int(instant(window["end"]).timestamp() * 1000)
    headers, interval = [], None
    for offset in offsets:
        magic, high, low, step = WORDS.unpack_from(data, offset * 16)
        ts = high * 2**32 + low
        if magic != MAGIC or not 1000 <= step <= 60000 or 1800000 % step:
            raise ValueError("invalid_slice_header")
        if not expected_start <= ts < expected_end or (ts - expected_start) % step:
            raise ValueError("slice_outside_requested_window")
        if interval is not None and step != interval or headers and ts <= headers[-1]:
            raise ValueError("inconsistent_slice_order_or_interval")
        interval = step
        headers.append(ts)
    w, s, e, n = cfg["bbox"]
    cells = {f"{lon}:{lat}": {"id": f"{lon}:{lat}", "bbox": [lon, lat, lon+1, lat+1],
                              "intervals_with_observations": 0, "_ids": set()}
             for lat in range(s, n) for lon in range(w, e)}
    totals, all_ids, frames, source_counts = Counter(), set(), [], Counter()
    rejected = []
    for index, offset in enumerate(offsets):
        stop = offsets[index+1] if index+1 < count else size
        records, conflicts, q = {}, set(), Counter()
        for entry in range(offset + 1, stop):
            words = ENTRY.unpack_from(data, entry * 16)
            if words[0] == MAGIC:
                raise ValueError("unindexed_slice_marker")
            try:
                row = position(words)
            except ValueError as exc:
                q["invalid_rows"] += 1
                if len(rejected) < 100:
                    rejected.append({"record_index": entry, "slice_at": stamp(headers[index]), "reason": str(exc)})
                continue
            if row is None:
                q["metadata_rows"] += 1
                continue
            q["position_rows"] += 1
            ident = row["identifier"]
            if ident in records:
                q["duplicate_rows"] += 1
                if row != records[ident]:
                    conflicts.add(ident)
            else:
                records[ident] = row
        q["conflicting_identifiers"] = len(conflicts)
        for ident in conflicts:
            del records[ident]  # no per-point time with which to resolve the conflict
        region = [r for r in records.values() if w <= r["lon"] <= e and s <= r["lat"] <= n]
        ids = sorted(r["identifier"] for r in region)
        all_ids.update(ids)
        visited = set()
        for row in region:
            cell = f"{min(math.floor(row['lon']),e-1)}:{min(math.floor(row['lat']),n-1)}"
            cells[cell]["_ids"].add(row["identifier"])
            visited.add(cell)
            source_counts[row["position_source"]] += 1
        for cell in visited:
            cells[cell]["intervals_with_observations"] += 1
        q["unknown_source_rows"] = sum(r["position_source"] == "unknown" for r in records.values())
        totals.update(q)
        frames.append({"start": stamp(headers[index]), "end": stamp(headers[index] + interval),
                       "identifiers": ids, "identifiers_in_region": len(ids), "global_identifiers": len(records),
                       "on_ground_reported": sum(r["on_ground"] is True for r in region),
                       "ground_status_unknown": sum(r["on_ground"] is None for r in region),
                       "observed_cells": len(visited), "quality": dict(q)})
    expected_count = (expected_end - expected_start) // interval
    missing = sorted(set(range(expected_start, expected_end, interval)) - set(headers))
    for cell in cells.values():
        cell["unique_identifiers"] = len(cell.pop("_ids"))
        cell["intervals_observed_in_file"] = count
        cell["expected_intervals"] = expected_count
        cell["receiver_coverage"] = "unknown"
        cell["status"] = "observed" if cell["intervals_with_observations"] else "no_observation"
    numbers = [f["identifiers_in_region"] for f in frames]
    return {"window": window, "status": "partial" if missing or totals["invalid_rows"] or totals["conflicting_identifiers"] or totals["unknown_source_rows"] else "ok",
            "decoded_bytes": len(data), "interval_seconds": interval / 1000,
            "intervals": count, "expected_intervals": expected_count, "missing_intervals": [stamp(x) for x in missing],
            "empty_global_intervals": sum(f["global_identifiers"] == 0 for f in frames),
            "empty_region_intervals": numbers.count(0), "unique_identifiers_in_window": len(all_ids),
            "identifiers_per_interval": {"min": min(numbers), "median": median(numbers), "max": max(numbers)},
            "observed_cells": sum(c["status"] == "observed" for c in cells.values()),
            "total_cells": len(cells), "quality": dict(totals), "position_sources": dict(sorted(source_counts.items())),
            "cells": list(cells.values()), "frames": frames, "rejected_record_examples": rejected,
            "position_age_available": False, "aircraft_classification_available": False,
            "provider_instance": None, "first_available_at": None}
