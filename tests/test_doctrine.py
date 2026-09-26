from types import SimpleNamespace

import pytest

from osint_dashboard import doctrine
from osint_dashboard.common import digest, read_json, write_json


@pytest.fixture
def library(tmp_path, monkeypatch):
    root = tmp_path / "project"
    source = root / "data/doctrine_rag/test.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"synthetic test bytes; mocked PDF extractor")
    registry = root / "config/doctrine-sources.json"
    index = root / "data/doctrine_index"
    write_json(registry, {"documents": [{"id": "synthetic", "title": "Synthetic reference", "local_path": "data/doctrine_rag/test.pdf",
                                        "sha256": digest(source.read_bytes()), "pdf_pages": 3, "status": "ready_for_passage_review"}]})
    monkeypatch.setattr(doctrine, "ROOT", root)
    monkeypatch.setattr(doctrine, "REGISTRY", registry)
    monkeypatch.setattr(doctrine, "INDEX", index)
    monkeypatch.setattr(doctrine.shutil, "which", lambda name: "/mock/pdftotext")
    text = "Synthetic reference for retrieval tests. " * 3
    def extract(*args, **kwargs):
        assert kwargs["timeout"] == 45
        return SimpleNamespace(stdout=text + "\f\f" + "Kontrola refleksyjna. Łódź. " + text + "\f", stderr="")
    monkeypatch.setattr(doctrine.subprocess, "run", extract)
    return root, source, registry, index


def test_page_alignment_retains_blank_pages_and_rejects_ambiguous_extraction():
    assert doctrine.pages_from_text("first\f\flast\f", 3) == ["first", "", "last"]
    with pytest.raises(ValueError, match="alignment"):
        doctrine.pages_from_text("first\flast", 3)


def test_index_search_cites_real_pdf_position_and_keeps_prior_editions(library):
    root, source, registry, index = library
    first = doctrine.build_index()
    assert first["indexed_pages"] == 2
    result = doctrine.search("kontrola lodz", index_dir=index)
    assert result["results"][0]["page_pdf"] == 3
    assert result["results"][0]["source_kind"] == "doctrine"
    assert result["results"][0]["file"] == str(source)
    second = doctrine.build_index()
    assert first["index_id"] != second["index_id"]
    assert (index / first["index_id"] / "pages.jsonl").is_file()


@pytest.mark.parametrize("change,message", [("pdf", "PDF changed"), ("index", "integrity"), ("registry", "registry changed")])
def test_changed_reference_or_index_cannot_be_cited(library, change, message):
    root, source, registry, index = library
    built = doctrine.build_index()
    if change == "pdf":
        source.write_bytes(b"modified synthetic reference")
    elif change == "index":
        (index / built["index_id"] / "pages.jsonl").write_text("tampered")
    else:
        config = read_json(registry)
        config["version"] = "changed"
        write_json(registry, config)
    with pytest.raises(ValueError, match=message):
        doctrine.search("kontrola", index_dir=index)


def test_unregistered_changed_and_missing_documents_are_explicit(library):
    root, source, registry, index = library
    extra = source.parent / "new.pdf"
    extra.write_bytes(b"unregistered synthetic bytes")
    source.write_bytes(b"changed synthetic reference")
    built = doctrine.build_index()
    assert built["indexed_pages"] == 0
    assert built["unregistered_files"] == ["data/doctrine_rag/new.pdf"]
    assert built["documents"][0]["status"] == "changed_file_requires_review"
    source.unlink()
    built = doctrine.build_index()
    assert built["documents"][0]["status"] == "missing_file"


def test_doctrine_registry_cannot_read_outside_library(library):
    root, source, registry, index = library
    config = read_json(registry)
    config["documents"][0]["local_path"] = "elsewhere/private.pdf"
    write_json(registry, config)
    with pytest.raises(ValueError, match="inside data/doctrine_rag"):
        doctrine.build_index()
