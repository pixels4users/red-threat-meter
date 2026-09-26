#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ] || ! .venv/bin/python -c 'import h3' >/dev/null 2>&1; then
  sh scripts/setup.sh
fi
if [ -f data/early_warning/latest.json ]; then
  .venv/bin/python scripts/early_warning.py collect
else
  .venv/bin/python scripts/early_warning.py collect --days 30
fi
EARLY_REPORT_PATH="$(.venv/bin/python -c 'import json,pathlib; d=pathlib.Path("data/early_warning"); print((d/json.loads((d/"latest.json").read_text())["report"]).resolve())')"
open "$EARLY_REPORT_PATH"
printf '\nRaport obserwacyjny zapisany. RTB pozostaje osobnym odczytem.\n'
