import copy
from datetime import datetime, timedelta

import pytest

from osint_dashboard.common import ROOT, UTC, now, read_json
from osint_dashboard.pipeline import create_inputs
from osint_dashboard.review import import_review
from osint_dashboard.scoring import score, window_for
from conftest import batch, decision_for, seed, source_checks


def reviewed_inputs(store, source, source_config):
    material, candidate = seed(store, source)
    import_review(store, batch(decision_for(material, candidate)))
    return create_inputs(store, source_config, read_json(ROOT / "config/scoring-v0.json"),
                         source_checks(source_config), now(), "fixture", "test-run")


def test_verified_event_adds_five_points_only_once(store, source, source_config):
    inputs = reviewed_inputs(store, source, source_config)
    result, _ = score(inputs)
    assert result["score"] == 15
    inputs["incidents"] *= 20
    again, _ = score(inputs)
    assert again["score"] == 15
    assert len(again["contributions"]) == 1


@pytest.mark.parametrize("change,reason", [
    ({"country": "UA"}, "outside_geographic_scope"),
    ({"attribution": {"actor": "unknown", "status": "unverified", "reason": "Nie ustalono sprawcy."}}, "hostile_attribution_not_confirmed"),
    ({"status": "refuted"}, "occurrence_not_confirmed"),
    ({"occurred_on": None}, "occurrence_date_unknown"),
    ({"criteria": {}}, "category_criteria_not_met"),
    ({"category": "context"}, "context_only"),
])
def test_unqualified_events_do_not_score(store, source, source_config, change, reason):
    inputs = reviewed_inputs(store, source, source_config)
    inputs["incidents"][0].update(change)
    result, _ = score(inputs)
    assert result["score"] == (None if reason == "occurrence_date_unknown" else 10)
    assert result["exclusions"][0]["reason"] == reason


def test_old_event_in_new_article_not_counted(store, source, source_config):
    inputs = reviewed_inputs(store, source, source_config)
    inputs["incidents"][0]["occurred_on"] = (datetime.now(UTC).date() - timedelta(days=30)).isoformat()
    result, _ = score(inputs)
    assert result["score"] == 10
    assert result["exclusions"][0]["reason"] == "outside_event_window"


def test_missing_source_gates_number_instead_of_lowering_risk(store, source, source_config):
    inputs = reviewed_inputs(store, source, source_config)
    inputs["source_checks"][0]["status"] = "error"
    result, _ = score(inputs)
    assert result["score"] is None
    assert result["capped_reviewed_sum"] == 5


def test_unreviewed_or_incomplete_window_blocks_number(store, source, source_config):
    inputs = reviewed_inputs(store, source, source_config)
    inputs["resolutions"] = {}
    inputs["source_checks"][0]["window_complete"] = False
    result, coverage = score(inputs)
    assert result["score"] is None
    assert coverage["unreviewed_current_candidates"] == 1
    assert any(b.startswith("source_window_incomplete") for b in result["blockers"])


def test_campaign_and_category_caps(store, source, source_config):
    inputs = reviewed_inputs(store, source, source_config)
    original = inputs["incidents"][0]
    for i in range(10):
        event = copy.deepcopy(original)
        event["incident_id"] = f"new-{i}"
        event["revision_id"] = f"rev-{i}"
        event["candidate_ids"] = [f"cand-{i}"]
        inputs["resolutions"][f"cand-{i}"] = {"revision_ids": {f"new-{i}": f"rev-{i}"}}
        inputs["incidents"].append(event)
    result, _ = score(inputs)
    assert result["score"] == 35  # 10 base + category cap 25
    for event in inputs["incidents"]:
        event["campaign_id"] = "one-campaign"
    result, _ = score(inputs)
    assert result["score"] == 15


def test_warsaw_calendar_window_handles_dst():
    config = read_json(ROOT / "config/scoring-v0.json")
    w = window_for("2026-03-30T12:00:00+00:00", config)
    assert w["start"] == "2026-03-23T23:00:00+00:00"


def test_later_source_revision_invalidates_earlier_review(store, source, source_config):
    inputs = reviewed_inputs(store, source, source_config)
    inputs["latest_material_ids"] = []
    result, _ = score(inputs)
    assert result["score"] is None
    assert result["exclusions"][0]["reason"] == "source_has_newer_version"


def test_source_configuration_change_requires_fresh_collection(store, source, source_config):
    inputs = reviewed_inputs(store, source, source_config)
    inputs["source_config"]["sources"][0]["url"] += "-different"
    result, _ = score(inputs)
    assert result["score"] is None
    assert "source_config_changed:rcb" in result["blockers"]


def test_old_publication_with_unreviewed_content_still_needs_review(store, source, source_config):
    inputs = reviewed_inputs(store, source, source_config)
    inputs["candidates"][0]["published_at"] = "2020-01-01T00:00:00+00:00"
    inputs["resolutions"] = {}
    result, coverage = score(inputs)
    assert result["score"] is None
    assert coverage["unreviewed_current_candidates"] == 1
