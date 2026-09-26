"""Descriptive, paired-cell GNSS comparison. No alert threshold or prediction."""
from __future__ import annotations

from datetime import timedelta
from statistics import median, quantiles

from ..common import digest, instant

SPEC = {
    "version": "gnss-comparison-1",
    "metric": "share_of_cells_with_gpsjam_formula_gte_10_pct",
    "reference": "strictly_prior_days_in_latest_provider_regime_without_suspect_flag",
    "cohort": "same_cells_present_above_sample_floor_on_target_and_all_reference_days",
    "sensitivity_sample_floors": [1, 5, 10, 20],
    "quartile_method": "inclusive_linear_interpolation",
    "detector_enabled": False,
    "normality_verified": False,
}


def compare(records, as_of, expected_day):
    cutoff = instant(as_of)
    known = [r for r in records if r["observation"]["data"]["type"] == "gnss_daily"
             and instant(r["last_fetched_at"]) <= cutoff
             and instant(r["observation"]["times"]["first_seen_at"]) <= cutoff
             and instant(r["observation"]["times"]["observed_end"]) <= cutoff
             and r["observation"]["data"]["day"] <= expected_day]
    known.sort(key=lambda r: r["observation"]["data"]["day"])
    result = {"spec": SPEC, "status": "latest_day_missing", "target_day": expected_day,
              "target_observation_id": None, "reference_ids": [], "reference_days": [],
              "excluded_suspect_days": [], "regime_boundary_day": None, "missing_reference_days": [],
              "variants": [], "comparison_id": None,
              "limitations": ["Odniesienie opisuje obserwowaną historię, nie potwierdzony stan normalny.",
                              "Stałe komórki nie oznaczają stałej liczby lub składu samolotów; pozostaje wpływ pokrycia i tras.",
                              "Historia jest retrospektywna; nie sprawdzono sezonowości, ćwiczeń ani skuteczności ostrzeżeń.",
                              "Wynik nie zmienia statusu sygnału ani RTB; odchylenie nie jest prawdopodobieństwem zagrożenia."]}
    if not known or known[-1]["observation"]["data"]["day"] != expected_day:
        return result
    target = known[-1]["observation"]
    result["target_observation_id"] = target["observation_id"]
    if target["data"]["manifest_suspect"]:
        result["status"] = "target_suspect"
        return result
    reference = []
    for record in reversed(known[:-1]):
        obs = record["observation"]
        if (obs["source_config_hash"], obs["data"]["provider"], obs["dependency_groups"]) != (target["source_config_hash"], target["data"]["provider"], target["dependency_groups"]):
            result["regime_boundary_day"] = obs["data"]["day"]
            break
        if obs["data"]["manifest_suspect"]:
            result["excluded_suspect_days"].append(obs["data"]["day"])
            continue
        reference.append(obs)
    reference.reverse()
    result["reference_ids"] = [o["observation_id"] for o in reference]
    result["reference_days"] = [o["data"]["day"] for o in reference]
    if not reference:
        result["status"] = "no_prior_comparable_days"
        return result
    earliest = instant(reference[0]["times"]["observed_start"])
    latest = instant(target["times"]["observed_start"])
    included = set(result["reference_days"]) | set(result["excluded_suspect_days"])
    result["missing_reference_days"] = [str((earliest + timedelta(days=i)).date()) for i in range((latest - earliest).days)
                                        if str((earliest + timedelta(days=i)).date()) not in included]
    for floor in SPEC["sensitivity_sample_floors"]:
        maps = [{c["h3"]: c for c in o["data"]["cells"] if c["sample"] >= floor} for o in [*reference, target]]
        common = set(maps[0]).intersection(*(set(cells) for cells in maps[1:]))
        ids = sorted(common)
        variant = {"sample_floor": floor, "cells": ids, "cell_count": len(ids),
                   "target_eligible_cells": len(maps[-1]), "reference_day_count": len(reference),
                   "status": "no_common_cells", "series": [], "current_pct": None, "reference_median_pct": None,
                   "difference_pp": None, "reference_q1_pct": None, "reference_q3_pct": None,
                   "reference_min_pct": None, "reference_max_pct": None, "reference_smaller_days": None,
                   "reference_equal_days": None, "reference_larger_days": None}
        if ids:
            counts = [sum(10 * (cells[h]["bad"] - 1) >= cells[h]["sample"] for h in ids) for cells in maps]
            percentages = [100 * n / len(ids) for n in counts]
            past, current = percentages[:-1], percentages[-1]
            q1, _, q3 = quantiles(past, n=4, method="inclusive") if len(past) > 1 else [past[0]] * 3
            variant.update(status="descriptive_only", current_pct=round(current, 4),
                           reference_median_pct=round(median(past), 4), difference_pp=round(current - median(past), 4),
                           reference_q1_pct=round(q1, 4), reference_q3_pct=round(q3, 4),
                           reference_min_pct=round(min(past), 4), reference_max_pct=round(max(past), 4),
                           reference_smaller_days=sum(n < counts[-1] for n in counts[:-1]),
                           reference_equal_days=sum(n == counts[-1] for n in counts[:-1]),
                           reference_larger_days=sum(n > counts[-1] for n in counts[:-1]))
            variant["series"] = [{"day": o["data"]["day"], "observation_id": o["observation_id"],
                                  "high_cells": count, "share_pct": round(pct, 4),
                                  "median_cell_sample": median([cells[h]["sample"] for h in ids]), "is_reference": i < len(reference)}
                                 for i, (o, cells, count, pct) in enumerate(zip([*reference, target], maps, counts, percentages))]
        result["variants"].append(variant)
    result["status"] = "descriptive_only" if any(v["cell_count"] for v in result["variants"]) else "no_common_cells"
    result["comparison_id"] = "ewc_" + digest(result)[:24]
    return result
