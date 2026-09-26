import copy
from datetime import datetime

import pytest

from osint_dashboard.common import ROOT, UTC, now, read_json
from osint_dashboard.pipeline import create_inputs
from osint_dashboard.report import geojson
from osint_dashboard.review import import_review, validate_evidence
from osint_dashboard.scoring import alert_for, score
from conftest import batch, decision_for, seed, source_checks


def preparation_inputs(store, source, source_config, country="BY", regional_proof=False):
    today = datetime.now(UTC).date().isoformat()
    statements = {
        "occurrence": "Rosyjskie wojsko rozbudowało zaplecze medyczne na Białorusi.",
        "timing": f"Dnia {today}",
        "logistics_or_medical_change": "Dodano trzy szpitale polowe.",
        "baseline_anomaly": "Wzrost z jednego do czterech szpitali względem poprzednich 30 dni przy tym samym pokryciu obserwacji.",
        "operational_relevance": "Nowe zaplecze obsługuje zgromadzone oddziały wojskowe.",
        "routine_explanation_checked": "Sprawdzono plan ćwiczeń i rotacje; nowa infrastruktura pozostała po zakończeniu ćwiczeń.",
        "kaliningrad_oblast": "Wariant regionalny testu dotyczy obwodu królewieckiego.",
    }
    material, candidate = seed(store, source, text="TEST SYNTHETYCZNY, NIE PRAWDZIWE ZDARZENIE. " + " ".join(statements.values()))
    decision = decision_for(material, candidate, "synthetic-preparation")
    event = decision["incident"]
    event.update(category="military_preparation", country=country,
                 title="TEST SYNTHETYCZNY — przygotowania wojskowe")
    evidence = []
    for key, quote in statements.items():
        evidence.append({"id": key, "claim": key if key in ("occurrence", "timing") else "criterion",
                         "material_id": material["material_id"], "quote": quote, "stance": "supports",
                         "origin_id": "synthetic-authority", "origin_reason": "Syntetyczny komunikat do testów, bez związku z rzeczywistymi wydarzeniami."})
    evidence.append({**evidence[0], "id": "attribution", "claim": "attribution"})
    event["evidence"] = evidence
    event["criteria"] = {k: [k] for k in ("logistics_or_medical_change", "baseline_anomaly", "operational_relevance", "routine_explanation_checked")}
    if regional_proof:
        event["criteria"]["kaliningrad_oblast"] = ["kaliningrad_oblast"]
    import_review(store, batch(decision))
    return create_inputs(store, source_config, read_json(ROOT / "config/scoring-v0.json"),
                         source_checks(source_config), now(), "fixture", "v02-test")


def test_preparation_scores_separately_from_hostile_activity(store, source, source_config):
    result, _ = score(preparation_inputs(store, source, source_config))
    assert result["score"] == 25
    assert result["components"] == {"hostile_activity": 0, "preparation": 15}
    assert result["alert"] == {"status": "no_threshold_triggered", "triggered_rules": [], "calibrated": False}


@pytest.mark.parametrize("country,regional_proof,expected", [("RU", False, 10), ("RU", True, 25), ("UA", True, 10), ("PL", False, 10)])
def test_preparation_requires_permitted_country_and_regional_evidence(store, source, source_config, country, regional_proof, expected):
    result, _ = score(preparation_inputs(store, source, source_config, country, regional_proof))
    assert result["score"] == expected


@pytest.mark.parametrize("missing", ["logistics_or_medical_change", "baseline_anomaly", "operational_relevance", "routine_explanation_checked"])
def test_preparation_without_each_necessary_finding_is_excluded(store, source, source_config, missing):
    inputs = preparation_inputs(store, source, source_config)
    del inputs["incidents"][0]["criteria"][missing]
    result, _ = score(inputs)
    assert result["score"] == 10
    assert result["exclusions"][0]["reason"] == "category_criteria_not_met"


def test_preparation_caps_and_campaign_deduplication(store, source, source_config):
    inputs = preparation_inputs(store, source, source_config)
    for i in range(4):
        event = copy.deepcopy(inputs["incidents"][0])
        event.update(incident_id=f"event-{i}", revision_id=f"revision-{i}", candidate_ids=[f"candidate-{i}"])
        inputs["resolutions"][f"candidate-{i}"] = {"revision_ids": {f"event-{i}": f"revision-{i}"}}
        inputs["incidents"].append(event)
    result, _ = score(inputs)
    assert result["score"] == 40
    assert result["components"]["preparation"] == 30
    for event in inputs["incidents"]:
        event["campaign_id"] = "synthetic-one-operation"
    result, _ = score(inputs)
    assert result["score"] == 25
    assert len(result["contributions"]) == 1


def test_strategic_priority_requires_location_evidence_and_never_adds_points(store, source, source_config):
    inputs = preparation_inputs(store, source, source_config)
    event = inputs["incidents"][0]
    event["strategic_context"] = {"area_ids": ["brest_region"], "reason": "Syntetyczna lokalizacja służąca wyłącznie sprawdzeniu walidatora.", "evidence_ids": ["occurrence"]}
    materials = {m["material_id"]: m for m in inputs["materials"]}
    with pytest.raises(ValueError, match="location evidence"):
        validate_evidence(event, materials)
    event["evidence"].append({**event["evidence"][0], "id": "location", "claim": "location"})
    event["strategic_context"]["evidence_ids"] = ["location"]
    result, _ = score(inputs)
    assert result["score"] == 25
    assert geojson({"run_id": "synthetic", "incidents": [event]})["features"][0]["properties"]["strategic_area_ids"] == ["brest_region"]


@pytest.mark.parametrize("kind", ["doctrine", "reference"])
def test_reference_kind_cannot_prove_incident(store, source, source_config, kind):
    inputs = preparation_inputs(store, source, source_config)
    materials = {m["material_id"]: {**m, "source_kind": kind} for m in inputs["materials"]}
    with pytest.raises(ValueError, match="cannot serve as incident evidence"):
        validate_evidence(inputs["incidents"][0], materials)


def test_review_threshold_is_strict_and_never_evaluates_incomplete_score(store, source, source_config):
    config = read_json(ROOT / "config/scoring-v0.json")
    assert alert_for(60, config)["status"] == "no_threshold_triggered"
    assert alert_for(61, config)["status"] == "analyst_review_required"
    assert alert_for(None, config)["status"] == "not_assessed"
    inputs = preparation_inputs(store, source, source_config)
    inputs["source_checks"][0]["status"] = "error"
    result, _ = score(inputs)
    assert result["score"] is None
    assert result["components"]["preparation"] == 15
    assert result["alert"]["status"] == "not_assessed"


def test_unknown_operator_preparation_does_not_score(store, source, source_config):
    inputs = preparation_inputs(store, source, source_config)
    inputs["incidents"][0]["attribution"].update(actor="unknown", status="unverified")
    result, _ = score(inputs)
    assert result["score"] == 10
    assert result["components"]["preparation"] == 0
