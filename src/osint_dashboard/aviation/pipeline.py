from __future__ import annotations

import os
import re
import shutil
import uuid
from datetime import timedelta

from ..common import ROOT, atomic_write, canonical_json, digest, instant, read_json, write_json
from ..pipeline import check_mode, locked
from .collector import collect
from .contracts import config, now, validate, validate_config, validate_sample
from .report import build_report, geojson, make_snapshot
from .store import Store, raw_bytes

FILES = {"replay-input.json", "snapshot.json", "report.md", "coverage.geojson"}


def code_hash():
    files = []
    for folder, pattern in (("src/osint_dashboard/aviation", "*.py"), ("schemas/aviation", "*.json"), ("migrations/aviation", "*.sql")):
        files.extend((ROOT / folder).glob(pattern))
    files.extend(ROOT / p for p in ("src/osint_dashboard/common.py", "src/osint_dashboard/pipeline.py", "scripts/aviation.py", "requirements.lock"))
    return digest([(str(p.relative_to(ROOT)), digest(p.read_bytes())) for p in sorted(files)])


def validate_inputs(inputs):
    validate_config(inputs["config"])
    cutoff = instant(inputs["as_of"])
    start = cutoff - timedelta(hours=inputs["config"]["history_hours"])
    ids = set()
    previous = None
    for sample in inputs["samples"]:
        validate_sample(sample)
        end = instant(sample["finished_at"])
        if not start <= end <= cutoff:
            raise ValueError("Sample was not known at cutoff or outside the report window")
        if sample["mode"] != inputs["mode"] or sample["sample_id"] in ids or previous and end < previous:
            raise ValueError("Invalid mode, order or duplicate sample")
        ids.add(sample["sample_id"])
        previous = end


def publish(store, inputs, snap):
    folder, run_id = store.folder, inputs["run_id"]
    target = folder / "snapshots" / run_id
    staging = folder / "snapshots" / (".staging-" + run_id)
    staging.mkdir(parents=True, exist_ok=False)
    try:
        write_json(staging / "replay-input.json", inputs)
        write_json(staging / "snapshot.json", snap)
        write_json(staging / "coverage.geojson", geojson(snap))
        atomic_write(staging / "report.md", build_report(snap))
        write_json(staging / "manifest.json", {"run_id": run_id, "files": {name: digest((staging / name).read_bytes()) for name in sorted(FILES)}})
        os.replace(staging, target)
        with store.db:
            store.db.execute("INSERT INTO releases VALUES (?,?,?)", (run_id, inputs["as_of"], canonical_json(snap["counts"])))
        write_json(folder / "latest.json", {"run_id": run_id, "as_of": inputs["as_of"],
                                            "report": f"snapshots/{run_id}/report.md", "snapshot": f"snapshots/{run_id}/snapshot.json",
                                            "geojson": f"snapshots/{run_id}/coverage.geojson"})
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return target


def run(folder, config_path=None, offline=False, mode="live", fetcher_factory=None, progress=lambda s: None):
    folder = folder.resolve()
    if folder in ((ROOT / "data").resolve(), (ROOT / "data/early_warning").resolve()):
        raise ValueError("Aviation requires its own data directory")
    if mode not in ("live", "fixture") or fetcher_factory and mode != "fixture":
        raise ValueError("Test fetchers require fixture mode")
    if mode == "fixture" and folder.is_relative_to(ROOT / "data") and not folder.is_relative_to(ROOT / "data/demo"):
        raise ValueError("Synthetic data cannot use the live data tree")
    cfg = config(config_path)
    with locked(folder):
        check_mode(folder, mode)
        with Store(folder) as store:
            if not offline:
                sample = collect(folder, cfg, mode, fetcher_factory(folder, cfg) if fetcher_factory else None, progress)
                store.add(sample)
            as_of = now()
            run_id = "av-" + instant(as_of).strftime("%Y-%m-%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
            inputs = {"run_id": run_id, "as_of": as_of, "mode": mode, "config": cfg,
                      "samples": store.samples(as_of, cfg["history_hours"]), "code_hash": code_hash()}
            validate_inputs(inputs)
            snap = make_snapshot(inputs, folder)
            validate("snapshot", snap)
            target = publish(store, inputs, snap)
            return {"run_id": run_id, "report": str(target / "report.md"), "counts": store.counts(),
                    "summary": snap["counts"], "latest_quality": snap["latest"]["metrics"] if snap["latest"] else None, "rtb_effect": "none"}


def replay(folder, run_id):
    if not re.fullmatch(r"av-[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{6}Z-[0-9a-f]{8}", run_id):
        raise ValueError("Invalid aviation release id")
    target = folder / "snapshots" / run_id
    manifest = read_json(target / "manifest.json")
    if set(manifest["files"]) != FILES or manifest["run_id"] != run_id:
        raise ValueError("Incomplete release manifest")
    for name, sha in manifest["files"].items():
        if digest((target / name).read_bytes()) != sha:
            raise ValueError("Release integrity check failed")
    inputs = read_json(target / "replay-input.json")
    if inputs["run_id"] != run_id or inputs["code_hash"] != code_hash():
        raise ValueError("Restore the recorded code and dependencies for replay")
    validate_inputs(inputs)
    for sample in inputs["samples"]:
        for receipt in sample["requests"]:
            if receipt["raw_ref"]:
                raw_bytes(folder, receipt["raw_ref"])
    snap = make_snapshot(inputs, folder)
    validate("snapshot", snap)
    for name, value in (("snapshot.json", snap), ("coverage.geojson", geojson(snap))):
        if canonical_json(value) != canonical_json(read_json(target / name)):
            raise ValueError("Replayed artifact differs: " + name)
    if build_report(snap) != (target / "report.md").read_text():
        raise ValueError("Replayed report differs")
    return {"run_id": run_id, "identical": True, "network_requests": 0, "samples_checked": len(inputs["samples"]), "rtb_effect": "none"}
