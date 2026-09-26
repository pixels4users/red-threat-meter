from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
import sqlite3
import re
import xml.etree.ElementTree as ET

import h3
import pytest

from osint_dashboard.common import ROOT, atomic_write, digest, read_json, write_json
from osint_dashboard.early_warning import collectors, pipeline, store as storage
from osint_dashboard.early_warning.contracts import config, identity, validate_observation
from osint_dashboard.early_warning.report import make_snapshot, geojson
from osint_dashboard.early_warning.store import Store, import_reviews
from osint_dashboard.early_warning import translations

AS_OF = "2026-09-23T12:00:00+00:00"
DAY = date(2026, 9, 22)
CELL = h3.latlng_to_cell(52, 21, 4)
CELL2 = h3.latlng_to_cell(54, 22, 4)
CSV = f"hex,count_good_aircraft,count_bad_aircraft\n{CELL},8,2\n{CELL2},1,0\n".encode()
TEXT = "TEST SYNTETYCZNY. Publikacja opisuje dawne transporty i wymaga sprawdzenia daty zdarzenia."


def rss(text=TEXT, pubdate="Tue, 22 Sep 2026 10:00:00 +0000", content=True):
    body = f"<content:encoded><![CDATA[<p>{text}</p>]]></content:encoded>" if content else f"<description>{text}</description>"
    return f'''<rss xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel><item>
    <title>TEST SYNTETYCZNY — raport o historii</title><link>https://belzhd.info/news/synthetic/</link>
    <pubDate>{pubdate}</pubDate><category>Воинские перевозки</category>{body}</item></channel></rss>'''.encode()


class Fixtures:
    def __init__(self):
        self.fail_source = None
        self.fail_day = None
        self.csv = CSV
        self.feed = rss()

    def __call__(self, source, data_dir):
        parent = self
        class Fetcher:
            raw_refs = None

            def __init__(self):
                self.raw_refs = []

            def get(self, url):
                if source["id"] == parent.fail_source or parent.fail_day and parent.fail_day in url:
                    raise OSError("synthetic source outage")
                if "manifest.csv" in url:
                    lines = ["date,suspect,num_bad_aircraft_hexes,source"]
                    for i in range(30):
                        day = DAY - timedelta(days=i)
                        provider = "merged" if i < 2 else "adsbexchange"
                        lines.append(f"{day},false,1,{provider}")
                    body = ("\n".join(lines) + "\n").encode()
                elif source["id"] == "gpsjam":
                    body = parent.csv
                else:
                    body = parent.feed
                ref = f"raw/{source['id']}/{digest(body)}.bin"
                atomic_write(data_dir / ref, body)
                self.raw_refs.append(ref)
                return body, "text/plain", url, ref
        return Fetcher()


@pytest.fixture
def env(tmp_path, monkeypatch):
    for module in (collectors, pipeline, storage, translations):
        monkeypatch.setattr(module, "now", lambda: AS_OF)
    return tmp_path / "observations", Fixtures()


def run_fixture(env, **kw):
    folder, fixtures = env
    return pipeline.run(folder, days=3, mode="fixture", fetcher_factory=fixtures, **kw)


def saved(folder, result, name="snapshot.json"):
    return read_json(folder / "snapshots" / result["run_id"] / name)


def review_for(obs, status="urgent_review"):
    data = obs["data"]
    evidence = {"kind": "quote", "quote": TEXT} if data["type"] == "publication" else {
        "kind": "measurement", "cell": CELL, "field": "sample", "value": 10}
    return {"observation_id": obs["observation_id"], "previous_revision": 0, "status": status,
            "reason": "TEST SYNTETYCZNY: priorytet sprawdzenia skutków, bez potwierdzenia zdarzenia.",
            "alternatives": ["TEST SYNTETYCZNY: możliwy opis dawnego, rutynowego zdarzenia."],
            "evidence": [evidence], "attribution": {"actor": None, "status": "unknown", "reason": "Brak dowodu sprawcy w materiale."}, "event_key": None}


def batch(*decisions):
    return {"schema_version": "ew-review-1", "reviewer": {"type": "agent", "name": "Synthetic test"}, "decisions": list(decisions)}


def test_history_separates_provider_regimes_missing_coverage_and_known_time(env):
    folder, _ = env
    result = run_fixture(env)
    snap = saved(folder, result)
    assert snap["rtb_effect"] == "none"
    assert snap["gnss"]["reference"]["prior_same_provider_days"] == 1  # excludes current day and other provider
    assert snap["gnss"]["reference"]["status"] == "not_calibrated"
    assert len(snap["gnss"]["missing_days"]) == 27
    day = snap["gnss"]["latest"]
    assert (day["eligible_cells"], day["low_sample_cells"], day["high_cells"]) == (1, 1, 1)
    assert day["high_cell_share_pct"] == 100  # exactly 10% follows map implementation
    assert day["missing_cells"] == day["grid_cells"] - 2
    inputs = saved(folder, result, "replay-input.json")
    for record in inputs["observations"]:
        assert record["observation"]["times"]["first_seen_at"] == AS_OF
        assert record["observation"]["times"]["first_available_at"] is None
    pub = next(r["observation"] for r in inputs["observations"] if r["observation"]["source_id"] == "belzhd_public")
    assert pub["times"]["observed_start"] is None
    assert pub["location"]["bbox"] is None
    features = geojson(inputs, snap)["features"]
    missing = next(f for f in features if f["properties"].get("quality") == "missing")
    assert missing["properties"]["source_adjusted_pct"] is None
    assert features[-1]["geometry"] is None
    lon, lat = features[0]["geometry"]["coordinates"][0][0]
    assert 13 < lon < 30 and 48 < lat < 61


def test_repeat_fetches_deduplicate_versions_and_replay_offline(env, monkeypatch):
    folder, _ = env
    first = run_fixture(env)
    second = run_fixture(env)
    assert second["new_observation_versions"] == 0
    assert second["counts"]["fetches"] == 2 * first["counts"]["fetches"]
    monkeypatch.setattr(collectors.Fetcher, "get", lambda *a: pytest.fail("Replay attempted a network call"))
    assert pipeline.replay(folder, second["run_id"])["identical"]
    with Store(folder) as db:
        assert db.doctor()["integrity"] == "ok"


def test_one_source_failure_keeps_other_stream_and_marks_current_gap(env):
    folder, fixtures = env
    fixtures.fail_source = "gpsjam"
    result = run_fixture(env)
    snap = saved(folder, result)
    assert len(snap["publications"]) == 1
    assert snap["gnss"]["latest"] is None
    assert {c["source_id"]: c["status"] for c in snap["source_checks"]} == {"gpsjam": "error", "belzhd_public": "ok"}
    fixtures.fail_source = None
    fixtures.fail_day = str(DAY)
    snap = saved(folder, run_fixture(env))
    assert str(DAY) in snap["gnss"]["missing_days"]
    assert not snap["gnss"]["latest_is_expected_day"]


def test_offline_does_not_refresh_checks_or_import_future_knowledge(env, monkeypatch):
    folder, _ = env
    result = run_fixture(env)
    inputs = saved(folder, result, "replay-input.json")
    inputs["as_of"] = "2026-09-22T12:00:00+00:00"
    with pytest.raises(ValueError, match="not known"):
        pipeline.validate_inputs(inputs)
    monkeypatch.setattr(pipeline, "now", lambda: "2026-09-25T12:00:00+00:00")
    offline = pipeline.run(folder, offline=True, mode="fixture")
    snap = saved(folder, offline)
    assert all(c["checked_at"] == AS_OF and c["stale"] for c in snap["source_checks"])
    assert not snap["gnss"]["latest_is_expected_day"]


def test_urgent_single_source_unknown_attribution_and_atomic_review_conflicts(env):
    folder, _ = env
    result = run_fixture(env)
    records = saved(folder, result, "replay-input.json")["observations"]
    pub = next(r["observation"] for r in records if r["observation"]["source_id"] == "belzhd_public")
    gnss = next(r["observation"] for r in records if r["observation"]["source_id"] == "gpsjam")
    with Store(folder) as db:
        invalid = review_for(gnss)
        invalid["evidence"][0]["value"] = 999
        with pytest.raises(ValueError, match="Measurement differs"):
            import_reviews(db, batch(review_for(pub), invalid))
        assert db.counts()["reviews"] == 0
        import_reviews(db, batch(review_for(pub)))
        with pytest.raises(ValueError, match="revision conflict"):
            import_reviews(db, batch(review_for(pub)))
    output = pipeline.run(folder, offline=True, mode="fixture")
    signal = saved(folder, output)["signals"][0]
    assert signal["status"] == "urgent_review" and signal["attribution"]["actor"] is None
    assert signal["review"]["reviewer"]["type"] == "agent"
    assert output["rtb_effect"] == "none"


def test_content_change_requires_new_review_and_reversion_uses_latest_fetch(env):
    folder, fixtures = env
    first = run_fixture(env)
    pub = next(r["observation"] for r in saved(folder, first, "replay-input.json")["observations"] if r["observation"]["source_id"] == "belzhd_public")
    with Store(folder) as db:
        import_reviews(db, batch(review_for(pub)))
    fixtures.feed = rss(TEXT + " ZMIENIONA WERSJA.")
    changed = run_fixture(env)
    snap = saved(folder, changed)
    assert changed["new_observation_versions"] == 1
    assert next(s for s in snap["signals"] if s["source_id"] == "belzhd_public")["reviewed"] is False
    with Store(folder) as db:
        with pytest.raises(ValueError, match="superseded"):
            import_reviews(db, batch(review_for(pub)))
    fixtures.feed = rss()
    reverted = run_fixture(env)
    assert reverted["new_observation_versions"] == 0
    assert saved(folder, reverted)["publications"][0]["observation_id"] == pub["observation_id"]


@pytest.mark.parametrize("row", [f"{CELL},0,0", f"{CELL},-1,2", f"{CELL},1.5,2", "bad-h3,1,2", f"{h3.latlng_to_cell(52,21,5)},1,2", f"{CELL},1,2\n{CELL},2,3"])
def test_corrupt_sensor_rows_are_not_silently_dropped(row):
    cfg = config()
    body = ("hex,count_good_aircraft,count_bad_aircraft\n" + row + "\n").encode()
    with pytest.raises(ValueError):
        collectors.parse_gnss(body, DAY, {"provider": "merged", "suspect": False}, cfg["sources"][0], cfg,
                              "https://gpsjam.org/data/merged/2026-09-22-h3_4.csv", ["raw/gpsjam/" + "0"*64 + ".bin"], AS_OF)


def test_negative_source_formula_is_preserved_and_incomplete_day_rejected():
    cfg = config()
    args = (cfg["sources"][0], cfg, "https://gpsjam.org/data/merged/2026-09-22-h3_4.csv", ["raw/gpsjam/" + "0"*64 + ".bin"], AS_OF)
    obs = collectors.parse_gnss(CSV, DAY, {"provider": "merged", "suspect": True}, *args)
    assert next(c for c in obs["data"]["cells"] if c["h3"] == CELL2)["source_adjusted_pct"] == -100
    assert obs["quality"]["integrity"] == "suspect_by_publisher"
    with pytest.raises(ValueError, match="completed UTC day"):
        collectors.parse_gnss(CSV, DAY + timedelta(days=1), {"provider": "merged", "suspect": False}, *args)


@pytest.mark.parametrize("pubdate", ["", "bad date", "Wed, 23 Sep 2026 13:00:00 +0000", "Tue, 22 Sep 2026 10:00:00"])
def test_invalid_missing_and_future_publication_times_stay_unknown(pubdate):
    cfg = config()
    item = ET.fromstring(rss(pubdate=pubdate)).find("./channel/item")
    obs, partial = collectors.parse_publication(item, cfg["sources"][1], cfg, "raw/belzhd_public/" + "0"*64 + ".bin", AS_OF)
    assert partial and obs["times"]["published_at"] is None
    assert obs["times"]["observed_start"] is None


def test_source_scope_entities_and_missing_full_content(env):
    folder, fixtures = env
    cfg = config()
    item = ET.fromstring(rss(content=False)).find("./channel/item")
    obs, partial = collectors.parse_publication(item, cfg["sources"][1], cfg, "raw/belzhd_public/" + "0"*64 + ".bin", AS_OF)
    assert partial and obs["data"]["text_kind"] == "rss_summary"
    item.find("link").text = "https://evil.example/steal"
    with pytest.raises(ValueError, match="allowlist"):
        collectors.parse_publication(item, cfg["sources"][1], cfg, "raw/belzhd_public/" + "0"*64 + ".bin", AS_OF)
    fixtures.feed = b'<!DOCTYPE rss [<!ENTITY x "unsafe">]><rss><channel/></rss>'
    snapshot = saved(folder, run_fixture(env))
    assert not snapshot["publications"]
    assert next(c for c in snapshot["source_checks"] if c["source_id"] == "belzhd_public")["status"] == "error"


def test_raw_tampering_audit_tables_and_release_integrity(env):
    folder, _ = env
    result = run_fixture(env)
    with Store(folder) as db:
        with pytest.raises(sqlite3.IntegrityError, match="Append-only"):
            db.db.execute("DELETE FROM observations")
        db.db.rollback()
    path = folder / "snapshots" / result["run_id"] / "snapshot.json"
    path.write_text(path.read_text() + " ")
    with pytest.raises(ValueError, match="integrity"):
        pipeline.replay(folder, result["run_id"])
    raw = next((folder / "raw").rglob("*.bin"))
    raw.write_text("changed evidence")
    with Store(folder) as db:
        with pytest.raises(ValueError, match="changed raw"):
            db.doctor()


def test_mode_separation_and_failed_export_preserve_latest(env, monkeypatch):
    folder, fixtures = env
    first = run_fixture(env)
    with pytest.raises(ValueError, match="Fixture and live"):
        pipeline.run(folder, offline=True)
    with pytest.raises(ValueError, match="Synthetic"):
        pipeline.run(ROOT / "data/early_warning", mode="fixture", fetcher_factory=fixtures)
    with pytest.raises(ValueError, match="Test fetchers"):
        pipeline.run(folder, fetcher_factory=fixtures)
    original = pipeline.write_json
    def fail(path, data):
        if Path(path).name == "snapshot.json":
            raise OSError("synthetic disk failure")
        return original(path, data)
    monkeypatch.setattr(pipeline, "write_json", fail)
    with pytest.raises(OSError):
        pipeline.run(folder, offline=True, mode="fixture")
    assert read_json(folder / "latest.json")["run_id"] == first["run_id"]
    assert not list((folder / "snapshots").glob(".staging-*"))


def test_config_change_does_not_mix_old_measurements_into_new_region(env, tmp_path):
    folder, _ = env
    run_fixture(env)
    cfg = config()
    cfg["region"]["min_cell_sample"] = 10
    path = tmp_path / "config.json"
    write_json(path, cfg)
    result = pipeline.run(folder, config_path=path, offline=True, mode="fixture")
    snap = saved(folder, result)
    assert snap["gnss"]["latest"] is None and len(snap["publications"]) == 1
    assert snap["counts"]["excluded_configuration_versions"] == 3
    cfg["sources"][0]["allowed_hosts"] = ["evil.example"]
    write_json(path, cfg)
    with pytest.raises(ValueError, match="supported public adapter"):
        config(path)


RUSSIAN_TITLE = "Испытание перевода публикации"
RUSSIAN_TEXT = "СИНТЕТИЧЕСКИЙ ТЕСТ. Здесь описаны прошлые перевозки, а не новое событие."


def russian_publication(env):
    folder, fixtures = env
    fixtures.feed = rss(RUSSIAN_TEXT).replace("TEST SYNTETYCZNY — raport o historii".encode(), RUSSIAN_TITLE.encode())
    result = run_fixture(env)
    obs = next(r["observation"] for r in saved(folder, result, "replay-input.json")["observations"]
               if r["observation"]["data"]["type"] == "publication")
    return result, obs


def translation_for(obs):
    return {"observation_id": obs["observation_id"], "previous_revision": 0,
            "source_title": obs["data"]["title"], "source_text_hash": digest(obs["data"]["text"]),
            "title_pl": "TEST SYNTETYCZNY — próba tłumaczenia publikacji",
            "summary_pl": "TEST SYNTETYCZNY: materiał opisuje dawne przewozy; nie jest doniesieniem o nowym zdarzeniu.",
            "basis_quotes": [RUSSIAN_TEXT], "uncertainties_pl": ["Przykład testowy bez rzeczywistych zdarzeń."]}


def translation_batch(*items):
    return {"schema_version": "ew-translation-1", "translator": {"type": "agent", "name": "Agent testowy"}, "translations": list(items)}


def test_polish_display_preserves_original_evidence_and_replays(env):
    folder, _ = env
    before, obs = russian_publication(env)
    assert saved(folder, before)["counts"]["pending_translations"] == 1
    assert RUSSIAN_TITLE not in (folder / "snapshots" / before["run_id"] / "report.md").read_text()
    packet = folder / "translation.json"
    write_json(packet, translation_batch(translation_for(obs)))
    output = pipeline.run(folder, offline=True, mode="fixture", translation_path=packet)
    snap = saved(folder, output)
    assert snap["counts"]["pending_translations"] == 0
    assert snap["counts"]["unreviewed_signals"] == 2  # translation is not a review
    pub = snap["publications"][0]
    assert pub["title"] == translation_for(obs)["title_pl"]
    assert pub["title_original"] == RUSSIAN_TITLE
    report = (folder / "snapshots" / output["run_id"] / "report.md").read_text()
    assert not re.search(r"[\u0400-\u052f]", report)
    assert saved(folder, output, "observations.geojson")["features"][-1]["properties"]["title"] == pub["title"]
    with Store(folder) as db:
        assert db.observation(obs["observation_id"]) == obs
        assert db.translations(AS_OF)[obs["observation_id"]]["basis_quotes"] == [RUSSIAN_TEXT]
        assert db.doctor()["integrity"] == "ok"
    assert pipeline.replay(folder, output["run_id"])["identical"]


@pytest.mark.parametrize("field,value", [("source_title", "Wrong title"), ("source_text_hash", "0" * 64),
                                          ("basis_quotes", ["This quotation does not occur in the source"]),
                                          ("title_pl", RUSSIAN_TITLE)])
def test_translation_rejects_mismatched_evidence_or_untranslated_title(env, field, value):
    folder, _ = env
    _, obs = russian_publication(env)
    item = translation_for(obs)
    item[field] = value
    with Store(folder) as db:
        with pytest.raises(ValueError):
            translations.import_translations(db, translation_batch(item))
        assert db.counts()["translations"] == 0


def test_translation_batch_is_atomic_and_revisions_append_only(env):
    folder, _ = env
    _, obs = russian_publication(env)
    item = translation_for(obs)
    with Store(folder) as db:
        with pytest.raises(ValueError, match="Duplicate"):
            translations.import_translations(db, translation_batch(item, item))
        assert db.counts()["translations"] == 0
        translations.import_translations(db, translation_batch(item))
        first_id = db.translations(AS_OF)[obs["observation_id"]]["translation_id"]
        with pytest.raises(ValueError, match="revision conflict"):
            translations.import_translations(db, translation_batch(item))
        item.update(previous_revision=1, title_pl="Poprawiony tytuł — przykład syntetyczny")
        translations.import_translations(db, translation_batch(item))
        current = db.translations(AS_OF)[obs["observation_id"]]
        assert current["revision"] == 2 and current["translation_id"] != first_id
        assert db.counts()["translations"] == 2
        with pytest.raises(sqlite3.IntegrityError, match="Append-only"):
            db.db.execute("DELETE FROM translations")
        db.db.rollback()


def test_changed_source_needs_own_translation_and_as_of_excludes_future(env, monkeypatch):
    folder, fixtures = env
    _, obs = russian_publication(env)
    item = translation_for(obs)
    with Store(folder) as db:
        translations.import_translations(db, translation_batch(item))
        assert db.translations("2026-09-23T11:59:59Z") == {}
        assert db.translations("2026-09-23T14:00:00+02:00")[obs["observation_id"]]["revision"] == 1
    changed_feed = fixtures.feed.replace(RUSSIAN_TEXT.encode(), (RUSSIAN_TEXT + " Изменение.").encode())
    fixtures.feed = changed_feed
    changed = run_fixture(env)
    assert saved(folder, changed)["counts"]["pending_translations"] == 1
    with Store(folder) as db:
        with pytest.raises(ValueError, match="superseded"):
            translations.import_translations(db, translation_batch(item))
    inputs = saved(folder, changed, "replay-input.json")
    inputs["translations"][obs["observation_id"]]["created_at"] = "2026-09-24T00:00:00Z"
    with pytest.raises(ValueError, match="Translation was not known"):
        pipeline.validate_inputs(inputs)


def test_schema_one_database_migrates_without_rewriting_observations(env):
    folder, _ = env
    _, obs = russian_publication(env)
    # Reconstruct a real schema-1 database from the fixture rows, not a live archive.
    legacy = folder.parent / "schema-one"
    legacy_db = legacy / "database/observations.sqlite3"
    legacy_db.parent.mkdir(parents=True)
    with sqlite3.connect(legacy_db) as db:
        db.executescript((ROOT / "migrations/early-warning/001_initial.sql").read_text())
        from osint_dashboard.common import canonical_json
        payload = canonical_json(obs)
        db.execute("INSERT INTO observations VALUES (?,?,?)", (obs["observation_id"], obs["logical_key"], payload))
    with Store(legacy) as db:
        assert db.db.execute("PRAGMA user_version").fetchone()[0] == 2
        assert db.db.execute("SELECT payload FROM observations").fetchone()[0] == payload
        assert db.counts()["observations"] == 1 and db.counts()["translations"] == 0
        with pytest.raises(sqlite3.IntegrityError, match="Append-only"):
            db.db.execute("UPDATE observations SET payload='{}'")
