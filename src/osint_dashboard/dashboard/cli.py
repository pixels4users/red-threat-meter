from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..common import ROOT, read_json, write_json
from ..pipeline import run
from .contract import build_report, load_snapshot, load_commentary_record
from .publication import LocalPublications, SupabasePublications, load_environment


def main(argv=None):
    p = argparse.ArgumentParser(description="Publikacje dashboardu — ręcznie, bez harmonogramu")
    p.add_argument("command", choices=["export", "publish", "cycle", "status"])
    p.add_argument("--snapshot-dir", type=Path)
    p.add_argument("--input", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--type", choices=["daily", "weekly"], default="daily")
    p.add_argument("--supersedes")
    p.add_argument("--data-dir", type=Path, default=ROOT / "data")
    p.add_argument("--offline", action="store_true")
    p.add_argument("--fixture", type=Path)
    p.add_argument("--review", type=Path)
    p.add_argument("--local-store", type=Path, help="Izolowana baza publikacji do testów; wyłącznie dane fixture")
    args = p.parse_args(argv)
    try:
        if args.fixture and (not args.local_store or args.data_dir.resolve() == (ROOT / "data").resolve()):
            p.error("Fixture requires separate --data-dir and --local-store")
        load_environment()
        repository = None if args.command == "export" else LocalPublications(args.local_store) if args.local_store else SupabasePublications()
        if args.command == "status":
            result = repository.latest(args.type)
            print(json.dumps({"connected": True, "report_id": result["report"]["report_id"] if result else None}, ensure_ascii=False))
            return 0
        if args.command == "publish":
            if not args.input:
                p.error("publish requires --input")
            report = read_json(args.input)
            folder = args.snapshot_dir or args.data_dir / "snapshots" / report["provenance"]["run_id"]
            if not folder.resolve().is_relative_to((args.data_dir / "snapshots").resolve()):
                raise ValueError("Snapshot directory outside configured archive")
            commentary_record = load_commentary_record(folder) if report["commentary"]["text"] is not None else None
        else:
            folder = args.snapshot_dir
            if args.command == "cycle":
                result = run(args.data_dir, offline=args.offline, fixture=args.fixture, review_path=args.review,
                             progress=lambda m: print(m, file=sys.stderr))
                folder = Path(result["snapshot"]).parent
            if not folder:
                p.error("export requires --snapshot-dir")
            snapshot, sources = load_snapshot(folder)
            commentary_record = load_commentary_record(folder)
            previous = repository.latest(args.type, before=snapshot["as_of"]) if repository else None
            report = build_report(snapshot, sources, report_type=args.type,
                                  previous=previous["report"] if previous else None, supersedes=args.supersedes,
                                  commentary_record=commentary_record)
        if args.output:
            write_json(args.output, report)
        if args.command == "export":
            if not args.output:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print(json.dumps({"report_id": report["report_id"], "output": str(args.output)}))
        else:
            result = repository.publish(report, commentary_record=commentary_record)
            print(json.dumps({**result, "rtb": report["rtb"]["score"], "mode": report["mode"]}, ensure_ascii=False))
        return 0
    except Exception as exc:
        # No source bodies, HTTP errors or credentials in operational output.
        print(json.dumps({"error": "dashboard_operation_failed", "type": type(exc).__name__}), file=sys.stderr)
        return 1
