#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
  sh scripts/setup.sh
fi
if ! .venv/bin/python scripts/publish_dashboard.py cycle --output data/dashboard/exports/ostatni.json; then
  printf '\nNie udało się opublikować raportu. Sprawdź konfigurację dostępu opisaną w docs/dashboard-runbook.md.\n'
  exit 1
fi
printf '\nRaport zapisany w Supabase. Otwarty dashboard odczyta go w ciągu 30 sekund.\n'
printf 'Nowe doniesienia mogą wymagać przeglądu; wówczas indeks pozostaje niewyliczony.\n'
