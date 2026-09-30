from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
UTC = timezone.utc


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def instant(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    return result.astimezone(UTC)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: object) -> str:
    raw = value if isinstance(value, bytes) else canonical_json(value).encode()
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, value: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value.encode("utf-8") if isinstance(value, str) else value
    fd, name = tempfile.mkstemp(prefix=".writing-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def write_json(path: Path, value: object) -> None:
    atomic_write(path, json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def canonical_url(url: str) -> str:
    p = urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
        raise ValueError("Expected a public HTTP(S) URL without credentials")
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or "/", urlencode(sorted(query)), ""))


def load_config(path: Path | None = None) -> dict:
    config = read_json(path or ROOT / "config/sources.json")
    if not isinstance(config, dict) or not config.get("sources"):
        raise ValueError("Empty source configuration")
    Draft202012Validator(read_json(ROOT / "schemas/sources.schema.json")).validate(config)
    ids = [s["id"] for s in config["sources"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate source identifier")
    for source in config["sources"]:
        if source["enabled"]:
            if urlsplit(canonical_url(source["url"])).hostname not in source["allowed_hosts"]:
                raise ValueError(f"Source host is not allowed: {source['id']}")
    return config


def load_scoring(version: str | None = None) -> dict:
    version = version or read_json(ROOT / 'config/analysis.json')['methodology_version']
    paths = {'rtb-v0.2': 'scoring-v0.json', 'rtb-v0.3': 'scoring-v0.3.json'}
    if version not in paths:
        raise ValueError('Unsupported methodology version')
    config = read_json(ROOT / 'config' / paths[version])
    if config['version'] != version:
        raise ValueError('Scoring version mismatch')
    if version == 'rtb-v0.3':
        Draft202012Validator(read_json(ROOT / 'schemas/scoring-v03.schema.json')).validate(config)
    return config
