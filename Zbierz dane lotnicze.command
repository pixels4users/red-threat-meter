#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
  sh scripts/setup.sh
fi
.venv/bin/python scripts/aviation.py collect
AVIATION_REPORT_PATH="$(.venv/bin/python -c 'import json,pathlib; d=pathlib.Path("data/aviation"); print((d/json.loads((d/"latest.json").read_text())["report"]).resolve())')"
open "$AVIATION_REPORT_PATH"
printf '\nZapisano pojedynczą próbę i raport jakości. Kolektor nie pracuje w tle.\n'
