from __future__ import annotations

import json
from datetime import date
from zoneinfo import ZoneInfo

from jsonschema import Draft202012Validator, FormatChecker

from .common import ROOT, canonical_json, clean_text, digest, instant, now, read_json


def validate_schema(name: str, value: dict) -> None:
    schema = read_json(ROOT / f"schemas/{name}.schema.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)


def evidence_strength(evidence: list[dict], materials: dict[str, dict], claim: str) -> str:
    relevant = [e for e in evidence if e["claim"] == claim]
    if any(e["stance"] == "contradicts" for e in relevant):
        return "disputed"
    supporting = [e for e in relevant if e["stance"] == "supports"]
    sources = {materials[e["material_id"]]["source_id"] for e in supporting}
    origins = {e["origin_id"] for e in supporting}
    if len(sources) >= 2 and len(origins) >= 2:
        return "corroborated"
    if any(materials[e["material_id"]]["source_kind"] == "primary" for e in supporting):
        return "confirmed_primary"
    return "unverified"


def validate_evidence(incident: dict, materials: dict[str, dict]) -> None:
    by_id = {e["id"]: e for e in incident["evidence"]}
    if len(by_id) != len(incident["evidence"]):
        raise ValueError("Evidence IDs must be unique")
    relevance = incident.get('security_relevance')
    if relevance:
        if any(ref not in by_id or by_id[ref]['stance'] != 'supports' for ref in relevance['evidence_ids']):
            raise ValueError('Security relevance requires supporting evidence')
        if relevance['classification'] == 'out_of_scope' and (
                incident['category'] != 'context' or incident['criteria'] or
                incident.get('assessment_v03') or incident.get('assessment_v04') or incident.get('official_warning')):
            raise ValueError('An out-of-scope correction cannot hide scoring or official warnings')
    for evidence in incident["evidence"]:
        material = materials.get(evidence["material_id"])
        if material is None:
            raise ValueError("Evidence references a material outside reviewed candidates")
        if material.get("source_kind") not in ("primary", "secondary", "analysis"):
            raise ValueError("Doctrinal or reference material cannot serve as incident evidence")
        if 'measurement' in evidence:
            from .gnss_bridge import validate_numeric_evidence
            validate_numeric_evidence(evidence, material, incident)
            continue
        if material.get('text_kind') == 'measurement':
            raise ValueError('Measurements require numeric evidence, not generated quotes')
        haystack = clean_text(material["title"] + " " + material["text"])
        if clean_text(evidence["quote"]) not in haystack:
            raise ValueError(f"Evidence quote is not present in saved source: {evidence['id']}")
    for refs, claim in [(incident["date_evidence_ids"], "timing"),
                        (incident["location"]["evidence_ids"], "location"),
                        (incident.get("strategic_context", {}).get("evidence_ids", []), "location")]:
        for ref in refs:
            if ref not in by_id or by_id[ref]["claim"] != claim or by_id[ref]["stance"] != "supports":
                raise ValueError(f"Invalid {claim} evidence reference: {ref}")
    for criterion, refs in incident["criteria"].items():
        if any(ref not in by_id or by_id[ref]["claim"] != "criterion" or by_id[ref]["stance"] != "supports" for ref in refs):
            raise ValueError(f"Invalid criterion evidence: {criterion}")
    if incident["occurred_on"] is not None and not incident["date_evidence_ids"]:
        raise ValueError("Occurrence date requires evidence; publication date is not an occurrence date")
    location = incident["location"]
    if location["geometry"] is not None and (location["precision"] in ("unknown", "country", "region") or not location["evidence_ids"]):
        raise ValueError("Point coordinates require location evidence and explicit precision")
    for claim, declared in [("occurrence", incident["status"]), ("attribution", incident["attribution"]["status"])]:
        strength = evidence_strength(incident["evidence"], materials, claim)
        if declared == "corroborated" and strength != "corroborated":
            raise ValueError(f"{claim}: independent corroboration is not established")
        if declared == "confirmed_primary" and strength not in ("confirmed_primary", "corroborated"):
            raise ValueError(f"{claim}: primary confirmation is not established")
    if incident.get('assessment_v03') or incident.get('assessment_v04') or incident.get('official_warning'):
        from .scoring_v03 import validate_assessment, validate_warning
        validate_assessment(incident)
        validate_warning(incident, materials)
    presentation = incident.get('dashboard_context')
    if presentation:
        refs = presentation['evidence_ids']
        if any(ref not in by_id or by_id[ref]['stance'] != 'supports' for ref in refs):
            raise ValueError('Dashboard context requires supporting evidence')
        if bool(presentation['region_ids']) != (presentation['scope'] == 'regional'):
            raise ValueError('Dashboard regional scope requires explicit region IDs')
        if presentation['scope'] in ('national', 'regional') and not any(by_id[r]['claim'] == 'location' for r in refs):
            raise ValueError('Dashboard geographic scope requires location evidence')
        if presentation['scope'] == 'regional' and incident['country'] != 'PL':
            raise ValueError('Polish regional scope requires country PL')
        if presentation.get('place_id'):
            place = read_json(ROOT / 'config/map-places.json')['places'].get(presentation['place_id'])
            if (not place or place['country'] != incident['country'] or
                    place['region_id'] not in presentation['region_ids'] or
                    location['precision'] != 'city' or location['label'] != place['label'] or
                    not any(by_id[r]['claim'] == 'location' for r in refs)):
                raise ValueError('Map city reference requires a matching reviewed location and region')


def import_review(store, batch: dict) -> dict:
    validate_schema("review", batch)
    seen, kinds = set(), {}
    for decision in batch["decisions"]:
        key = decision.get("incident", {}).get("event_key", "exclude")
        for cid in decision["candidate_ids"]:
            if (cid, key) in seen or (cid in kinds and kinds[cid] != decision["kind"]):
                raise ValueError("Conflicting or duplicate decisions for one candidate")
            seen.add((cid, key))
            kinds[cid] = decision["kind"]
    recorded_at = now()
    latest = {m["document_id"]: m["material_id"] for m in store.latest_materials(recorded_at)}
    prepared = []
    for decision in batch["decisions"]:
        materials = {}
        for candidate_id in decision["candidate_ids"]:
            row = store.db.execute("SELECT material_id FROM candidates WHERE candidate_id=?", (candidate_id,)).fetchone()
            if row is None:
                raise ValueError(f"Unknown candidate: {candidate_id}")
            material = store.material(row[0])
            if latest.get(material["document_id"]) != material["material_id"]:
                raise ValueError(f"Source has a newer version; review the current candidate: {candidate_id}")
            materials[row[0]] = material
        if decision["kind"] == "incident":
            event = decision["incident"]
            validate_evidence(event, materials)
            if event["occurred_on"] and date.fromisoformat(event["occurred_on"]) > instant(recorded_at).astimezone(ZoneInfo("Europe/Warsaw")).date():
                raise ValueError("Occurrence date lies in the future")
        prepared.append((decision, materials))
    result = {"new_revisions": 0, "new_resolutions": 0, "unchanged": 0}
    with store.db:
        for decision, materials in prepared:
            incident_id, revision_id = None, None
            if decision["kind"] == "incident":
                event = decision["incident"]
                incident_id = "evt_" + digest(event["event_key"])[:24]
                row = store.db.execute("SELECT revision,payload FROM incident_revisions WHERE incident_id=? ORDER BY revision DESC LIMIT 1", (incident_id,)).fetchone()
                previous = json.loads(row[1]) if row else None
                semantic = {**event, "candidate_ids": sorted(decision["candidate_ids"]), "reviewer": batch["reviewer"]}
                same = previous and all(previous.get(k) == v for k, v in semantic.items())
                if same:
                    revision_id = previous["revision_id"]
                    result["unchanged"] += 1
                else:
                    current_revision = row[0] if row else 0
                    if current_revision != decision["previous_revision"]:
                        raise ValueError("Stale incident revision; read latest revision before applying a correction")
                    payload = {**semantic, "incident_id": incident_id, "revision": current_revision + 1,
                               "recorded_at": recorded_at, "revision_id": "rev_" + digest([incident_id, current_revision + 1, semantic])[:24]}
                    validate_schema("incident", payload)
                    revision_id = payload["revision_id"]
                    store.db.execute("INSERT INTO incident_revisions VALUES (?,?,?,?,?)", (revision_id, incident_id, payload["revision"], recorded_at, canonical_json(payload)))
                    result["new_revisions"] += 1
            for candidate_id in decision["candidate_ids"]:
                row = store.db.execute("SELECT payload,resolution_id FROM resolutions WHERE candidate_id=? ORDER BY recorded_at DESC,rowid DESC LIMIT 1", (candidate_id,)).fetchone()
                old = json.loads(row[0]) if row else {}
                bindings = dict(old.get("revision_ids", {})) if old.get("kind") == "incident" else {}
                if decision["kind"] == "incident":
                    if bindings.get(incident_id) == revision_id and old.get("reviewer") == batch["reviewer"]:
                        continue
                    bindings[incident_id] = revision_id
                else:
                    bindings = {}
                payload = {"candidate_id": candidate_id, "kind": decision["kind"], "reviewer": batch["reviewer"],
                           "reason": decision.get("reason", decision.get("incident", {}).get("summary", "")),
                           "revision_ids": bindings}
                if all(old.get(k) == v for k, v in payload.items()):
                    continue
                # Include the preceding decision so excluding and later reinstating
                # an unchanged event remains a new, auditable transition.
                resolution_id = "res_" + digest([row[1] if row else None, payload])[:24]
                payload["recorded_at"] = recorded_at
                store.db.execute("INSERT INTO resolutions VALUES (?,?,?,?)", (resolution_id, candidate_id, recorded_at, canonical_json(payload)))
                result["new_resolutions"] += 1
    return result
