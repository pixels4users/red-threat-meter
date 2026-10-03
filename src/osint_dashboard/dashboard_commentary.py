"""Fail-closed presentation boundary for a future dashboard publisher.

No model calls, score changes, or writes to historical snapshots. Approval and
analysis completeness must come from the publisher, never the model response.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import unicodedata

from jsonschema import ValidationError

from .common import ROOT, read_json
from .review import validate_schema

LOGGER = logging.getLogger(__name__)
SYSTEM_PROMPT_PATH = ROOT / "prompts/dashboard-commentary-system.md"
PROMPT_VERSION = "dashboard-commentary-v3"
META = re.compile(
    r"\b(?:jako\s+(?:ai|model|asystent)|w\s+modelowym\s+scenariuszu|"
    r"as\s+an?\s+(?:ai|language\s+model)|nie\s+moge|nie\s+jestem\s+w\s+stanie|"
    r"nie\s+mam\s+dostepu|nie\s+posiadam\s+dostepu|"
    r"ponizej\s+(?:przedstawiam|prezentuje)|oto\s+(?:analiza|podsumowanie)|"
    r"mam\s+nadzieje|moge\s+(?:pomoc|przygotowac)|"
    r"model\s+jezykowy|sztuczna\s+inteligencja|"
    r"parser|traceback|stack\s*trace|system\s*prompt|llm|"
    r"json|schema|exception|parsererror|rtb-v\d|api\s*key|"
    r"blad\s+parsera|ocena\s+i\s+wklad\s+rtb\s+wymagaja\s+osobnego\s+przegladu)\b"
    r"|\b(?:zbieznosc\s+czasu\s+publikacji|dane\s+wskazuja\s+na|"
    r"doniesieni\w*\s+pozostaj\w*\s+niepotwierdzon\w*|"
    r"wymag\w*\s+(?:osobnego\s+)?przeglad\w*|"
    r"brakuje\s+niezaleznego\s+potwierdzenia|"
    r"informacja\s+.+?\s+pozostaje\s+niepotwierdzona)\b"
    r"|\b(?:error|warning)\s*:",
    re.IGNORECASE,
)
MARKUP = re.compile(r"[<>`{}\[\]*#]|https?://|(?:^|\s)(?:assistant|system):", re.I)
SENTENCE_BREAK = re.compile(r"[.!?][\"'»”]*\s+\S")


def build_generation_request(context: object) -> dict | None:
    """Load the actual system prompt and exclude uncertain input before the LLM.

    Context is assembled by a trusted reviewer/publisher. An LLM must not grant
    itself accepted status. This provider-neutral envelope performs no API call.
    """
    try:
        validate_schema("dashboard/commentary-context", context)
    except ValidationError:
        LOGGER.info("dashboard_generation_unavailable reason=invalid_context")
        return None
    if not context["analysis_complete"] or context["rtb"]["score"] is None:
        LOGGER.info("dashboard_generation_unavailable reason=analysis_incomplete")
        return None
    findings = context["findings"]
    if len({item["id"] for item in findings}) != len(findings):
        LOGGER.info("dashboard_generation_unavailable reason=duplicate_finding")
        return None
    accepted = [item for item in findings if item["status"] == "accepted"]
    if any(not item["evidence_refs"] for item in accepted):
        LOGGER.info("dashboard_generation_unavailable reason=evidence_missing")
        return None
    if not accepted or not any(ref != "rtb:score" for item in accepted for ref in item["evidence_refs"]):
        LOGGER.info("dashboard_generation_unavailable reason=verified_findings_missing")
        return None
    # Exclude uncertain/rejected prose entirely, rather than asking the model
    # to filter it after reading it or infer the missing parts from the score.
    packet = {key: context[key] for key in ("snapshot_id", "mode", "rtb")}
    packet["findings"] = [{key: item[key] for key in ("id", "role", "text_pl", "evidence_refs")} for item in accepted]
    prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return {
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(packet, ensure_ascii=False, sort_keys=True)},
        ],
        "output_schema": {"anyOf": [read_json(ROOT / "schemas/dashboard/commentary-candidate.schema.json"), {"type": "null"}]},
    }


def candidate_digest(candidate: dict) -> str:
    """Bind independent editorial approval to this exact text AND snapshot."""
    raw = json.dumps(candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _fold(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", text.casefold()).replace("ł", "l")
        if unicodedata.category(char) != "Mn"
    )


def _reject(reason: str) -> dict:
    # Log a fixed code only: validation exceptions may contain the entire input.
    LOGGER.info("dashboard_commentary_unavailable reason=%s", reason)
    return {"text": None}


def prepare_commentary(
    candidate: object,
    *,
    expected_snapshot_id: str,
    analysis_complete: bool = False,
    approved_sha256: str | None = None,
) -> dict:
    """Return only public text or null. Never strip offending clauses and publish.

    The publisher supplies the digest after a separate editorial/evidence review.
    A keyword filter alone cannot guarantee the meaning or language of arbitrary
    generated prose; unreviewed, changed or out-of-context drafts stay private.
    """
    if analysis_complete is not True:
        return _reject("analysis_incomplete")
    if candidate is None:
        return _reject("missing")
    try:
        validate_schema("dashboard/commentary-candidate", candidate)
    except ValidationError:
        return _reject("invalid_contract")
    if not expected_snapshot_id or candidate["snapshot_id"] != expected_snapshot_id:
        return _reject("snapshot_mismatch")
    sentences = candidate["sentences"]
    if any(
        unicodedata.category(char).startswith("C") or unicodedata.category(char) in ("Zl", "Zp")
        for sentence in sentences for char in sentence
    ):
        return _reject("control_characters")
    text = " ".join(sentence.strip() for sentence in sentences)
    if len(text) > 600 or any(SENTENCE_BREAK.search(sentence.strip()) for sentence in sentences):
        return _reject("not_concise_sentences")
    if any(not sentence.strip().endswith(".") for sentence in sentences):
        return _reject("incomplete_prose")
    if MARKUP.search(text) or META.search(_fold(text)):
        return _reject("non_editorial_content")
    if (
        not isinstance(approved_sha256, str)
        or not re.fullmatch(r"[0-9a-f]{64}", approved_sha256)
        or not hmac.compare_digest(approved_sha256, candidate_digest(candidate))
    ):
        return _reject("approval_missing_or_changed")
    result = {"text": text}
    if 'sections' in candidate:
        indices = list(candidate['sections'].values())
        if len(set(indices)) != len(indices) or set(indices) != set(range(len(sentences))):
            return _reject('invalid_section_assignment')
        result['sections'] = {key: sentences[index].strip() for key, index in candidate['sections'].items()}
    return result
