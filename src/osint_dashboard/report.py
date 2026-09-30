from __future__ import annotations

REASONS = {
    'v03_assessment_missing': 'Brak oceny czasu i zasięgu według v0.3',
    'occurrence_time_unknown': 'Nieustalony czas zdarzenia',
    'occurrence_after_cutoff': 'Czas zdarzenia wykracza poza odcięcie',
    'decay_time_ambiguous': 'Dokładność czasu nie pozwala wyznaczyć jednej wagi',
    'expired_weight': 'Wygasły wkład modelu',
    'episode_conflict': 'Sprzeczne opisy wspólnego epizodu',
    'same_episode': 'Ten sam epizod, bez podwójnego naliczenia',
    'component_in_multiple_episodes': 'Obiekt przypisany do więcej niż jednego epizodu',
    "context_only": "Kontekst, bez punktów RTB",
    "occurrence_date_unknown": "Brak potwierdzonej daty zdarzenia",
    "outside_event_window": "Poza oknem zdarzeń",
    "occurrence_not_confirmed": "Zdarzenie niepotwierdzone lub obalone",
    "outside_geographic_scope": "Poza zakresem geograficznym RTB",
    "hostile_attribution_not_confirmed": "Brak potwierdzonego przypisania RU/BY",
    "source_has_newer_version": "Źródło zmienione — potrzebny ponowny przegląd",
    "category_criteria_not_met": "Niespełnione kryteria kategorii",
    "same_campaign_and_category": "Wspólna kampania i kategoria — bez powielania punktów",
    "superseded_review": "Późniejsza ocena zastąpiła tę kwalifikację",
    "evidence_validation_failed": "Dowody nie przeszły walidacji",
    "review_after_cutoff": "Ocena powstała po chwili odcięcia",
    "evidence_after_cutoff": "Materiał pozyskany po chwili odcięcia",
}


def safe(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;").replace("[", "\\[").replace("]", "\\]")


def link(title: str, url: str) -> str:
    # Angle brackets make URLs containing parentheses safe in Markdown destinations.
    return f"[{safe(title)}](<{url}>)"


def build_report(snapshot: dict) -> str:
    rtb = snapshot["rtb"]
    mode = "DANE SYNTETYCZNE — TEST" if snapshot["mode"] == "fixture" else "PILOTAŻ — MATERIAŁY Z RZECZYWISTYCH ŹRÓDEŁ"
    value = f"{rtb['score']}/100 — indeks eksperymentalny" if rtb["score"] is not None else "Niewyliczony — dane lub przegląd niepełne"
    lines = ["# Geopolitical Brief / RTB", "", "## 1. Podsumowanie", "", f"**{mode}**", "", f"**RTB: {value}**", "",
             f"Stan wiedzy: {snapshot['as_of']}. Wersja reguł: `{snapshot['methodology_version']}`.",
             f"Okno: {snapshot['window']['start']} → {snapshot['window']['end']} (wyświetlenie czasu w UTC).", "",
             "Wynik opisuje nasilenie potwierdzonych sygnałów istotnych dla Polski i wschodniej flanki NATO. Nie jest prawdopodobieństwem eskalacji ani oceną zamiaru ataku.", "",
             "Trend: brak porównywalnego odczytu odniesienia." if rtb["delta_points"] is None else f"Zmiana: {rtb['delta_points']:+d} pkt.", ""]
    alert = rtb.get("alert", {}).get("status")
    if alert == "analyst_review_required":
        lines += ["**Próg roboczy przekroczony: wymagany pilny przegląd analityczny.** Nie oznacza to wysokiego prawdopodobieństwa wojny.", ""]
    if "components" in rtb:
        lines += [f"Wkłady po limitach: działania przeciw państwom regionu — {rtb['components']['hostile_activity']} pkt; sygnały przygotowań — {rtb['components']['preparation']} pkt. Baza nie jest częścią tych sum.", ""]
    if rtb["blockers"]:
        lines += ["**Co ogranicza odczyt:**", ""]
        for blocker in rtb["blockers"]:
            if blocker.startswith("unreviewed_candidates:"):
                message = "Doniesienia oczekujące na przegląd: " + blocker.split(":")[-1]
            elif blocker.startswith("source_window_incomplete:"):
                message = "Dostępna lista publikacji nie obejmuje całego okna: " + blocker.split(":")[-1]
            elif blocker.startswith("source_unavailable_or_partial:"):
                message = "Źródło niedostępne lub pobrane częściowo: " + blocker.split(":")[-1]
            elif blocker.startswith("source_check_stale:"):
                message = "Ostatnie pobranie źródła jest starsze niż 8 godzin: " + blocker.split(":")[-1]
            elif blocker.startswith("source_config_changed:"):
                message = "Zmieniono konfigurację źródła; potrzebne nowe pobranie: " + blocker.split(":")[-1]
            elif blocker.startswith("unresolved_event:"):
                message = "Zdarzenie wymaga uzupełnienia daty lub dowodów: " + blocker.split(":")[-1]
            elif blocker.startswith("stale_event_review:"):
                message = "Ocena zdarzenia dotyczy starszej wersji źródła: " + blocker.split(":")[-1]
            else:
                message = 'Nie zakończono przeglądu 216 godzin historii zdarzeń i ich korekt.' if blocker == 'event_history_unverified' else blocker
            lines.append("- " + safe(message))
        lines.append("")
    if 'regions' in rtb:
        lines += ['**Wyniki regionalne — widoki wojewódzkie**', '', '| Widok | RTB | Wkład bezpośredni | Wkład przeniesiony |', '|---|---:|---:|---:|']
        for label,region in [('Warszawa / mazowieckie','PL-14'),('Łódź / łódzkie','PL-10')]:
            r=rtb['regions'][region]
            lines.append(f"| {label} | {r['score'] if r['score'] is not None else 'niewyliczony'} | {r['direct_points']:.3f} | {r['propagated_points']:.3f} |")
        lines += ['', 'Wkłady przy niepełnej ocenie są diagnostyką. Korelacja GNSS: ' + ('dopuszczona według konfiguracji.' if rtb['diagnostics']['gnss_correlation_enabled'] else 'nieoceniona — brak dopuszczonego detektora o odpowiedniej rozdzielczości.'), '']
        if rtb['alert']['status']=='analyst_review_required' and not rtb['red_priority']['eligible']:
            lines += ['Czerwony priorytet wstrzymany: brak wymaganych niezależnych dowodów bezpośrednich.', '']
        for warning in rtb['official_warnings']:
            lines += [f"**Oficjalne ostrzeżenie: {safe(warning['area'])} — {safe(warning['status'])}**",safe(warning['instruction_pl']), '']
    lines += ["**Stan źródeł**", "", "| Źródło | Pobranie | Pozycji | Pokrycie okna publikacji |", "|---|---|---:|---|"]
    for source in snapshot["sources"]:
        lines.append(f"| {safe(source['publisher'])} | {safe(source['status'])} | {source['item_count']} | {'tak' if source['window_complete'] else 'niepełne'} |")
    for source in snapshot["sources"]:
        for error in source["errors"]:
            lines.append(f"\n- {safe(source['publisher'])}: {safe(error)}")
    if rtb["score"] is not None and not rtb["contributions"]:
        lines += ["", "Odczyt równy bazie 10 oznacza brak zakwalifikowanych punktów w zebranym pakiecie. Nie potwierdza niskiego zagrożenia ani braku incydentów poza monitorowanymi źródłami."]
    lines += ["", snapshot["coverage"]["note"], "", "Wnioski o intencjach, szczeblu eskalacji i scenariuszach na 2–6 tygodni wymagają osobnego przeglądu analityka. Ten eksport nie wyprowadza ich automatycznie z punktów.", "", "## 2. Zestawienie obserwacji i incydentów", ""]
    sources = {m["material_id"]: m for m in snapshot["materials"]}
    contribution = {c["incident_id"]: c["points"] for c in rtb["contributions"]}
    exclusions = {e["incident_id"]: REASONS.get(e["reason"], e["reason"]) for e in rtb["exclusions"]}
    if not snapshot["incidents"]:
        lines += ["Brak zdarzeń z zarejestrowanym przeglądem. Zebrane publikacje nie są automatycznie traktowane jako potwierdzone incydenty.", ""]
    for event in snapshot["incidents"]:
        lines += [f"### {safe(event['title'])}", "", safe(event["summary"]), "",
                  f"Data zdarzenia: {event['occurred_on'] or 'nieustalona'}. Status: `{event['status']}`. "
                  f"Atrybucja: `{event['attribution']['actor']}` / `{event['attribution']['status']}`.",
                  f"Ocenił: {safe(event['reviewer']['name'])} ({event['reviewer']['type']}); rewizja {event['revision']}.",
                  f"Punkty: {contribution.get(event['incident_id'], 0)}. {exclusions.get(event['incident_id'], 'Spełnione warunki naliczania.')}", ""]
        used = set()
        for evidence in event["evidence"]:
            material = sources[evidence["material_id"]]
            if material["material_id"] not in used:
                lines.append("- " + link(material["title"], material["url"]) + f" — {safe(material['publisher'])}")
                used.add(material["material_id"])
        lines.append("")
    lines += ["**Rejestr publikacji i ocen**", "", "| Publikacja | Źródło | Ocena | Uzasadnienie |", "|---|---|---|---|"]
    labels = {"unreviewed": "Wymaga przeglądu", "exclude": "Poza punktacją", "incident": "Powiązana z obserwacją"}
    for candidate in snapshot["candidates"]:
        lines.append(f"| {link(candidate['title'], candidate['url'])} | {safe(candidate['source_id'])} | {safe(labels[candidate['status']])} | {safe(candidate['resolution_reason'] or 'Brak zapisanej oceny')} |")
    lines += ["", f"Suma punktów z kwalifikujących się ocen: {rtb['raw_reviewed_sum']}; po limitach kategorii: {rtb['capped_reviewed_sum']}. "
              "Przy niepełnych danych ta suma jest wyłącznie diagnostyką obliczeń.", "",
              "**Ograniczenia**", ""]
    lines += ["- " + safe(item) for item in snapshot["limitations"]]
    lines += ["", "## 3. Dane przestrzenne", "", "Plik `incidents.geojson` w tym wydaniu zawiera lokalizacje WGS84, z kolejnością długość/szerokość. Nieustalona geometria pozostaje `null`. Bliskość obszaru strategicznego nie dodaje punktów. Baza lokalna: SQLite; PostGIS nie jest wymagany.", "",
              f"Identyfikator wydania: `{snapshot['run_id']}`. Raport i eksport odnoszą się do tego samego zapisanego przebiegu.", ""]
    return "\n".join(lines)


def geojson(snapshot: dict) -> dict:
    return {"type": "FeatureCollection", "run_id": snapshot["run_id"],
            "features": [{"type": "Feature", "id": e["incident_id"], "geometry": e["location"]["geometry"],
                          "properties": {"title": e["title"], "category": e["category"], "status": e["status"],
                                         "occurred_on": e["occurred_on"], "precision": e["location"]["precision"],
                                         "revision_id": e["revision_id"],
                                         "strategic_area_ids": e.get("strategic_context", {}).get("area_ids", [])}} for e in snapshot["incidents"]]}
