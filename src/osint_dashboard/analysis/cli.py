from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..common import ROOT, digest, read_json
from ..dashboard.contract import build_report, load_commentary_record, load_snapshot
from ..dashboard.publication import LocalPublications, SupabasePublications, load_environment
from . import cycle
from .reviewer import AnalysisError


def main(argv=None):
    parser = argparse.ArgumentParser(description="Cykl analityczny wykonywany przez Codexa, bez API modelu")
    parser.add_argument("command", choices=("prepare", "check", "apply", "history-context", "calculate", "editorial", "finish", "publish"))
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--cycle")
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--offline", action="store_true")
    inputs.add_argument("--fixture", type=Path)
    parser.add_argument("--proposal", type=Path)
    parser.add_argument("--proposal-hash")
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--context", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--reviewer-name", default="Codex")
    parser.add_argument('--review-incident', action='append', default=[], help='Explicit offline correction of an existing incident')
    parser.add_argument("--type", choices=("daily", "weekly"), default="daily")
    parser.add_argument("--local-store", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command != "prepare" and not args.cycle:
            parser.error("--cycle is required")
        if args.command == "prepare":
            result = cycle.prepare(args.data_dir, offline=args.offline, fixture=args.fixture,
                                   review_incidents=args.review_incident,
                                   progress=lambda message: print(message, file=sys.stderr, flush=True))
        elif args.command == "check":
            if not args.proposal:
                parser.error("--proposal is required")
            result = cycle.check(args.data_dir, args.cycle, read_json(args.proposal), args.reviewer_name)
        elif args.command == "apply":
            if not args.proposal_hash or not args.audit:
                parser.error("--proposal-hash and --audit are required")
            result = cycle.apply(args.data_dir, args.cycle, args.proposal_hash, read_json(args.audit))
        elif args.command == "history-context":
            result = cycle.history_context(args.data_dir, args.cycle)
        elif args.command == "calculate":
            result = cycle.calculate(args.data_dir, args.cycle)
        elif args.command == "editorial":
            if not args.context or not args.candidate:
                parser.error("--context and --candidate are required")
            result = cycle.editorial_input(args.data_dir, args.cycle, read_json(args.context), read_json(args.candidate))
        elif args.command == "finish":
            result = cycle.finish(args.data_dir, args.cycle,
                                  context=read_json(args.context) if args.context else None,
                                  candidate=read_json(args.candidate) if args.candidate else None,
                                  audit=read_json(args.audit) if args.audit else None, reviewer_name=args.reviewer_name)
        else:
            folder, _ = cycle.load_cycle(args.data_dir, args.cycle)
            receipt = read_json(folder / "finished.json")
            snapshot_folder = args.data_dir / "snapshots" / args.cycle
            snapshot, sources = load_snapshot(snapshot_folder)
            record = load_commentary_record(snapshot_folder)
            if args.local_store and snapshot["mode"] != "fixture":
                raise AnalysisError("local_store_is_fixture_only")
            if snapshot["mode"] == "fixture" and not args.local_store:
                raise AnalysisError("fixture_cannot_publish_live")
            load_environment()
            repo = LocalPublications(args.local_store) if args.local_store else SupabasePublications()
            export = folder / ("publication-" + args.type + ".json")
            if export.exists():
                report = read_json(export)
            else:
                previous = repo.latest(args.type, before=snapshot["as_of"])
                report = build_report(snapshot, sources, report_type=args.type,
                                      previous=previous["report"] if previous else None, commentary_record=record)
                cycle.write_once(export, report)
            if (report["provenance"]["run_id"] != receipt["cycle_id"] or
                    report["provenance"]["snapshot_sha256"] != digest(snapshot)):
                raise AnalysisError("publication_cycle_mismatch")
            publication = repo.publish(report, commentary_record=record)
            stored = repo.get(report["report_id"])
            if not stored or stored["report"] != report:
                raise AnalysisError("publication_readback_mismatch")
            result = {**publication, "verified_readback": True, "score": report["rtb"]["score"], "export": str(export)}
            cycle.write_once(folder / ("published-" + args.type + ".json"), {"report_id": report["report_id"], "verified_readback": True})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        code = str(exc) if isinstance(exc, AnalysisError) else "analysis_operation_failed"
        print(json.dumps({"error": code, "type": type(exc).__name__}), file=sys.stderr)
        return 1
