#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
  sh scripts/setup.sh
fi
.venv/bin/python scripts/run_pipeline.py
REPORT_PATH="$(.venv/bin/python -c 'import json,pathlib; d=pathlib.Path("data"); print((d/json.loads((d/"latest.json").read_text())["report"]).resolve())')"
open "$REPORT_PATH"
printf '\nRaport zapisany. Zebrane doniesienia mogą wymagać przeglądu.\n'
