"""Local reference lookup, isolated from incident ingestion and scoring."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import unicodedata
import uuid
from pathlib import Path

from .common import ROOT, atomic_write, digest, now, read_json, write_json

REGISTRY = ROOT / "config/doctrine-sources.json"
INDEX = ROOT / "data/doctrine_index"


def normalized(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold().replace("ł", "l"))
                   if not unicodedata.combining(c))


def pages_from_text(text: str, expected: int) -> list[str]:
    pages = text.split("\f")
    if len(pages) == expected + 1 and not pages[-1].strip():
        pages.pop()
    if len(pages) != expected:
        raise ValueError("PDF page alignment failed; cannot produce reliable page citations")
    return pages


def build_index() -> dict:
    extractor = shutil.which("pdftotext")
    if not extractor:
        raise RuntimeError("Poppler pdftotext is required for local PDF indexing")
    config = read_json(REGISTRY)
    pages, documents = [], []
    known_paths = {(ROOT / d["local_path"]).resolve() for d in config["documents"] if "local_path" in d}
    unregistered = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "data/doctrine_rag").rglob("*")
                          if p.is_file() and p.suffix.lower() == ".pdf" and p.resolve() not in known_paths)
    for entry in config["documents"]:
        if "local_path" not in entry:
            continue
        source = (ROOT / entry["local_path"]).resolve()
        if not source.is_relative_to((ROOT / "data/doctrine_rag").resolve()):
            raise ValueError("Doctrine source must be inside data/doctrine_rag")
        row = {"id": entry["id"], "title": entry["title"], "local_path": entry["local_path"],
               "sha256": entry["sha256"], "pdf_pages": entry["pdf_pages"], "indexed_pages": 0,
               "status": entry["status"]}
        documents.append(row)
        if not source.is_file():
            row["status"] = "missing_file"
            continue
        if digest(source.read_bytes()) != entry["sha256"]:
            row["status"] = "changed_file_requires_review"
            continue
        if entry["status"] != "ready_for_passage_review":
            continue
        try:
            result = subprocess.run([extractor, "-layout", "-enc", "UTF-8", str(source), "-"],
                                    capture_output=True, text=True, timeout=45, check=True)
            texts = pages_from_text(result.stdout, entry["pdf_pages"])
            row["extractor_warnings"] = bool(result.stderr.strip())
            for n, text in enumerate(texts, start=1):
                if len(text.strip()) < 80:
                    continue
                pages.append({"document_id": entry["id"], "source_kind": "doctrine",
                              "sha256": entry["sha256"], "page_pdf": n, "text": text.strip()})
                row["indexed_pages"] += 1
            row["status"] = "indexed_text_requires_passage_review" if row["indexed_pages"] else "needs_ocr"
            row["pages_without_substantial_text"] = len(texts) - row["indexed_pages"]
        except (subprocess.SubprocessError, ValueError) as exc:
            row["status"] = "extraction_failed"
            row["error"] = type(exc).__name__ + ": " + str(exc)[:200]
    index_id = now().replace(":", "") + "-" + uuid.uuid4().hex[:8]
    folder = INDEX / index_id
    folder.mkdir(parents=True, exist_ok=False)
    atomic_write(folder / "pages.jsonl", "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pages))
    manifest = {"index_id": index_id, "created_at": now(), "registry_hash": digest(config),
                "pages_sha256": digest((folder / "pages.jsonl").read_bytes()), "source_kind": "doctrine",
                "indexed_pages": len(pages), "documents": documents, "unregistered_files": unregistered,
                "note": "Mechaniczna ekstrakcja, nie przeczytanie lub potwierdzenie wszystkich tez. Numery odnoszą się do stron PDF, nie druku. OCR, mapy i tabele wymagają sprawdzenia obrazu."}
    write_json(folder / "manifest.json", manifest)
    write_json(INDEX / "latest.json", {"index_id": index_id})
    return {"index_id": index_id, "indexed_pages": len(pages), "unregistered_files": unregistered,
            "documents": [{k: d[k] for k in ("id", "status", "indexed_pages")} for d in documents]}


def search(query: str, limit: int = 5, index_dir: Path = INDEX) -> dict:
    tokens = list(dict.fromkeys(re.findall(r"\w{2,}", normalized(query))))
    if not tokens or not 1 <= limit <= 20:
        raise ValueError("Provide a query and a result limit between 1 and 20")
    index_id = read_json(index_dir / "latest.json")["index_id"]
    if Path(index_id).name != index_id:
        raise ValueError("Invalid reference index identifier")
    folder = index_dir / index_id
    manifest = read_json(folder / "manifest.json")
    if manifest["registry_hash"] != digest(read_json(REGISTRY)):
        raise ValueError("Doctrine registry changed; rebuild the index")
    raw = (folder / "pages.jsonl").read_bytes()
    if digest(raw) != manifest["pages_sha256"]:
        raise ValueError("Doctrine index integrity check failed")
    documents = {d["id"]: d for d in manifest["documents"]}
    hits = []
    for line in raw.decode("utf-8").splitlines():
        page = json.loads(line)
        body = normalized(page["text"])
        if all(token in body for token in tokens):
            first = min(body.index(token) for token in tokens)
            hits.append((sum(body.count(t) for t in tokens), page, first))
    results, checked = [], set()
    for rank, page, first in sorted(hits, key=lambda h: (-h[0], h[1]["document_id"], h[1]["page_pdf"]))[:limit]:
        doc = documents[page["document_id"]]
        path = ROOT / doc["local_path"]
        if doc["id"] not in checked:
            if not path.is_file() or digest(path.read_bytes()) != doc["sha256"]:
                raise ValueError("Reference PDF changed or is missing; review and rebuild the index")
            checked.add(doc["id"])
        results.append({"document_id": doc["id"], "title": doc["title"], "source_kind": "doctrine",
                        "file": str(path), "page_pdf": page["page_pdf"], "sha256": doc["sha256"],
                        "snippet": " ".join(page["text"][max(0, first - 100):first + 450].split())})
    return {"query": query, "index_id": index_id, "method": "local_lexical_all_terms",
            "note": "Wyniki są kontekstem. Otwórz wskazaną stronę przed cytowaniem; nie używaj ich jako dowodu bieżącego incydentu.",
            "results": results}
