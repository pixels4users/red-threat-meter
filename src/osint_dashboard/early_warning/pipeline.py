from __future__ import annotations

import os
import re
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

import h3

from ..common import ROOT, atomic_write, canonical_json, digest, instant, now, read_json, write_json
from ..pipeline import check_mode, locked
from .collectors import collect
from .contracts import config, validate_observation
from .report import build_report, geojson, make_snapshot
from .store import Store, check_raw, import_reviews
from .translations import import_translations, validate_translation

FILES = {"snapshot.json", "report.md", "observations.geojson", "replay-input.json", "review_queue.json", "translation_queue.json"}


def code_hash():
    files = list((ROOT / "src/osint_dashboard/early_warning").glob("*.py"))
    for folder, pattern in (("schemas/early-warning", "*.json"), ("migrations/early-warning", "*.sql"),
                            ("agents/early-warning", "*.md")):
        files += list((ROOT / folder).glob(pattern))
    files += [ROOT / p for p in ("src/osint_dashboard/common.py", "src/osint_dashboard/collect.py",
                                "src/osint_dashboard/pipeline.py", "skills/rss-feeds/scripts/feed.py", "requirements.lock")]
    return digest({"files": [(str(p.relative_to(ROOT)), digest(p.read_bytes())) for p in sorted(files)], "h3": h3.versions()})


def validate_inputs(inputs):
    cutoff = instant(inputs["as_of"])
    for record in inputs["observations"]:
        obs = record["observation"]
        validate_observation(obs)
        if instant(record["last_fetched_at"]) > cutoff or instant(obs["times"]["first_seen_at"]) > cutoff:
            raise ValueError("Observation was not known at the report cutoff")
    if any(instant(c["checked_at"]) > cutoff for c in inputs["source_checks"]):
        raise ValueError("Source check was not known at cutoff")
    if any(instant(r["created_at"]) > cutoff for r in inputs["reviews"].values()):
        raise ValueError("Review was not known at cutoff")
    by_id = {r["observation"]["observation_id"]: r["observation"] for r in inputs["observations"]}
    for oid, translation in inputs["translations"].items():
        if instant(translation["created_at"]) > cutoff:
            raise ValueError("Translation was not known at cutoff")
        if oid in by_id:
            validate_translation(translation, by_id[oid])


def queue(inputs, snapshot):
    ids = {s["observation_id"] for s in snapshot["signals"]}
    return {"schema_version": "ew-queue-1", "mode": inputs["mode"], "as_of": inputs["as_of"],
            "instructions": "agents/early-warning/reviewer.md",
            "items": [{**r, "previous_review": inputs["reviews"].get(r["observation"]["observation_id"])}
                      for r in inputs["observations"] if r["observation"]["observation_id"] in ids]}


def translation_queue(inputs, snapshot):
    ids = {p["observation_id"] for p in snapshot["publications"]}
    return {"schema_version": "ew-translation-queue-1", "language": "pl", "mode": inputs["mode"], "as_of": inputs["as_of"],
            "instructions": "agents/early-warning/translator.md",
            "items": [{**r, "source_text_hash": digest(r["observation"]["data"]["text"]),
                       "previous_translation": inputs["translations"].get(r["observation"]["observation_id"])}
                      for r in inputs["observations"] if r["observation"]["observation_id"] in ids]}


def publish(store, inputs, snapshot):
    run_id, data_dir = inputs["run_id"], store.data_dir
    target = data_dir / "snapshots" / run_id
    staging = data_dir / "snapshots" / (".staging-" + run_id)
    staging.mkdir(parents=True, exist_ok=False)
    try:
        write_json(staging / "replay-input.json", inputs)
        write_json(staging / "snapshot.json", snapshot)
        write_json(staging / "review_queue.json", queue(inputs, snapshot))
        write_json(staging / "translation_queue.json", translation_queue(inputs, snapshot))
        write_json(staging / "observations.geojson", geojson(inputs, snapshot))
        atomic_write(staging / "report.md", build_report(snapshot))
        write_json(staging / "manifest.json", {"run_id": run_id, "files": {name: digest((staging / name).read_bytes()) for name in sorted(FILES)}})
        os.replace(staging, target)
        with store.db:
            store.db.execute("INSERT INTO releases VALUES (?,?,?)", (run_id, inputs["as_of"], canonical_json(snapshot["counts"])))
        write_json(data_dir / "latest.json", {"run_id": run_id, "as_of": inputs["as_of"],
                                             "report": f"snapshots/{run_id}/report.md", "snapshot": f"snapshots/{run_id}/snapshot.json",
                                             "review_queue": f"snapshots/{run_id}/review_queue.json", "translation_queue": f"snapshots/{run_id}/translation_queue.json",
                                             "geojson": f"snapshots/{run_id}/observations.geojson"})
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return target


def run(data_dir: Path, config_path=None, days=None, offline=False, review_path=None,
        mode="live", fetcher_factory=None, progress=lambda m: None, translation_path=None):
    data_dir = data_dir.resolve()
    if data_dir == (ROOT / "data").resolve():
        raise ValueError("Early observations require a separate data directory")
    if mode not in ("live", "fixture"):
        raise ValueError("Invalid data mode")
    if mode == "fixture" and data_dir.is_relative_to(ROOT / "data") and not data_dir.is_relative_to(ROOT / "data/demo"):
        raise ValueError("Synthetic data cannot use the live data tree")
    if fetcher_factory and mode != "fixture":
        raise ValueError("Test fetchers require fixture mode")
    cfg = config(config_path)
    days = cfg["refresh_days"] if days is None else days
    if not 1 <= days <= 90:
        raise ValueError("Collection must be bounded to 1–90 days")
    if (review_path or translation_path) and not offline:
        raise ValueError("Review or translate an existing version with the offline command")
    run_id = "ew-" + now().replace(":", "").replace("+0000", "Z") + "-" + uuid.uuid4().hex[:8]
    with locked(data_dir):
        check_mode(data_dir, mode)
        with Store(data_dir) as store:
            new_count = 0
            if not offline:
                end = instant(now()).date() - timedelta(days=1)
                sources = [s for s in cfg["sources"] if s["enabled"]]
                with ThreadPoolExecutor(max_workers=2) as pool:
                    tasks = [(s, pool.submit(collect, s, cfg, data_dir, days, end,
                                            fetcher_factory(s, data_dir) if fetcher_factory else None, progress)) for s in sources]
                    for source, task in tasks:
                        observations, check = task.result()
                        with store.db:
                            for obs in observations:
                                new_count += int(store.add(obs, run_id))
                            store.add_check(run_id, check)
                        progress(f"{source['id']}: {check['status']}; obserwacje: {len(observations)}.")
            reviewed = import_reviews(store, read_json(review_path)) if review_path else None
            translated = import_translations(store, read_json(translation_path)) if translation_path else None
            as_of = now()
            inputs = {"run_id": run_id, "as_of": as_of, "mode": mode, "config": cfg,
                      "observations": store.latest(as_of), "source_checks": store.checks(as_of),
                      "reviews": store.reviews(as_of), "translations": store.translations(as_of), "code_hash": code_hash()}
            validate_inputs(inputs)
            snapshot = make_snapshot(inputs)
            target = publish(store, inputs, snapshot)
            return {"run_id": run_id, "mode": mode, "new_observation_versions": new_count,
                    "review": reviewed, "translation": translated, "counts": store.counts(), "report": str(target / "report.md"),
                    "review_queue": str(target / "review_queue.json"), "summary": snapshot["counts"], "rtb_effect": "none"}


def replay(data_dir: Path, run_id: str):
    if not re.fullmatch(r"ew-[A-Za-z0-9T_.+-]+", run_id):
        raise ValueError("Invalid early-warning release identifier")
    folder = data_dir / "snapshots" / run_id
    manifest = read_json(folder / "manifest.json")
    if set(manifest["files"]) != FILES or manifest["run_id"] != run_id:
        raise ValueError("Release manifest is incomplete")
    for name, expected in manifest["files"].items():
        if digest((folder / name).read_bytes()) != expected:
            raise ValueError("Release integrity check failed")
    inputs = read_json(folder / "replay-input.json")
    if inputs["run_id"] != run_id or inputs["code_hash"] != code_hash():
        raise ValueError("Code, dependencies or contracts changed; restore the recorded version for exact replay")
    validate_inputs(inputs)
    refs = set()
    for record in inputs["observations"]:
        refs.update(record["observation"]["raw_refs"])
        refs.update(record["last_raw_refs"])
    for check in inputs["source_checks"]:
        refs.update(check["raw_refs"])
    check_raw(data_dir, sorted(refs))
    snapshot = make_snapshot(inputs)
    for name, value in (("snapshot.json", snapshot), ("review_queue.json", queue(inputs, snapshot)),
                        ("translation_queue.json", translation_queue(inputs, snapshot)),
                        ("observations.geojson", geojson(inputs, snapshot))):
        if canonical_json(value) != canonical_json(read_json(folder / name)):
            raise ValueError("Replayed artifact differs: " + name)
    if build_report(snapshot) != (folder / "report.md").read_text():
        raise ValueError("Replayed report differs")
    return {"run_id": run_id, "identical": True, "network_requests": 0, "raw_files_checked": len(refs), "rtb_effect": "none"}
