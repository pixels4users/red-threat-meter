import copy
import json
import sqlite3
from datetime import datetime, timedelta

import pytest

from osint_dashboard.common import UTC, now
from osint_dashboard.extract import extract_candidates
from osint_dashboard.review import import_review
from conftest import batch, decision_for, item_for, seed


def test_import_is_idempotent_and_history_append_only(store, source):
    material, candidate = seed(store, source)
    review = batch(decision_for(material, candidate))
    assert import_review(store, review)["new_revisions"] == 1
    assert import_review(store, review)["new_revisions"] == 0
    assert store.counts()["incident_revisions"] == 1
    with pytest.raises(sqlite3.IntegrityError, match="Append-only"):
        store.db.execute("DELETE FROM materials")
    store.db.rollback()


def test_fabricated_quote_and_false_corroboration_rejected(store, source):
    material, candidate = seed(store, source)
    decision = decision_for(material, candidate)
    decision["incident"]["evidence"][0]["quote"] = "To nie występuje w materiale źródłowym"
    with pytest.raises(ValueError, match="not present"):
        import_review(store, batch(decision))
    decision = decision_for(material, candidate)
    decision["incident"]["status"] = "corroborated"
    with pytest.raises(ValueError, match="corroboration"):
        import_review(store, batch(decision))
    assert store.counts()["incident_revisions"] == 0


def test_syndicated_copies_not_independent(store, source):
    m1, c1 = seed(store, source)
    source2 = {**source, "id": "second_publisher", "kind": "secondary", "publisher": "Second publisher"}
    m2, c2 = seed(store, source2)
    decision = decision_for(m1, c1)
    decision["candidate_ids"].append(c2["candidate_id"])
    evidence = copy.deepcopy(decision["incident"]["evidence"][0])
    evidence.update(id="copy", material_id=m2["material_id"])
    decision["incident"]["evidence"].append(evidence)
    decision["incident"]["status"] = "corroborated"
    with pytest.raises(ValueError, match="corroboration"):
        import_review(store, batch(decision))


def test_correction_creates_revision_and_keeps_original(store, source):
    material, candidate = seed(store, source)
    decision = decision_for(material, candidate)
    import_review(store, batch(decision))
    changed = copy.deepcopy(decision)
    changed["previous_revision"] = 1
    changed["incident"]["status"] = "refuted"
    changed["incident"]["summary"] = "Skorygowano syntetyczną ocenę po sprawdzeniu nowych informacji."
    import_review(store, batch(changed))
    assert store.counts()["incident_revisions"] == 2
    assert store.latest_incidents(now())[0]["status"] == "refuted"
    old = json.loads(store.db.execute("SELECT payload FROM incident_revisions WHERE revision=1").fetchone()[0])
    assert old["status"] == "confirmed_primary"


def test_batch_rolls_back_on_stale_revision(store, source):
    m, c = seed(store, source)
    first = decision_for(m, c)
    import_review(store, batch(first))
    new = decision_for(m, c, "synthetic-second-event")
    stale = copy.deepcopy(first)
    stale["incident"]["summary"] = "Zmieniona ocena, lecz podano niewłaściwą poprzednią rewizję."
    with pytest.raises(ValueError, match="Stale"):
        import_review(store, batch(new, stale))
    assert store.counts()["incident_revisions"] == 1


def test_one_article_can_describe_two_events(store, source):
    material, candidate = seed(store, source)
    one = decision_for(material, candidate)
    two = decision_for(material, candidate, "synthetic-drone-2")
    result = import_review(store, batch(one, two))
    assert result["new_revisions"] == 2
    assert len(store.resolutions(now())[candidate["candidate_id"]]["revision_ids"]) == 2
    repeated = import_review(store, batch(one, two))
    assert repeated["new_resolutions"] == repeated["new_revisions"] == 0


def test_exclusion_then_reinstatement_preserves_each_transition(store, source):
    material, candidate = seed(store, source)
    decision = decision_for(material, candidate)
    import_review(store, batch(decision))
    exclusion = {"kind": "exclude", "candidate_ids": [candidate["candidate_id"]],
                 "reason": "Tymczasowe wyłączenie syntetycznego przykładu."}
    import_review(store, batch(exclusion))
    assert store.resolutions(now())[candidate["candidate_id"]]["kind"] == "exclude"
    result = import_review(store, batch(decision))
    assert result["new_revisions"] == 0
    assert result["new_resolutions"] == 1
    assert store.resolutions(now())[candidate["candidate_id"]]["kind"] == "incident"
    assert store.counts()["resolutions"] == 3


def test_updated_source_requires_new_review_and_reversion_is_observed(store, source):
    t0 = datetime.now(UTC) - timedelta(seconds=10)
    m1, c1 = seed(store, source, fetched_at=t0.isoformat())
    import_review(store, batch(decision_for(m1, c1)))
    original = item_for()
    original["published_at"] = m1["published_at"]
    changed = {**original, "text": original["text"] + " Sprostowanie."}
    with store.db:
        m2, _ = store.add_material(source, changed, "raw/new.bin", (t0 + timedelta(seconds=1)).isoformat())
    with pytest.raises(ValueError, match="newer version"):
        import_review(store, batch(decision_for(m1, c1)))
    with store.db:
        m3, added = store.add_material(source, original, "raw/old.bin", (t0 + timedelta(seconds=2)).isoformat())
    assert not added
    assert m3["material_id"] == m1["material_id"]
    assert store.latest_materials(now())[0]["material_id"] == m1["material_id"]


def test_backup_restores_integrity_and_records(store, source, tmp_path):
    seed(store, source)
    path = tmp_path / "backup.sqlite3"
    store.backup(path)
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db.execute("SELECT COUNT(*) FROM materials").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 1
