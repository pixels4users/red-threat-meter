from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

from .collect import collect_source
from .common import ROOT, atomic_write, canonical_json, digest, instant, load_config, load_scoring, now, read_json, write_json
from .extract import extract_candidates
from .report import build_report, geojson
from .review import import_review, validate_schema
from .scoring import score, window_for
from .store import Store


@contextmanager
def locked(data_dir: Path):
    data_dir.mkdir(parents=True, exist_ok=True)
    with (data_dir / ".pipeline.lock").open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another process is using this data directory") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def check_mode(data_dir: Path, mode: str) -> None:
    path = data_dir / ".mode.json"
    if path.exists():
        if read_json(path)["mode"] != mode:
            raise ValueError("Fixture and live data must use separate directories")
    else:
        write_json(path, {"mode": mode})


def code_hash() -> str:
    files = list((ROOT / "src/osint_dashboard").glob("*.py"))
    files += list((ROOT / "schemas").glob("*.json")) + list((ROOT / "migrations").glob("*.sql"))
    files += list((ROOT / "agents").glob("*.md")) + [ROOT / "skills/rss-feeds/scripts/feed.py"]
    files += list((ROOT / "src/osint_dashboard/analysis").glob("*.py"))
    files += list((ROOT / "schemas/analysis").glob("*.json"))
    files += list((ROOT / "prompts").glob("analysis-*.md"))
    files += list((ROOT / "schemas/dashboard").glob("commentary-*.schema.json"))
    files += [ROOT / "prompts/dashboard-commentary-system.md"]
    # The GNSS bridge reuses these numerical contracts; freeze them for replay.
    files += list((ROOT / "src/osint_dashboard/early_warning").glob("*.py"))
    files += list((ROOT / "schemas/early-warning").glob("*.json"))
    files += [ROOT / 'requirements.lock', ROOT / 'config/signal-presentation.json', ROOT / 'config/map-places.json']
    return digest([(str(p.relative_to(ROOT)), digest(p.read_bytes())) for p in sorted(files)])


def cached_checks(store) -> list[dict]:
    row = store.db.execute("SELECT run_id FROM runs WHERE status IN ('complete','collected') ORDER BY finished_at DESC,rowid DESC LIMIT 1").fetchone()
    if row is None:
        raise ValueError("No previous collection exists; run collection first")
    return [json.loads(r[0]) for r in store.db.execute("SELECT payload FROM source_checks WHERE run_id=?", (row[0],))]


def create_inputs(store, source_config, scoring, checks, as_of, mode, run_id) -> dict:
    latest = store.latest_materials(as_of)
    candidates = extract_candidates(store, latest)
    incidents = store.latest_incidents(as_of)
    all_materials = {m["material_id"]: m for m in latest}
    for event in incidents:
        for evidence in event["evidence"]:
            mid = evidence["material_id"]
            if mid not in all_materials:
                all_materials[mid] = store.material(mid)
    return {"run_id": run_id, "as_of": as_of, "mode": mode, "source_config": source_config,
            "scoring": scoring, "source_checks": checks, "materials": list(all_materials.values()),
            "latest_material_ids": [m["material_id"] for m in latest], "candidates": candidates,
            "incidents": incidents, "resolutions": store.resolutions(as_of), "code_hash": code_hash()}


def make_snapshot(inputs: dict) -> dict:
    rtb, coverage = score(inputs)
    candidates = []
    for candidate in inputs["candidates"]:
        resolution = inputs["resolutions"].get(candidate["candidate_id"])
        candidates.append({**candidate, "status": resolution["kind"] if resolution else "unreviewed",
                           "resolution_reason": resolution["reason"] if resolution else None})
    keys = ("material_id", "source_id", "publisher", "title", "url", "published_at", "fetched_at", "text_kind")
    snapshot = {"schema_version": "1", "run_id": inputs["run_id"], "as_of": inputs["as_of"],
                "mode": inputs["mode"], "methodology_version": inputs["scoring"]["version"],
                "config_hash": digest(inputs["scoring"]), "code_hash": inputs["code_hash"],
                "source_config_hash": digest(inputs["source_config"]),
                "window": window_for(inputs["as_of"], inputs["scoring"]), "rtb": rtb, "coverage": coverage,
                "sources": inputs["source_checks"], "incidents": inputs["incidents"], "candidates": candidates,
                "materials": [{k: m[k] for k in keys} for m in inputs["materials"]],
                "limitations": inputs["scoring"]["limitations"]}
    validate_schema("snapshot", snapshot)
    return snapshot


def publish(store, inputs: dict, snapshot: dict, extras: dict | None = None) -> Path:
    data_dir, run_id = store.data_dir, inputs["run_id"]
    target = data_dir / "snapshots" / run_id
    staging = data_dir / "snapshots" / (".staging-" + run_id)
    staging.mkdir(parents=True, exist_ok=False)
    try:
        write_json(staging / "snapshot.json", snapshot)
        write_json(staging / "incidents.geojson", geojson(snapshot))
        report_text = build_report(snapshot)
        if (extras or {}).get("commentary-review.json"):
            from .analysis.commentary import public_commentary
            commentary = public_commentary(extras["commentary-review.json"], digest(snapshot), snapshot["run_id"], snapshot["rtb"]["score"])
            report_text += "\n## Komentarz analityczny\n\n" + commentary["text"] + "\n"
        atomic_write(staging / "report.md", report_text)
        write_json(staging / "replay-input.json", inputs)
        for name, content in (extras or {}).items():
            if name not in ("analysis-audit.json", "commentary-review.json"):
                raise ValueError("Unknown snapshot supplement")
            write_json(staging / name, content)
        manifest = {"run_id": run_id, "schema_version": "1", "files": {
            p.name: digest(p.read_bytes()) for p in staging.iterdir() if p.is_file()}}
        write_json(staging / "manifest.json", manifest)
        os.replace(staging, target)
        with store.db:
            store.db.execute("INSERT INTO snapshots VALUES (?,?,?)", (run_id, inputs["as_of"], canonical_json(snapshot)))
        store.finish_run(run_id, "complete")
        write_json(data_dir / "latest.json", {"run_id": run_id, "as_of": snapshot["as_of"],
                                              "snapshot": f"snapshots/{run_id}/snapshot.json",
                                              "report": f"snapshots/{run_id}/report.md",
                                              "geojson": f"snapshots/{run_id}/incidents.geojson"})
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return target


def run(data_dir: Path, sources_path: Path | None = None, offline: bool = False,
        fixture: Path | None = None, review_path: Path | None = None, collect_only: bool = False,
        progress=lambda message: None, methodology: str | None = None) -> dict:
    data_dir = data_dir.resolve()
    mode = "fixture" if fixture else "live"
    source_config = load_config(sources_path)
    scoring = load_scoring(methodology)
    enabled = [s for s in source_config["sources"] if s["enabled"]]
    run_id = now().replace(":", "").replace("+0000", "Z") + "-" + uuid.uuid4().hex[:8]
    with locked(data_dir):
        check_mode(data_dir, mode)
        with Store(data_dir) as store:
            store.start_run(run_id)
            try:
                checks = []
                new_materials = 0
                if fixture:
                    fixture_data = read_json(fixture)
                    if fixture_data.get("synthetic") is not True:
                        raise ValueError("Fixture must declare synthetic=true")
                    outcomes = fixture_data["source_results"]
                    for outcome in outcomes:
                        outcome["checked_at"] = now()
                elif offline:
                    outcomes = []
                    checks = cached_checks(store)
                    progress("Używam zapisanych materiałów; daty kontroli źródeł pozostają bez zmian.")
                else:
                    start = instant(window_for(now(), scoring)["start"])
                    progress(f"Pobieram {len(enabled)} źródła.")
                    from .osw import pending_backlog
                    latest, resolutions = store.latest_materials(now()), store.resolutions(now())
                    backlogs = {s["id"]: pending_backlog(latest, resolutions, s["id"])
                                for s in enabled if s.get("article_parser") == "osw"}
                    with ThreadPoolExecutor(max_workers=3) as pool:
                        futures = [(s, pool.submit(collect_source, s, data_dir, start, backlog=backlogs.get(s["id"], ()),
                                                  known_full_urls={m["url"] for m in latest if m["source_id"] == s["id"] and
                                                                   m["text_kind"] in ("article_body", "pdf_text")}))
                                   for s in enabled]
                        outcomes = []
                        for source, future in futures:
                            result = future.result()
                            progress(f"{source['id']}: {result['status']}; publikacji: {len(result['items'])}")
                            outcomes.append(result)
                source_by_id = {s["id"]: s for s in enabled}
                with store.db:
                    for outcome in outcomes:
                        source = source_by_id[outcome["source_id"]]
                        for item in outcome["items"]:
                            raw_ref = item.get("raw_ref")
                            if mode == "fixture":
                                raw_ref = f"raw/fixtures/{digest(item)}.json"
                                write_json(data_dir / raw_ref, item)
                            if not raw_ref or not (data_dir / raw_ref).is_file():
                                raise ValueError("Material must reference an archived raw response")
                            _, added = store.add_material(source, item, raw_ref, outcome["checked_at"])
                            new_materials += int(added)
                        checks.append({k: v for k, v in outcome.items() if k != "items"} | {"item_count": len(outcome["items"])})
                    for check in checks:
                        store.db.execute("INSERT INTO source_checks VALUES (?,?,?)", (run_id, check["source_id"], canonical_json(check)))
                as_of = now()
                inputs = create_inputs(store, source_config, scoring, checks, as_of, mode, run_id)
                queue_path = data_dir / "runs" / run_id / "review_queue.json"
                write_json(queue_path, {"instructions": "agents/evidence-reviewer.md", "mode": mode,
                                        "candidates": inputs["candidates"], "materials": inputs["materials"],
                                        "existing_resolutions": inputs["resolutions"]})
                write_json(queue_path.with_name("review-input.json"), inputs)
                if collect_only:
                    store.finish_run(run_id, "collected")
                    return {"run_id": run_id, "new_materials": new_materials, "review_queue": str(queue_path), "counts": store.counts()}
                reviewed = None
                if review_path:
                    reviewed = import_review(store, read_json(review_path))
                    as_of = now()
                    inputs = create_inputs(store, source_config, scoring, checks, as_of, mode, run_id)
                snapshot = make_snapshot(inputs)
                target = publish(store, inputs, snapshot)
                return {"run_id": run_id, "mode": mode, "new_materials": new_materials, "review": reviewed,
                        "rtb": snapshot["rtb"]["score"], "blockers": snapshot["rtb"]["blockers"],
                        "report": str(target / "report.md"), "snapshot": str(target / "snapshot.json"),
                        "review_queue": str(queue_path), "counts": store.counts()}
            except Exception as exc:
                store.finish_run(run_id, "failed", f"{type(exc).__name__}: {str(exc)[:500]}")
                raise


def replay(data_dir: Path, run_id: str) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9T_.+-]+", run_id):
        raise ValueError("Invalid run identifier")
    folder = data_dir / "snapshots" / run_id
    manifest = read_json(folder / "manifest.json")
    for filename, expected in manifest["files"].items():
        if Path(filename).name != filename or digest((folder / filename).read_bytes()) != expected:
            raise ValueError("Snapshot integrity check failed")
    inputs = read_json(folder / "replay-input.json")
    if inputs["code_hash"] != code_hash():
        raise ValueError("Code or schemas changed; restore the recorded version before exact replay")
    reconstructed = make_snapshot(inputs)
    expected = read_json(folder / "snapshot.json")
    if canonical_json(reconstructed) != canonical_json(expected):
        raise ValueError("Replay result differs from the saved snapshot")
    return {"run_id": run_id, "identical": True, "rtb": reconstructed["rtb"]["score"], "network_requests": 0}
