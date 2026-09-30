#!/usr/bin/env python3
"""Prepare public commentary JSON locally; does not publish or call a model."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import _bootstrap  # noqa: F401
from osint_dashboard.dashboard_commentary import prepare_commentary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--analysis-complete", action="store_true")
    parser.add_argument("--approved-sha256")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        with args.input.open("rb") as stream:
            raw = stream.read(16385)
        if len(raw) > 16384:
            raise ValueError("input_too_large")
        candidate = json.loads(raw)
    except (OSError, UnicodeError, ValueError, RecursionError):
        logging.info("dashboard_commentary_unavailable reason=input_unreadable")
        public = {"text": None}
    else:
        public = prepare_commentary(
            candidate,
            expected_snapshot_id=args.snapshot_id,
            analysis_complete=args.analysis_complete,
            approved_sha256=args.approved_sha256,
        )
    # stdout is the browser contract; stderr contains codes, never rejected prose.
    print(json.dumps(public, ensure_ascii=False))


if __name__ == "__main__":
    main()
