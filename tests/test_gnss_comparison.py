from copy import deepcopy
from datetime import date, timedelta

import pytest

from osint_dashboard.early_warning.comparison import compare

AS_OF = "2026-09-23T12:00:00+00:00"
TARGET = "2026-09-22"


def record(day, cells, provider="merged", suspect=False):
    # Minimal input for the pure comparison function; no synthetic data on disk.
    return {"last_fetched_at": AS_OF, "observation": {
        "observation_id": "fixture-" + day, "source_config_hash": "fixture-config",
        "dependency_groups": [provider],
        "times": {"first_seen_at": AS_OF, "observed_start": day + "T00:00:00Z",
                  "observed_end": str(date.fromisoformat(day) + timedelta(days=1)) + "T00:00:00Z"},
        "data": {"type": "gnss_daily", "day": day, "provider": provider, "manifest_suspect": suspect,
                 "cells": [{"h3": name, "sample": sample, "bad": bad} for name, sample, bad in cells]}}}


def variant(result, floor=5):
    return next(v for v in result["variants"] if v["sample_floor"] == floor)


def test_coverage_only_change_does_not_create_a_paired_cell_change():
    prior = record("2026-09-21", [("a", 10, 2), ("b", 10, 0)])
    current = record(TARGET, [("a", 10, 2)])
    result = compare([prior, current], AS_OF, TARGET)
    v = variant(result)
    # Unpaired share would jump from 50% to 100%; the common cell is unchanged.
    assert v["cells"] == ["a"] and v["difference_pp"] == 0
    assert v["current_pct"] == v["reference_median_pct"] == 100
    assert result["spec"]["detector_enabled"] is False
    assert result["spec"]["normality_verified"] is False


def test_target_not_in_reference_and_change_is_percentage_points():
    cells = [("a", 10, 0), ("b", 10, 0)]
    data = [record("2026-09-20", cells), record("2026-09-21", cells), record(TARGET, [("a", 10, 2), ("b", 10, 0)])]
    result = compare(data, AS_OF, TARGET)
    v = variant(result)
    assert result["reference_days"] == ["2026-09-20", "2026-09-21"]
    assert v["reference_median_pct"] == 0 and v["difference_pp"] == 50
    assert v["reference_q1_pct"] == v["reference_q3_pct"] == 0
    assert v["reference_smaller_days"] == 2
    assert [s["is_reference"] for s in v["series"]] == [True, True, False]
    assert compare(list(reversed(data)), AS_OF, TARGET) == result


def test_provider_reversion_stops_at_intervening_regime():
    cells = [("a", 20, 5)]
    data = [record("2026-09-19", cells), record("2026-09-20", cells, "adsbexchange"),
            record("2026-09-21", cells), record(TARGET, cells)]
    result = compare(data, AS_OF, TARGET)
    assert result["reference_days"] == ["2026-09-21"]
    assert result["regime_boundary_day"] == "2026-09-20"


@pytest.mark.parametrize("field,value", [("source_config_hash", "other"), ("dependency_groups", ["other"])])
def test_incompatible_definitions_stop_reference(field, value):
    cells = [("a", 20, 5)]
    prior = record("2026-09-21", cells)
    prior["observation"][field] = value
    result = compare([prior, record(TARGET, cells)], AS_OF, TARGET)
    assert result["status"] == "no_prior_comparable_days"


def test_suspect_days_and_gaps_remain_explicit():
    cells = [("a", 20, 5)]
    result = compare([record("2026-09-18", cells), record("2026-09-20", cells, suspect=True),
                      record("2026-09-21", cells), record(TARGET, cells)], AS_OF, TARGET)
    assert result["reference_days"] == ["2026-09-18", "2026-09-21"]
    assert result["excluded_suspect_days"] == ["2026-09-20"]
    assert result["missing_reference_days"] == ["2026-09-19"]
    assert compare([record(TARGET, cells, suspect=True)], AS_OF, TARGET)["status"] == "target_suspect"


def test_absence_low_sample_and_missing_latest_are_not_zeros():
    cells = [("a", 4, 2)]
    result = compare([record("2026-09-21", cells), record(TARGET, cells)], AS_OF, TARGET)
    assert variant(result)["cell_count"] == 0 and variant(result)["current_pct"] is None
    assert variant(result, 1)["current_pct"] == 100
    result = compare([record("2026-09-21", cells), record(TARGET, [])], AS_OF, TARGET)
    assert result["status"] == "no_common_cells"
    assert compare([record("2026-09-21", cells)], AS_OF, TARGET)["status"] == "latest_day_missing"


def test_later_retrieval_and_incomplete_day_do_not_leak_into_comparison():
    cells = [("a", 10, 0)]
    earlier = record("2026-09-21", cells)
    current = record(TARGET, cells)
    for field in ("first_seen_at", "observed_end"):
        future = deepcopy(current)
        future["observation"]["times"][field] = "2026-09-24T00:00:00Z"
        assert compare([earlier, future], AS_OF, TARGET)["status"] == "latest_day_missing"
    future = deepcopy(current)
    future["last_fetched_at"] = "2026-09-24T00:00:00Z"
    assert compare([earlier, future], AS_OF, TARGET)["status"] == "latest_day_missing"
    future_day = record("2026-09-23", cells)
    assert compare([earlier, current, future_day], AS_OF, TARGET) == compare([earlier, current], AS_OF, TARGET)
