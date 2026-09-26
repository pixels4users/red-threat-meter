from __future__ import annotations

from ..common import digest, instant
from .analysis import analyze_sample

STATUS = {"ok": "pobrano cały zakres zapytań", "partial": "częściowe dane", "unavailable": "brak danych bieżących"}
ERRORS = {"http_error": "błąd HTTP", "network_error": "błąd połączenia", "response_too_large": "przekroczony limit odpowiedzi",
          "not_requested_after_http_error": "pominięto po błędzie dostępu lub limitu",
          "invalid_contract": "odpowiedź niezgodna z kontraktem", "stale_or_future_response": "nieaktualny lub przyszły czas danych"}
LIMITATIONS = [
    "Wynik dotyczy widocznych identyfikatorów nadajników w krótkich próbach. Nie jest liczbą lotów, operacji ani wszystkich samolotów regionu.",
    "Zapytanie regionalne wybiera obiekty z pozycją. Nie mierzy liczby niewidocznych nadajników ani rzeczywistego pokrycia odbiornikami.",
    "Pole bez obserwacji nie dowodzi braku ruchu. Awaria zapytania i brak świeżych pozycji pozostają osobnymi stanami.",
    "Typy i flaga wojskowa pochodzą z bazy dostawcy. Brak flagi nie potwierdza cywilnego operatora; nie ustalono operatorów, misji ani intencji.",
    "Próby są uruchamiane ręcznie; przerwy między nimi nie są okresem monitorowanym. Brak harmonogramu, kalibracji oraz alertów.",
    "ADSB.lol i produkty wykorzystujące tę sieć mają wspólne pochodzenie. Wspólne odbiorniki z innymi sieciami pozostają nieustalone.",
    "Pilot nie zmienia RTB ani statusów GNSS/logistyki. Długa historia i test skuteczności ostrzeżeń pozostają dalszą pracą.",
]


def make_snapshot(inputs, folder):
    cfg, as_of = inputs["config"], inputs["as_of"]
    samples = [analyze_sample(s, folder) for s in inputs["samples"] if digest(s["config"]) == digest(cfg)]
    latest = samples[-1] if samples else None
    comparable = [s for s in samples if s["status"] == "ok"]
    gaps = [round((instant(b["started_at"]) - instant(a["finished_at"])).total_seconds(), 3) for a, b in zip(samples, samples[1:])]
    empty = sum(s["metrics"]["rows_received"] == 0 for s in comparable)
    age = (instant(as_of) - instant(latest["finished_at"])).total_seconds() if latest else None
    series = [{k: s[k] for k in ("sample_id", "started_at", "finished_at", "status", "metrics", "content_fingerprint")} for s in samples]
    usable = [s for s in samples if s["metrics"]["usable_queries"]]
    return {"schema_version": "aviation-snapshot-1", "language": "pl", "run_id": inputs["run_id"], "as_of": as_of,
            "mode": inputs["mode"], "code_hash": inputs["code_hash"], "config_hash": digest(cfg), "region": cfg["region"],
            "source": cfg["source"], "quality_rules": {k: cfg[k] for k in ("response_max_age_seconds", "position_max_age_seconds", "report_max_age_seconds")},
            "counts": {"samples": len(samples), "excluded_configuration_samples": len(inputs["samples"]) - len(samples),
                       "complete_samples": len(comparable), "partial_samples": sum(s["status"] == "partial" for s in samples),
                       "unavailable_samples": sum(s["status"] == "unavailable" for s in samples), "complete_empty_samples": empty,
                       "unavailable_sample_share_pct": round(100 * sum(s["status"] == "unavailable" for s in samples) / len(samples), 2) if samples else None,
                       "distinct_usable_payload_sets": len({s["content_fingerprint"] for s in usable})},
            "latest": latest, "latest_age_seconds": round(age, 3) if age is not None else None,
            "latest_is_current": age is not None and 0 <= age <= cfg["report_max_age_seconds"] and latest["status"] != "unavailable",
            "series": series, "gaps_seconds": gaps, "history_hours": cfg["history_hours"],
            "receiver_coverage": "unknown", "rtb_effect": "none", "limitations": LIMITATIONS}


def value(number):
    return "brak danych" if number is None else str(number).replace(".", ",")


def build_report(snap):
    unavailable_share = snap['counts']['unavailable_sample_share_pct']
    share_label = 'brak prób do porównania' if unavailable_share is None else value(unavailable_share) + '%'
    lines = ["# Dane lotnicze — pilotaż jakości ADSB.lol", "",
             f"Stan wiedzy: **{snap['as_of']}**. Dane: **{'rzeczywiste' if snap['mode'] == 'live' else 'syntetyczne — test'}**.", "",
             "Źródło: [ADSB.lol](https://www.adsb.lol/). Licencja danych: [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). RTB: bez zmian.", "",
             f"Region badawczy: bbox **{snap['region']['bbox']}**. Cztery zapytania o koła o promieniu 250 mil morskich, przycięcie do prostokąta i usunięcie powtórzeń identyfikatora.", "",
             "## Dostępność prób", "",
             f"Próby w ostatnich {snap['history_hours']} godzinach: **{snap['counts']['samples']}**; pełne zapytania: **{snap['counts']['complete_samples']}**; częściowe: **{snap['counts']['partial_samples']}**; bez danych bieżących: **{snap['counts']['unavailable_samples']}**.",
             f"Udział prób bez danych bieżących: **{share_label}**. Pełne odpowiedzi bez rekordów: **{snap['counts']['complete_empty_samples']}**.",
             f"Różne zestawy użytecznych odpowiedzi: **{snap['counts']['distinct_usable_payload_sets']}**. Przerwy między końcem a początkiem kolejnych prób: **{', '.join(value(g) for g in snap['gaps_seconds']) or 'brak porównania'}** sekund.", ""]
    latest = snap["latest"]
    if not latest:
        lines += ["**Brak prób dla obecnej konfiguracji w oknie. Nie oznacza to braku lotów.**", ""]
    else:
        m = latest["metrics"]
        lines += ["## Ostatnia próba", "", f"Czas: **{latest['started_at']}–{latest['finished_at']}**. Wynik: **{STATUS[latest['status']]}**.",
                  f"Aktualna na moment raportu: **{'tak' if snap['latest_is_current'] else 'nie'}**; wiek próby: **{value(snap['latest_age_seconds'])} s**. Poniższe liczby opisują chwilę zakończenia próby, nie ruch po jej zakończeniu.", "",
                  "| Miara | Wynik |", "|---|---:|",
                  f"| Użyteczne odpowiedzi / plan | {m['usable_queries']}/{m['planned_queries']} |",
                  f"| Rekordy w poprawnie odczytanych odpowiedziach | {m['rows_received']} |",
                  f"| Odrzucone wiersze niezgodne z formatem | {m['invalid_rows']} |",
                  f"| Usunięte powtórzenia między odpowiedziami i w odpowiedziach | {m['overlap_rows_removed']} |",
                  f"| Świeże identyfikatory w regionie | {value(m['fresh_in_region'])} |",
                  f"| W regionie: pozycja nieaktualna lub przyszła / wiek nieznany | {m['stale_or_future_position']} / {m['unknown_position_age']} |",
                  f"| W odpowiedziach: brak pozycji / ostatnia pozycja poza regionem | {m['missing_position']} / {m['outside_region']} |",
                  f"| Wiek świeżej pozycji: mediana / percentyl 95 | {value(m['position_age_median_seconds'])} / {value(m['position_age_p95_seconds'])} s |",
                  f"| Pola siatki z obserwacją / wszystkie pola | {m['observed_cells']}/{m['total_cells']} |",
                  f"| Pola bez obserwacji przy dostępnym zakresie zapytania | {m['empty_observed_scope_cells']} |",
                  f"| Pola bez obserwacji i bez pełnego dostępnego zapytania | {m['query_gap_cells']} |", "",
                  "Zasięg zapytania jest znany; rzeczywiste pokrycie odbiornikami pozostaje **nieustalone**. Siatka ma pola 1° × 1° i nie mierzy procentu obserwowanej przestrzeni powietrznej.", "",
                  "| Część regionu | HTTP | Rekordy odpowiedzi | Odrzucone wiersze | Stan |", "|---|---:|---:|---:|---|"]
        for r in latest["requests"]:
            state = ERRORS.get(r["error"], "poprawny odczyt" if not r["rejected_row_indices"] else "odczyt z odrzuconymi wierszami")
            lines.append(f"| {r['label']} | {r['http_status'] or 'brak'} | {value(r['reported_rows'])} | {len(r['rejected_row_indices'])} | {state} |")
        if m["fresh_in_region"] is not None:
            lines += ["", "## Oznaczenia dostawcy", "",
                      f"Wśród świeżych identyfikatorów: **{m['fresh_airborne_reported']}** z liczbową wysokością barometryczną, **{m['fresh_on_ground_reported']}** z oznaczeniem naziemnym, **{m['ground_status_unknown']}** bez rozstrzygnięcia. To oznaczenia rekordu, nie liczba wykonanych lotów.",
                      f"Flaga wojskowa w bazie dostawcy: **{m['military_flag_yes']}**; flaga nieustawiona: **{m['military_flag_absent']}**; brak pola flag: **{m['military_flag_unknown']}**. Operatorzy niezależnie ustaleni: **0**.",
                      "Typy statków powietrznych według dostawcy: " + (", ".join(f"{t if t != 'unknown' else 'nieznany'}: {v}" for t, v in m["reported_aircraft_types"].items()) or "brak") + ".",
                      "Flaga nie potwierdza bieżącego operatora ani zadania. Nie wyliczamy na jej podstawie aktywności RU/BY lub NATO.", ""]
    lines += ["## Historia prób", "", "| Koniec próby UTC | Dostęp | Świeże identyfikatory w regionie | Pola z obserwacją |", "|---|---|---:|---:|"]
    for s in snap["series"]:
        lines.append(f"| {s['finished_at']} | {STATUS[s['status']]} | {value(s['metrics']['fresh_in_region'])} | {s['metrics']['observed_cells']} |")
    lines += ["", "## Ograniczenia", "", *["- " + x for x in snap["limitations"]], "",
              f"Wydanie: `{snap['run_id']}`. Dane liczbowe: `snapshot.json`; przestrzenne agregaty: `coverage.geojson`. Oryginalne odpowiedzi i znaczniki czasu zachowano lokalnie.", ""]
    return "\n".join(lines)


def geojson(snap):
    latest = snap["latest"]
    features = []
    if latest:
        for cell in latest["cells"]:
            w, s, e, n = cell["bbox"]
            features.append({"type": "Feature", "id": cell["id"],
                             "geometry": {"type": "Polygon", "coordinates": [[[w,s],[e,s],[e,n],[w,n],[w,s]]]},
                             "properties": {k: v for k, v in cell.items() if k not in ("bbox", "id")} |
                                           {"sampled_at": latest["finished_at"], "is_current": snap["latest_is_current"],
                                            "receiver_coverage": "unknown", "source": "ADSB.lol", "license": "ODbL-1.0"}})
    return {"type": "FeatureCollection", "features": features}
