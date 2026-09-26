from __future__ import annotations

import html
from datetime import date, timedelta
from urllib.parse import quote

import h3

from ..common import digest, instant
from .contracts import source_hash, validate
from .comparison import compare
from .translations import display

STATUS = {"new_report": "nowe doniesienie", "anomaly_to_review": "anomalia do sprawdzenia",
          "urgent_review": "pilny przegląd", "explained": "wyjaśnione", "insufficient_data": "brak podstaw do oceny"}
SOURCE_NAMES = {"gpsjam": "GPSJAM", "belzhd_public": "belzhd.info"}
SOURCE_STATUS = {"ok": "pobrano", "partial": "częściowe dane", "error": "błąd pobrania", "unavailable": "brak kontroli źródła"}
PROVIDER_NAMES = {"merged": "ADS-B Exchange + airplanes.live", "adsbexchange": "ADS-B Exchange", "airplaneslive": "airplanes.live"}
ATTRIBUTION = {"unknown": "nieustalona", "reported_unverified": "twierdzenie niepotwierdzone"}
LIMITATIONS = [
    "Warstwa obserwacyjna nie zmienia RTB. Priorytet przeglądu nie oznacza potwierdzenia, atrybucji ani prognozy ataku.",
    "Nie skalibrowano odniesienia ani detektora. Historia pobrana teraz nie jest zapisem wcześniejszej wiedzy systemu.",
    "Prostokąt badawczy nie jest granicą państwa. Brak komórki GNSS oznacza brak danych, nie zerowy poziom zakłóceń.",
    "Dobowy agregat GNSS nie ustala przyczyny, sprawcy ani ciągłości zakłóceń. Wspólni dostawcy nie są niezależnym dowodem.",
    "Publikacje jednego wydawcy nie zapewniają pełnej obserwacji transportów. Data publikacji nie jest datą zdarzenia.",
    "Nie ma harmonogramu, automatycznego modelu AI ani wysyłania alertów. Eksport jest lokalny; warunki redystrybucji nieustalone.",
]


def eligible_cells(obs):
    data = obs["data"]
    return [c for c in data["cells"] if c["sample"] >= data["min_cell_sample"]]


def daily_summary(record):
    obs = record["observation"]
    data = obs["data"]
    eligible = eligible_cells(obs)
    # Compare the exact counts, not the rounded display percentage. The map's
    # implementation assigns red at >=10%; the FAQ describes it as >10%.
    high = sum(10 * (c["bad"] - 1) >= c["sample"] for c in eligible)
    return {"observation_id": obs["observation_id"], "day": data["day"], "provider": data["provider"],
            "suspect": data["manifest_suspect"], "reported_cells": len(data["cells"]),
            "grid_cells": len(data["expected_cells"]), "missing_cells": len(data["expected_cells"]) - len(data["cells"]),
            "eligible_cells": len(eligible), "low_sample_cells": len(data["cells"]) - len(eligible),
            "sample_floor": data["min_cell_sample"], "high_cells": high,
            "high_cell_share_pct": round(100 * high / len(eligible), 4) if eligible else None,
            "aircraft_category_cell_sum": sum(c["sample"] for c in data["cells"]),
            "first_seen_at": obs["times"]["first_seen_at"], "last_fetched_at": record["last_fetched_at"],
            "url": obs["url"]}


def make_snapshot(inputs):
    as_of, cfg = inputs["as_of"], inputs["config"]
    end = instant(as_of).date() - timedelta(days=1)
    start = end - timedelta(days=cfg["history_days"] - 1)
    enabled = {s["id"]: s for s in cfg["sources"] if s["enabled"]}
    hashes = {sid: source_hash(s, cfg) for sid, s in enabled.items()}
    records = [r for r in inputs["observations"] if hashes.get(r["observation"]["source_id"]) == r["observation"]["source_config_hash"]]
    checks_by_id = {c["source_id"]: c for c in inputs["source_checks"]}
    checks = []
    for sid in sorted(enabled):
        check = checks_by_id.get(sid)
        if check is None or check["source_config_hash"] != hashes[sid]:
            checks.append({"source_id": sid, "status": "unavailable", "checked_at": None, "stale": True,
                           "errors": ["No check for the current source configuration"], "items": 0})
        else:
            age = (instant(as_of) - instant(check["checked_at"])).total_seconds() / 3600
            checks.append({**check, "age_hours": round(age, 2), "stale": age > cfg["check_max_age_hours"]})
    gnss_records = sorted([r for r in records if r["observation"]["data"]["type"] == "gnss_daily"
                           and start <= date.fromisoformat(r["observation"]["data"]["day"]) <= end],
                          key=lambda r: r["observation"]["data"]["day"])
    daily = [daily_summary(r) for r in gnss_records]
    latest = daily[-1] if daily else None
    missing_days = [str(start + timedelta(days=i)) for i in range(cfg["history_days"])
                    if str(start + timedelta(days=i)) not in {d["day"] for d in daily}]
    comparison = compare(gnss_records, as_of, str(end))
    reference_variant = next((v for v in comparison["variants"] if v["sample_floor"] == cfg["region"]["min_cell_sample"]), None)
    gnss = {"region": cfg["region"], "daily": daily, "latest": latest, "missing_days": missing_days,
            "comparison": comparison,
            "latest_is_expected_day": bool(latest and latest["day"] == str(end)),
            "source_regimes": sorted({d["provider"] for d in daily}),
            "reference": {"status": "not_calibrated", "detector_version": None,
                          "prior_same_provider_days": len(comparison["reference_days"]),
                          "common_eligible_cells": reference_variant["cell_count"] if reference_variant else None,
                          "reason": "Tylko diagnostyka pokrycia. Sama liczba dni nie potwierdza porównywalności ani normalnego poziomu aktywności."}}
    publications, signals = [], []
    source_freshness = {c["source_id"]: {k: c[k] for k in ("status", "stale")} for c in checks}
    for record in records:
        obs = record["observation"]
        data, oid = obs["data"], obs["observation_id"]
        if data["type"] == "publication":
            polish = display(obs, inputs.get("translations", {}).get(oid))
            publications.append({"observation_id": oid, "title": polish["title"], "title_original": data["title"],
                                 "summary": polish["summary"], "language": "pl", "translation": polish, "url": obs["url"],
                                 "published_at": obs["times"]["published_at"], "observed_start": None,
                                 "publication_age_days": round((instant(as_of) - instant(obs["times"]["published_at"])).total_seconds() / 86400, 2) if obs["times"]["published_at"] else None,
                                 "first_seen_at": obs["times"]["first_seen_at"], "last_fetched_at": record["last_fetched_at"],
                                 "text_kind": data["text_kind"], "categories_original": data["categories"],
                                 "military_transport_tag": data["military_transport_tag"],
                                 "dependency_groups": obs["dependency_groups"]})
            title = polish["title"]
            default_status = "new_report"
            default_reason = "Nowa dla lokalnego rejestru publikacja, bez weryfikacji twierdzeń i czasu zdarzenia."
        elif latest and oid == latest["observation_id"]:
            polish = None
            title = "Dobowy odczyt GNSS: " + data["day"]
            default_status = "insufficient_data"
            default_reason = "Pomiar dostępny; brak skalibrowanego odniesienia do rozpoznania anomalii."
        else:
            continue
        review = inputs["reviews"].get(oid)
        signals.append({"observation_id": oid, "source_id": obs["source_id"], "title": title, "url": obs["url"], "translation": polish,
                        "published_at": obs["times"]["published_at"], "observed_start": obs["times"]["observed_start"],
                        "first_seen_at": obs["times"]["first_seen_at"],
                        "status": review["status"] if review else default_status,
                        "reason": review["reason"] if review else default_reason,
                        "alternatives": review["alternatives"] if review else [],
                        "review": review, "reviewed": bool(review),
                        "attribution": review["attribution"] if review else {"actor": None, "status": "unknown", "reason": "Nie przeprowadzono przeglądu atrybucji."},
                        "source_freshness": source_freshness[obs["source_id"]], "event_key": review["event_key"] if review else None})
    publications.sort(key=lambda p: (p["published_at"] or "", p["observation_id"]), reverse=True)
    rank = {s: i for i, s in enumerate(("urgent_review", "anomaly_to_review", "new_report", "insufficient_data", "explained"))}
    signals.sort(key=lambda s: (rank[s["status"]], s["observation_id"]))
    snapshot = {"schema_version": "ew-snapshot-2", "language": "pl", "run_id": inputs["run_id"], "as_of": as_of, "mode": inputs["mode"],
                "window": {"start": str(start), "end": str(end)}, "config_hash": digest(cfg), "code_hash": inputs["code_hash"],
                "counts": {"current_versions": len(records), "excluded_configuration_versions": len(inputs["observations"]) - len(records),
                           "gnss_days_in_window": len(daily), "publications": len(publications),
                           "signals": len(signals), "unreviewed_signals": sum(not s["reviewed"] for s in signals),
                           "pending_translations": sum(p["translation"]["status"] != "ready" for p in publications)},
                "source_checks": checks, "gnss": gnss, "publications": publications, "signals": signals,
                "limitations": LIMITATIONS, "rtb_effect": "none"}
    validate("snapshot", snapshot)
    return snapshot


def label(value):
    value = html.escape(str(value)).replace("\n", " ")
    for ch in ("\\", "|", "[", "]", "*", "_", "`"):
        value = value.replace(ch, "\\" + ch)
    return value


def link(title, url):
    return f"[{label(title)}](<{quote(url, safe=':/?=&%+#')}>)"


def build_report(snapshot):
    gnss = snapshot["gnss"]
    lines = ["# Sygnały wczesne — pilotaż obserwacyjny", "",
             f"Stan wiedzy: **{snapshot['as_of']}**. Dane: **{'rzeczywiste' if snapshot['mode'] == 'live' else 'syntetyczne — test'}**.", "",
             "RTB: bez zmian. Sygnały i priorytety przeglądu nie są potwierdzeniem zagrożenia ani prognozą ataku.", "",
             "## Dostępność i aktualność źródeł", "",
             "| Źródło | Pobranie | Ostatnia kontrola | Bieżąca kontrola wygasła |", "|---|---|---|---|"]
    for check in snapshot["source_checks"]:
        lines.append(f"| {SOURCE_NAMES[check['source_id']]} | {SOURCE_STATUS[check['status']]} | {check['checked_at'] or 'brak'} | {'tak' if check['stale'] else 'nie'} |")
    for check in snapshot["source_checks"]:
        if check["errors"]:
            lines += ["", f"**{SOURCE_NAMES[check['source_id']]} — problemy z dostępnością lub jakością: {len(check['errors'])}.** Szczegółowa diagnostyka pozostaje w danych źródłowych wydania."]
    lines += ["", "## GNSS — pomiary i pokrycie", "",
              f"Okno UTC: {snapshot['window']['start']}–{snapshot['window']['end']}. Obszar: {label(gnss['region']['label'])}; bbox {gnss['region']['bbox']}.", "",
              f"Dostępne dni: **{len(gnss['daily'])}/{len(gnss['daily']) + len(gnss['missing_days'])}**. Brakujące pliki dobowe: {', '.join(gnss['missing_days']) or 'brak'}. "]
    latest = gnss["latest"]
    if latest:
        lines += ["", f"Najnowszy pomiar: **{latest['day']}**, dostawca: **{PROVIDER_NAMES[latest['provider']]}**; oczekiwany ostatni dzień: **{'dostępny' if gnss['latest_is_expected_day'] else 'BRAK'}**.",
                  f"Obserwowane komórki: **{latest['reported_cells']}/{latest['grid_cells']}**; bez danych: **{latest['missing_cells']}**; poniżej roboczego minimum próby {latest['sample_floor']}: **{latest['low_sample_cells']}**.",
                  f"Komórki z wartością GPSJAM ≥10% wśród spełniających minimum próby: **{latest['high_cells']}/{latest['eligible_cells']}** ({latest['high_cell_share_pct'] if latest['high_cell_share_pct'] is not None else 'brak'}%). To udział komórek, nie lotów ani prawdopodobieństwo zagrożenia.", "",
                  "| Dzień UTC | Dostawca | Komórki z danymi | Komórki spełniające minimum próby | Komórki ≥10% | Zastrzeżenie wydawcy |",
                  "|---|---|---:|---:|---:|---|"]
        for day in gnss["daily"][-7:]:
            lines.append(f"| {day['day']} | {PROVIDER_NAMES[day['provider']]} | {day['reported_cells']} | {day['eligible_cells']} | {day['high_cells']} | {'tak' if day['suspect'] else 'nie'} |")
    else:
        lines += ["", "**Brak pomiarów w wybranym oknie. Nie oznacza to braku zakłóceń.**"]
    ref = gnss["reference"]
    lines += ["", f"Odniesienie: **nieskalibrowane**. Wcześniejsze dni z tym samym zestawem dostawców, bez zastrzeżeń wydawcy: **{ref['prior_same_provider_days']}**; wspólne komórki spełniające minimum próby: **{ref['common_eligible_cells'] if ref['common_eligible_cells'] is not None else 'nie wyliczono'}**.",
              f"Zestawy dostawców w historii: {', '.join(PROVIDER_NAMES[p] for p in gnss['source_regimes']) or 'brak'}. Zmiana dostawcy kończy serię odniesienia.", ""]
    comparison = gnss["comparison"]
    lines += ["## GNSS — porównanie tego samego obszaru", ""]
    if comparison["status"] == "descriptive_only":
        lines += [f"Porównuję dobę **{comparison['target_day']}** z **{len(comparison['reference_days'])} wcześniejszymi dobami** z bieżącego zestawu dostawców. Każdy wariant używa tych samych komórek we wszystkich porównywanych dniach.", "",
                  "| Minimum próby w komórce | Wspólne komórki | Obecny udział komórek ≥10% | Mediana wcześniejszych dni | Różnica w pkt proc. |", "|---:|---:|---:|---:|---:|"]
        for v in comparison["variants"]:
            values = [f"{v[k]:.2f}" if v[k] is not None else "brak" for k in ("current_pct", "reference_median_pct", "difference_pp")]
            lines.append(f"| {v['sample_floor']} | {v['cell_count']} | {values[0]} | {values[1]} | {values[2]} |")
        lines += ["", f"Okres odniesienia: **{comparison['reference_days'][0]}–{comparison['reference_days'][-1]}**. Pominięte dni z zastrzeżeniem wydawcy: {', '.join(comparison['excluded_suspect_days']) or 'brak'}. Brakujące dni wewnątrz okresu: {', '.join(comparison['missing_reference_days']) or 'brak'}.",
                  "", "To opis zmiany względem zebranej historii. Historia nie została uznana za normalny poziom aktywności; warianty minimum próby pokazują wrażliwość wyniku. Nie wyliczam prawdopodobieństwa zagrożenia i nie uruchamiam alertu na podstawie tej tabeli."]
    else:
        reasons = {"latest_day_missing": "Brakuje pomiaru za oczekiwaną dobę.", "target_suspect": "Wydawca zgłasza zastrzeżenia do najnowszej doby.",
                   "no_prior_comparable_days": "Brakuje wcześniejszych dni z bieżącego zestawu dostawców.", "no_common_cells": "Brakuje wspólnych komórek spełniających minimum próby."}
        lines.append("**Porównanie niedostępne.** " + reasons[comparison["status"]])
    lines += ["",
              "## Publikacje logistyczne", "", "Nowe oznacza nowe dla tego rejestru. Data poniżej dotyczy publikacji; czas opisanego zdarzenia pozostaje nieustalony.", "",
              "| Publikacja UTC | Materiał | Rubryka wojskowa | Treść |", "|---|---|---|---|"]
    for pub in snapshot["publications"]:
        lines.append(f"| {pub['published_at'] or 'nieustalona'} | {link(pub['title'], pub['url'])} | {'tak' if pub['military_transport_tag'] else 'nie'} | {'pełna w RSS' if pub['text_kind'] == 'rss_full_content' else 'skrót'} |")
    lines += ["", f"Tytuły i streszczenia przygotowano po polsku. Pełne źródła oraz oryginalne cytaty pozostają w archiwum dowodowym. Materiały oczekujące na polski opis: **{snapshot['counts']['pending_translations']}**."]
    lines += ["", "## Kolejka sygnałów i przegląd", ""]
    for signal in snapshot["signals"]:
        lines += [f"### {label(STATUS[signal['status']])}: {label(signal['title'])}", "",
                  f"Publikacja: {signal['published_at'] or 'nieustalona / nie dotyczy'}. Początek pomiaru lub zdarzenia: {signal['observed_start'] or 'nieustalony'}. Pierwsze pozyskanie lokalne: {signal['first_seen_at']}.", "",
                  f"{label(signal['reason'])}", "",
                  f"Atrybucja: {ATTRIBUTION[signal['attribution']['status']]}; sprawca: {label(signal['attribution']['actor'] or 'nieustalony')}. "
                  + (f"Ocena: {'agent AI' if signal['review']['reviewer']['type'] == 'agent' else 'analityk'} / {label(signal['review']['reviewer']['name'])}, rewizja {signal['review']['revision']}." if signal['reviewed'] else "Przegląd: oczekuje."),
                  f"Źródło: {link('materiał', signal['url'])}. Wersja: `{signal['observation_id']}`.", ""]
        if signal["alternatives"]:
            lines += ["Alternatywne wyjaśnienia: " + "; ".join(label(a) for a in signal["alternatives"]), ""]
        if signal["translation"]:
            lines += ["**Streszczenie źródła po polsku:** " + label(signal["translation"]["summary"]), ""]
            if signal["translation"]["uncertainties"]:
                lines += ["Zastrzeżenia do opisu: " + "; ".join(label(u) for u in signal["translation"]["uncertainties"]), ""]
    lines += ["## Ograniczenia", ""] + ["- " + s for s in snapshot["limitations"]]
    lines += ["", f"Wydanie: `{snapshot['run_id']}`. Pełna seria: `snapshot.json`; dowody lokalne: `review_queue.json`; geometrie: `observations.geojson`.", ""]
    return "\n".join(lines)


def geojson(inputs, snapshot):
    features = []
    latest = snapshot["gnss"]["latest"]
    if latest:
        obs = next(r["observation"] for r in inputs["observations"] if r["observation"]["observation_id"] == latest["observation_id"])
        cells = {c["h3"]: c for c in obs["data"]["cells"]}
        for hid in obs["data"]["expected_cells"]:
            boundary = [[lon, lat] for lat, lon in h3.cell_to_boundary(hid)]
            cell = cells.get(hid)
            quality = "missing" if cell is None else "low_sample" if cell["sample"] < obs["data"]["min_cell_sample"] else "observed"
            features.append({"type": "Feature", "id": hid, "geometry": {"type": "Polygon", "coordinates": [boundary + [boundary[0]]]},
                             "properties": {"kind": "gnss_daily", "observation_id": obs["observation_id"], "day": latest["day"],
                                            "h3": hid, "quality": quality, "source_adjusted_pct": cell["source_adjusted_pct"] if cell else None,
                                            "sample": cell["sample"] if cell else None, "provider": latest["provider"],
                                            "suspect": latest["suspect"], "attribution": "unknown"}})
    for pub in snapshot["publications"]:
        features.append({"type": "Feature", "id": pub["observation_id"], "geometry": None,
                         "properties": {"kind": "publication", "title": pub["title"], "url": pub["url"],
                                        "published_at": pub["published_at"], "observed_start": None, "location_precision": "unknown"}})
    return {"type": "FeatureCollection", "features": features}
