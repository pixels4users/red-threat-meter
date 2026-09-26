from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .common import ROOT, digest, load_config, now, read_json, write_json
from .pipeline import locked, replay, run
from .review import import_review
from .store import Store


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Lokalny OSINT / eksperymentalny RTB")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("run", "collect"):
        s = sub.add_parser(name, help="Pobranie i raport" if name == "run" else "Pobranie i kolejka przeglądu")
        s.add_argument("--data-dir", type=Path)
        s.add_argument("--sources", type=Path)
        group = s.add_mutually_exclusive_group()
        group.add_argument("--offline", action="store_true", help="Użyj zapisanych materiałów, bez odświeżania dat kontroli")
        group.add_argument("--fixture", type=Path, help="Dane syntetyczne, domyślnie w data/demo")
        s.add_argument("--review", type=Path, help="Zastosuj pakiet ocen przed raportem")
    s = sub.add_parser("review", help="Zapisz oceny, bez pobierania danych")
    s.add_argument("file", type=Path)
    s.add_argument("--data-dir", type=Path, default=ROOT / "data")
    s = sub.add_parser("replay", help="Odtwórz obliczenia z zamrożonych wejść")
    s.add_argument("run_id")
    s.add_argument("--data-dir", type=Path, default=ROOT / "data")
    for name in ("doctor", "latest"):
        s = sub.add_parser(name)
        s.add_argument("--data-dir", type=Path, default=ROOT / "data")
    s = sub.add_parser("backup", help="Spójna kopia SQLite, włącznie z zapisami WAL")
    s.add_argument("--data-dir", type=Path, default=ROOT / "data")
    s.add_argument("--output", type=Path)
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command in ("run", "collect"):
            data_dir = args.data_dir or ROOT / ("data/demo" if args.fixture else "data")
            if args.fixture and data_dir.resolve() == (ROOT / "data").resolve():
                raise ValueError("Synthetic fixtures must not use the live data directory")
            result = run(data_dir, args.sources, args.offline, args.fixture, args.review,
                         args.command == "collect", progress=lambda m: print(m, file=sys.stderr, flush=True))
        elif args.command == "replay":
            result = replay(args.data_dir, args.run_id)
        elif args.command == "latest":
            latest = read_json(args.data_dir / "latest.json")
            result = {**latest, "report": str((args.data_dir / latest["report"]).resolve()),
                      "snapshot": str((args.data_dir / latest["snapshot"]).resolve())}
        elif args.command == "review":
            with locked(args.data_dir), Store(args.data_dir) as store:
                result = import_review(store, read_json(args.file))
        elif args.command == "doctor":
            sources = load_config()
            with Store(args.data_dir) as store:
                integrity = store.db.execute("PRAGMA integrity_check").fetchone()[0]
                fk = store.db.execute("PRAGMA foreign_key_check").fetchall()
                result = {"python": sys.version.split()[0], "database": str(args.data_dir / "database/osint.sqlite3"),
                          "integrity": integrity, "foreign_key_errors": len(fk), "counts": store.counts(),
                          "enabled_sources": [s["id"] for s in sources["sources"] if s["enabled"]],
                          "disabled_sources": {s["id"]: s["notes"] for s in sources["sources"] if not s["enabled"]},
                          "ai_mode": "supervised_review_import; no background model or paid API",
                          "scheduler": "not_installed", "frontend": "not_built_stage_3"}
                if integrity != "ok" or fk:
                    raise ValueError("Database integrity check failed")
        elif args.command == "backup":
            path = args.output or args.data_dir / "backups" / ("osint-" + now().replace(":", "") + ".sqlite3")
            with locked(args.data_dir), Store(args.data_dir) as store:
                store.backup(path)
                metadata = {"created_at": now(), "sqlite_file": str(path), "sha256": digest(path.read_bytes()),
                            "counts": store.counts(),
                            "note": "Kopia SQLite. Do pełnego odtworzenia zachowaj raw/, snapshots/, runs/ i config/."}
                write_json(path.with_suffix(".json"), metadata)
                result = metadata
        else:
            raise ValueError("Unknown command")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
