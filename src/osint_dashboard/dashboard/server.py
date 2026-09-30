from __future__ import annotations

import json
import re
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from ..common import ROOT, read_json


def create_server(repository, port=8765, directory=None):
    class Handler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            super().end_headers()

        def do_GET(self):
            url = urlsplit(self.path)
            if not url.path.startswith("/api/"):
                return super().do_GET()
            # Bind only to loopback, deny cross-origin page access and DNS rebinding.
            if self.headers.get("Host", "").split(":")[0] not in ("localhost", "127.0.0.1"):
                return self.respond(403, {"error": "forbidden"})
            if self.headers.get("Sec-Fetch-Site") == "cross-site":
                return self.respond(403, {"error": "forbidden"})
            q = parse_qs(url.query)
            kind = q.get("type", ["daily"])[0]
            if kind not in ("daily", "weekly"):
                return self.respond(400, {"error": "invalid_request"})
            try:
                if url.path == "/api/config":
                    config = read_json(ROOT / "config/dashboard.json")
                    return self.respond(200, {k: config[k] for k in ("refresh_seconds", "stale_after_hours")})
                if url.path == "/api/latest":
                    return self.respond(200, repository.latest(kind))
                if url.path == "/api/reports":
                    offset = int(q.get("offset", ["0"])[0])
                    if offset < 0 or offset > 100000:
                        raise ValueError("Invalid offset")
                    return self.respond(200, repository.history(kind, offset, q.get("anchor", [None])[0]))
                match = re.fullmatch(r"/api/reports/(rpt_[a-f0-9]{64})(?:/(geojson|json))?", url.path)
                if match:
                    result = repository.get(match[1])
                    if not result:
                        return self.respond(404, {"error": "not_found"})
                    if match[2]:
                        data = result["report"]["geojson"] if match[2] == "geojson" else result["report"]
                        return self.respond(200, data, match[1] + "." + match[2])
                    return self.respond(200, result)
                return self.respond(404, {"error": "not_found"})
            except ValueError:
                return self.respond(400, {"error": "invalid_request"})
            except Exception:
                return self.respond(503, {"error": "temporarily_unavailable"})

        def respond(self, status, data, download=None):
            body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            if download:
                self.send_header("Content-Disposition", f'attachment; filename="{download}"')
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(directory or ROOT / "dist")))
