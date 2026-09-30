#!/usr/bin/env python3
import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from osint_dashboard.dashboard.publication import LocalPublications, SupabasePublications, load_environment
from osint_dashboard.dashboard.server import create_server

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Lokalny frontend i serwerowy odczyt publikacji Supabase")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--local-store", type=Path)
    args = p.parse_args()
    load_environment()
    repo = LocalPublications(args.local_store) if args.local_store else SupabasePublications()
    server = create_server(repo, args.port)
    print(f"Dashboard: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
