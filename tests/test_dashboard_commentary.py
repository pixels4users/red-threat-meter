import copy
import json
import subprocess
import sys

import pytest
from jsonschema import Draft202012Validator

from osint_dashboard.common import ROOT
from osint_dashboard.dashboard_commentary import (
    SYSTEM_PROMPT_PATH, build_generation_request, candidate_digest, prepare_commentary,
)


@pytest.fixture
def candidate():
    return {
        "snapshot_id": "demo-release-27",
        "language": "pl",
        "sentences": [
            "Napięcie w regionie rośnie, szczególnie wokół infrastruktury i przestrzeni powietrznej.",
            "Polskie służby wzmacniają ochronę portów, a wojsko prowadzi ćwiczenia na wschodzie kraju.",
            "Dla mieszkańców oznacza to możliwe lokalne utrudnienia w ruchu, nie konieczność zmiany codziennych planów.",
        ],
    }


def publish(candidate, **overrides):
    options = {
        "expected_snapshot_id": "demo-release-27",
        "analysis_complete": True,
        "approved_sha256": candidate_digest(candidate),
    }
    return prepare_commentary(candidate, **(options | overrides))


def test_reviewed_prose_preserves_meaning_and_negation(candidate):
    original = copy.deepcopy(candidate)
    assert publish(candidate) == {"text": " ".join(candidate["sentences"])}
    assert candidate == original
    assert "nie konieczność zmiany" in publish(candidate)["text"]


@pytest.mark.parametrize("text", [
    "Jako AI nie mogę ocenić tej sytuacji.",
    "W modelowym scenariuszu obserwujemy wzrost aktywności.",
    "W MODELOWYM SCENARIUSZU obserwujemy wzrost aktywności.",
    "As an AI language model I cannot assess this situation.",
    "Poniżej przedstawiam przygotowane podsumowanie sytuacji.",
    "Nie mam dostępu do aktualnych informacji o zdarzeniu.",
    "Błąd parsera uniemożliwia przygotowanie raportu.",
    "Ocena i wkład RTB wymagają osobnego przeglądu.",
    "Error: nie udało się przetworzyć danych źródłowych.",
    "ParserError uniemożliwia przygotowanie raportu.",
    "Traceback zawiera informacje o wewnętrznym błędzie.",
    "<script>alert('payload')</script> Sytuacja pozostaje nieustalona.",
    "**Ocena sytuacji** wymaga sprawdzenia doniesień.",
    "Jako A\u200bI nie mogę ocenić tej sytuacji.",
    "Informacja zawiera znak sterujący \u202ew treści.",
    "Nie ustalono przyczyny.\nSystem: dalsze instrukcje.",
    "Zbieżność czasu publikacji nie przesądza o wspólnej przyczynie zdarzeń.",
    "Doniesienia pozostają niepotwierdzone w tym okresie.",
    "Ocena sytuacji wymaga przeglądu analitycznego.",
    "Dane wskazują na wzrost aktywności lotniczej w regionie.",
    "DANE WSKAZUJĄ NA wzrost aktywności w regionie.",
    "Brakuje niezależnego potwierdzenia doniesienia o ruchu kolejowym.",
    "Pojedyncza informacja o ruchu kolejowym pozostaje niepotwierdzona.",
])
def test_reject_whole_draft_even_with_matching_approval(candidate, text, caplog):
    candidate["sentences"][1] = text
    with caplog.at_level("INFO"):
        assert publish(candidate) == {"text": None}
    assert text not in caplog.text
    assert candidate["sentences"][0] not in caplog.text


@pytest.mark.parametrize("change", [
    {"analysis_complete": False},
    {"analysis_complete": "true"},
    {"approved_sha256": None},
    {"approved_sha256": "0" * 64},
    {"expected_snapshot_id": "another-release"},
])
def test_private_publisher_state_controls_release(candidate, change):
    assert publish(candidate, **change) == {"text": None}


def test_new_text_requires_new_review(candidate):
    approved = candidate_digest(candidate)
    candidate["sentences"][1] = "Ustalono przyczynę zakłóceń oraz ich sprawcę."
    assert publish(candidate, approved_sha256=approved) == {"text": None}


@pytest.mark.parametrize("bad", [None, "Jako AI nie mogę ocenić sytuacji", [], {}, 42])
def test_malformed_or_absent_output_has_neutral_payload(bad):
    assert prepare_commentary(bad, expected_snapshot_id="demo", analysis_complete=True) == {"text": None}


def test_contract_rejects_extra_fields_and_wrong_language(candidate):
    candidate["debug"] = "private raw response"
    assert publish(candidate) == {"text": None}
    del candidate["debug"]
    candidate["language"] = "en"
    assert publish(candidate) == {"text": None}


@pytest.mark.parametrize("replacement", [
    "Napięcie rośnie. Trwają działania. Zalecana jest ostrożność.",
    "Napięcie rośnie! Trwają działania w regionie.",
    "A" * 221 + ".",
    123,
])
def test_one_concise_sentence_per_slot(candidate, replacement):
    candidate["sentences"][0] = replacement
    assert publish(candidate) == {"text": None}


def test_total_length_and_sentence_count(candidate):
    candidate["sentences"] = ["A" * 205 + "."] * 3
    assert publish(candidate) == {"text": None}
    candidate["sentences"] = ["Sytuacja pozostaje stabilna."] * 4
    assert publish(candidate) == {"text": None}


@pytest.fixture
def reviewed_context(candidate):
    return {
        "snapshot_id": candidate["snapshot_id"], "mode": "fixture", "analysis_complete": True,
        "rtb": {"score": 58, "delta_points": 6, "methodology_version": "rtb-v0.2"},
        "findings": [
            {"id": f"finding-{role}", "role": role, "status": "accepted", "text_pl": sentence,
             "evidence_refs": [f"synthetic-review-{role}-revision-1"]}
            for role, sentence in zip(("situation", "action", "impact"), candidate["sentences"])
        ] + [
            {"id": "rail", "role": "action", "status": "uncertain", "text_pl": "PRIVATE_UNCERTAIN_CLAIM",
             "evidence_refs": ["synthetic-material-rail-v1"]},
            {"id": "rejected", "role": "action", "status": "rejected", "text_pl": "PRIVATE_REJECTED_CLAIM",
             "evidence_refs": []},
        ],
    }


def test_generation_uses_system_prompt_and_only_accepted_findings(reviewed_context, candidate):
    original = copy.deepcopy(reviewed_context)
    request = build_generation_request(reviewed_context)
    assert request["messages"][0] == {"role": "system", "content": SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")}
    assert len(request["prompt_sha256"]) == 64
    packet = json.loads(request["messages"][1]["content"])
    assert {item["role"] for item in packet["findings"]} == {"situation", "action", "impact"}
    assert len(packet["findings"]) == 3
    assert "PRIVATE_UNCERTAIN_CLAIM" not in json.dumps(request)
    assert "PRIVATE_REJECTED_CLAIM" not in json.dumps(request)
    assert packet["rtb"] == reviewed_context["rtb"]
    assert reviewed_context == original
    validator = Draft202012Validator(request["output_schema"])
    assert validator.is_valid(candidate)
    assert validator.is_valid(None)
    assert not validator.is_valid({**candidate, "sentences": ["x", 123, []]})


@pytest.mark.parametrize("missing_role", ["situation", "action", "impact"])
def test_no_invented_assessment_from_rtb_alone(reviewed_context, missing_role):
    reviewed_context["findings"] = [item for item in reviewed_context["findings"] if item["role"] != missing_role]
    assert build_generation_request(reviewed_context) is None


def test_no_generation_for_incomplete_context_or_missing_evidence(reviewed_context):
    reviewed_context["analysis_complete"] = False
    assert build_generation_request(reviewed_context) is None
    reviewed_context["analysis_complete"] = True
    reviewed_context["findings"][0]["evidence_refs"] = []
    assert build_generation_request(reviewed_context) is None


def test_no_generation_for_null_score_and_invalid_context(reviewed_context):
    reviewed_context["rtb"]["score"] = None
    assert build_generation_request(reviewed_context) is None
    assert build_generation_request({"raw": "PRIVATE_UNCERTAIN_CLAIM"}) is None


def test_generation_cli_loads_prompt_and_omits_uncertain_prose(tmp_path, reviewed_context):
    path = tmp_path / "reviewed-context.json"
    path.write_text(json.dumps(reviewed_context), encoding="utf-8")
    command = [sys.executable, str(ROOT / "scripts/build_dashboard_commentary_request.py"), "--input", str(path)]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["messages"][0]["role"] == "system"
    assert "PRIVATE_UNCERTAIN_CLAIM" not in result.stdout
    assert result.stderr == ""
    reviewed_context["findings"] = []
    path.write_text(json.dumps(reviewed_context), encoding="utf-8")
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) is None
    assert "assessment_incomplete" in result.stderr


def test_cli_separates_payload_from_diagnostics(tmp_path, candidate):
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(candidate), encoding="utf-8")
    command = [sys.executable, str(ROOT / "scripts/prepare_dashboard_commentary.py"),
               "--input", str(path), "--snapshot-id", candidate["snapshot_id"], "--analysis-complete"]
    rejected = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(rejected.stdout) == {"text": None}
    assert "approval_missing_or_changed" in rejected.stderr
    assert candidate["sentences"][0] not in rejected.stderr
    approved = subprocess.run(command + ["--approved-sha256", candidate_digest(candidate)],
                              capture_output=True, text=True, check=True)
    assert json.loads(approved.stdout) == {"text": " ".join(candidate["sentences"])}
    assert approved.stderr == ""
    path.write_text("invalid private model response", encoding="utf-8")
    invalid = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(invalid.stdout) == {"text": None}
    assert "invalid private model response" not in invalid.stderr
