from __future__ import annotations

import re
from .common import canonical_json, digest

KEYWORDS = {
    "military_preparation": r"szpital.*polow|zapas.*amunic|logistyk.*wojsk|field hospital|military logistics|полев.*госпитал|военн.*логист",
    "sabotage": r"sabota|dywers|sabotage",
    "arms_explosion": r"eksploz|wybuch|explosion",
    "airspace_breach": r"naruszen.*przestrzeni|airspace.*(violation|breach)|wtargn.*przestrze",
    "air_activity": r"zagrożenie z powietrza|zagrożenie atakiem z powietrza|lotnictw|samolot|aircraft|fighter|dron|missile",
    "cyberattack": r"cyberatak|cyberattack|ddos|ransomware",
    "border_pressure": r"presj.*migrac|granicy.*białoru|migrant",
    "gps_jamming": r"gps|gnss|zagłuszan|jamming",
}


def make_candidate(material: dict) -> dict:
    text = (material["title"] + " " + material["text"]).lower()
    suggested = [key for key, pattern in KEYWORDS.items() if re.search(pattern, text)]
    flags = []
    if re.search(r"ćwicze|trening|exercise|drill|neutralizac.*niewybuch", material["title"].lower()):
        flags.append("possible_exercise_or_planned_activity")
    if re.search(r"odwoł|brak zagrożenia|zagrożenie ustało|aktualizac", text):
        flags.append("contains_update_or_cancellation")
    if material["text_kind"] not in ("article_body", "pdf_text", "official_dataset", "social_post"):
        flags.append("summary_only")
    if material["text_kind"].startswith("social_post"):
        flags.append("social_report_primary_origin_required")
    if material["published_at"] is None:
        flags.append("publication_date_unknown")
    return {"candidate_id": "cand_" + digest(material["material_id"])[:24],
            "material_id": material["material_id"], "document_id": material["document_id"],
            "title": material["title"], "url": material["url"], "source_id": material["source_id"],
            "published_at": material["published_at"], "suggested_categories": suggested or ["context"],
            "status": "unreviewed", "flags": flags,
            "method": "keyword_triage_v1_not_fact_verification"}


def extract_candidates(store, materials: list[dict]) -> list[dict]:
    candidates = []
    with store.db:
        for material in materials:
            candidate = make_candidate(material)
            store.db.execute("INSERT OR IGNORE INTO candidates VALUES (?,?,?)",
                             (candidate["candidate_id"], material["material_id"], canonical_json(candidate)))
            candidates.append(candidate)
    return candidates
