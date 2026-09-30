# Obsługa lokalnego procesu

Zaakceptowana specyfikacja: `docs/methodology.md`, rtb-v0.3. Działające polecenia domyślnie wykonują rtb-v0.3; poprzednie reguły zachowano w `docs/archive/methodology-v0.2.md`. Rejestr źródeł do pobrania: `config/sources.json`. Kandydaci i biblioteka doktryny nie uruchamiają dodatkowych kolektorów.

Akceptacja z 25.09.2026 obejmuje procedury PAŻP/RCB/RSO i sanity check przed odczytem dobowym lub tygodniowym. Heurystyki v0.3 są zatwierdzoną specyfikacją w [metodologii](methodology.md#wygaszanie-regiony-i-korelacja); polecenia poniżej wykonują v0.3. Ręczne sprawdzenie nowego źródła nie oznacza działającego adaptera ani zmiany konfiguracji live.

Ten dokument dotyczy procesu RTB. Działająca osobno warstwa GNSS/logistyki używa `config/early-warning.json`, własnej bazy i polecenia `scripts/early_warning.py`. Jej uruchamianie, przegląd, kopie i metodologia: [instrukcja sygnałów wczesnych](early-warning-runbook.md). `scripts/backup.py` opisany poniżej nie obejmuje nowej bazy obserwacji.

## Zwykły przebieg

Przy pełnym cyklu Codexa najpierw wykonaj [odczyt kont X](x-sources.md):
`.venv/bin/python scripts/collect_x.py collect`. Pobranie API ma limity kosztów
i częstości; `status` sprawdza lokalny licznik bez sieci. Nie resetuj limitów
ani nie ponawiaj odczytu po błędzie.
Sam kolektor Python czyta ostatnie zapisane paczki i nie odświeża ich dat.
Brak aktualnego odczytu pozostaje jawnym brakiem źródła opcjonalnego.
OSW czyta teraz również ograniczone archiwum. Wybrane dokumenty Łotwy
służą wyjaśnieniu konkretnych spraw; nie są pełnym monitoringiem Bałtyku.

1. Uruchom `Zbierz dane.command` albo `.venv/bin/python scripts/collect_sources.py` w katalogu projektu.
2. Przejrzyj wskazany plik `data/runs/<id>/review_queue.json` według `agents/evidence-reviewer.md`. Domyślne kategorie pochodzą ze słów kluczowych i nie są ustaleniami.
3. Zapisz decyzje zgodne z `schemas/review.schema.json` w `data/reviews/`. Każde wykluczenie ma uzasadnienie. Każde zdarzenie ma cytaty z konkretnych zapisanych materiałów, status i osobną atrybucję.
4. Zastosuj pakiet: `.venv/bin/python scripts/review_incidents.py data/reviews/oceny.json`.
5. Przed końcowym odczytem wykonaj [kontrolę PAŻP, RCB i RSO](early-warning-runbook.md#kontrola-przed-odczytem) oraz [sanity check epizodów](early-warning-runbook.md#sanity-check-epizodow). Zapisz protokół i rzeczywiste braki rozszerzenia; w razie wykrytej pomyłki popraw ocenę nową rewizją przed obliczeniem.
6. Wygeneruj nowe wydanie: `.venv/bin/python scripts/run_pipeline.py --offline`, a interpretację z odnośnikiem do protokołu zapisz osobno.

Przebieg `run_pipeline.py` bez `--offline` pobiera źródła i publikuje stan. Może to być raport niepełny, jeśli nowe materiały nie mają ocen. Sam przegląd nie zmienia istniejących raportów; potrzebny jest nowy przebieg.

Główny cykl pobiera teraz PAŻP/AUP i ogólne RSO. Nie weryfikuje automatycznie aktywacji stref ani semantyki ostrzeżeń. Do pełnego odczytu v0.3 używaj `analysis_cycle.py` i przeglądu 216 godzin historii: [instrukcja wdrożenia](v0.3-implementation.md). Sam `run_pipeline.py` bez tego przeglądu zapisze wynik niepełny.

## Zasady przeglądu i korekt

`reviewer.type` ma wartość `agent` dla oceny AI albo `human` dla rzeczywistego przeglądu człowieka. Używamy niezmiennego `event_key` dla tego samego zdarzenia. Początkowo `previous_revision=0`; dla korekty trzeba odczytać aktualną rewizję i podać jej numer. Konflikt powoduje wycofanie całego pakietu.

Przy zmianie materiału źródłowego poprzedni kandydat nie może być ponownie zatwierdzony. Nową wersję przypisujemy do tego samego zdarzenia po sprawdzeniu treści i tworzymy rewizję. Cytaty odnoszą się do nowego `material_id`. Historia zachowuje poprzednie wersje, również gdy źródło później wróci do wcześniejszego brzmienia.

Wykluczenie kandydata zastępuje jego bieżące powiązania ze zdarzeniami. Ponowne przypisanie tworzy nową decyzję w historii. Jeśli jedna publikacja zawiera kilka zdarzeń, pakiet może przypisać tego samego kandydata do kilku różnych `event_key`; powtórne zastosowanie tego samego pakietu nie powiela ocen. Aby odwołać tylko jedno zdarzenie z takiej publikacji, popraw jego rewizję z uzasadnieniem, zamiast wykluczać cały materiał.

Wątpliwa, niepełna treść pozostaje do przeglądu. Nie wolno oznaczać jej jako „poza zakresem” wyłącznie w celu uzyskania liczbowego RTB. Nieprzeczytanego pełnego artykułu nie przedstawiamy jako zweryfikowanego na podstawie pustego skrótu RSS.

Od 29.09 kolektor OSW uzupełnia artykuły z RSS pełnym HTML lub tekstem PDF
oraz wraca do znanych nierozstrzygniętych publikacji spoza kanału. Uruchamia go
zwykłe pobranie lub `analysis_cycle.py prepare`; nie wymaga osobnego polecenia.
Raporty PDF potrzebują Popplera (`pdfinfo`, `pdftotext`). Brak narzędzia,
nieczytelny dokument, zmiana struktury strony lub przekroczenie limitu pozostawia
źródło niepełne. `pdf_text` nie oznacza odczytania wykresów i map; twierdzenia
oparte na grafice sprawdzaj w oryginalnym PDF. Szczegóły i limity: [źródła](sources.md).

Uzupełnienie treści tworzy nowego kandydata, także gdy wcześniejszy skrót był
wykluczony. Powiąż ponownie aktualne dowody z istniejącym zdarzeniem, zamiast
tworzyć drugi incydent. Pobranie starszego artykułu dzisiaj nie zmienia daty
zdarzenia ani historycznej wiedzy systemu.

### Przed odczytem dobowym i tygodniowym

Zamroź wspólny czas odcięcia po kontrolach. Sprawdź strefy ADHOC/R/D/NPZ w PAŻP, rozdziel plan AUP/UUP od potwierdzonej aktywacji i porównaj ze zwykłym użyciem przestrzeni. Sprawdź pełne treści RCB oraz obowiązujące komunikaty RSO, ich obszary, klasy L1/L2/L3, aktualizacje i odwołania. Zapisz URL, wersję/hash dowodu i rzeczywisty czas odczytu. Niedostępne lub niewdrożone źródło ma jawny status; nie wpisuj „brak aktywności”. Szczegółowa lista i robocze limity świeżości są w [procedurze kontroli](early-warning-runbook.md#kontrola-przed-odczytem).

Dobowa i tygodniowa publikacja to rytm odczytu tego samego stanu na `T`; w zaakceptowanej v0.3 wiek oblicza funkcja wygaszania. Nie dodawaj do siebie dziennych indeksów i nie odświeżaj wieku zdarzenia datą artykułu. RCB pozostaje źródłem wymaganym; PAŻP/RSO mają ograniczony zakres bieżący i są opcjonalne. W v0.3 brak istotnego pokrycia blokuje odpowiedni wynik lub bonus zgodnie z nowym kontraktem.

### Sanity check przed zatwierdzeniem ocen

Meldunek ukraiński i relacjonujący go artykuł o tym samym incydencie muszą wskazywać jeden `event_key`; przedruk nie dodaje niezależnego `origin_id`. Jeśli dowód jest rzeczywiście niezależny, uzupełnia potwierdzenie tego samego zdarzenia. Przy niepewności związku zachowaj stan nierozstrzygnięty. Weryfikuj również przejścia między próbkami, zmienione identyfikatory obiektów i odwołania, aby ponowne pobranie nie tworzyło drugiego incydentu.

RCB i jego dystrybucja w RSO tworzą jeden alert. PAŻP, GNSS i OSINT są dowodami różnych twierdzeń w epizodzie, nie trzema automatycznie punktowanymi atakami. Wspólny dostawca lub cytowany komunikat wyklucza deklarowanie niezależności bez dalszych dowodów. Procedura [sanity check](early-warning-runbook.md#sanity-check-epizodow) jest wspólna dla obu rytmów raportowania; obecny kod nie zastępuje tego przeglądu.

## Doktryna i interpretacja

Zarejestruj metadane i hash nowego PDF-u w `config/doctrine-sources.json`, następnie uruchom `.venv/bin/python scripts/doctrine.py index`. Polecenie `.venv/bin/python scripts/doctrine.py search 'kontrola refleksyjna'` zwróci strony do przeczytania. Pliki nieobecne, zmienione, nieprzeczytane skany i nowe niezarejestrowane PDF-y są sygnalizowane jawnie. Poppler jest wymagany do indeksacji doktryny i pobierania raportów PDF OSW, ale nie do obliczeń na zamrożonych tekstach ani replay. Szczegóły: `docs/doctrine.md`.

Interpretację scenariuszową zapisuj jako osobny plik `data/briefs/<data>-<run_id>.md`, z konkretnym snapshotem oraz cytowaniami dokumentów. Utwórz katalog przy pierwszym zapisie. Nie zmieniaj gotowego raportu w snapshots. Korzystaj z `docs/templates/analytical-brief.md`. Indeks tekstowy nie jest automatycznym generatorem ocen ani scenariuszy.

Zmiany `military_preparation` muszą mieć dowody odniesienia i kontroli rutynowych wyjaśnień. `strategic_context` wymaga dowodów lokalizacji. Po przekroczeniu 60 punktów przeprowadź przegląd dowodów, duplikatów, pokrycia i alternatywnych wyjaśnień; nie tłumacz progu na procent szans wojny. Przy niepełnych danych alert pozostaje nieoceniony.

## Przejście z v0.1 do v0.2

Nie edytuj ani nie kasuj dawnych wydań. Nowa konfiguracja tworzy nowe odczyty; nie łącz ich z v0.1 w jeden trend. Archiwalne reguły zapisano w `config/archive/scoring-v0.1.json` i `docs/archive/methodology-v0.1.md`. Oryginalną instrukcję po zmianach użytkownika zachowano w `docs/archive/OSINT-threat-barometer-user-2026-09-23.md`.

Replay sprawdza również kod i instrukcje agentów. Dla wydań v0.1 użyj osobnej kopii repozytorium na commicie `cc98b68` oraz skopiowanych danych, bez zmieniania bieżącego katalogu. Nie wyłączaj kontroli hashy, aby wymusić replay dawnych wydań nowym kodem. Zasady przywracania bazy i pozostałych plików opisano dalej.

## Akceptacja v0.3 i stan migracji

Metodologia v0.3 i dobór nowych źródeł zostały zaakceptowane 25.09.2026. Dokładne reguły v0.2 zachowano w `docs/archive/methodology-v0.2.md` oraz `config/archive/scoring-v0.2.json`; działające `config/scoring-v0.json` nadal wskazuje v0.2. Silnik v0.3 implementuje wygaszanie, graf PRG, grupowanie, bramki korelacji i kontrakty; przypadki matematyczne sprawdzają testy. Akceptacja źródła w rejestrze kandydatów nie podłącza adaptera.

Nie zmieniaj etykiet metodologii w zapisanych odczytach ani nie dopisuj wyników v0.3 do serii v0.2. Instrukcje w `agents/` używają kontraktu v0.3. Dane do dashboardu przechodzą przez wersjonowany eksport i Supabase; harmonogram i hosting są osobnymi etapami.

## Błędy i odzyskiwanie pracy

| Komunikat lub stan | Działanie |
|---|---|
| Źródło `error`/`partial` | Sprawdź błędy w raporcie; ponów później. Przy zmianie struktury strony popraw parser i jego test. Nie usuwaj bramki kompletności. |
| `source_window_incomplete` | Lista publikacji nie sięgnęła początku okna. Sprawdź limit, paginację albo ograniczoną historię kanału. |
| `source_check_stale` | Uruchom nowe pobranie. Offline nie odświeża kontroli źródeł. |
| `source_config_changed` | Pobierz ponownie po zmianie konfiguracji; stary odczyt nie potwierdza nowego źródła. |
| `unreviewed_candidates` | Przygotuj oceny wskazanych aktualnych wersji materiałów. |
| `unresolved_event` | Ustal datę lub popraw dowody; nie wpisuj daty publikacji jako zastępczej. |
| `stale_event_review` | Sprawdź nowszą wersję źródła i zapisz korektę oceny. |
| Drugi proces używa danych | Poczekaj na zakończenie pierwszego. Blokada systemowa znika po zakończeniu procesu; sam plik blokady może pozostać. |
| Przerwano eksport | Odczytuj poprzednie `data/latest.json`. Ponowny przebieg otrzyma nowy identyfikator. |

Nowe wydanie powstaje w katalogu tymczasowym. Wskaźnik `latest.json` zmienia się dopiero po zapisie spójnego kompletu. Nie edytuj ręcznie ukończonych katalogów `snapshots/`; korekta powinna tworzyć nowe wydanie. Przy twardym przerwaniu procesu może pozostać niewskazywany katalog tymczasowy lub zapis `running` — nie jest to aktualny raport.

## Kopia i odtworzenie

Wykonaj `.venv/bin/python scripts/backup.py`. Skrypt używa mechanizmu backup SQLite, uwzględnia WAL, sprawdza integralność i odmawia nadpisania istniejącej kopii. Obok zapisuje hash i liczniki rekordów.

Pełny pakiet odzyskiwania obejmuje kopię SQLite, `data/raw/`, `data/snapshots/`, `data/runs/`, `data/reviews/`, `data/fetch-state/` (blokady źródeł), `data/latest.json`, `data/.mode.json` oraz właściwą wersję repozytorium i `requirements.lock`. Sama kopia bazy nie zawiera surowych odpowiedzi ani wszystkich plików eksportu. Na etapie 2 nie ma automatycznych kopii na osobny dysk.

Odtwarzaj najpierw **do nowego katalogu**, nie nadpisuj aktywnej bazy:

1. Zatrzymaj proces korzystający z docelowego katalogu i skopiuj plik kopii jako `NOWY_KATALOG/database/osint.sqlite3`.
2. Dołącz zachowane `raw/`, `snapshots/`, `runs/`, `reviews/`, `latest.json` i `.mode.json`.
3. Uruchom `.venv/bin/python scripts/doctor.py --data-dir NOWY_KATALOG` i sprawdź integralność oraz liczniki.
4. Uruchom `.venv/bin/python scripts/replay_run.py ID_WYDANIA --data-dir NOWY_KATALOG`.

Replay sprawdza manifest wydania i identyczność ponownie obliczonego snapshotu; nie pobiera internetu. Zmiana kodu, schematów lub agentów wymaga przywrócenia odpowiadającej wersji Git. Przywrócenie starszej metodologii wykonuj w osobnym katalogu, zachowując obecne dane.

## Dane testowe

Testy uruchamiane przez `.venv/bin/python -m pytest` tworzą jawnie syntetyczne dane w katalogach tymczasowych. Obejmują również przypadek dający 15 punktów: baza 10 + jeden fikcyjny, prawidłowo udokumentowany incydent za 5. Ta wartość nie opisuje rzeczywistych wydarzeń.

Opcja `--fixture PLIK.json` domyślnie zapisuje do `data/demo`. Plik musi deklarować `synthetic: true`; oznaczenie fixture pozostaje w eksporcie i raporcie. Nie mieszamy tego katalogu z danymi live. Przykładowy format znajduje się w `tests/fixtures/`; daty przykładu są stałe i nie służą do symulowania aktualnej sytuacji.

## Co wymaga dalszej realizacji

Pełne teksty dodatkowych źródeł, geokoder z oceną niepewności, kontrola nadrabiania długich przerw, automatyczny przegląd modelem i limit kosztów, harmonogram, alarmy, porównywalne odczyty historyczne oraz dashboard. Płatny odczyt X jest ograniczony zaakceptowanym pilotażem; instalacja nie zamawia nowych usług ani nie wysyła powiadomień.
