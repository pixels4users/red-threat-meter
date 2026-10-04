from __future__ import annotations

import re
from pathlib import Path

from ..common import ROOT, canonical_json, digest, load_config, load_scoring, now, read_json, write_json
from ..pipeline import cached_checks, code_hash, create_inputs, locked, make_snapshot, publish, run
from ..review import import_review, validate_schema
from ..store import Store
from .commentary import check_context, evidence_catalog, make_record
from .reviewer import AnalysisError, convert_proposal, packet_for, preview_import


def write_once(path, value):
    if path.exists():
        if read_json(path) != value:
            raise AnalysisError("frozen_file_already_exists")
        return
    write_json(path, value)


def input_state(inputs):
    return digest({"materials": sorted(inputs["latest_material_ids"]),
                   "incidents": sorted(e["revision_id"] for e in inputs["incidents"]),
                   "resolutions": inputs["resolutions"], "source_checks": sorted(inputs["source_checks"], key=lambda s: s["source_id"])})


def store_state(store):
    stamp = now()
    return input_state({"latest_material_ids": [m["material_id"] for m in store.latest_materials(stamp)],
                        "incidents": store.latest_incidents(stamp), "resolutions": store.resolutions(stamp),
                        "source_checks": cached_checks(store)})


def cycle_folder(data_dir, cycle_id):
    if not re.fullmatch(r"[0-9TZ+-]{8,40}-[a-f0-9]{8}", cycle_id):
        raise AnalysisError("invalid_cycle_id")
    return data_dir / "analysis/cycles" / cycle_id


def load_cycle(data_dir, cycle_id):
    folder = cycle_folder(data_dir, cycle_id)
    prepared = read_json(folder / "prepared.json")
    if read_json(folder / "manifest.json")["prepared_sha256"] != digest(prepared):
        raise AnalysisError("cycle_integrity_failed")
    if (prepared["code_hash"] != code_hash() or prepared["analysis_config_hash"] != digest(read_json(ROOT / "config/analysis.json")) or
            prepared["inputs"]["source_config"] != load_config() or
            prepared["inputs"]["scoring"] != load_scoring()):
        raise AnalysisError("cycle_code_or_config_changed")
    if prepared["inputs"]["run_id"] != cycle_id:
        raise AnalysisError("cycle_id_mismatch")
    return folder, prepared


def require_state(store, expected):
    if store_state(store) != expected:
        raise AnalysisError("cycle_state_changed_prepare_again")


def prepare(data_dir: Path, *, offline=False, fixture=None, review_incidents=(), progress=lambda message: None):
    config = read_json(ROOT / "config/analysis.json")
    validate_schema("analysis/config", config)
    if fixture and data_dir.resolve() == (ROOT / "data").resolve():
        raise AnalysisError("fixture_requires_isolated_directory")
    if review_incidents and not offline:
        raise AnalysisError('correction_requires_offline')
    result = run(data_dir, offline=offline, fixture=fixture, collect_only=True, progress=progress)
    inputs = read_json(Path(result["review_queue"]).with_name("review-input.json"))
    if inputs["scoring"]["version"] != config["methodology_version"]:
        raise AnalysisError("analysis_methodology_mismatch")
    targets = [c["candidate_id"] for c in inputs["candidates"] if c["candidate_id"] not in inputs["resolutions"]]
    if review_incidents:
        events = {event['incident_id']: event for event in inputs['incidents']}
        if not set(review_incidents) <= events.keys():
            raise AnalysisError('correction_unknown_incident')
        # Explicit corrections reuse saved evidence; unresolved candidates stay
        # in the packet and must still receive an honest decision.
        targets = sorted(set(targets) | {cid for eid in review_incidents for cid in events[eid]['candidate_ids']})
    if len(targets) > config["max_candidates_per_packet"]:
        raise AnalysisError("packet_candidate_limit")
    with locked(data_dir), Store(data_dir) as store:
        require_state(store, input_state(inputs))
        packet = packet_for(store, inputs, targets)
        if len(canonical_json(packet).encode()) > config["max_packet_bytes"]:
            raise AnalysisError("packet_size_limit")
        folder = cycle_folder(data_dir, inputs["run_id"])
        prepared = {"version": "codex-cycle-v1", "inputs": inputs, "packet": packet,
                    "code_hash": code_hash(), "analysis_config_hash": digest(config), "state_sha256": input_state(inputs)}
        if review_incidents:
            prepared['correction_incident_ids'] = sorted(set(review_incidents))
        write_once(folder / "prepared.json", prepared)
        write_once(folder / "manifest.json", {"prepared_sha256": digest(prepared)})
        write_once(folder / "packet.json", packet)
    return {"cycle_id": inputs["run_id"], "pending": len(targets), "packet": str(folder / "packet.json"),
            "instructions": str(ROOT / "agents/analysis-cycle.md"), "mode": inputs["mode"]}


def check(data_dir, cycle_id, proposal, reviewer_name):
    folder, prepared = load_cycle(data_dir, cycle_id)
    if not reviewer_name.strip():
        raise AnalysisError("reviewer_name_required")
    reviewer = {"type": "agent", "name": reviewer_name}
    batch, decisions = convert_proposal(proposal, prepared["packet"], reviewer)
    with locked(data_dir), Store(data_dir) as store:
        require_state(store, prepared["state_sha256"])
        if batch["decisions"]:
            preview_import(store, batch)
    checked = {"proposal": proposal, "review": batch, "decisions": decisions,
               "packet_sha256": digest(prepared["packet"]), "reviewer": reviewer}
    key = digest(proposal)
    write_once(folder / "checked" / key / "checked.json", checked)
    write_once(folder / "checked" / key / "manifest.json", {"checked_sha256": digest(checked)})
    audit_input = {"packet": prepared["packet"], "decisions": decisions,
                   "proposal_sha256": key, "instructions": "prompts/analysis-audit.md"}
    write_once(folder / "checked" / key / "audit-input.json", audit_input)
    return {"proposal_sha256": key, "valid": True, "audit_input": str(folder / "checked" / key / "audit-input.json")}


def apply(data_dir, cycle_id, proposal_hash, audit):
    folder, prepared = load_cycle(data_dir, cycle_id)
    if not re.fullmatch("[a-f0-9]{64}", proposal_hash):
        raise AnalysisError("invalid_proposal_hash")
    checked_path = folder / "checked" / proposal_hash
    checked = read_json(checked_path / "checked.json")
    if (read_json(checked_path / "manifest.json")["checked_sha256"] != digest(checked) or
            digest(checked["proposal"]) != proposal_hash or checked["packet_sha256"] != digest(prepared["packet"])):
        raise AnalysisError("checked_proposal_integrity_failed")
    validate_schema("analysis/audit", audit)
    verdicts = {a["decision_id"]: a for a in audit["items"]}
    if len(verdicts) != len(audit["items"]) or set(verdicts) != {d["decision_id"] for d in checked["decisions"]}:
        raise AnalysisError("audit_decisions_mismatch")
    held = set()
    for d in checked["decisions"]:
        a = verdicts[d["decision_id"]]
        if not d["review_decision"] or a["verdict"] != "accept" or not all(a["checks"].values()):
            held.update(d["proposal"]["candidate_ids"])
    # Keep every decision for one article together, including a multi-article event.
    while True:
        expanded = held | {cid for d in checked["decisions"] if held.intersection(d["proposal"]["candidate_ids"]) for cid in d["proposal"]["candidate_ids"]}
        if expanded == held:
            break
        held = expanded
    accepted = [d["review_decision"] for d in checked["decisions"] if d["review_decision"] and not held.intersection(d["proposal"]["candidate_ids"])]
    with locked(data_dir), Store(data_dir) as store:
        if (folder / "applied.json").exists():
            existing = read_json(folder / "applied.json")
            if existing["proposal_sha256"] != proposal_hash or existing["audit"] != audit:
                raise AnalysisError("cycle_already_reviewed")
            require_state(store, existing["state_sha256"])
            return {"accepted": existing["accepted"], "held": existing["held"], "unchanged": True}
        require_state(store, prepared["state_sha256"])
        batch = {**checked["review"], "decisions": accepted}
        result = import_review(store, batch) if accepted else {"new_revisions": 0, "new_resolutions": 0, "unchanged": 0}
        covered = {cid for decision in accepted for cid in decision["candidate_ids"]}
        targets = set(prepared["packet"]["target_candidate_ids"])
        record = {"proposal_sha256": proposal_hash, "audit": audit, "review": batch,
                  "state_sha256": store_state(store), "accepted": len(targets & covered),
                  "held": len(targets - covered), "recorded_at": now(), "result": result}
        write_once(folder / "applied.json", record)
        write_once(folder / "applied-manifest.json", {"applied_sha256": digest(record)})
    return {"accepted": record["accepted"], "held": record["held"], "unchanged": False}


def applied_record(folder, prepared):
    if not prepared["packet"]["target_candidate_ids"]:
        return {"state_sha256": prepared["state_sha256"], "accepted": 0, "held": 0}
    record = read_json(folder / "applied.json")
    if read_json(folder / "applied-manifest.json")["applied_sha256"] != digest(record):
        raise AnalysisError("applied_integrity_failed")
    return record


def history_context(data_dir, cycle_id):
    """Prepare evidence for an explicit audit; this never certifies completeness."""
    from ..scoring import window_for
    from ..scoring_v03 import history_fingerprint
    folder, prepared = load_cycle(data_dir, cycle_id)
    applied = applied_record(folder, prepared)
    with locked(data_dir), Store(data_dir) as store:
        require_state(store, applied['state_sha256'])
        original = prepared['inputs']
        inputs = create_inputs(store, original['source_config'], original['scoring'], original['source_checks'], now(), original['mode'], cycle_id)
        context = {'inputs_sha256': history_fingerprint(inputs), 'required_window': window_for(inputs['as_of'], inputs['scoring']),
                   'source_checks': inputs['source_checks'], 'materials': inputs['materials'],
                   'incidents': inputs['incidents'], 'resolutions': inputs['resolutions'],
                   'instruction': 'Zweryfikuj historię zdarzeń i rewizji z 216 godzin, nie sam wiek publikacji. Brak pokrycia oznacza brak history-review.json; w v0.4 obniża pewność danych, bez blokowania RTB. Wersje historyczne zachowują dawne bramki.'}
        path = folder / 'history-context.json'
        write_json(path, context)
    return {'history_context': str(path), 'inputs_sha256': context['inputs_sha256'], 'required_window': context['required_window']}


def calculate(data_dir, cycle_id):
    folder, prepared = load_cycle(data_dir, cycle_id)
    applied = applied_record(folder, prepared)
    with locked(data_dir), Store(data_dir) as store:
        require_state(store, applied["state_sha256"])
        if (folder / "draft.json").exists():
            draft = read_json(folder / "draft.json")
            if read_json(folder / "draft-manifest.json")["draft_sha256"] != digest(draft):
                raise AnalysisError("draft_integrity_failed")
        else:
            original = prepared["inputs"]
            inputs = create_inputs(store, original["source_config"], original["scoring"], original["source_checks"], now(), original["mode"], cycle_id)
            # Optional, explicit audit of the nine-day event/revision history.
            # Bound to frozen inputs, never inferred from the age of an RSS item.
            history_path = folder / 'history-review.json'
            if history_path.exists():
                inputs['history_review'] = read_json(history_path)
                validate_schema('history-review', inputs['history_review'])
            snapshot = make_snapshot(inputs)
            draft = {"snapshot": snapshot, "inputs": inputs, "evidence_review": applied,
                     "state_sha256": store_state(store)}
            write_once(folder / "draft.json", draft)
            write_once(folder / "draft-manifest.json", {"draft_sha256": digest(draft)})
        catalog = evidence_catalog(draft["snapshot"], draft["inputs"])
        write_once(folder / "commentary-evidence.json", {"snapshot_id": cycle_id, "rtb": draft["snapshot"]["rtb"],
                                                        "mode": draft["snapshot"]["mode"], "evidence": catalog})
    return {"cycle_id": cycle_id, "score": draft["snapshot"]["rtb"]["score"],
            "blockers": draft["snapshot"]["rtb"]["blockers"],
            "confidence": draft["snapshot"]["rtb"].get("confidence"),
            "quality_issues": draft["snapshot"]["rtb"].get("quality_issues", []), "draft": str(folder / "draft.json"),
            "commentary_evidence": str(folder / "commentary-evidence.json")}


def editorial_input(data_dir, cycle_id, context, candidate):
    folder, _ = load_cycle(data_dir, cycle_id)
    draft = read_json(folder / "draft.json")
    if read_json(folder / "draft-manifest.json")["draft_sha256"] != digest(draft):
        raise AnalysisError("draft_integrity_failed")
    catalog = check_context(draft["snapshot"], draft["inputs"], context)
    validate_schema("dashboard/commentary-candidate", candidate)
    subject = {"context": context, "candidate": candidate}
    value = {"subject_sha256": digest(subject), **subject, "evidence": catalog,
             "instructions": "prompts/analysis-editor.md"}
    path = folder / "editorial" / digest(subject) / "input.json"
    write_once(path, value)
    return {"editorial_input": str(path), "subject_sha256": digest(subject)}


def finish(data_dir, cycle_id, *, context=None, candidate=None, audit=None, reviewer_name="Codex"):
    folder, prepared = load_cycle(data_dir, cycle_id)
    draft = read_json(folder / "draft.json")
    if read_json(folder / "draft-manifest.json")["draft_sha256"] != digest(draft):
        raise AnalysisError("draft_integrity_failed")
    snapshot = draft["snapshot"]
    # An unchanged retry returns the exact frozen edition, never a new timestamp.
    finish_key = digest({"context": context, "candidate": candidate, "audit": audit, "reviewer_name": reviewer_name})
    with locked(data_dir), Store(data_dir) as store:
        if (folder / "finished.json").exists():
            receipt = read_json(folder / "finished.json")
            if receipt["finish_key"] != finish_key:
                raise AnalysisError("finished_cycle_cannot_change")
            return receipt
        require_state(store, draft["state_sha256"])
        supplied = [context is not None, candidate is not None, audit is not None]
        if any(supplied) and not all(supplied):
            raise AnalysisError("editorial_package_incomplete")
        extras = {"analysis-audit.json": draft["evidence_review"]}
        if all(supplied):
            extras["commentary-review.json"] = make_record(snapshot, draft["inputs"], context, candidate, audit, reviewer_name)
        target = data_dir / "snapshots" / cycle_id
        if target.exists():
            # Recovery after snapshot commit but before writing this workflow receipt.
            if read_json(target / "snapshot.json") != snapshot:
                raise AnalysisError("existing_snapshot_differs")
            for name, content in extras.items():
                saved = read_json(target / name)
                if name == "commentary-review.json":
                    saved = {**saved, "reviewed_at": content["reviewed_at"]}
                if saved != content:
                    raise AnalysisError("existing_snapshot_differs")
        else:
            publish(store, draft["inputs"], snapshot, extras=extras)
        receipt = {"cycle_id": cycle_id, "snapshot_dir": str(target), "score": snapshot["rtb"]["score"],
                   "finish_key": finish_key, "mode": snapshot["mode"]}
        write_once(folder / "finished.json", receipt)
    return receipt
