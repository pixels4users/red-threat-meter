from __future__ import annotations

from zoneinfo import ZoneInfo

from ..common import digest, instant, now
from ..dashboard_commentary import build_generation_request, candidate_digest, prepare_commentary
from ..review import validate_schema
from .reviewer import AnalysisError, public_material


def evidence_catalog(snapshot: dict, inputs: dict) -> dict:
    """Private references for prose; only current, dated, confirmed observations."""
    catalog = {}
    if snapshot["rtb"]["score"] is not None:
        catalog["rtb:score"] = {"score": snapshot["rtb"]["score"], "meaning": "Eksperymentalny indeks, bez oceny prawdopodobieństwa wojny ani bezpieczeństwa ludności."}
    if snapshot['methodology_version'] == 'rtb-v0.4':
        catalog['rtb:score']['confidence'] = snapshot['rtb']['confidence']
        catalog['rtb:score']['meaning'] += ' Zero oznacza brak naliczonych sygnałów. Nie uzasadnia tezy o spokoju, normie, spadku zagrożenia ani bezpieczeństwie. Pewność to heurystyka pokrycia danych.'
    current = set(inputs["latest_material_ids"])
    materials = {m["material_id"]: m for m in inputs["materials"]}
    zone = ZoneInfo(snapshot["window"]["timezone"])
    start = instant(snapshot["window"]["start"]).astimezone(zone).date().isoformat()
    end = instant(snapshot["as_of"]).astimezone(zone).date().isoformat()
    for event in snapshot["incidents"]:
        if event["status"] not in ("confirmed_primary", "corroborated") or not event["occurred_on"]:
            continue
        if not start <= event["occurred_on"] <= end:
            continue
        if any(inputs["resolutions"].get(cid, {}).get("revision_ids", {}).get(event["incident_id"]) != event["revision_id"] for cid in event["candidate_ids"]):
            continue
        if any(e["material_id"] not in current for e in event["evidence"]):
            continue
        for evidence in event["evidence"]:
            if evidence["stance"] != "supports":
                continue
            if evidence["claim"] == "attribution" and event["attribution"]["status"] not in ("confirmed_primary", "corroborated"):
                continue
            catalog[event["revision_id"] + ":" + evidence["id"]] = {
                "incident_id": event["incident_id"], "occurred_on": event["occurred_on"],
                "title": event["title"], "summary": event["summary"],
                "attribution": event["attribution"], "evidence": evidence,
                "material": public_material(materials[evidence["material_id"]])}
    return catalog


def check_context(snapshot, inputs, context):
    validate_schema("dashboard/commentary-context", context)
    if (context["snapshot_id"] != snapshot["run_id"] or context["mode"] != snapshot["mode"] or
            context["analysis_complete"] != (snapshot["rtb"]["score"] is not None) or
            context["rtb"] != {"score": snapshot["rtb"]["score"], "delta_points": snapshot["rtb"]["delta_points"],
                               "methodology_version": snapshot["methodology_version"]}):
        raise AnalysisError("commentary_context_mismatch")
    catalog = evidence_catalog(snapshot, inputs)
    for finding in context["findings"]:
        if finding["status"] == "accepted" and not set(finding["evidence_refs"]) <= catalog.keys():
            raise AnalysisError("commentary_unknown_evidence")
    if build_generation_request(context) is None:
        raise AnalysisError("commentary_incomplete_findings")
    return catalog


def make_record(snapshot, inputs, context, candidate, audit, reviewer_name):
    check_context(snapshot, inputs, context)
    validate_schema("analysis/editorial-audit", audit)
    subject = {"context": context, "candidate": candidate}
    if audit["subject_sha256"] != digest(subject):
        raise AnalysisError("editorial_audit_text_changed")
    if audit["verdict"] != "accept" or not all(audit["checks"].values()):
        raise AnalysisError("editorial_audit_held")
    text = prepare_commentary(candidate, expected_snapshot_id=snapshot["run_id"],
                              analysis_complete=snapshot["rtb"]["score"] is not None,
                              approved_sha256=candidate_digest(candidate))
    if text["text"] is None:
        raise AnalysisError("commentary_not_publishable")
    return {"version": "codex-editorial-v1", "snapshot_sha256": digest(snapshot),
            "context": context, "candidate": candidate, "audit": audit,
            "reviewer": {"type": "agent", "name": reviewer_name}, "reviewed_at": now()}


def public_commentary(record: dict, snapshot_hash: str, run_id: str, score) -> dict:
    """Validate a server-written receipt; it is provenance, not proof of truth."""
    if (record.get("version") != "codex-editorial-v1" or record.get("snapshot_sha256") != snapshot_hash or
            record.get("reviewer", {}).get("type") != "agent" or not record.get("reviewer", {}).get("name")):
        raise AnalysisError("invalid_editorial_record")
    validate_schema("dashboard/commentary-context", record["context"])
    validate_schema("analysis/editorial-audit", record["audit"])
    if (record["context"]["snapshot_id"] != run_id or record["context"]["rtb"]["score"] != score or
            build_generation_request(record["context"]) is None):
        raise AnalysisError("invalid_editorial_context")
    if (record["audit"]["subject_sha256"] != digest({k: record[k] for k in ("context", "candidate")}) or
            record["audit"]["verdict"] != "accept" or not all(record["audit"]["checks"].values())):
        raise AnalysisError("invalid_editorial_audit")
    instant(record["reviewed_at"])
    result = prepare_commentary(record["candidate"], expected_snapshot_id=run_id,
                                 analysis_complete=score is not None,
                                 approved_sha256=candidate_digest(record["candidate"]))
    if result["text"] is None:
        raise AnalysisError("invalid_editorial_text")
    return {**result, "review": {"record_sha256": digest(record), "snapshot_sha256": snapshot_hash,
                                "text_sha256": digest(result["text"]), "reviewer_type": "agent",
                                "method": "codex-editorial-v1"}}


def verify_publication_record(report, record):
    if report["commentary"]["text"] is None:
        if "review" in report["commentary"]:
            raise AnalysisError("empty_commentary_with_review")
        return
    if record is None:
        raise AnalysisError("editorial_record_required")
    expected = public_commentary(record, report["provenance"]["snapshot_sha256"], report["provenance"]["run_id"], report["rtb"]["score"])
    if expected != report["commentary"]:
        raise AnalysisError("editorial_record_mismatch")
