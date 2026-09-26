# Geopolitical Brief — szablon interpretacji

Uzupełnia analityk po przeglądzie dowodów. Pola w nawiasach są miejscem na ustalenia, nie przykładowymi faktami. Nie zmieniaj ukończonego raportu w `snapshots/`; zapisz interpretację jako nowy plik w `data/briefs/` ze wskazaniem wydania.

## 1. Podsumowanie i scenariusze

- Wydanie danych: [run_id]. Stan wiedzy: [as_of]. Metodologia: [version i config_hash].
- RTB: [liczba ze snapshot.json albo brak odczytu i przyczyny]. Status progu przeglądu: [alert.status].
- Wkłady: [hostile_activity] oraz [preparation], po limitach, bez bazy. Przy niepełnym odczycie wyłącznie diagnostyka.
- Trend: [porównywalny odczyt odniesienia albo „brak podstaw do porównania”].
- Najważniejsze ustalenia: [do trzech, z odnośnikami do zdarzeń i dowodów].
- Pokrycie i luki: [źródła, opóźnienia, nieprzejrzane materiały, brak danych pomiarowych].

| Hipoteza / scenariusz na 14–42 dni | Dowody wspierające | Kontrargument / alternatywa | Co zwiększy lub osłabi ocenę | Pewność i ograniczenia |
|---|---|---|---|---|
| [Warunkowy rozwój sytuacji] | [Identyfikatory zdarzeń i dowodów] | [Inne wyjaśnienie] | [Obserwowalny sygnał rozstrzygający] | [Uzasadnienie słowne, bez niekalibrowanych procentów] |

Odwołanie doktrynalne: [document_id, autor, rok; strona PDF i SHA-256 albo URL i sekcja]. Parafraza: [teza]. Rola: [jak pomaga postawić hipotezę]. Granica zastosowania: [czego nie dowodzi]. Kilka opracowań cytujących tę samą tezę nie stanowi niezależnego potwierdzenia bieżącego zdarzenia.

## 2. Obserwacje i incydenty

| Data zdarzenia | Kraj / kategoria | Ustalenie i event_id / rewizja | Źródła URL | Status / atrybucja | Wkład lub wykluczenie |
|---|---|---|---|---|---|
| [Data albo nieustalona] | [Wartości z odczytu] | [Fakt, bez dopisywania intencji] | [Zapisane wersje] | [Osobne oceny] | [Z odczytu] |

Zaznacz korekty wcześniejszych ocen, informacje niepotwierdzone, zdarzenia na Ukrainie oraz działania obronne NATO jako odrębny kontekst, jeśli są istotne.

## 3. Dane przestrzenne

Plik: [ścieżka do incidents.geojson tego samego wydania]. Układ WGS84, kolejność długość/szerokość. Geometria nieustalona: `null`. Obszary strategiczne podawaj wyłącznie z uzasadnieniem i dowodem; nie dodają punktów. Archiwum i historia: SQLite.
