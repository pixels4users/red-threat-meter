#!/usr/bin/env python3
"""Manual source trials; never writes incidents to the live database."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from osint_dashboard.source_pilots import collect, parse_capture, settings


def main():
    parser = argparse.ArgumentParser(description="Ograniczony pilotaż źródeł poza cyklem RTB")
    parser.add_argument("command", choices=["collect", "parse"])
    parser.add_argument("--source", choices=list(settings()["sources"]), required=True)
    parser.add_argument("--capture", type=Path, help="Zapisany katalog próby; tylko dla parse")
    args = parser.parse_args()
    if (args.command == "parse") != (args.capture is not None):
        parser.error("parse wymaga --capture; collect nie przyjmuje --capture")
    try:
        result = collect(args.source) if args.command == "collect" else parse_capture(args.capture, args.source)
        print(json.dumps({"source": result["source_id"], "fetched_at": result["fetched_at"],
                          "records": len(result["records"]),
                          "priority_for_review": sum(r["priority_hint"] == "context_review" for r in result["records"]),
                          "runtime_enabled": False, "publication": "none"}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "error", "error_type": type(exc).__name__,
                          "message": str(exc) if isinstance(exc, ValueError) else "Próba przerwana; bez ponowień."}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
