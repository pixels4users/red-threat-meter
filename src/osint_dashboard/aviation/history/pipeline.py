from __future__ import annotations

import os
import re
import shutil
import uuid

from ...common import ROOT, atomic_write, canonical_json, digest, instant, read_json, write_json
from ...pipeline import check_mode, locked
from ..pipeline import replay as replay_live
from .contracts import now, validate, validate_acquisition
from .report import build_report, geojson, make_snapshot

FILES = {"replay-input.json", "snapshot.json", "report.md", "coverage.geojson"}


def code_hash():
    files = []
    for relative, pattern in (("src/osint_dashboard/aviation/history", "*.py"), ("src/osint_dashboard/aviation", "*.py"),
                              ("src/osint_dashboard", "*.py"), ("schemas/aviation/history", "*.json")):
        files.extend((ROOT / relative).glob(pattern))
    files.extend(ROOT / name for name in ("scripts/aviation_history.py", "requirements.lock"))
    return digest([(str(p.relative_to(ROOT)), digest(p.read_bytes())) for p in sorted(files)])


def live_references(folder, cfg):
    refs = []
    for ident in cfg["live_releases"]:
        replay_live(folder, ident)
        path = folder / "snapshots" / ident / "snapshot.json"
        snap = read_json(path)
        latest = snap["latest"]
        if not latest:
            raise ValueError("Referencja API nie zawiera próby")
        refs.append({"run_id": ident, "source_snapshot_sha256": digest(path.read_bytes()), "source_code_hash": snap["code_hash"],
                     "mode": snap["mode"], "bbox": snap["region"]["bbox"], "available_at": snap["as_of"],
                     "started_at": latest["started_at"], "finished_at": latest["finished_at"], "status": latest["status"],
                     "identifiers": sorted(r["identifier"] for r in latest["records"] if r["quality"] == "fresh")})
    return refs


def report(folder, live_folder=None):
    folder = folder.resolve()
    live_folder = live_folder or ROOT / "data/aviation"
    with locked(folder):
        pointer = read_json(folder / "latest-collection.json")
        if not re.fullmatch(r"ahc-\d{8}T\d{6}Z-[0-9a-f]{8}", pointer["id"]) or pointer["path"] != f"collections/{pointer['id']}.json":
            raise ValueError("Nieprawidłowy wskaźnik pobrania")
        acq = read_json(folder / pointer["path"])
        if digest(acq) != pointer["sha256"] or acq["id"] != pointer["id"]:
            raise ValueError("Zmienione wejścia pobrania")
        validate_acquisition(acq)
        check_mode(folder, acq["mode"])
        as_of = now()
        ident = "ah-" + instant(as_of).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        inputs = {"run_id": ident, "as_of": as_of, "code_hash": code_hash(), "acquisition": acq,
                  "live_references": live_references(live_folder, acq["config"])}
        snap = make_snapshot(inputs, folder)
        validate("snapshot", snap)
        target = folder / "snapshots" / ident
        stage = folder / "snapshots" / (".staging-" + ident)
        stage.mkdir(parents=True, exist_ok=False)
        try:
            write_json(stage / "replay-input.json", inputs)
            write_json(stage / "snapshot.json", snap)
            write_json(stage / "coverage.geojson", geojson(snap))
            atomic_write(stage / "report.md", build_report(snap))
            write_json(stage / "manifest.json", {"run_id": ident, "files": {name: digest((stage / name).read_bytes()) for name in sorted(FILES)}})
            os.replace(stage, target)
            write_json(folder / "latest.json", {"run_id": ident, "report": f"snapshots/{ident}/report.md"})
        finally:
            if stage.exists():
                shutil.rmtree(stage)
        return {"run_id": ident, "report": str(target / "report.md"), "counts": snap["counts"], "comparisons": snap["live_comparisons"], "rtb_effect": "none"}


def replay(folder, ident):
    if not re.fullmatch(r"ah-\d{8}T\d{6}Z-[0-9a-f]{8}", ident):
        raise ValueError("Nieprawidłowy identyfikator wydania historii")
    target = folder / "snapshots" / ident
    manifest = read_json(target / "manifest.json")
    if manifest["run_id"] != ident or set(manifest["files"]) != FILES:
        raise ValueError("Niepełny manifest wydania")
    for name, sha in manifest["files"].items():
        if digest((target / name).read_bytes()) != sha:
            raise ValueError("Zmienione pliki wydania")
    inputs = read_json(target / "replay-input.json")
    if inputs["run_id"] != ident or inputs["code_hash"] != code_hash():
        raise ValueError("Odtwórz wskazaną wersję kodu i zależności")
    snap = make_snapshot(inputs, folder)
    validate("snapshot", snap)
    for name, value in (("snapshot.json", snap), ("coverage.geojson", geojson(snap))):
        if canonical_json(value) != canonical_json(read_json(target / name)):
            raise ValueError("Odtworzony wynik różni się od archiwum")
    if build_report(snap) != (target / "report.md").read_text():
        raise ValueError("Odtworzony raport różni się od archiwum")
    return {"run_id": ident, "identical": True, "network_requests": 0, "raw_files_checked": sum(bool(r["raw_ref"]) for r in inputs["acquisition"]["requests"]), "rtb_effect": "none"}
