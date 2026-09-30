# Kontrakt publikacji dashboardu

Wersja `dashboard-v1`, uzupełnienie 29.09.2026. Schemat: `schemas/dashboard/report.schema.json`
(JSON Schema 2020-12). Eksporter: `src/osint_dashboard/dashboard/contract.py`.
Ten kontrakt nie zmienia metodologii punktacji. Aktualny silnik liczy **rtb-v0.2**.

## Granica danych

Zamrożone wydanie procesu RTB → weryfikacja manifestu → eksport z listy dozwolonych
pól → walidacja → atomowa publikacja → API odczytu → frontend.

Do przeglądarki nie trafiają surowe artykuły, cytaty dowodowe, odpowiedzi API,
pliki przeglądu, nazwy osób oceniających, ścieżki robocze, błędy ani sekrety.
Materiały źródłowe zachowujemy lokalnie. Oczyszczone adresy artykułów pozostają
w publikacji; usuwamy parametry śledzące i znane parametry poświadczeń.

Pierwsza wersja publikuje incydenty istniejącego procesu RTB. Osobne pomiary
GNSS, logistyki i lotnictwa wymagają własnych adapterów prezentacyjnych.
Nie kopiujemy ich do punktacji ani nie przedstawiamy jako podłączonych strumieni.

## Tożsamość i czas

- `report_id`: SHA-256 kanonicznej treści kontraktu z prefiksem `rpt_`.
  Obejmuje wszystkie pola poza samym identyfikatorem. Identyczny pakiet ma ten
  sam identyfikator; ponowienie publikacji nie tworzy kolejnego raportu.
- `mode`: `live` lub `fixture`; Supabase odrzuca `fixture` przed wysłaniem i w RPC.
- `report_type`: `daily` lub `weekly`. To etykieta wydania, nie zmiana punktacji:
  oba przedstawiają odczyt kroczącego okna silnika, nie średnią dobową/tygodniową.
- `as_of`: rzeczywisty czas odcięcia analizy, a nie czas załadowania strony.
- `window`: początek i koniec okna modelu oraz strefa prezentacji `Europe/Warsaw`.
- `provenance`: identyfikator przebiegu, faktyczna metodologia, skróty konfiguracji,
  źródeł, kodu, wejściowego snapshotu i eksportera. Umożliwia powiązanie z replay.
- `supersedes`: identyfikator wcześniejszego wydania, jeżeli to korekta tej samej
  daty odcięcia i rodzaju. Starego raportu nie usuwamy.
- `published_at`: nadawany przez bazę przy pierwszym zapisie, **poza** kontraktem
  haszowanej treści. API zwraca kopertę `{report, published_at}` albo `null`.

Najnowszy raport wybieramy według `as_of`, potem czasu publikacji i identyfikatora.
Późne przesłanie starego wydania nie zastępuje bieżącego. Nie wybieramy tylko
raportów z wynikiem: nowszy brak oceny jest istotnym stanem do pokazania.

## RTB, pewność i braki

`rtb.score` to liczba 1–100 albo `null`. `status=insufficient_data` wymaga `null`;
`status=available` wymaga liczby. Komponenty `hostile_activity` i `preparation`
zachowują rozdzielenie wkładów działań i przygotowań. Wynik ponad 60 oznacza
przegląd analityczny. Nie jest prawdopodobieństwem wojny.

`rtb.confidence.percent` pozostaje `null`, `method=not_calibrated`. Nie mamy
podstaw do nadania procentu pewności. Osobna `coverage` opisuje liczbę wymaganych
i gotowych źródeł oraz materiały oczekujące na ocenę; jej procent nie zastępuje
pewności i nie mierzy całego regionu.

`gaps` zawiera kontrolowane kody i krótkie polskie objaśnienia. `sources`
przekazuje czas ostatniego sprawdzenia i stan `current`, `stale`, `partial` lub
`unavailable`. Utrata źródła nie jest dowodem deeskalacji. Frontend pokazuje
datę analizy, opóźnienie odczytu i brak połączenia jako trzy odrębne informacje.

`rtb.trend` porównuje wcześniejszy kompletny odczyt tego samego rodzaju i trybu,
metodologii oraz skrótów konfiguracji, źródeł i kodu. Nieporównywalne wartości
dają `unavailable`, bez strzałki i procentowej delty. Wykres pozostawia przerwę.

## Incydenty, źródła i mapa

`incidents` ma jeden rekord na `id` incydentu z najnowszą rewizją znaną w danym
wydaniu. Powiązane artykuły są listą `sources` tego rekordu. Kolejna kopia
artykułu nie staje się kolejnym punktem na osi czasu.

Każdy wpis zachowuje polski tytuł i streszczenie, kategorię, status oceny,
atrybucję, typ autora przeglądu, aktualność oceny i wkład RTB. `published_at`
to najwcześniejszy znany czas publikacji powiązanego materiału; `occurred_on`
to odrębna data zdarzenia, a `recorded_at` — zapis w systemie. Brak daty
pozostaje `null`. Oś czasu grupuje publikacje; wpis bez daty jest w dzienniku.

`geojson` jest `FeatureCollection` z geometriami **Point** wyłącznie dla
współrzędnych potwierdzonych w wejściu. Walidator sprawdza zgodność punktów
z rekordami incydentów. Brak miejsca pozostaje widoczny w liczniku braków.

Zdarzenia o zasięgu krajowym nie dostają fikcyjnego punktu incydentu. Frontend
może wyświetlić flagę w stolicy z osobnego `web/assets/capitals.json`, z
wyraźnym opisem reprezentowanego obszaru. Taka kotwica UI nie trafia do eksportu
GeoJSON. Nieznany kraj pozostaje w dzienniku do uzupełnienia katalogu kotwic.

## Komentarz i wersjonowanie

`commentary.text` zawiera trzy zdania zatwierdzonego podsumowania lub `null`.
Niepusty tekst wymaga opcjonalnego obiektu `commentary.review`: skrótów
prywatnego rekordu przeglądu, snapshotu i tekstu, `reviewer_type=agent` oraz
`method=codex-editorial-v1`. Eksporter `dashboard-export-v2` sprawdza je
względem prywatnego pliku `commentary-review.json` objętego manifestem wydania.
Wydawca ponownie wymaga tego pliku przed zapisem do Supabase.

Sam status accepted i filtr językowy nie wystarczają. Cykl Codexa rozwiązuje
odnośniki do konkretnych, aktualnych dowodów i zapisuje osobny przegląd
znaczenia trzech zdań. To pochodzenie i ocena agenta, nie gwarancja prawdziwości
ani kontrola człowieka. Surowy kontekst i audyt nie są eksportowane.
Niepełny RTB lub brak podstaw do komentarza daje `text=null` bez obiektu review.
Starsze publikacje z `text=null` zachowują zgodność z kontraktem.

Zmiana schematu o niezgodnym znaczeniu wymaga nowej wersji kontraktu. Zmiana
treści raportu tworzy nowy identyfikator. Migracja bazy nie zmienia historii
lokalnych dowodów ani odtwarzania dawnych wydań.

## Rozszerzenie v0.3 — 29.09.2026

`score`, wkłady i delta dopuszczają liczby ułamkowe, bez zaokrąglania w eksporcie.
`rtb.regions` zawiera wyniki województw i wkłady direct_points/propagated_points;
`red_priority` oznacza bramkę priorytetu, odrębną od review_required.
`official_warnings` przekazuje tylko alert_key, authority, level, status,
effective_at, valid_until, area i instruction_pl. Aktywne i nieustalone
instrukcje są wyświetlane także przy niewyliczonym indeksie. Brak audytu
216 godzin historii to publiczna luka event_history_unverified.
Wcześniejsze wydania v0.2 pozostają poprawnymi pakietami bez tych rozszerzeń.
