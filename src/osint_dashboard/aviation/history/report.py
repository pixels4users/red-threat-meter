from __future__ import annotations

import zlib

from ...common import instant
from .contracts import raw_bytes, validate_acquisition
from .decode import decode

LIMITATIONS = [
    "Trzy krótkie okna służą ocenie jakości. Nie stanowią normalnego poziomu aktywności ani progu alarmowego.",
    "Licznik opisuje identyfikatory w przedziale próbkowania; nie liczbę lotów, operacji ani wszystkich samolotów. Obejmuje także oznaczenia naziemne.",
    "Znaczniki czasu określają przedziały historii. Format nie zachowuje dokładnego czasu każdej pozycji ani jej wieku z bieżącego API.",
    "Puste przedziały i komórki oznaczają brak obserwacji. Nie dowodzą braku ruchu ani pełnego pokrycia odbiornikami.",
    "Historia mapy i API mają wspólną grupę pochodzenia ADSB.lol. Skład odbiorników i tożsamość instancji serwera pozostają nieustalone.",
    "Format nie zawiera kodów typu samolotu ani flag wojskowych. Nie uzupełniamy ich wstecz dzisiejszymi etykietami; operator i intencja pozostają nieustalone.",
    "Wysokość historii może być barometryczna albo geometryczna; format nie rozróżnia ich przy pojedynczej pozycji.",
    "Dane pozyskano dopiero w czasie podanym w raporcie. Last-Modified nie jest dowodem wcześniejszej dostępności dla systemu.",
    "Porównanie z API jest diagnostyką retrospektywną, bez niezależnej prawdy referencyjnej, miary trafności ani punktów RTB.",
]

ERRORS = {"network_error": "błąd połączenia", "http_error": "błąd HTTP",
          "response_too_large_or_invalid_length": "przekroczony limit lub błędny rozmiar",
          "truncated_or_oversized_response": "odpowiedź ucięta lub osiągnięty limit",
          "not_requested_after_access_error": "pominięto po błędzie dostępu lub limitu", "invalid_format": "niezgodny format archiwum"}


def compare_live(reference, decoded):
    start = instant(reference["started_at"])
    candidates = [(d, f) for d in decoded for f in d["frames"] if instant(f["end"]) <= start
                  and 0 <= (start - instant(f["end"])).total_seconds() < d["interval_seconds"]]
    base = {"live_release": reference["run_id"], "live_started_at": reference["started_at"],
            "live_finished_at": reference["finished_at"], "status": "no_matching_interval"}
    if len(candidates) != 1:
        return base
    d, frame = candidates[0]
    if d["status"] != "ok" or reference["status"] != "ok":
        return {**base, "status": "incomplete_quality"}
    a, b = set(reference["identifiers"]), set(frame["identifiers"])
    return {**base, "status": "diagnostic_only", "historical_interval_start": frame["start"],
            "historical_interval_end": frame["end"], "seconds_before_live_start": round((start - instant(frame["end"])).total_seconds(), 3),
            "live_identifiers": len(a), "historical_identifiers": len(b), "common_identifiers": len(a & b),
            "only_live": len(a - b), "only_history": len(b - a), "freshness_equivalent": False, "independent_sources": False}


def make_snapshot(inputs, folder):
    acq = inputs["acquisition"]
    validate_acquisition(acq)
    if instant(acq["finished_at"]) > instant(inputs["as_of"]):
        raise ValueError("Raport wyprzedza rzeczywiste pozyskanie historii")
    results, decoded = [], []
    for receipt in acq["requests"]:
        body = raw_bytes(folder, receipt["raw_ref"]) if receipt["raw_ref"] else None
        if body is not None and len(body) != receipt["bytes"]:
            raise ValueError("Rozmiar dowodu nie zgadza się z potwierdzeniem")
        record = {"window": receipt["window"], "http_status": receipt["http_status"], "downloaded_bytes": receipt["bytes"],
                  "received_at": receipt["received_at"], "raw_ref": receipt["raw_ref"], "error": receipt["error"],
                  "status": "unavailable", "source_last_modified": receipt["headers"].get("last-modified")}
        if receipt["http_status"] == 200 and not receipt["error"]:
            try:
                data = decode(body, receipt["window"], acq["config"])
            except (ValueError, OSError, EOFError, zlib.error):
                record["error"] = "invalid_format"
            else:
                decoded.append(data)
                record.update({k: v for k, v in data.items() if k != "frames"})
                record["series"] = [{k: v for k, v in f.items() if k != "identifiers"} for f in data["frames"]]
        results.append(record)
    refs = inputs["live_references"]
    if [r["run_id"] for r in refs] != acq["config"]["live_releases"]:
        raise ValueError("Referencje API nie zgadzają się z planem")
    for ref in refs:
        if ref["bbox"] != acq["config"]["bbox"] or ref["mode"] != acq["mode"]:
            raise ValueError("Niezgodny region lub tryb referencji API")
        if not instant(ref["started_at"]) <= instant(ref["finished_at"]) <= instant(ref["available_at"]) <= instant(inputs["as_of"]):
            raise ValueError("Referencja API nie była dostępna w chwili raportu")
        if len(ref["identifiers"]) != len(set(ref["identifiers"])):
            raise ValueError("Powtórzone identyfikatory referencji")
    cell_sets = [{c["id"] for c in d["cells"] if c["status"] == "observed"} for d in decoded]
    complete = sum(d["status"] == "ok" for d in decoded)
    return {"version": "aviation-history-report-1", "language": "pl", "run_id": inputs["run_id"],
            "as_of": inputs["as_of"], "mode": acq["mode"], "code_hash": inputs["code_hash"], "acquisition_id": acq["id"],
            "acquired_from": acq["started_at"], "acquired_until": acq["finished_at"], "bbox": acq["config"]["bbox"],
            "source": "ADSB.lol", "license": acq["config"]["license"], "dependency_group": acq["config"]["dependency_group"],
            "counts": {"planned_windows": len(results), "complete_windows": complete,
                       "partial_windows": len(decoded) - complete, "unavailable_windows": len(results) - len(decoded),
                       "downloaded_bytes": sum(r["bytes"] for r in acq["requests"]),
                       "decoded_bytes": sum(d["decoded_bytes"] for d in decoded),
                       "intervals": sum(d["intervals"] for d in decoded),
                       "missing_intervals_in_decoded_files": sum(len(d["missing_intervals"]) for d in decoded),
                       "cells_observed_in_each_decoded_window": len(set.intersection(*cell_sets)) if cell_sets else None,
                       "cells_observed_in_any_decoded_window": len(set.union(*cell_sets)) if cell_sets else None},
            "windows": results, "live_comparisons": [compare_live(r, decoded) for r in refs],
            "comparability": {"same_utc_slot": len({w["window"]["chunk"] for w in results}) == 1,
                              "same_interval_in_decoded_files": len({d["interval_seconds"] for d in decoded}) == 1 if decoded else None,
                              "provider_instance_consistency": "unverified", "receiver_coverage_equivalence": "unverified",
                              "live_freshness_equivalence": False, "classification_available": False,
                              "baseline_eligible": False, "status": "descriptive_only"},
            "rtb_effect": "none", "limitations": LIMITATIONS}


def value(x):
    return "brak danych" if x is None else str(x).replace(".", ",")


def build_report(s):
    c = s["counts"]
    outcome = ("Wycinek umożliwia opis obserwacji i diagnostykę jakości. Nie jest skalibrowanym odniesieniem ani serią równoważną bieżącemu API."
               if c["complete_windows"] + c["partial_windows"] else "Brak poprawnie odczytanych okien. Brak podstaw do empirycznego porównania aktywności.")
    lines = ["# Historia lotnicza — audyt jakości i porównywalności", "",
             f"Stan analizy: **{s['as_of']}**. Dane: **{'rzeczywiste' if s['mode'] == 'live' else 'syntetyczne — test'}**.",
             f"Pozyskano: **{s['acquired_from']} – {s['acquired_until']}**. Obszar: **{s['bbox']}**.", "",
             "Źródło: [ADSB.lol](https://www.adsb.lol/), [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Wspólne pochodzenie z bieżącym API; RTB bez zmian.", "",
             f"**Wynik: {outcome}**", "",
             "## Dostęp i rozmiar", "",
             f"Okna planowane: **{c['planned_windows']}**; poprawne: **{c['complete_windows']}**; częściowe: **{c['partial_windows']}**; niedostępne: **{c['unavailable_windows']}**.",
             f"Pobrane treści: **{c['downloaded_bytes']} bajtów**; po rozpakowaniu poprawnie odczytanych plików: **{c['decoded_bytes']} bajtów**. Wielkości nie obejmują całego dziennego archiwum ani narzutu sieciowego.",
             f"Odczytane przedziały: **{c['intervals']}**. Brakujące przedziały w odczytanych plikach: **{c['missing_intervals_in_decoded_files']}**. Dla niedostępnego pliku nie zakładamy zerowej aktywności.", "",
             "| Dzień i okno UTC | HTTP | Treść w bajtach | Stan |", "|---|---:|---:|---|"]
    for w in s["windows"]:
        label = ERRORS.get(w["error"], "poprawny" if w["status"] == "ok" else "częściowy")
        lines.append(f"| {w['window']['date']}, {w['window']['start'][11:16]}–{w['window']['end'][11:16]} | {w['http_status'] or 'brak'} | {w['downloaded_bytes']} | {label} |")
    lines += ["", "## Obserwacje w wybranym regionie", "",
              "| Dzień | Przedziały / oczekiwane | Krok | Identyfikatory na przedział: min / mediana / max | Unikalne w całym oknie | Pola z obserwacją |", "|---|---:|---:|---:|---:|---:|"]
    for w in s["windows"]:
        if w["status"] == "unavailable":
            continue
        n = w["identifiers_per_interval"]
        lines.append(f"| {w['window']['date']} | {w['intervals']}/{w['expected_intervals']} | {value(w['interval_seconds'])} s | {n['min']} / {value(n['median'])} / {n['max']} | {w['unique_identifiers_in_window']} | {w['observed_cells']}/{w['total_cells']} |")
    lines += ["", "| Dzień | Odrzucone rekordy | Powtórzone rekordy | Konflikty identyfikatorów | Puste przedziały w regionie |", "|---|---:|---:|---:|---:|"]
    for w in s["windows"]:
        if w["status"] == "unavailable":
            continue
        q = w["quality"]
        lines.append(f"| {w['window']['date']} | {q.get('invalid_rows',0)} | {q.get('duplicate_rows',0)} | {q.get('conflicting_identifiers',0)} | {w['empty_region_intervals']} |")
    lines += ["", "Powtarzający się identyfikator w kolejnych przedziałach jest kolejną obserwacją, nie kolejnym lotem. Przedział zawiera wybrane punkty śladu; dokładny czas pojedynczej pozycji nie jest zachowany.",
              f"Pola z obserwacją w każdym odczytanym oknie: **{value(c['cells_observed_in_each_decoded_window'])}**; w co najmniej jednym: **{value(c['cells_observed_in_any_decoded_window'])}**. To obecność obserwacji, nie pomiar zasięgu odbiorników.", "",
              "## Porównanie z zachowanymi pomiarami API", "",
              "Wybieramy ostatni pełny przedział historii zakończony przed rozpoczęciem danego pomiaru API, bez wybierania pozycji z przyszłości. Miary mają odmienne reguły próbkowania i świeżości. Wspólne identyfikatory nie stanowią niezależnego potwierdzenia.", "",
              "| Początek pomiaru API UTC | Identyfikatory API | Historia | Wspólne | Tylko API | Tylko historia | Odstęp od końca przedziału |", "|---|---:|---:|---:|---:|---:|---:|"]
    for r in s["live_comparisons"]:
        if r["status"] != "diagnostic_only":
            lines.append(f"| {r['live_started_at']} | brak porównywalnego przedziału | — | — | — | — | — |")
        else:
            lines.append(f"| {r['live_started_at']} | {r['live_identifiers']} | {r['historical_identifiers']} | {r['common_identifiers']} | {r['only_live']} | {r['only_history']} | {value(r['seconds_before_live_start'])} s |")
    if not s["live_comparisons"]:
        lines += ["", "Nie wskazano zapisanych pomiarów API do porównania."]
    lines += ["", "## Decyzja metodologiczna", "",
              "Zachowujemy dwie odrębne serie: obserwacje API z kontrolą wieku pozycji i przedziały historyczne. Na podstawie tego wycinka nie wyliczamy delty zagrożenia, aktywności RU/BY lub NATO ani alarmu.",
              "Dalsza walidacja wymaga różnych pór i dni, sprawdzenia zmian źródła oraz osobnego, historycznie poprawnego rejestru klas obiektów. Nie przypisujemy dawnym obserwacjom dzisiejszych etykiet operatora.", "",
              "## Ograniczenia", "", *["- " + x for x in s["limitations"]], "",
              f"Wydanie: `{s['run_id']}`. Dane: `snapshot.json`; siatka: `coverage.geojson`; zamrożone wejścia: `replay-input.json`. Odtwarzanie nie używa internetu.", ""]
    return "\n".join(lines)


def geojson(s):
    features = []
    for window in s["windows"]:
        for cell in window.get("cells", []):
            w, south, e, n = cell["bbox"]
            features.append({"type": "Feature", "id": window["window"]["date"] + ":" + str(window["window"]["chunk"]) + ":" + cell["id"],
                             "geometry": {"type": "Polygon", "coordinates": [[[w,south],[e,south],[e,n],[w,n],[w,south]]]},
                             "properties": {k: v for k, v in cell.items() if k not in ("bbox", "id")} |
                                           {"window_start": window["window"]["start"], "window_end": window["window"]["end"],
                                            "source": "ADSB.lol", "license": "ODbL-1.0", "historical": True}})
    return {"type": "FeatureCollection", "features": features}
