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

Dla v0.4 `rtb.score` to zawsze liczba 0–100, a `status` to available lub provisional. Zero oznacza brak naliczonych sygnałów; nie zastępuje awarii odczytu ani nie potwierdza bezpieczeństwa. Historyczne v0.2/v0.3 zachowują zakres 1–100 albo null ze statusem insufficient_data.

`rtb.confidence` v0.4 zawiera obliczony percent 0–100, metodę coverage-review-history-v1, calibrated=false, osiem domains i coverage_percent, review_percent, history_percent. Wzór jest w metodologii. Starsze wersje zachowują percent=null i method=not_calibrated. Osobne coverage z liczbą wymaganych źródeł nie jest już podstawą do prezentowania pełności obserwacji.

`gaps` opisuje quality_issues. Braki nie blokują całego indeksu. Oficjalne ostrzeżenia i ich status są oddzielne od liczby; nie wolno z niskiego RTB wyprowadzić odwołania instrukcji służb. Trend wymaga również równego confidence.comparison_key; przy poprzednim RTB=0 procentowa delta pozostaje null. Historia API zawiera confidence_key.

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

`commentary.text` zawiera 1–3 zdania zatwierdzonego podsumowania lub `null`.
Opis sprawdzonych wydarzeń nie wymaga oceny trendu ani skutków dla Polski;
takie oceny pojawiają się tylko przy osobnych podstawach.
Niepusty tekst wymaga opcjonalnego obiektu `commentary.review`: skrótów
prywatnego rekordu przeglądu, snapshotu i tekstu, `reviewer_type=agent` oraz
`method=codex-editorial-v1`. Eksporter `dashboard-export-v2` sprawdza je
względem prywatnego pliku `commentary-review.json` objętego manifestem wydania.
Wydawca ponownie wymaga tego pliku przed zapisem do Supabase.

Sam status accepted i filtr językowy nie wystarczają. Cykl Codexa rozwiązuje
odnośniki do konkretnych, aktualnych dowodów i zapisuje osobny przegląd
znaczenia każdego zdania. To pochodzenie i ocena agenta, nie gwarancja prawdziwości
ani kontrola człowieka. Surowy kontekst i audyt nie są eksportowane.
Historyczny brak RTB lub brak podstaw do komentarza daje `text=null` bez obiektu review.
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

## Rozwinięcie prezentacji — 03.10.2026

`dashboard-v1` pozostaje kompatybilny ze starszymi publikacjami. Eksporter
`dashboard-export-v5` dodaje opcjonalne `incidents[].presentation` w wersji
`signals-v1`: `topics`, `kind`, `scope`, `region_ids`, `episode_id`.
To opis do nawigacji; `category` i punktacja zachowują znaczenie.

Metadane pochodzą z przejrzanego `dashboard_context`, ocen regionalnych
albo jawnej, wspólnej taksonomii `config/signal-presentation.json`. Reguły
dla wyspecjalizowanych źródeł przypisują temat (np. CERT → Cyber), nie
wykonanie ataku, intencję czy sprawcę. Regiony wymagają dowodu lokalizacji.
Przegląd przyjmuje nieznany zasięg; zakres krajowy RSO nie jest przyjmowany
bez jawnych metadanych. Backend nie dodaje współrzędnych.

Komentarz może mieć `sections.situation`, `sections.impact` i
`sections.recommendation`. Prywatny kandydat wiąże je z indeksami zdań,
a audyt obejmuje również ten podział. `review.sections_sha256` zabezpiecza
dokładną treść pól. Każde zdanie jest przypisane raz; pozostaje limit 1–3.
Wpływ wymaga osobnego zaakceptowanego ustalenia, a rekomendacja aktualnej
instrukcji służb. Brak pól nie unieważnia historycznego komentarza.

Frontend scala wyłącznie publiczne raporty przez istniejące endpointy.
Stronicowanie historii ma stałą kotwicę `published_at`; raporty i rewizje
z przyszłości względem otwartego raportu są pomijane. Korekta z tego samego
czasu analizy zastępuje starszą wersję w roboczym zbiorze, nie w archiwum.
Identyfikator sygnału/epizodu jest liczony raz. Jawna korekta daty publikacji
w nowej rewizji obowiązuje w aktualnym widoku; nie odtwarzamy błędnej starej
daty. Przedruki są łączone w procesie analizy, nie przez podobieństwo tytułu.

Porównanie liczników wymaga raportu sięgającego początku obu okien,
ciągłości odczytów (przerwa maksymalnie 36 h), tej samej konfiguracji źródeł
i wersji eksportera, ukończonego przeglądu oraz pełnych odczytów źródeł.
To ostrożny warunek dostępności porównania, nie dowód pełnej obserwacji świata.
Częściowe dane zachowują liczby i etykietę „Brak danych do porównania”.
Okna: `[as_of−336h, as_of−168h)` i `[as_of−168h, as_of)`.
Filtry kalendarzowe używają Europe/Warsaw i daty raportu; bez daty to osobny
zbiór. Archiwum jest ładowane na żądanie, z limitem 800 metadanych raportów;
niepowodzenie zachowuje najnowsze dane i jawnie opisuje niepełną historię.

Regionalna pewność procentowa nie jest jeszcze obliczana. UI pokazuje
„Nieustalona dla regionu”; wynik regionalny czyta z silnika (również null),
a osobno podpisana pewność całego obszaru pozostaje globalna.
