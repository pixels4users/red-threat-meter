#!/usr/bin/env python3
"""Explicitly collect a bounded paid X sample, or inspect the local budget."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from osint_dashboard.common import ROOT
from osint_dashboard.pipeline import locked
from osint_dashboard.x_api import XError, budget_status, collect, load_settings


def main():
    parser = argparse.ArgumentParser(description="Odczyt X z ograniczeniem kosztów; status nie wywołuje API")
    parser.add_argument("command", choices=["collect", "status"])
    args = parser.parse_args()
    try:
        if args.command == "collect":
            result = collect()
        else:
            with locked(ROOT / "data"):
                result = budget_status(ROOT / "data/x-api", load_settings())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("status") == "incomplete" else 0
    except Exception as exc:
        # Never print response bodies, exception reprs or environment contents.
        print(json.dumps({"error": str(exc) if isinstance(exc, XError) else type(exc).__name__}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
