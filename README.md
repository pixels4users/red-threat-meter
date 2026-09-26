# OSINT Threat Dashboard

Lokalny pilotaż OSINT / Indicators & Warnings dla Polski i wschodniej flanki NATO. Gotowy jest proces danych z etapów 0–2: pobranie → archiwum → kolejka przeglądu → SQLite → raport i JSON/GeoJSON. Zaakceptowana metodologia to **RTB v0.3**; działający silnik nadal liczy według v0.2, do wdrożenia nowych reguł i kontraktów. Nowe źródła pierwotne są wybrane do integracji bez pośrednictwa Strażnika. Projekt dashboardu oraz sposobu zasilania frontendu danymi jest osobnym, następnym krokiem.

Działa również **osobny pilotaż sygnałów wczesnych**: dzienne pomiary GPSJAM i publikacje logistyczne belzhd. Pierwsze pobranie obejmuje 30 dni GNSS i 10 publikacji. Warstwa zachowuje obserwacje bez ustalonego sprawcy, pokazuje jakość danych i umożliwia przegląd. Nie ma jeszcze skalibrowanego detektora anomalii.

Raport zawiera **polskie tytuły i streszczenia** publikacji, z zachowanym oryginałem w archiwum. Działa również porównanie GNSS na wspólnych komórkach i w obrębie tego samego zestawu dostawców. Porównanie opisuje zebraną historię; nie wyznacza prawdopodobieństwa zagrożenia.

Uruchomiono także **pilotaż jakości danych lotniczych ADSB.lol**: regionalne próbki, kontrola wieku pozycji i duplikatów oraz raport luk w obserwacjach. To osobne dane obserwacyjne; nie ustalają operatorów, intencji ani punktów RTB. [Obsługa danych lotniczych](docs/aviation-runbook.md).

Sprawdzono również **trzy półgodzinne wycinki historii lotniczej** z 22–24.09.2026: 78,1 MB pobranych treści, 540 przedziałów po 10 sekund. Historia mapy i bieżące API mają odmienne reguły próbkowania, dlatego pozostają osobnymi seriami. [Metoda i obsługa historii](docs/aviation-history.md), [wyniki](docs/STATUS.md).

## Jak korzystać

Na tym Macu środowisko jest już przygotowane. Uruchom plik **`Zbierz dane.command`** z katalogu projektu. Pobierze dostępne publikacje i otworzy raport. Przy pierwszym uruchomieniu na innym komputerze potrzebny jest Python 3.11+ oraz dostęp do internetu do instalacji zależności.

Dla pomiarów GNSS i logistyki uruchom **`Zbierz sygnały wczesne.command`**. Otwiera osobny raport obserwacyjny i nie zmienia odczytu RTB. Przy pierwszym uruchomieniu zbiera 30 dni GNSS, potem odświeża trzy ostatnie doby oraz RSS. [Instrukcja sygnałów wczesnych](docs/early-warning-runbook.md).

Dla danych lotniczych uruchom **`Zbierz dane lotnicze.command`**. Pobiera jedną próbę (do czterech zapytań) i otwiera raport jakości po polsku. Procesy uruchamia się ręcznie; nie są usługami działającymi w tle. Kolektor lotniczy wymaga co najmniej minuty przerwy od zakończenia poprzedniej próby i respektuje blokadę po błędzie limitu API. Osobny audyt historii ma polecenia opisane poniżej.

Nowe lub zmienione publikacje otrzymują polski opis w przeglądzie agenta. Możesz zlecić: „Przygotuj brakujące polskie tytuły i streszczenia według translator.md, przejrzyj nowe sygnały i odśwież raport”. Sam kolektor nie wywołuje płatnego modelu: do czasu przeglądu pokazuje polski komunikat oczekiwania zamiast obcojęzycznego tytułu.

Raport może pokazać **„Niewyliczony — dane lub przegląd niepełne”**. To prawidłowy stan, kiedy pojawiły się nieocenione wiadomości albo nie działa wymagane źródło. Samo pobranie tekstu nie potwierdza incydentu. RTB jest niewalidowanym indeksem; wynik ponad 60 oznacza potrzebę pilnego przeglądu, bez przypisywania mu prawdopodobieństwa wojny.

Nowe materiały wymagają przeglądu w Codex lub przez analityka. Gotowa instrukcja znajduje się w `agents/evidence-reviewer.md`. Możesz zlecić: „Przejrzyj najnowszą kolejkę OSINT zgodnie z instrukcją evidence-reviewer, zapisz oceny i odśwież raport”. Oceny AI są jawnie oznaczone jako wykonane przez agenta. W tle nie działa jeszcze autonomiczny model ani harmonogram.

## Polecenia

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
| `data/snapshots/<id>/snapshot.json` | Kontrakt danych dla przyszłego dashboardu |
| `data/snapshots/<id>/incidents.geojson` | Obserwacje i lokalizacje; geometria może być `null` |
| `data/runs/<id>/review_queue.json` | Materiały wymagające oceny wraz z wcześniejszymi decyzjami |
| `data/reviews/` | Pakiety ocen przygotowane przez analityka lub agenta |
| `data/database/osint.sqlite3` | Materiały, rewizje ocen i historia przebiegów |
| `data/raw/` | Zachowane odpowiedzi źródeł, identyfikowane hashem |
| `data/doctrine_rag/` | Dostarczone PDF-y kontekstu strategicznego i historycznego |
| `data/doctrine_index/` | Wersjonowane indeksy tekstu stron, poza bazą incydentów |
| `data/briefs/` | Interpretacje analityka wskazujące konkretne wydanie danych, tworzone w razie potrzeby |

Dane robocze i klucze są wyłączone z Git. Nie udostępniaj całego katalogu projektu serwerem WWW. Frontend będzie korzystał z osobnego, ograniczonego eksportu, a nie bezpośrednio z bazy i surowych treści.

## Dokumentacja i dalszy zakres

- [GitHub i Supabase](supabase/README.md) — repozytorium, wskazany projekt, konfiguracja gałęzi i zakres przyszłej integracji. Samo połączenie usług nie wdraża kolektorów ani strony.
- [Metodologia RTB v0.3](docs/methodology.md) — zaakceptowane reguły, dowody, ograniczenia i jawny stan wdrożenia; [reguły silnika v0.2](docs/archive/methodology-v0.2.md).
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

Następny krok to zaprojektowanie dashboardu i sposobu zasilania frontendu danymi; nie rozpoczynamy go w ramach akceptacji metodologii. Przed implementacją przedstawimy dwa kierunki wizualne dla mapy, rejestru zdarzeń i historii odczytów. Rozwój danych odniesienia i niezależna weryfikacja źródeł mogą przebiegać obok prac nad interfejsem; strona pokaże osobno rodziny danych, daty i braki. Automatyzacja oraz walidacja progów pozostają dalszymi etapami; wcześniejsze osobiste cele projektu mają wyłącznie status archiwalny.
