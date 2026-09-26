from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..common import ROOT, read_json
from ..pipeline import locked
from .pipeline import replay, run
from .store import Store


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lokalny pilotaż obserwacji GNSS i logistyki; niezależny od RTB.")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/early_warning")
    parser.add_argument("--config", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    collection = commands.add_parser("collect", help="Pobierz dane i zapisz raport; domyślnie ostatnie trzy doby GNSS.")
    collection.add_argument("--days", type=int)
    commands.add_parser("report", help="Odśwież raport bez internetu i bez odmładzania kontroli źródeł.")
    review = commands.add_parser("review", help="Zaimportuj oceny konkretnych wersji i zapisz raport offline.")
    review.add_argument("path", type=Path)
    translate = commands.add_parser("translate", help="Zaimportuj polskie tytuły i streszczenia konkretnych wersji źródeł.")
    translate.add_argument("translation_path", type=Path)
    restore = commands.add_parser("replay", help="Sprawdź i odtwórz zamrożone wydanie bez sieci.")
    restore.add_argument("run_id", nargs="?")
    commands.add_parser("doctor", help="Sprawdź bazę, kontrakty i hashe surowych materiałów.")
    args = parser.parse_args(argv)
    try:
        if args.command == "replay":
            run_id = args.run_id or read_json(args.data_dir / "latest.json")["run_id"]
            result = replay(args.data_dir, run_id)
        elif args.command == "doctor":
            if not (args.data_dir / "database/observations.sqlite3").exists():
                raise ValueError("Observation database does not yet exist; collect first")
            with locked(args.data_dir), Store(args.data_dir) as store:
                result = store.doctor()
        else:
            result = run(args.data_dir, args.config, days=getattr(args, "days", None),
                         offline=args.command != "collect", review_path=getattr(args, "path", None),
                         translation_path=getattr(args, "translation_path", None),
                         progress=lambda message: print(message, flush=True))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Błąd: {exc}\n")
