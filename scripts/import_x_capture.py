#!/usr/bin/env python3
"""Import a browser transcript read by Codex; this command never calls X."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from osint_dashboard.common import ROOT, load_config, read_json
from osint_dashboard.x_sources import import_capture


def main():
    parser = argparse.ArgumentParser(description="Zachowaj rzeczywisty odczyt wpisów z X")
    parser.add_argument("capture", type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    source = next(s for s in load_config()["sources"] if s["id"] == args.source)
    if args.capture.stat().st_size > 500_000:
        parser.error("Capture exceeds 500 KB")
    print(json.dumps(import_capture(args.data_dir, source, read_json(args.capture)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
