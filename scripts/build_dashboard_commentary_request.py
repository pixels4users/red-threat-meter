#!/usr/bin/env python3
"""Build a private LLM request; no network calls or publication."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import _bootstrap  # noqa: F401
from osint_dashboard.dashboard_commentary import build_generation_request


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Private reviewed context JSON")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        with args.input.open("rb") as stream:
            raw = stream.read(1048577)
        if len(raw) > 1048576:
            raise ValueError("input_too_large")
        context = json.loads(raw)
    except (OSError, UnicodeError, ValueError, RecursionError):
        logging.info("dashboard_generation_unavailable reason=input_unreadable")
        request = None
    else:
        request = build_generation_request(context)
    # This output is PRIVATE, unlike prepare_dashboard_commentary.py's payload.
    print(json.dumps(request, ensure_ascii=False))


if __name__ == "__main__":
    main()
