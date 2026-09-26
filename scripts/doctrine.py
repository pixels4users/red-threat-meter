#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from osint_dashboard.doctrine import build_index, search

parser = argparse.ArgumentParser(description="Lokalny katalog kontekstu doktrynalnego; poza RTB")
sub = parser.add_subparsers(dest="command", required=True)
sub.add_parser("index")
lookup = sub.add_parser("search")
lookup.add_argument("query")
lookup.add_argument("--limit", type=int, default=5)
args = parser.parse_args()
try:
    result = build_index() if args.command == "index" else search(args.query, args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
except Exception as exc:
    print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
    raise SystemExit(1)
