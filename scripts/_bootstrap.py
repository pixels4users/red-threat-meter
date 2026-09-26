from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from osint_dashboard.cli import main  # noqa: E402


def command(name):
    raise SystemExit(main([name, *sys.argv[1:]]))
