#!/usr/bin/env python3
"""Build the local design preview from one template and canonical theme tokens."""
from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from osint_dashboard.common import ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = ROOT / "ui/dashboard-fragment.html"
    tokens = ROOT / "theme.css"
    output = args.output.resolve()
    if output in (source.resolve(), tokens.resolve()):
        parser.error("output must differ from source files")
    fragment = source.read_text(encoding="utf-8")
    marker = "/* @rtb-theme */"
    if fragment.count(marker) != 1:
        parser.error("expected exactly one theme insertion point")
    rendered = fragment.replace(marker, tokens.read_text(encoding="utf-8"))
    if len(rendered.encode("utf-8")) >= 1_000_000:
        parser.error("preview exceeds the inline size limit")
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            parser.exit(1, "preview differs from source\n")
        print("preview matches source")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
