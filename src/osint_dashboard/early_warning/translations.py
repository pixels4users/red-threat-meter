from __future__ import annotations

import re

from ..common import canonical_json, digest, now
from .contracts import validate


def validate_translation(record, observation):
    data = observation["data"]
    if data["type"] != "publication":
        raise ValueError("Only publications can have text translations")
    if record["observation_id"] != observation["observation_id"] or record["source_title"] != data["title"] or record["source_text_hash"] != digest(data["text"]):
        raise ValueError("Translation does not match this publication version")
    if any(q not in data["text"] for q in record["basis_quotes"]):
        raise ValueError("Translation basis quote is absent from the source")
    # This is only a script check, not a claim that a machine validates translation
    # accuracy or Polish grammar. Semantic checking remains the translator's task.
    for value in [record["title_pl"], record["summary_pl"], *record["uncertainties_pl"]]:
        if re.search(r"[\u0400-\u052f]", value):
            raise ValueError("Polish display fields must not contain untranslated Cyrillic")


def import_translations(store, batch):
    from .store import check_raw

    validate("translation", batch)
    created_at = now()
    latest = {r["observation"]["observation_id"] for r in store.latest(created_at)}
    previous = store.translations(created_at)
    seen = set()
    with store.db:
        for item in batch["translations"]:
            oid = item["observation_id"]
            if oid not in latest or oid in seen:
                raise ValueError("Duplicate translation or superseded observation version")
            seen.add(oid)
            obs = store.observation(oid)
            check_raw(store.data_dir, obs["raw_refs"])
            validate_translation(item, obs)
            revision = previous.get(oid, {}).get("revision", 0)
            if item["previous_revision"] != revision:
                raise ValueError("Translation revision conflict")
            record = {**item, "revision": revision + 1, "created_at": created_at, "translator": batch["translator"],
                      "language": "pl", "scope": "translated_title_and_polish_summary"}
            record["translation_id"] = "ewt_" + digest(record)[:24]
            store.db.execute("INSERT INTO translations VALUES (?,?,?,?,?)",
                             (record["translation_id"], oid, revision + 1, created_at, canonical_json(record)))
    return {"imported": len(seen), "language": "pl", "scope": "translated_title_and_polish_summary"}


def display(observation, translation):
    if translation:
        validate_translation(translation, observation)
        return {"title": translation["title_pl"], "summary": translation["summary_pl"],
                "uncertainties": translation["uncertainties_pl"], "status": "ready",
                "translation_id": translation["translation_id"], "translator": translation["translator"]}
    return {"title": "Publikacja oczekująca na polskie tłumaczenie", "summary": "Oryginał zachowano w archiwum. Polski opis wymaga przygotowania dla tej wersji materiału.",
            "uncertainties": [], "status": "pending", "translation_id": None, "translator": None}
