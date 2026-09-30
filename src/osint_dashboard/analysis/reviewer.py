from __future__ import annotations

from copy import copy, deepcopy
import sqlite3

from ..common import digest
from ..dashboard_commentary import MARKUP, META, _fold
from ..review import import_review, validate_schema


class AnalysisError(RuntimeError):
    """Fixed operational codes; private source bodies never become CLI errors."""


def public_material(material: dict) -> dict:
    fields = ("material_id", "document_id", "content_hash", "source_id", "publisher", "source_kind",
              "title", "text", "text_kind", "url", "published_at", "fetched_at")
    result = {key: material[key] for key in fields}
    if "content_provenance" in material:
        result["content_provenance"] = material["content_provenance"]
    return result


def packet_for(store, inputs, targets):
    current = {m["material_id"]: m for m in inputs["materials"] if m["material_id"] in inputs["latest_material_ids"]}
    candidates = {c["candidate_id"]: c for c in inputs["candidates"]}
    events = inputs["incidents"]
    needed = {candidates[cid]["material_id"] for cid in targets}
    needed.update(e["material_id"] for event in events for e in event["evidence"] if e["material_id"] in current)
    return {"as_of": inputs["as_of"], "mode": inputs["mode"],
            "scoring": inputs["scoring"], "target_candidate_ids": targets,
            "candidates": [{key: c[key] for key in ("candidate_id", "material_id", "document_id", "title", "source_id", "flags")} for c in candidates.values()],
            "materials": [public_material(current[mid]) for mid in sorted(needed)],
            "existing_incidents": [{k: v for k, v in event.items() if k != "reviewer"} for event in events]}


def convert_proposal(proposal: dict, packet: dict, reviewer: dict) -> tuple[dict, list[dict]]:
    validate_schema("analysis/proposal", proposal)
    targets = set(packet["target_candidate_ids"])
    candidates = {c["candidate_id"]: c for c in packet["candidates"]}
    materials = {m["material_id"]: m for m in packet["materials"]}
    previous = {e["event_key"]: e for e in packet["existing_incidents"]}
    coverage, event_keys, decisions, private = set(), set(), [], []
    for item in proposal["decisions"]:
        ids = item["candidate_ids"]
        if len(ids) != len(set(ids)) or not set(ids) <= candidates.keys() or not targets.intersection(ids):
            raise AnalysisError("proposal_candidate_scope")
        if any(candidates[cid]["material_id"] not in materials for cid in ids):
            raise AnalysisError("proposal_unseen_material")
        coverage.update(targets.intersection(ids))
        private.append({"decision_id": digest(item), "proposal": item, "review_decision": None})
        if item["kind"] != "incident":
            if item["incident"] is not None or item["previous_revision"] != 0 or not set(ids) <= targets:
                raise AnalysisError("proposal_invalid_exclusion")
            if item["kind"] == "exclude":
                decision = {"kind": "exclude", "candidate_ids": ids, "reason": item["reason"]}
                decisions.append(decision)
                private[-1]["review_decision"] = decision
            continue
        if item["incident"] is None:
            raise AnalysisError("proposal_missing_incident")
        event = deepcopy(item["incident"])
        if event["event_key"] in event_keys:
            raise AnalysisError("proposal_duplicate_event")
        event_keys.add(event["event_key"])
        old = previous.get(event["event_key"])
        if item["previous_revision"] != (old["revision"] if old else 0):
            raise AnalysisError("proposal_stale_revision")
        if old:
            # A revision must not silently sever current evidence bindings.
            current_old_ids = {cid for cid in old["candidate_ids"] if cid in candidates}
            if not current_old_ids <= set(ids):
                raise AnalysisError("proposal_dropped_current_evidence")
        pairs = event["criteria"]
        if len({p["key"] for p in pairs}) != len(pairs):
            raise AnalysisError("proposal_duplicate_criterion")
        event["criteria"] = {p["key"]: p["evidence_ids"] for p in pairs}
        if event["location"]["geometry"] is not None:
            raise AnalysisError("proposal_inferred_coordinates")
        if (event["country"] is not None or event["location"]["label"]) and not event["location"]["evidence_ids"]:
            raise AnalysisError("proposal_location_without_evidence")
        for text in (event["title"], event["summary"]):
            if MARKUP.search(text) or META.search(_fold(text)):
                raise AnalysisError("proposal_non_editorial_text")
        decisions.append({"kind": "incident", "candidate_ids": ids,
                          "previous_revision": item["previous_revision"], "incident": event})
        private[-1]["review_decision"] = decisions[-1]
    if coverage != targets:
        raise AnalysisError("proposal_missing_candidates")
    if len({row["decision_id"] for row in private}) != len(private):
        raise AnalysisError("proposal_duplicate_decision")
    return {"schema_version": "1", "reviewer": reviewer, "decisions": decisions}, private


def preview_import(store, batch):
    """Run all existing semantic/transaction checks against a disposable DB copy."""
    probe = copy(store)
    probe.db = sqlite3.connect(":memory:")
    probe.db.row_factory = sqlite3.Row
    try:
        store.db.backup(probe.db)
        return import_review(probe, batch)
    finally:
        probe.db.close()
