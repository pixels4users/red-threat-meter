from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .common import UTC, digest, instant
from .review import validate_evidence


def window_for(as_of: str, config: dict) -> dict:
    zone = ZoneInfo(config["timezone"])
    end = instant(as_of)
    first_day = end.astimezone(zone).date() - timedelta(days=config["window_days"] - 1)
    start = datetime.combine(first_day, time.min, tzinfo=zone).astimezone(UTC)
    return {"start": start.isoformat(), "end": end.isoformat(), "timezone": config["timezone"],
            "definition": config["window_definition"]}


def alert_for(value: int | None, config: dict) -> dict:
    thresholds = config.get("thresholds", [])
    if value is None:
        return {"status": "not_assessed", "triggered_rules": [], "calibrated": False}
    triggered = [t["id"] for t in thresholds if value > t["above"]]
    return {"status": "analyst_review_required" if triggered else "no_threshold_triggered",
            "triggered_rules": triggered, "calibrated": False}


def score(inputs: dict) -> tuple[dict, dict]:
    config, as_of = inputs["scoring"], inputs["as_of"]
    window = window_for(as_of, config)
    zone = ZoneInfo(config["timezone"])
    first = instant(window["start"]).astimezone(zone).date()
    last = instant(as_of).astimezone(zone).date()
    materials = {m["material_id"]: m for m in inputs["materials"]}
    current_ids = set(inputs["latest_material_ids"])
    outcomes = {s["source_id"]: s for s in inputs["source_checks"]}
    required = [s for s in inputs["source_config"]["sources"] if s["enabled"] and s["required"]]
    blockers = []
    for source in required:
        check = outcomes.get(source["id"])
        if check is None or check["status"] != "ok":
            blockers.append(f"source_unavailable_or_partial:{source['id']}")
        elif check.get("source_definition_hash") != digest(source):
            blockers.append(f"source_config_changed:{source['id']}")
        elif not check["window_complete"]:
            blockers.append(f"source_window_incomplete:{source['id']}")
        elif abs((instant(as_of) - instant(check["checked_at"])).total_seconds()) > 8 * 3600:
            blockers.append(f"source_check_stale:{source['id']}")
    if not required:
        blockers.append("no_required_sources_configured")
    pending = []
    for candidate in inputs["candidates"]:
        # An old publication can contain a fresh update. Only a review can
        # establish whether its event lies outside the scoring window.
        if candidate["candidate_id"] not in inputs["resolutions"]:
            pending.append(candidate["candidate_id"])
    if pending:
        blockers.append(f"unreviewed_candidates:{len(pending)}")
    eligible, exclusions, seen = [], [], set()
    for event in sorted(inputs["incidents"], key=lambda e: (e["incident_id"], -e["revision"])):
        if event["incident_id"] in seen:
            continue
        seen.add(event["incident_id"])
        reason = None
        if instant(event["recorded_at"]) > instant(as_of):
            reason = "review_after_cutoff"
        elif any(inputs["resolutions"].get(cid, {}).get("revision_ids", {}).get(event["incident_id"]) != event["revision_id"] for cid in event["candidate_ids"]):
            reason = "superseded_review"
        elif event["category"] not in config["categories"]:
            reason = "context_only"
        elif event["occurred_on"] is None:
            reason = "occurrence_date_unknown"
        elif not first <= date.fromisoformat(event["occurred_on"]) <= last:
            reason = "outside_event_window"
        elif event["status"] not in config["accepted_statuses"]:
            reason = "occurrence_not_confirmed"
        elif event["country"] not in config["categories"][event["category"]].get("scope_countries", config["scope_countries"]):
            reason = "outside_geographic_scope"
        elif (event["attribution"]["actor"] not in config["attributed_actors"] or
              event["attribution"]["status"] not in config["accepted_statuses"]):
            reason = "hostile_attribution_not_confirmed"
        elif any(e["material_id"] not in current_ids for e in event["evidence"]):
            reason = "source_has_newer_version"
        elif any(instant(materials[e["material_id"]]["fetched_at"]) > instant(as_of) for e in event["evidence"]):
            reason = "evidence_after_cutoff"
        else:
            try:
                validate_evidence(event, materials)
            except ValueError:
                reason = "evidence_validation_failed"
            rule = config["categories"][event["category"]]
            required_criteria = rule["criteria"] + rule.get("country_criteria", {}).get(event["country"], [])
            if not reason and any(not event["criteria"].get(key) for key in required_criteria):
                reason = "category_criteria_not_met"
        if reason:
            if reason == "source_has_newer_version":
                blockers.append(f"stale_event_review:{event['incident_id']}")
            elif reason in ("occurrence_date_unknown", "evidence_validation_failed", "evidence_after_cutoff"):
                blockers.append(f"unresolved_event:{event['incident_id']}")
            exclusions.append({"incident_id": event["incident_id"], "revision_id": event["revision_id"],
                               "title": event["title"], "reason": reason})
        else:
            eligible.append(event)
    used_campaigns, totals, contributions = set(), defaultdict(int), []
    components = {"hostile_activity": 0, "preparation": 0}
    raw_total = 0
    for event in eligible:
        category = event["category"]
        campaign_key = (category, event["campaign_id"])
        if event["campaign_id"] and campaign_key in used_campaigns:
            exclusions.append({"incident_id": event["incident_id"], "revision_id": event["revision_id"],
                               "title": event["title"], "reason": "same_campaign_and_category"})
            continue
        used_campaigns.add(campaign_key)
        rule = config["categories"][category]
        raw_total += rule["weight"]
        points = min(rule["weight"], max(0, rule["cap"] - totals[category]))
        totals[category] += points
        family = rule.get("family", "hostile_activity")
        components[family] += points
        contributions.append({"incident_id": event["incident_id"], "revision_id": event["revision_id"],
                              "title": event["title"], "category": category, "nominal_points": rule["weight"],
                              "points": points, "family": family, "evidence_ids": [e["id"] for e in event["evidence"]]})
    result = {"score": None if blockers else min(config["maximum"], config["base"] + sum(totals.values())),
              "raw_reviewed_sum": raw_total, "capped_reviewed_sum": sum(totals.values()),
              "status": "incomplete" if blockers else "experimental", "blockers": blockers,
              "contributions": contributions, "exclusions": exclusions,
              "delta_points": None, "comparison_run_id": None}
    result["components"] = components
    result["alert"] = alert_for(result["score"], config)
    coverage = {"scope": "pilot_configured_publications", "required_sources": [s["id"] for s in required],
                "successful_sources": [s["source_id"] for s in inputs["source_checks"] if s["status"] == "ok"],
                "unreviewed_current_candidates": len(pending), "pending_candidate_ids": pending,
                "note": "Pokrycie dotyczy podłączonych publikacji, nie wszystkich zdarzeń w regionie."}
    return result, coverage
