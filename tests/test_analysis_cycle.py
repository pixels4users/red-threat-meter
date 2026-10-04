import copy
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.usefixtures("legacy_engine")
from jsonschema import ValidationError

from osint_dashboard.analysis import cycle
from osint_dashboard.analysis.cli import main
from osint_dashboard.analysis.commentary import evidence_catalog
from osint_dashboard.analysis.reviewer import AnalysisError, packet_for
from osint_dashboard.common import digest, now, read_json
from osint_dashboard.dashboard.contract import build_report, load_commentary_record, load_snapshot, validate_report
from osint_dashboard.dashboard.publication import LocalPublications, SupabasePublications
from osint_dashboard.pipeline import replay
from osint_dashboard.review import validate_schema
from osint_dashboard.store import Store
from conftest import decision_for, item_for


@pytest.fixture
def prepared(tmp_path, fixture_file):
    data = tmp_path / "analysis"
    result = cycle.prepare(data, fixture=fixture_file)
    return data, result["cycle_id"]


def proposal_for(data, cid):
    folder, prepared = cycle.load_cycle(data, cid)
    packet = prepared["packet"]
    materials = {m["material_id"]: m for m in packet["materials"]}
    decisions = []
    for c in packet["candidates"]:
        if c["source_id"] == "rcb":
            d = decision_for(materials[c["material_id"]], c)
            event = d["incident"]
            event["security_relevance"] = {"classification": "direct", "reason": "Syntetyczne naruszenie przestrzeni w izolowanym teście.", "evidence_ids": ["occurrence"]}
            location = copy.deepcopy(event["evidence"][0])
            location.update(id="place", claim="location")
            event["evidence"].append(location)
            event["location"]["evidence_ids"] = ["place"]
            event["criteria"] = [{"key": k, "evidence_ids": v} for k, v in event["criteria"].items()]
            d["reason"] = "Syntetyczny przykład do kontroli dowodów i publikowania."
            decisions.append(d)
        else:
            decisions.append({"kind": "exclude", "candidate_ids": [c["candidate_id"]],
                              "reason": "Syntetyczny kontekst służący izolowanemu testowi.",
                              "previous_revision": 0, "incident": None})
    return {"decisions": sorted(decisions, key=lambda d: d["kind"] != "incident")}


def test_packet_preserves_evidence_and_bindings_without_unusable_resolved_candidates(prepared):
    data, cid = prepared
    _, frozen = cycle.load_cycle(data, cid)
    inputs = copy.deepcopy(frozen["inputs"])
    target = inputs["candidates"][0]
    current = inputs["candidates"][1]
    inputs["incidents"] = [{"event_key": "synthetic-existing-event",
                            "candidate_ids": [current["candidate_id"]],
                            "evidence": [{"material_id": current["material_id"]}],
                            "reviewer": {"type": "agent", "name": "fixture"}}]
    same_material = {**target, "candidate_id": "cand_same_material"}
    inputs["candidates"].append(same_material)
    original = copy.deepcopy(inputs)
    packet = packet_for(None, inputs, [target["candidate_id"]])
    assert {c["candidate_id"] for c in packet["candidates"]} == {
        target["candidate_id"], current["candidate_id"], same_material["candidate_id"]}
    assert packet["target_candidate_ids"] == [target["candidate_id"]]
    assert {m["material_id"] for m in packet["materials"]} == {
        target["material_id"], current["material_id"]}
    assert packet["existing_incidents"][0]["evidence"] == inputs["incidents"][0]["evidence"]
    assert 'title' not in next(c for c in packet['candidates'] if c['candidate_id'] == target['candidate_id'])
    assert next(m for m in packet['materials'] if m['material_id'] == target['material_id'])['title'] == target['title']
    assert inputs == original

    # Even a binding without current material must remain visible to the
    # revision checks, so packet compaction cannot allow severing evidence.
    missing = inputs["candidates"][2]
    inputs["incidents"][0]["candidate_ids"].append(missing["candidate_id"])
    packet = packet_for(None, inputs, [target["candidate_id"]])
    assert missing["candidate_id"] in {c["candidate_id"] for c in packet["candidates"]}


def test_explicit_offline_correction_keeps_history_and_withdraws_unscored_context(prepared, fixture_file):
    data, cid = prepared
    proposal = proposal_for(data, cid)
    event = proposal['decisions'][0]['incident']
    event['category'], event['criteria'] = 'context', []
    event['security_relevance']['classification'] = 'operational_context'
    checked = cycle.check(data, cid, proposal, 'Fixture')
    cycle.apply(data, cid, checked['proposal_sha256'], audit_for(checked))
    cycle.calculate(data, cid)
    old = read_json(cycle.cycle_folder(data, cid) / 'draft.json')
    previous = old['snapshot']['incidents'][0]
    with pytest.raises(AnalysisError, match='correction_requires_offline'):
        cycle.prepare(data, review_incidents=[previous['incident_id']])
    next_cycle = cycle.prepare(data, offline=True, fixture=fixture_file, review_incidents=[previous['incident_id']])['cycle_id']
    revised = copy.deepcopy(proposal['decisions'][0])
    revised['previous_revision'] = 1
    revised['incident']['security_relevance']['classification'] = 'out_of_scope'
    revised['incident']['security_relevance']['reason'] = 'Syntetyczna korekta: pokaz bez udokumentowanej zmiany operacyjnej.'
    checked = cycle.check(data, next_cycle, {'decisions': [revised]}, 'Fixture')
    cycle.apply(data, next_cycle, checked['proposal_sha256'], audit_for(checked))
    cycle.calculate(data, next_cycle)
    draft = read_json(cycle.cycle_folder(data, next_cycle) / 'draft.json')
    report = build_report(draft['snapshot'], draft['inputs']['source_config'])
    assert report['incidents'] == [] and report['geojson']['features'] == []
    assert report['excluded_incidents'][0]['id'] == previous['incident_id']
    assert report['excluded_incidents'][0]['revision'] == 2
    assert evidence_catalog(draft['snapshot'], draft['inputs']) == {'rtb:score': evidence_catalog(draft['snapshot'], draft['inputs'])['rtb:score']}
    assert read_json(cycle.cycle_folder(data, cid) / 'draft.json') == old
    with Store(data) as store:
        assert store.counts()['incident_revisions'] == 2


def audit_for(result):
    packet = read_json(Path(result["audit_input"]))
    checks = {key: True for key in ("quotes_support_claims", "independent_origins", "event_identity", "dates_and_locations", "category_and_scope", "polish_and_factual")}
    return {"items": [{"decision_id": d["decision_id"], "verdict": "accept", "checks": checks.copy(),
                        "reason": "Wyłącznie syntetyczny werdykt do sprawdzenia kontraktu."} for d in packet["decisions"]]}


def reviewed(prepared):
    data, cid = prepared
    proposal = proposal_for(data, cid)
    checked = cycle.check(data, cid, proposal, "Codex — test syntetyczny")
    audit = audit_for(checked)
    applied = cycle.apply(data, cid, checked["proposal_sha256"], audit)
    return checked, audit, applied


def selection_for(context, catalog):
    # Test-only fixture; production assessments are made explicitly by a reviewer.
    refs = {v['incident_id']: k for k, v in catalog.items() if 'incident_id' in v}
    impact_ids = [f['id'] for f in context['findings'] if f['status'] == 'accepted' and f['role'] == 'impact']
    return {'version': 'editorial-selection-v1', 'items': [
        {'incident_id': eid, 'decision': 'lead' if i == 0 else 'omit', 'relevance': 'direct',
         'timeliness': 'new', 'reason': 'Syntetyczny wybór tematu w odseparowanym teście.', 'evidence_refs': [ref]}
        for i, (eid, ref) in enumerate(refs.items())],
        'poland_impact': {'status': 'supported' if impact_ids else 'not_established', 'finding_ids': impact_ids,
                          'reason': 'Syntetyczna ocena wpływu w odseparowanym teście.'}}


def commentary_for(data, cid):
    folder, _ = cycle.load_cycle(data, cid)
    draft = read_json(folder / "draft.json")
    snap = draft["snapshot"]
    refs = list(evidence_catalog(snap, draft["inputs"]))
    evidence_ref = next(ref for ref in refs if ref.endswith(":occurrence"))
    sentences = ["To syntetyczny scenariusz naruszenia polskiej przestrzeni powietrznej.",
                 "W scenariuszu rosyjski dron przekroczył granicę Polski.",
                 "Opis służy wyłącznie testowaniu aplikacji i nie odnosi się do rzeczywistego zagrożenia."]
    context = {"snapshot_id": cid, "mode": "fixture", "analysis_complete": True,
               "rtb": {"score": 15, "delta_points": None, "methodology_version": "rtb-v0.2"},
               "findings": [{"id": f"f{i}", "role": role, "status": "accepted", "text_pl": text,
                             "evidence_refs": [evidence_ref]} for i, (role, text) in enumerate(zip(("situation", "action", "impact"), sentences))]}
    context["findings"] = [context["findings"][0], context["findings"][2]]
    sentences = [sentences[0], sentences[2]]
    context["selection"] = selection_for(context, evidence_catalog(draft["snapshot"], draft["inputs"]))
    candidate = {"snapshot_id": cid, "language": "pl", "sentences": sentences, "sections": {"situation": 0, "impact": 1}}
    checked = cycle.editorial_input(data, cid, context, candidate)
    audit = {"subject_sha256": checked["subject_sha256"], "verdict": "accept",
             "checks": {key: True for key in ("supported_by_evidence", "no_false_reassurance", "no_inferred_actor_or_intent", "polish_civilian_prose", "current_and_in_scope", "security_relevance", "important_findings_covered", "poland_impact_considered", "continuity_checked")},
             "reason": "Syntetyczny werdykt redakcyjny, używany wyłącznie w odseparowanym teście."}
    return context, candidate, audit


def test_codex_cycle_review_commentary_publish_and_replay(prepared, tmp_path):
    data, cid = prepared
    checked, audit, applied = reviewed(prepared)
    assert applied["accepted"] == len(audit["items"]) and applied["held"] == 0
    assert cycle.apply(data, cid, checked["proposal_sha256"], audit)["unchanged"]
    assert cycle.calculate(data, cid)["score"] == 15
    context, candidate, editorial = commentary_for(data, cid)
    finish = cycle.finish(data, cid, context=context, candidate=candidate, audit=editorial, reviewer_name="Codex — fixture")
    assert cycle.finish(data, cid, context=context, candidate=candidate, audit=editorial, reviewer_name="Codex — fixture") == finish
    folder = Path(finish["snapshot_dir"])
    snapshot, sources = load_snapshot(folder)
    record = load_commentary_record(folder)
    report = build_report(snapshot, sources, commentary_record=record)
    assert report["commentary"]["text"] == " ".join(candidate["sentences"])
    assert report["incidents"][0]["reviewer_type"] == "agent"
    assert "Codex — fixture" not in json.dumps(report)
    repo = LocalPublications(tmp_path / "published.sqlite")
    assert repo.publish(report, commentary_record=record)["created"]
    assert not repo.publish(report, commentary_record=record)["created"]
    assert repo.get(report["report_id"])["report"] == report
    assert replay(data, cid)["identical"]
    assert "## Komentarz analityczny" in (folder / "report.md").read_text()


@pytest.mark.parametrize("count", [1, 2])
def test_short_commentary_without_trend_or_impact_survives_full_cycle(prepared, tmp_path, count):
    data, cid = prepared
    reviewed(prepared)
    cycle.calculate(data, cid)
    context, candidate, _ = commentary_for(data, cid)
    candidate["sentences"] = candidate["sentences"][:count]
    candidate.pop("sections", None)
    context["findings"] = context["findings"][:count]
    for finding in context["findings"]:
        finding["role"] = "action"
    context["selection"]["poland_impact"] = {"status": "not_established", "finding_ids": [], "reason": "W teście brak ustalenia wpływu; pozostaje opis zdarzenia."}
    checked = cycle.editorial_input(data, cid, context, candidate)
    audit = {"subject_sha256": checked["subject_sha256"], "verdict": "accept",
             "checks": {key: True for key in ("supported_by_evidence", "no_false_reassurance", "no_inferred_actor_or_intent", "polish_civilian_prose", "current_and_in_scope", "security_relevance", "important_findings_covered", "poland_impact_considered", "continuity_checked")},
             "reason": "Syntetyczny przegląd krótkiego komentarza, bez oceny trendu i wpływu na ludność."}
    finished = cycle.finish(data, cid, context=context, candidate=candidate, audit=audit)
    folder = Path(finished["snapshot_dir"])
    snapshot, sources = load_snapshot(folder)
    record = load_commentary_record(folder)
    report = build_report(snapshot, sources, commentary_record=record)
    repo = LocalPublications(tmp_path / "short-commentary.sqlite")
    repo.publish(report, commentary_record=record)
    assert repo.get(report["report_id"])["report"]["commentary"]["text"] == " ".join(candidate["sentences"])
    assert replay(data, cid)["identical"]


def test_wrong_quote_and_unknown_candidate_are_rejected(prepared):
    data, cid = prepared
    proposal = proposal_for(data, cid)
    bad = copy.deepcopy(proposal)
    bad["decisions"][0]["incident"]["evidence"][0]["quote"] = "Fragment, którego nie ma w oryginale źródłowym."
    with pytest.raises(ValueError, match="not present"):
        cycle.check(data, cid, bad, "Codex")
    proposal["decisions"][0]["candidate_ids"] = ["cand_unknown"]
    with pytest.raises(AnalysisError, match="candidate_scope"):
        cycle.check(data, cid, proposal, "Codex")
    with Store(data) as store:
        assert store.counts()["incident_revisions"] == 0


def test_audit_hold_keeps_candidate_pending(prepared):
    data, cid = prepared
    checked = cycle.check(data, cid, proposal_for(data, cid), "Codex")
    audit = audit_for(checked)
    audit["items"][0]["checks"]["quotes_support_claims"] = False
    assert cycle.apply(data, cid, checked["proposal_sha256"], audit)["held"] == 1
    result = cycle.calculate(data, cid)
    assert result["score"] is None
    assert "unreviewed_candidates:1" in result["blockers"]
    receipt = cycle.finish(data, cid)
    snap, cfg = load_snapshot(Path(receipt["snapshot_dir"]))
    assert build_report(snap, cfg)["commentary"]["text"] is None


def test_no_partial_resolution_of_article_with_second_held_event(prepared):
    data, cid = prepared
    proposal = proposal_for(data, cid)
    another = copy.deepcopy(proposal["decisions"][0])
    another["incident"]["event_key"] = "synthetic-second-event"
    proposal["decisions"].append(another)
    checked = cycle.check(data, cid, proposal, "Codex")
    audit = audit_for(checked); audit["items"][-1]["verdict"] = "hold"
    result = cycle.apply(data, cid, checked["proposal_sha256"], audit)
    assert result["held"] == 1
    with Store(data) as store:
        assert store.counts()["incident_revisions"] == 0


def test_audit_cannot_omit_or_approve_another_decision(prepared):
    data, cid = prepared
    checked = cycle.check(data, cid, proposal_for(data, cid), "Codex")
    audit = audit_for(checked); audit["items"][0]["decision_id"] = "other"
    with pytest.raises(AnalysisError, match="audit_decisions_mismatch"):
        cycle.apply(data, cid, checked["proposal_sha256"], audit)


def test_source_updated_after_prepare_requires_new_cycle(prepared, source):
    data, cid = prepared
    proposal = proposal_for(data, cid)
    with Store(data) as store, store.db:
        source_item = item_for(text="Nowa treść syntetycznej publikacji, która wymaga ponownego przeglądu.")
        store.add_material(source, source_item, "raw/synthetic-test", now())
    with pytest.raises(AnalysisError, match="state_changed"):
        cycle.check(data, cid, proposal, "Codex")


def test_commentary_requires_real_references_and_exact_text_audit(prepared):
    data, cid = prepared
    reviewed(prepared); cycle.calculate(data, cid)
    context, candidate, audit = commentary_for(data, cid)
    bad = copy.deepcopy(context); bad["findings"][0]["evidence_refs"] = ["made-up"]
    with pytest.raises(AnalysisError, match="unknown_evidence"):
        cycle.editorial_input(data, cid, bad, candidate)
    candidate["sentences"][0] = "Podmieniony tekst, którego nie objął przegląd redakcyjny."
    with pytest.raises(AnalysisError, match="text_changed"):
        cycle.finish(data, cid, context=context, candidate=candidate, audit=audit)


def test_editorial_hold_and_incomplete_context_do_not_publish(prepared):
    data, cid = prepared
    reviewed(prepared); cycle.calculate(data, cid)
    context, candidate, audit = commentary_for(data, cid)
    audit["checks"]["no_false_reassurance"] = False
    with pytest.raises(AnalysisError, match="held"):
        cycle.finish(data, cid, context=context, candidate=candidate, audit=audit)
    context["rtb"]["score"] = 68
    with pytest.raises(AnalysisError, match="context_mismatch"):
        cycle.editorial_input(data, cid, context, candidate)


def test_publish_requires_private_record_and_refuses_modified_text(prepared):
    data, cid = prepared
    reviewed(prepared); cycle.calculate(data, cid)
    ctx, candidate, audit = commentary_for(data, cid)
    receipt = cycle.finish(data, cid, context=ctx, candidate=candidate, audit=audit)
    path = Path(receipt["snapshot_dir"]); snap, cfg = load_snapshot(path)
    report = build_report(snap, cfg, commentary_record=load_commentary_record(path))
    repo = SupabasePublications("https://dubhsimiblpfcaudbvjb.supabase.co", "sb_secret_synthetic_key")
    repo._request = lambda *a: pytest.fail("No network call permitted")
    with pytest.raises(AnalysisError, match="record_required"):
        repo.publish(report)
    report["commentary"]["text"] = "Podmieniony tekst, który nie przeszedł kontroli."
    report["report_id"] = "rpt_" + digest({k: v for k, v in report.items() if k != "report_id"})
    with pytest.raises(ValueError, match="review registry"):
        validate_report(report)


def test_proposed_coordinates_are_never_inferred(prepared):
    data, cid = prepared
    proposal = proposal_for(data, cid)
    proposal["decisions"][0]["incident"]["location"]["geometry"] = {"type": "Point", "coordinates": [21, 52]}
    with pytest.raises(ValidationError):
        cycle.check(data, cid, proposal, "Codex")


def test_cli_fixture_publication_and_idempotent_retry(prepared, tmp_path, capsys):
    data, cid = prepared
    reviewed(prepared); cycle.calculate(data, cid); cycle.finish(data, cid)
    args = ["publish", "--data-dir", str(data), "--cycle", cid, "--local-store", str(tmp_path / "releases.sqlite")]
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["created"] and first["verified_readback"]
    assert main(args) == 0
    second = json.loads(capsys.readouterr().out)
    assert not second["created"] and second["verified_readback"]
    assert first["report_id"] == second["report_id"]


@pytest.mark.parametrize("response_lost_after_commit", [False, True])
def test_failed_publication_preserves_history_and_retries_frozen_report(
    prepared, tmp_path, capsys, monkeypatch, response_lost_after_commit
):
    from datetime import timedelta
    from osint_dashboard.common import instant
    from osint_dashboard.dashboard.publication import PublicationError

    data, cid = prepared
    reviewed(prepared); cycle.calculate(data, cid)
    receipt = cycle.finish(data, cid)
    snapshot, config = load_snapshot(Path(receipt["snapshot_dir"]))
    previous = copy.deepcopy(snapshot)
    previous["as_of"] = (instant(snapshot["as_of"]) - timedelta(days=1)).isoformat()
    previous["window"]["end"] = previous["as_of"]
    previous["window"]["start"] = (
        instant(snapshot["window"]["start"]) - timedelta(days=1)
    ).isoformat()
    old = build_report(previous, config)
    path = tmp_path / "releases.sqlite"
    repo = LocalPublications(path)
    repo.publish(old)
    args = ["publish", "--data-dir", str(data), "--cycle", cid, "--local-store", str(path)]
    publish = LocalPublications.publish

    def interrupted(self, report, **kwargs):
        if response_lost_after_commit:
            publish(self, report, **kwargs)
        raise PublicationError("Simulated connection failure")

    monkeypatch.setattr(LocalPublications, "publish", interrupted)
    assert main(args) == 1
    capsys.readouterr()
    folder, _ = cycle.load_cycle(data, cid)
    export = folder / "publication-daily.json"
    frozen = export.read_bytes()
    candidate = json.loads(frozen)
    assert not (folder / "published-daily.json").exists()
    assert repo.get(old["report_id"])["report"] == old
    expected_latest = candidate if response_lost_after_commit else old
    assert repo.latest()["report"] == expected_latest

    monkeypatch.setattr(LocalPublications, "publish", publish)
    assert main(args) == 0
    recovered = json.loads(capsys.readouterr().out)
    assert recovered["verified_readback"]
    assert recovered["created"] is not response_lost_after_commit
    assert recovered["report_id"] == candidate["report_id"]
    assert export.read_bytes() == frozen
    assert repo.latest()["report"] == candidate
    with repo.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 2


def test_snapshot_preserves_v02_military_preparation_category(prepared):
    data, cid = prepared
    proposal = proposal_for(data, cid)
    proposal["decisions"][0]["incident"].update(category="military_preparation", criteria=[])
    checked = cycle.check(data, cid, proposal, "Codex — test syntetyczny")
    cycle.apply(data, cid, checked["proposal_sha256"], audit_for(checked))
    result = cycle.calculate(data, cid)
    draft = read_json(Path(result["draft"]))
    assert draft["snapshot"]["incidents"][0]["category"] == "military_preparation"
    assert draft["snapshot"]["rtb"]["score"] == 10  # Missing preparation criteria never earn points.


def test_analysis_config_cannot_disable_audits_or_enable_model_api():
    from osint_dashboard.common import ROOT
    config = read_json(ROOT / "config/analysis.json")
    validate_schema("analysis/config", config)
    for key, value in (("require_evidence_audit", False), ("require_editorial_audit", False),
                           ("external_model_api", True), ("methodology_version", "rtb-v99")):
        with pytest.raises(ValidationError):
            validate_schema("analysis/config", {**config, key: value})


def test_presentation_metadata_survives_review_snapshot_and_publication(prepared):
    from osint_dashboard.dashboard.presentation import signal_presentation
    data, cid = prepared
    proposal = proposal_for(data, cid)
    event = proposal['decisions'][0]['incident']
    event['dashboard_context'] = {'topics': ['aviation'], 'kind': 'event', 'scope': 'national', 'region_ids': [], 'evidence_ids': ['place']}
    checked = cycle.check(data, cid, proposal, 'Codex — test syntetyczny')
    cycle.apply(data, cid, checked['proposal_sha256'], audit_for(checked))
    result = cycle.calculate(data, cid)
    assert result['score'] == 15  # Presentation is not a scoring input.
    folder, _ = cycle.load_cycle(data, cid)
    snap = read_json(folder / 'draft.json')['snapshot']
    assert snap['incidents'][0]['dashboard_context'] == event['dashboard_context']
    public = signal_presentation(snap['incidents'][0], [])
    assert public['version'] == 'signals-v1'
    assert public['topics'] == ['aviation']
    assert public['scope'] == 'national'
    assert 'evidence_ids' not in public


def test_regional_metadata_rejects_missing_evidence_or_unknown_regions(prepared):
    data, cid = prepared
    proposal = proposal_for(data, cid)
    event = proposal['decisions'][0]['incident']
    event['dashboard_context'] = {'topics': ['aviation'], 'kind': 'event', 'scope': 'regional', 'region_ids': ['PL-14'], 'evidence_ids': ['occurrence']}
    with pytest.raises((ValueError, AnalysisError), match='location|evidence|preview'):
        cycle.check(data, cid, proposal, 'Codex — test syntetyczny')
    event['dashboard_context']['evidence_ids'] = ['place']
    event['dashboard_context']['region_ids'] = ['PL-00']
    with pytest.raises(ValidationError):
        cycle.check(data, cid, proposal, 'Codex — test syntetyczny')


def test_reviewed_sections_are_exported_with_hash_and_tampering_is_rejected(prepared):
    data, cid = prepared
    reviewed(prepared); cycle.calculate(data, cid)
    context, candidate, audit = commentary_for(data, cid)
    candidate['sentences'] = [candidate['sentences'][0], candidate['sentences'][1]]
    candidate['sections'] = {'situation': 0, 'impact': 1}
    checked = cycle.editorial_input(data, cid, context, candidate)
    audit['subject_sha256'] = checked['subject_sha256']
    receipt = cycle.finish(data, cid, context=context, candidate=candidate, audit=audit)
    path = Path(receipt['snapshot_dir']); snap, cfg = load_snapshot(path)
    public = build_report(snap, cfg, commentary_record=load_commentary_record(path))
    assert public['commentary']['sections']['impact'] == candidate['sentences'][1]
    assert public['commentary']['review']['sections_sha256'] == digest(public['commentary']['sections'])
    validate_report(public)
    public['commentary']['sections']['impact'] = 'Podmienione zdanie bez przeglądu redakcyjnego.'
    public['report_id'] = 'rpt_' + digest({k:v for k,v in public.items() if k != 'report_id'})
    with pytest.raises(ValueError, match='sections'):
        validate_report(public)


def test_recommendation_cannot_be_inferred_from_an_incident_or_the_score(prepared):
    data, cid = prepared
    reviewed(prepared); cycle.calculate(data, cid)
    context, candidate, audit = commentary_for(data, cid)
    context['findings'][1]['role'] = 'recommendation'
    with pytest.raises(AnalysisError, match='without_current_instruction'):
        cycle.editorial_input(data, cid, context, candidate)


def test_city_reference_is_reviewed_metadata_not_incident_coordinates(prepared):
    from osint_dashboard.review import validate_evidence
    from osint_dashboard.dashboard.presentation import signal_presentation
    from copy import deepcopy
    data, cid = prepared
    event = proposal_for(data, cid)['decisions'][0]['incident']
    event['country'] = 'PL'
    event['location'].update(label='Łowicz', precision='city')
    event['dashboard_context'] = {'topics':['military'], 'kind':'event', 'scope':'regional',
                                 'region_ids':['PL-10'], 'evidence_ids':['place'], 'place_id':'lowicz'}
    # Metadata extraction must not overwrite the original event geometry.
    event['location']['geometry'] = None
    event['incident_id'] = 'evt_synthetic_city_reference'
    event['criteria'] = {p['key']:p['evidence_ids'] for p in event['criteria']}
    public = signal_presentation(event, [])
    assert public['map_anchor']['label'] == 'Łowicz'
    assert public['map_anchor']['precision'] == 'city'
    assert event['location']['geometry'] is None
    assert 'place_id' not in public and 'evidence_ids' not in public
    # Use real fixture materials to exercise evidence validation before mapping.
    from osint_dashboard.store import Store
    with Store(data) as store:
        materials = {e['material_id']:store.material(e['material_id']) for e in event['evidence']}
    validate_evidence(event, materials)
    for patch in ({'place_id':'missing-city'}, {'region_ids':['PL-18']}, {'evidence_ids':['occurrence']}):
        invalid = deepcopy(event); invalid['dashboard_context'].update(patch)
        with pytest.raises(ValueError, match='Map city|location evidence'):
            validate_evidence(invalid, materials)
