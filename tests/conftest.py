import copy
import json
from datetime import datetime, timedelta

import pytest

from osint_dashboard.common import ROOT, UTC, digest, now, read_json
from osint_dashboard.extract import extract_candidates
from osint_dashboard.review import import_review
from osint_dashboard.store import Store


@pytest.fixture
def source_config():
    return copy.deepcopy(read_json(ROOT / "config/sources.json"))


@pytest.fixture
def source(source_config):
    return source_config["sources"][0]


@pytest.fixture
def store(tmp_path):
    with Store(tmp_path / "data") as result:
        yield result


def item_for(index=1, text=None):
    today = datetime.now(UTC).date().isoformat()
    return {"url": f"https://www.gov.pl/web/rcb/synthetic-fixture-{index}",
            "title": f"TEST SYNTHETYCZNY — zdarzenie {index}", "published_at": now(),
            "text": text or f"TEST SYNTHETYCZNY. Dnia {today} rosyjski dron naruszył przestrzeń powietrzną Polski. Potwierdzono naruszenie przestrzeni NATO. To nie jest rzeczywiste zdarzenie.",
            "text_kind": "article_body"}


def seed(store, source, index=1, text=None, fetched_at=None):
    item = item_for(index, text)
    with store.db:
        material, _ = store.add_material(source, item, "raw/synthetic.bin", fetched_at or now())
    candidate = extract_candidates(store, [material])[0]
    return material, candidate


def decision_for(material, candidate, event_key="synthetic-drone-1"):
    text = material["text"]
    phrase = "rosyjski dron naruszył przestrzeń powietrzną Polski"
    today = datetime.now(UTC).date().isoformat()
    def ev(eid, claim, quote):
        return {"id": eid, "material_id": material["material_id"], "claim": claim, "stance": "supports",
                "quote": quote, "origin_id": "synthetic-authority", "origin_reason": "Pierwotny komunikat syntetyczny użyty wyłącznie w teście."}
    return {"kind": "incident", "candidate_ids": [candidate["candidate_id"]], "previous_revision": 0,
            "incident": {"event_key": event_key, "title": "TEST SYNTHETYCZNY — naruszenie przestrzeni", "summary": "Fikcyjny przypadek do sprawdzenia naliczania pięciu punktów, bez odniesienia do realnych wydarzeń.",
                         "category": "airspace_breach", "status": "confirmed_primary", "occurred_on": today,
                         "date_evidence_ids": ["timing"], "country": "PL",
                         "attribution": {"actor": "RU", "status": "confirmed_primary", "reason": "Wyłącznie syntetyczna atrybucja w danych testowych."},
                         "location": {"label": "Polska", "geometry": None, "precision": "country", "evidence_ids": []},
                         "criteria": {"nato_airspace_breach": ["criterion"]}, "campaign_id": None,
                         "evidence": [ev("occurrence", "occurrence", phrase), ev("attribution", "attribution", phrase),
                                      ev("timing", "timing", f"Dnia {today}"), ev("criterion", "criterion", "Potwierdzono naruszenie przestrzeni NATO")]}}


def batch(*decisions):
    return {"schema_version": "1", "reviewer": {"type": "agent", "name": "Synthetic test reviewer"}, "decisions": list(decisions)}


def source_checks(source_config, status="ok"):
    return [{"source_id": s["id"], "publisher": s["publisher"], "required": s["required"],
             "status": status, "checked_at": now(), "item_count": 1, "errors": [], "raw_refs": [],
             "window_complete": True, "scope": "synthetic_fixture", "source_definition_hash": digest(s)}
            for s in source_config["sources"] if s["enabled"]]


@pytest.fixture
def fixture_file(tmp_path, source_config):
    from osint_dashboard.common import write_json
    results = []
    for check in source_checks(source_config):
        check = {k: v for k, v in check.items() if k != "item_count"}
        check["items"] = [item_for()]
        results.append(check)
    path = tmp_path / "fixture.json"
    write_json(path, {"synthetic": True, "source_results": results})
    return path
