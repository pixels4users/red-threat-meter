# OSINT Threat Dashboard

Lokalny pilotaż OSINT / Indicators & Warnings dla Polski i wschodniej flanki NATO. Gotowy jest proces danych: pobranie → archiwum → kolejka przeglądu → SQLite → raport i JSON/GeoJSON. Frontend **B — Chronologia** czyta publikacje z Supabase przez lokalne API. Pełny cykl na rzeczywistych danych sprawdzono ponownie 01.10.2026; szczegóły opisują [stan realizacji](docs/STATUS.md) i [integracja Supabase](supabase/README.md). Silnik od 30.09 wykonuje **RTB v0.4**: wynik 0–100 i osobna pewność danych, zgodnie z decyzją użytkownika. Zachowuje wygaszanie i reguły v0.3; [kontrakt v0.4](docs/v0.4-implementation.md).

Działa również **osobny pilotaż sygnałów wczesnych**: dzienne pomiary GPSJAM i publikacje logistyczne belzhd. Pierwsze pobranie obejmuje 30 dni GNSS i 10 publikacji. Warstwa zachowuje obserwacje bez ustalonego sprawcy, pokazuje jakość danych i umożliwia przegląd. Nie ma jeszcze skalibrowanego detektora anomalii.

Raport zawiera **polskie tytuły i streszczenia** publikacji, z zachowanym oryginałem w archiwum. Działa również porównanie GNSS na wspólnych komórkach i w obrębie tego samego zestawu dostawców. Porównanie opisuje zebraną historię; nie wyznacza prawdopodobieństwa zagrożenia.

Uruchomiono także **pilotaż jakości danych lotniczych ADSB.lol**: regionalne próbki, kontrola wieku pozycji i duplikatów oraz raport luk w obserwacjach. To osobne dane obserwacyjne; nie ustalają operatorów, intencji ani punktów RTB. [Obsługa danych lotniczych](docs/aviation-runbook.md).

Sprawdzono również **trzy półgodzinne wycinki historii lotniczej** z 22–24.09.2026: 78,1 MB pobranych treści, 540 przedziałów po 10 sekund. Historia mapy i bieżące API mają odmienne reguły próbkowania, dlatego pozostają osobnymi seriami. [Metoda i obsługa historii](docs/aviation-history.md), [wyniki](docs/STATUS.md).

## Jak korzystać

Właściwy dashboard jest [publicznie dostępny online](https://redthreatalert.pl).
Czyta publikacje z Supabase przez serwerowe API;
nie wymaga uruchomionego lokalnego serwera WWW. [Hosting i domena](docs/hosting-runbook.md).

Na tym Macu środowisko jest już przygotowane. Uruchom plik **`Zbierz dane.command`** z katalogu projektu. Pobierze dostępne publikacje i otworzy raport. Przy pierwszym uruchomieniu na innym komputerze potrzebny jest Python 3.11+ oraz dostęp do internetu do instalacji zależności.

Dla pomiarów GNSS i logistyki uruchom **`Zbierz sygnały wczesne.command`**. Otwiera osobny raport obserwacyjny i nie zmienia odczytu RTB. Przy pierwszym uruchomieniu zbiera 30 dni GNSS, potem odświeża trzy ostatnie doby oraz RSS. [Instrukcja sygnałów wczesnych](docs/early-warning-runbook.md).

Dla danych lotniczych uruchom **`Zbierz dane lotnicze.command`**. Pobiera jedną próbę (do czterech zapytań) i otwiera raport jakości po polsku. Pilotaż lotniczy uruchamia się ręcznie; nie należy do harmonogramu RTB. Kolektor lotniczy wymaga co najmniej minuty przerwy od zakończenia poprzedniej próby i respektuje blokadę po błędzie limitu API. Osobny audyt historii ma polecenia opisane poniżej.

Nowe lub zmienione publikacje otrzymują polski opis w przeglądzie agenta. Możesz zlecić: „Przygotuj brakujące polskie tytuły i streszczenia według translator.md, przejrzyj nowe sygnały i odśwież raport”. Sam kolektor nie wywołuje płatnego modelu: do czasu przeglądu pokazuje polski komunikat oczekiwania zamiast obcojęzycznego tytułu.

Nowy raport v0.4 zawiera **wynik 0–100 i osobną pewność danych**. Nieocenione materiały, niepełna historia i niedostępność źródeł obniżają pewność, bez blokowania indeksu. Zero oznacza brak naliczonych wkładów, nie potwierdzenie bezpieczeństwa. Awaria procesu pozostawia poprzedni raport z jego datą; wcześniejsze wydania v0.2/v0.3 mogą zachować wynik niewyliczony. RTB jest niewalidowanym indeksem; wynik ponad 60 oznacza potrzebę pilnego przeglądu, bez przypisywania mu prawdopodobieństwa wojny.

Nowe materiały przegląda Codex. Możesz zlecić: **„Wykonaj pełny dzienny cykl
według agents/analysis-cycle.md, opublikuj wynik do Supabase i sprawdź odczyt”**.
Gotowy proces obejmuje pobranie, ocenę, drugi przegląd dowodów, obliczenie RTB
i komentarz oparty na ustaleniach. Oceny AI są oznaczone jako wykonane przez
agenta. Nie potrzeba osobnego API modelu. Od 01.10 aktywny jest lokalny
harmonogram Codexa: codziennie o **09:00 czasu Warszawy**. Pierwszy zaplanowany
przebieg 02.10 pozostaje do sprawdzenia; Mac i Codex muszą być włączone.
[Obsługa silnika](docs/analysis-runbook.md), [harmonogram](docs/automation-runbook.md).

## Polecenia

Dashboard budujemy przez `npm ci` i `npm run build`. Po skonfigurowaniu
prywatnego dostępu do Supabase uruchamia go
`.venv/bin/python scripts/serve_dashboard.py`. Publikacja kolejnego odczytu:
`.venv/bin/python scripts/publish_dashboard.py cycle`.
Strona sprawdza nowe publikacje co 30 sekund; przycisk odświeżania nie uruchamia
analizy. Na Macu ten sam cykl pobrania i publikacji uruchamia
`Opublikuj raport.command`; ten skrót nie wykonuje przeglądu Codexa.
[Pełna instrukcja i izolowany test](docs/dashboard-runbook.md),
[kontrakt danych](docs/dashboard-data-contract.md).

W Terminalu otwartym w katalogu projektu:

```sh
sh scripts/setup.sh
.venv/bin/python scripts/doctor.py
.venv/bin/python scripts/run_pipeline.py
```

Pierwsze polecenie jest potrzebne przy instalacji lub aktualizacji środowiska. Kod uruchamiamy skryptami z tego repozytorium; projekt nie jest przygotowany jako samodzielny pakiet dystrybucyjny.

Do pracy nad ocenami:

```sh
.venv/bin/python scripts/collect_sources.py
.venv/bin/python scripts/review_incidents.py data/reviews/oceny.json
.venv/bin/python scripts/run_pipeline.py --offline
```

Ścieżkę rzeczywistej kolejki `review_queue.json` wypisuje kolektor. Plik `oceny.json` trzeba przygotować według schematu, nie istnieje automatycznie. Można również przekazać `--review data/reviews/oceny.json` do przebiegu offline. Tryb offline zachowuje prawdziwy czas ostatniego pobrania; po 8 godzinach kontrola wymaganego źródła wygasa.

Testy i odtwarzanie:

```sh
.venv/bin/python -m pytest
.venv/bin/python scripts/replay_run.py IDENTYFIKATOR_WYDANIA
.venv/bin/python scripts/backup.py
```

Identyfikator wydania znajduje się w `data/latest.json` i na końcu raportu. Replay sprawdza sumy kontrolne i ponownie oblicza zapisany odczyt bez internetu. Wymaga tej samej wersji kodu, schematów i instrukcji agentów. Kopia SQLite jest zapisywana w `data/backups/`; pełne odtworzenie wymaga także pozostałych danych opisanych w instrukcji operacyjnej.

Biblioteka kontekstu (osobna od incydentów):

```sh
.venv/bin/python scripts/doctrine.py index
.venv/bin/python scripts/doctrine.py search 'kontrola refleksyjna' --limit 5
```

Lokalne wyszukiwanie wskazuje strony PDF do przeczytania. Wymaga Popplera (`pdftotext`); nie nalicza punktów, nie używa płatnego API i nie indeksuje automatycznie podanych linków WWW. Pełne zasady są w katalogu doktryny.

## Gdzie są wyniki

Sygnały wczesne mają własny wskaźnik `data/early_warning/latest.json`, bazę `data/early_warning/database/observations.sqlite3` i wydania w `data/early_warning/snapshots/`. Ich obsługa:

```sh
.venv/bin/python scripts/early_warning.py collect
.venv/bin/python scripts/early_warning.py report
.venv/bin/python scripts/early_warning.py doctor
.venv/bin/python scripts/early_warning.py replay
```

Pierwsze polecenie pobiera dane, drugie odświeża raport offline, pozostałe sprawdzają integralność i odtwarzalność. Pełne uzupełnienie trzydziestodniowego okna: `collect --days 30`. Daty pozyskania nie zastępują dat zdarzeń; materiał opublikowany dawniej nie staje się bieżącym incydentem.

Dane lotnicze mają osobny katalog `data/aviation/`, bazę `database/aviation.sqlite3`, wskaźnik `latest.json` oraz wersjonowane raporty i agregaty `coverage.geojson` w `snapshots/`. Obsługa:

```sh
.venv/bin/python scripts/aviation.py collect
.venv/bin/python scripts/aviation.py report
.venv/bin/python scripts/aviation.py doctor
.venv/bin/python scripts/aviation.py replay
```

Te polecenia mają te same role: pobranie jednej próby, raport offline, kontrola integralności i odtworzenie.

Ograniczony audyt historii ma własne archiwum `data/aviation_history/`. Zapisane już dane można odtwarzać bez ponownego pobierania:

```sh
.venv/bin/python scripts/aviation_history.py plan
.venv/bin/python scripts/aviation_history.py replay
```

`plan` pokazuje stałe daty i budżet bez internetu; `replay` sprawdza integralność i zgodność raportu. Osobne `collect` pobiera do trzech półgodzinnych plików (maksymalnie 96 MB), a `report` analizuje zapisane pobranie. Konfiguracja pilotażu nie przesuwa dat do dzisiaj. Pełna instrukcja: [audyt historii](docs/aviation-history.md). Poniższa tabela dotyczy procesu RTB.

| Ścieżka | Zawartość |
|---|---|
| `data/latest.json` | Wskaźnik ostatniego kompletnego wydania |
| `data/snapshots/<id>/report.md` | Czytelny raport ze źródłami i przyczynami wykluczeń |
| `data/snapshots/<id>/snapshot.json` | Wewnętrzny snapshot procesu; wejście eksportera dashboardu |
| `data/snapshots/<id>/incidents.geojson` | Obserwacje i lokalizacje; geometria może być `null` |
| `data/runs/<id>/review_queue.json` | Materiały wymagające oceny wraz z wcześniejszymi decyzjami |
| `data/reviews/` | Pakiety ocen przygotowane przez analityka lub agenta |
| `data/database/osint.sqlite3` | Materiały, rewizje ocen i historia przebiegów |
| `data/raw/` | Zachowane odpowiedzi źródeł, identyfikowane hashem |
| `data/doctrine_rag/` | Dostarczone PDF-y kontekstu strategicznego i historycznego |
| `data/doctrine_index/` | Wersjonowane indeksy tekstu stron, poza bazą incydentów |
| `data/briefs/` | Interpretacje analityka wskazujące konkretne wydanie danych, tworzone w razie potrzeby |

Dane robocze i klucze są wyłączone z Git. Nie udostępniaj całego katalogu projektu serwerem WWW. Frontend korzysta z osobnego, ograniczonego eksportu `dashboard-v1`. Lokalny serwer udostępnia wyłącznie `dist/` i API publikacji; surowe źródła pozostają poza nim.

## Dokumentacja i dalszy zakres

- [Dashboard — obsługa](docs/dashboard-runbook.md) — publikacja, historia, korekty, uruchomienie i testy.
- [Dashboard online i domena](docs/hosting-runbook.md) — wdrożenie Sites i przygotowane rekordy home.pl.
- [Silnik Codexa](docs/analysis-runbook.md) — pełny cykl analizy, dowody, komentarz i publikacja, bez osobnego API modelu.
- [Codzienny harmonogram](docs/automation-runbook.md) — warunki pracy, limity, odzyskiwanie po awarii i kontrola pierwszego wykonania.
- [Kontrakt dashboardu](docs/dashboard-data-contract.md) — dozwolone pola, daty, braki, wersje i granica eksportu.
- [Design System](design.md) — zaakceptowany układ B, kolory, komponenty i zasady UI.
- [GitHub i Supabase](supabase/README.md) — repozytorium, migracja, uprawnienia i rzeczywisty stan połączenia. Samo połączenie usług nie uruchamia kolektorów ani strony.
- [Metodologia RTB](docs/methodology.md) — bieżące v0.4, zaakceptowane reguły, dowody, ograniczenia i jawny stan wdrożenia; [reguły silnika v0.2](docs/archive/methodology-v0.2.md).
- [Biblioteka doktryny](docs/doctrine.md) — katalog materiałów, dwa dodane artykuły, lokalne wyszukiwanie i zasady interpretacji.
- [Szablon briefu](docs/templates/analytical-brief.md) — scenariusze warunkowe na 14–42 dni, dowody i kontrargumenty.
- [Źródła i pokrycie](docs/sources.md) — działające integracje i luki.
- [Projekt sygnałów wczesnych](docs/early-warning-design.md) — zaakceptowana architektura i dalsze etapy.
- [Pilotaż GNSS i logistyki](docs/early-warning-runbook.md) — działające kolektory, kontrakty, ograniczenia miar, przegląd i obsługa.
- [Porównanie GNSS](docs/gnss-reference-methodology.md) — wspólne komórki, odniesienie, wrażliwość na próbę i dalsza walidacja.
- [Ocena dostępu do danych lotniczych](docs/aviation-access.md) — wyniki sprawdzenia źródeł, historia, koszty i wybór kolejnego pilotażu.
- [Pilotaż jakości ADSB.lol](docs/aviation-runbook.md) — uruchamianie, zakres zapytań, miary, ograniczenia i odtwarzanie.
- [Audyt historii lotniczej](docs/aviation-history.md) — ograniczone pobrania, walidacja binarnego formatu i porównanie z zachowanymi próbkami API.
- [Instrukcja operacyjna](docs/runbook.md) — oceny, korekty, awarie, odtwarzanie.
- [Stan realizacji](docs/STATUS.md) — wynik sprawdzeń i następny etap.
- [Audyt i zaakceptowany plan](docs/AUDYT_I_PLAN.md) — pierwotna ocena materiałów; opis stanu sprzed wdrożenia.

Dwa kierunki UI zostały przedstawione; użytkownik zaakceptował B — Chronologia
i wdrożenie przepływu danych. Zapis i odczyt rzeczywistego wydania przez Supabase
oraz automatyczne odświeżenie ekranu zostały sprawdzone. Hosting aplikacji
działa w Sites pod adresem [redthreatalert.pl](https://redthreatalert.pl),
z publicznym dostępem. Silnik ma ścieżkę przeglądu
Codexa, zatwierdzania komentarza i aktywny harmonogram. Działa v0.4 oraz import
zweryfikowanych pomiarów GNSS do kontekstu i pokrycia. Uzupełnienie historii
zdarzeń i kalibracja pozostają dalszymi pracami.
