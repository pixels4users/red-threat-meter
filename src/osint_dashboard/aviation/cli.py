from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import ValidationError

from ..common import ROOT, read_json
from ..pipeline import locked
from .pipeline import replay, run
from .store import Store


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lokalny pilotaż jakości danych lotniczych ADSB.lol.")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/aviation")
    parser.add_argument("--config", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("collect", help="Pobierz jedną próbę: najwyżej cztery regionalne zapytania.")
    commands.add_parser("report", help="Odśwież raport z archiwum, bez internetu.")
    commands.add_parser("doctor", help="Sprawdź bazę i integralność surowych odpowiedzi.")
    restore = commands.add_parser("replay", help="Odtwórz wydanie bez sieci, na tej samej wersji kodu.")
    restore.add_argument("run_id", nargs="?")
    args = parser.parse_args(argv)
    try:
        if args.command == "replay":
            result = replay(args.data_dir, args.run_id or read_json(args.data_dir / "latest.json")["run_id"])
        elif args.command == "doctor":
            if not (args.data_dir / "database/aviation.sqlite3").exists():
                raise ValueError("Baza jeszcze nie istnieje. Najpierw pobierz próbę.")
            with locked(args.data_dir), Store(args.data_dir) as store:
                result = store.doctor()
        else:
            result = run(args.data_dir, args.config, offline=args.command == "report", progress=lambda s: print(s, flush=True))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, ValidationError) as exc:
        parser.exit(1, f"Błąd pilotażu lotniczego: {exc}\n")
