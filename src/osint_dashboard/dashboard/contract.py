from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ..common import ROOT, digest, instant, read_json
from ..analysis.commentary import public_commentary
from ..dashboard_commentary import MARKUP, META, _fold
from ..review import validate_schema

VERSION = "dashboard-v1"
EXPORTER = "dashboard-export-v5"

GAPS = {
    'time_precision_limited': 'Część zdarzeń ma przybliżony czas; uwzględniamy najniższy uzasadniony wkład.',
    "domain_not_observed": "Część obszarów zagrożeń nie jest jeszcze objęta systematyczną obserwacją.",
    'event_history_unverified': 'Brakuje pełnej oceny historii zdarzeń z ostatnich dziewięciu dni.',
    "source_unavailable_or_partial": "Część źródeł jest niedostępna lub niepełna.",
    "source_window_incomplete": "Dostępne publikacje nie obejmują całego okresu.",
    "source_check_stale": "Część źródeł wymaga odświeżenia.",
    "source_config_changed": "Zakres obserwowanych źródeł uległ zmianie.",
    "unreviewed_candidates": "Ocena części doniesień nie została zakończona.",
    "unresolved_event": "Brakuje informacji potrzebnych do oceny zdarzeń.",
    "stale_event_review": "Pojawiły się aktualizacje wcześniej ocenionych doniesień.",
    "no_required_sources_configured": "Zakres obserwacji nie został jeszcze ustalony.",
}


def safe_url(value: str) -> str:
    """Keep source links, never credentials, private paths or active URL schemes."""
    p = urlsplit(value)
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
        raise ValueError("Invalid source URL")
    if p.hostname in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Local source URL is not publishable")
    # Preserve article identifiers while omitting tracking and credential fields.
    sensitive = {"token", "access_token", "key", "api_key", "apikey", "signature", "password", "secret", "auth"}
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if k.lower() not in sensitive and not k.lower().startswith("utm_")]
    return urlunsplit((p.scheme, p.netloc, p.path or "/", urlencode(query), ""))


def load_snapshot(folder: Path) -> tuple[dict, dict]:
    """Verify the frozen package; do not include replay inputs in the public export."""
    manifest = read_json(folder / "manifest.json")
    for name in ("snapshot.json", "replay-input.json", "incidents.geojson", "report.md"):
        if manifest.get("files", {}).get(name) != digest((folder / name).read_bytes()):
            raise ValueError("Snapshot integrity check failed")
    for name, expected in manifest.get("files", {}).items():
        if Path(name).name != name or digest((folder / name).read_bytes()) != expected:
            raise ValueError("Snapshot supplement integrity check failed")
    snapshot, inputs = read_json(folder / "snapshot.json"), read_json(folder / "replay-input.json")
    validate_schema("snapshot", snapshot)
    if any(snapshot[key] != inputs[key] for key in ("run_id", "mode", "as_of", "code_hash")):
        raise ValueError("Snapshot/input mismatch")
    if (snapshot["methodology_version"] != inputs["scoring"]["version"] or
            snapshot["config_hash"] != digest(inputs["scoring"])):
        raise ValueError("Snapshot methodology/configuration mismatch")
    if snapshot["source_config_hash"] != digest(inputs["source_config"]):
        raise ValueError("Source configuration mismatch")
    return snapshot, inputs["source_config"]


def load_commentary_record(folder: Path) -> dict | None:
    load_snapshot(folder)
    manifest = read_json(folder / "manifest.json")
    if "commentary-review.json" not in manifest["files"]:
        return None
    return read_json(folder / "commentary-review.json")


def source_status(check: dict | None, as_of: str, blocked: set[str]) -> str:
    if not check or check.get("status") not in ("ok", "partial"):
        return "unavailable"
    if ("source_check_stale" in blocked or
            abs((instant(as_of) - instant(check["checked_at"])).total_seconds()) > 8 * 3600):
        return "stale"
    if check["status"] == "partial" or not check.get("window_complete") or blocked:
        return "partial"
    return "current"


def comparison(current: dict, previous: dict | None) -> dict:
    empty = {"delta_points": None, "percent": None, "direction": "unavailable", "reference_report_id": None}
    if not previous:
        return empty
    validate_report(previous)
    if (current["mode"] != previous["mode"] or current["report_type"] != previous["report_type"] or
            instant(previous["as_of"]) >= instant(current["as_of"])):
        return empty
    for key in ("methodology_version", "config_hash", "source_config_hash", "code_hash"):
        if current["provenance"][key] != previous["provenance"][key]:
            return empty
    for key in ("timezone", "definition"):
        if current["window"][key] != previous["window"][key]:
            return empty
    a, b = current["rtb"]["score"], previous["rtb"]["score"]
    if a is None or b is None:
        return empty
    if current['provenance']['methodology_version'] == 'rtb-v0.4' and (
            current['rtb']['confidence']['comparison_key'] != previous['rtb']['confidence']['comparison_key']):
        return empty
    delta = a - b
    return {"delta_points": delta, "percent": round(100 * delta / b, 1) if b else None,
            "direction": "up" if delta > 0 else "down" if delta < 0 else "stable",
            "reference_report_id": previous["report_id"]}


def build_report(snapshot: dict, source_config: dict, *, report_type: str = "daily",
                 previous: dict | None = None, supersedes: str | None = None,
                 commentary_record: dict | None = None) -> dict:
    validate_schema("snapshot", snapshot)
    if digest(source_config) != snapshot["source_config_hash"]:
        raise ValueError("Use the source configuration frozen with this snapshot")
    cfg = {s["id"]: s for s in source_config["sources"] if s["enabled"]}
    checks = {s["source_id"]: s for s in snapshot["sources"]}
    blockers = snapshot["rtb"].get("quality_issues", snapshot["rtb"]["blockers"])
    gaps = []
    for code in dict.fromkeys(b.split(":", 1)[0] for b in blockers):
        gaps.append({"code": code if code in GAPS else "other", "message": GAPS.get(code, "Ocena sytuacji jest niepełna.")})
    sources = []
    for sid, source in sorted(cfg.items()):
        check = checks.get(sid)
        blocked = {b.split(":")[0] for b in blockers if b.endswith(":" + sid)}
        sources.append({"id": sid, "name": source["publisher"], "url": safe_url(source["url"]),
                        "required": source["required"], "status": source_status(check, snapshot["as_of"], blocked),
                        "checked_at": check["checked_at"] if check else None,
                        "window_complete": bool(check and check.get("window_complete")),
                        "item_count": check.get("item_count", 0) if check else 0})
    required = [s for s in sources if s["required"]]
    usable = sum(s["status"] == "current" for s in required)
    materials = {m["material_id"]: m for m in snapshot["materials"]}
    points = {c["incident_id"]: c["points"] for c in snapshot["rtb"]["contributions"]}
    exclusions = {c["incident_id"]: c["reason"] for c in snapshot["rtb"]["exclusions"]}
    incidents, features = [], []
    # Keep one version of an incident per release; multiple articles are evidence,
    # never extra incident rows. The scoring engine owns campaign deduplication.
    seen = set()
    for event in sorted(snapshot["incidents"], key=lambda e: (e["incident_id"], -e["revision"])):
        if event["incident_id"] in seen or instant(event["recorded_at"]) > instant(snapshot["as_of"]):
            continue
        seen.add(event["incident_id"])
        refs = []
        for mid in dict.fromkeys(e["material_id"] for e in event["evidence"]):
            m = materials[mid]
            if instant(m["fetched_at"]) > instant(snapshot["as_of"]):
                raise ValueError("Evidence after cutoff")
            refs.append({"id": mid, "source_id": m["source_id"], "publisher": m["publisher"],
                         "url": safe_url(m["url"]), "published_at": m["published_at"]})
        dates = [r["published_at"] for r in refs if r["published_at"] and instant(r["published_at"]) <= instant(snapshot["as_of"])]
        loc = event["location"]
        geometry = deepcopy(loc["geometry"])
        if geometry is not None and (geometry["type"] != "Point" or loc["precision"] in ("unknown", "country", "region") or not loc["evidence_ids"]):
            raise ValueError("A map point requires an evidenced point location")
        item = {"id": event["incident_id"], "revision_id": event["revision_id"], "revision": event["revision"],
                "title": event["title"], "summary": event["summary"], "category": event["category"],
                "status": event["status"], "country": event["country"], "occurred_on": event["occurred_on"],
                "published_at": min(dates, key=instant) if dates else None, "recorded_at": event["recorded_at"],
                "attribution": {k: event["attribution"][k] for k in ("actor", "status")},
                "location": {"label": loc["label"], "precision": loc["precision"], "geometry": geometry},
                "sources": refs, "rtb_points": points.get(event["incident_id"], 0),
                "review_current": exclusions.get(event["incident_id"]) not in ("superseded_review", "source_has_newer_version"),
                "reviewer_type": event["reviewer"]["type"]}
        from .presentation import signal_presentation
        item['presentation'] = signal_presentation(event, refs)
        incidents.append(item)
        if geometry:
            features.append({"type": "Feature", "id": item["id"], "geometry": geometry,
                             "properties": {"incident_id": item["id"], "representation": "incident_location"}})
    # National markers are presentation anchors, not coordinates assigned to an
    # incident. The frontend may place only explicitly country-level records at a
    # documented capital; no city/region guessing is performed here.
    exporter_files = sorted(Path(__file__).parent.glob("*.py")) + [ROOT / "schemas/dashboard/report.schema.json", ROOT / "config/signal-presentation.json", ROOT / "config/map-places.json"]
    result = {"contract_version": VERSION, "mode": snapshot["mode"], "report_type": report_type,
              "supersedes": supersedes, "as_of": snapshot["as_of"], "window": deepcopy(snapshot["window"]),
              "provenance": {**{k: snapshot[k] for k in ("run_id", "methodology_version", "config_hash", "source_config_hash", "code_hash")},
                             "snapshot_sha256": digest(snapshot), "exporter_version": EXPORTER,
                             "exporter_sha256": digest([(p.name, digest(p.read_bytes())) for p in exporter_files])},
              "rtb": {"score": snapshot["rtb"]["score"],
                      "status": "insufficient_data" if snapshot["rtb"]["score"] is None else "provisional" if snapshot["rtb"]["status"] == "provisional" else "available",
                      "components": deepcopy(snapshot["rtb"].get("components", {"hostile_activity": 0, "preparation": 0})),
                      "confidence": deepcopy(snapshot["rtb"].get("confidence", {"percent": None, "method": "not_calibrated"})),
                      "review_required": snapshot["rtb"].get("alert", {}).get("status") == "analyst_review_required"},
              "coverage": {"required_sources": len(required), "usable_sources": usable,
                           "percent": round(100 * usable / len(required)) if required else None,
                           "pending_review": snapshot["coverage"].get("unreviewed_current_candidates", 0)},
              "gaps": gaps, "sources": sources, "incidents": incidents,
              "geojson": {"type": "FeatureCollection", "features": features},
              "commentary": {"text": None},
              "limitations": ["Indeks eksperymentalny; nie jest prawdopodobieństwem eskalacji.",
                              "Obserwacja obejmuje skonfigurowane źródła, nie wszystkie zdarzenia w regionie."]}
    if commentary_record is not None:
        result["commentary"] = public_commentary(commentary_record, digest(snapshot), snapshot["run_id"], snapshot["rtb"]["score"])
    if snapshot['methodology_version'] in ('rtb-v0.3', 'rtb-v0.4'):
        result['rtb']['red_priority'] = deepcopy(snapshot['rtb']['red_priority'])
        result['rtb']['regions'] = {k: {field: deepcopy(v[field]) for field in ('score','components','direct_points','propagated_points','red_priority')}
                                  for k,v in snapshot['rtb']['regions'].items()}
        result['rtb']['official_warnings'] = [{k:w[k] for k in ('alert_key','authority','level','status','effective_at','valid_until','area','instruction_pl')}
                                             for w in snapshot['rtb']['official_warnings']]
    if snapshot["methodology_version"] != "rtb-v0.4" and bool(blockers) != (result["rtb"]["score"] is None):
        raise ValueError("Inconsistent score/completeness state")
    result["rtb"]["trend"] = comparison(result, previous)
    result["report_id"] = "rpt_" + digest(result)
    validate_report(result)
    return result


def validate_report(report: dict) -> None:
    validate_schema("dashboard/report", report)
    content = {k: v for k, v in report.items() if k != "report_id"}
    if report["report_id"] != "rpt_" + digest(content):
        raise ValueError("Report content hash mismatch")
    if report["commentary"]["text"] is not None:
        text = report["commentary"]["text"]
        review = report["commentary"].get("review")
        if (not review or review["snapshot_sha256"] != report["provenance"]["snapshot_sha256"] or
                review["text_sha256"] != digest(text) or report["rtb"]["score"] is None or
                META.search(_fold(text)) or MARKUP.search(text)):
            raise ValueError("A matching commentary review registry receipt is required")
    elif "review" in report["commentary"]:
        raise ValueError("Empty commentary cannot claim a review")
    sections = report['commentary'].get('sections')
    if sections is not None:
        if (not report['commentary']['text'] or
                report['commentary'].get('review', {}).get('sections_sha256') != digest(sections) or
                any(text not in report['commentary']['text'] for text in sections.values())):
            raise ValueError('Commentary sections require a matching editorial receipt')
    if instant(report["window"]["end"]) != instant(report["as_of"]):
        raise ValueError("Window must end at the analysis cutoff")
    if instant(report["window"]["start"]) > instant(report["as_of"]):
        raise ValueError("Invalid report window")
    ids = [i["id"] for i in report["incidents"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate incidents")
    source_ids = [s["id"] for s in report["sources"]]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Duplicate source states")
    for source in report["sources"]:
        if safe_url(source["url"]) != source["url"]:
            raise ValueError("Source URL must be sanitized before publication")
    for incident in report["incidents"]:
        anchor = incident.get('presentation', {}).get('map_anchor')
        if anchor and (safe_url(anchor['reference_url']) != anchor['reference_url'] or
                       incident['location']['precision'] != 'city' or
                       incident['location']['label'] != anchor['label']):
            raise ValueError('Map reference requires a matching city and sanitized source URL')
        for ref in incident["sources"]:
            if safe_url(ref["url"]) != ref["url"]:
                raise ValueError("Source URL must be sanitized before publication")
        if incident["published_at"] and instant(incident["published_at"]) > instant(report["as_of"]):
            raise ValueError("Publication after cutoff")
    expected = {i["id"]: i["location"]["geometry"] for i in report["incidents"] if i["location"]["geometry"]}
    actual = {f["id"]: f["geometry"] for f in report["geojson"]["features"]}
    if actual != expected or len(actual) != len(report["geojson"]["features"]):
        raise ValueError("Map and incidents disagree")
    if report["rtb"]["score"] is None and report["rtb"]["trend"]["delta_points"] is not None:
        raise ValueError("An incomplete report has no numeric trend")
