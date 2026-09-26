from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import ValidationError

from ...common import ROOT, read_json
from .contracts import config, windows
from .fetch import collect
from .pipeline import replay, report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ograniczony audyt historii lotniczej, bez punktacji RTB.")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/aviation_history")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--live-data-dir", type=Path, default=ROOT / "data/aviation")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan", help="Pokaż okna czasu i maksymalny rozmiar, bez sieci.")
    commands.add_parser("collect", help="Pobierz najwyżej trzy półgodzinne pliki i zachowaj potwierdzenia.")
    commands.add_parser("report", help="Przelicz zapisane pobranie i porównaj z zachowanymi pomiarami API, bez sieci.")
    restore = commands.add_parser("replay", help="Sprawdź integralność i odtwórz raport bez internetu.")
    restore.add_argument("run_id", nargs="?")
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            cfg = config(args.config)
            result = {"windows": windows(cfg), "max_total_bytes": cfg["max_total_bytes"], "rtb_effect": "none"}
        elif args.command == "collect":
            a = collect(args.data_dir, args.config, progress=lambda s: print(s, flush=True))
            result = {"collection_id": a["id"], "downloaded_bytes": sum(r["bytes"] for r in a["requests"]),
                      "next_step": "Uruchom report, aby przeanalizować zapisane odpowiedzi."}
        elif args.command == "report":
            result = report(args.data_dir, args.live_data_dir)
        else:
            result = replay(args.data_dir, args.run_id or read_json(args.data_dir / "latest.json")["run_id"])
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, ValidationError) as exc:
        parser.exit(1, f"Błąd audytu historii: {exc}\n")
