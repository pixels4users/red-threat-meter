# Obserwacje wczesne — uruchomienie i metodologia pilotażu

Stan: 23.09.2026. Działa lokalny moduł z konfiguracją `early-warning-1`: dwa kolektory, osobna baza, historia wersji i pobrań, raport jakości, polskie tytuły i streszczenia, kolejki ocen i tłumaczeń oraz odtwarzanie offline. Kontrakt wyniku to `ew-snapshot-2`, baza ma wersję 2, a opisowe porównanie GNSS — `gnss-comparison-1`. Uzupełnia RTB v0.2. Detektor alarmowy i walidacja przewidywania pozostają kolejnym etapem.

Aktualizacja dokumentacji 25.09.2026: zaakceptowano kontrolę PAŻP/RCB/RSO przed odczytem dobowym i tygodniowym oraz procedurę łączenia dowodów jako część metodologii v0.3. Poniższe polecenia nadal obsługują istniejący pilotaż; nie pobierają nowych rodzin i nie wykonują mnożników RTB. Główny `analysis_cycle.py` od 29.09 pobiera PAŻP/AUP i RSO oraz wykonuje v0.3 po przeglądzie.

Aktualizacja 30.09.2026: domyślny RTB używa v0.4. `gpsjam_reviewed` importuje zweryfikowany pomiar dobowy do głównego przeglądu, bez dodatkowego pobrania. Dopiero akceptacja daje wpis kontekstowy i częściowe pokrycie confidence; sam pomiar nie nalicza punktów. [Instrukcja integracji](gnss-review-integration.md).

## Uruchomienie

Na tym Macu uruchom **`Zbierz sygnały wczesne.command`**. Przy pierwszym przebiegu zbiera 30 dni GNSS, później odświeża trzy ostatnie dni; w obu przypadkach czyta aktualny RSS belzhd. Otwiera raport w domyślnej aplikacji macOS. Dwukliku w Finderze nie testowano; sprawdzono polecenia i składnię skryptu.

W terminalu, z katalogu projektu:

```sh
.venv/bin/python scripts/early_warning.py collect --days 30
.venv/bin/python scripts/early_warning.py collect
.venv/bin/python scripts/early_warning.py report
.venv/bin/python scripts/early_warning.py doctor
.venv/bin/python scripts/early_warning.py replay
```

Pierwsze polecenie inicjalizuje lub uzupełnia historię; drugie jest zwykłym odświeżeniem. Zakres pobrania jest ograniczony do 1–90 dni. Raport pokazuje okno określone w `config/early-warning.json` (domyślnie 30 dni), niezależnie od zakresu ostatniego pobrania. Po dłuższej przerwie wykonaj ponownie `collect --days 30`; zwykłe trzydniowe odświeżenie nie uzupełni starszych luk. Rozszerzenie raportu do 90 dni wymaga też zmiany `history_days`.

`report` korzysta wyłącznie z archiwum i nie odświeża dat kontroli. `replay` odtwarza ostatnie wydanie; można podać wcześniejszy identyfikator. Globalne opcje poprzedzają polecenie: `scripts/early_warning.py --data-dir KATALOG replay ID`. Źródła kontrolowane ponad 36 godzin temu są oznaczone jako nieaktualne. Jest to roboczy limit świeżości procesu, a nie próg zagrożenia. Nie działa harmonogram ani usługa AI.

Nowa zależność `h3==4.5.0` jest przypięta w `requirements.lock`. Instalacja/aktualizacja: `sh scripts/setup.sh`. H3 tłumaczy identyfikatory komórek na prawdziwe wielokąty; nie geokoduje opisów artykułów. [Dokumentacja H3](https://uber.github.io/h3-py/api_quick.html).

## Dane i wersje

| Lokalna ścieżka | Znaczenie |
|---|---|
| `data/early_warning/database/observations.sqlite3` | Osobne tabele obserwacji, pobrań, kontroli źródeł, ocen, tłumaczeń i wydań |
| `data/early_warning/raw/<source>/<sha256>.bin` | Dokładne odpowiedzi HTTP, bez nadpisywania |
| `data/early_warning/latest.json` | Wskaźnik ostatniego spójnego wydania |
| `data/early_warning/snapshots/<id>/report.md` | Raport po polsku, stan źródeł, pokrycie i kolejka |
| `…/snapshot.json` | Seria dobowa, metadane publikacji i stany ocen; bez pełnych artykułów |
| `…/observations.geojson` | Najnowsza siatka GNSS i publikacje bez zgadywanych współrzędnych |
| `…/review_queue.json` | Aktualne wersje do oceny, pełne teksty lokalne i wcześniejsze decyzje |
| `…/translation_queue.json` | Oryginały, hashe tekstów i wcześniejsze tłumaczenia konkretnych wersji |
| `…/replay-input.json`, `…/manifest.json` | Zamrożone wejścia i sumy kontrolne wydania |
| `data/early_warning/reviews/` | Pakiety ocen analitycznych |
| `data/early_warning/translations/` | Pakiety polskich tytułów i streszczeń |

Kontrakty znajdują się w `schemas/early-warning/`. Jeden rekord GNSS opisuje jedną dobę i siatkę regionu; publikacja jest osobnym typem rekordu. Zmiana treści, danych lub istotnej konfiguracji tworzy nową wersję. Ponowne pobranie identycznej obserwacji dopisuje odczyt; nie tworzy duplikatu. Zmieniona otoczka RSS lub manifestu bez zmiany obserwacji jest nowym odczytem surowych danych. Powrót wydawcy do starszej treści wybiera ostatnio pobraną wersję, a nie ostatnio utworzoną wersję.

Tabele audytu blokują UPDATE/DELETE. Import ocen jest atomowy, wymaga numeru poprzedniej rewizji i wskazania aktualnej wersji. Wskaźnik `latest.json` zmienia się po zapisaniu kompletnego wydania. Awaria jednego źródła pozostawia dane drugiego widoczne i pokazuje błąd; nie wymazuje wcześniejszej historii.

Pierwsze dwa wydania z 23.09 (12:12 i 12:15 UTC) odpowiadają kodowi `a3848e1`, wydanie z 12:24 UTC — `6a6c7d8`. Tłumaczenia i porównanie GNSS zmieniają hash oraz manifest nowej warstwy. Replay dawnych wydań wykonuj w osobnej kopii kodu na właściwym commicie, bez pomijania kontroli integralności. Dla roboczego wydania z 13:14 UTC zachowano dokładny kod w `data/early_warning/backups/code-ew-2026-09-23T131458Z-80ddeb12/` i sprawdzono identyczny replay. Zatwierdzony wynik wskazuje `latest.json` i `docs/STATUS.md`. Hash dotychczasowego RTB v0.2 pozostaje zgodny.

Baza w wersji 1 przechodzi automatycznie do wersji 2: dopisywana jest tabela tłumaczeń i blokady zmiany/usuwania wpisów. Obserwacje, odczyty i oceny pozostają nienaruszone. Przed pierwszą migracją rzeczywistej bazy zapisano kopię SQLite w `data/early_warning/backups/before-translations-v2-20260923T131458Z.sqlite3`.

## Znaczenie czasu

- `observed_start/end`: dla GNSS granice zakończonej doby UTC. Dla publikacji pozostają `null`, dopóki osobna analiza nie ustali zdarzenia. Ten etap nie importuje jeszcze takiej strukturyzacji czasu z artykułów.
- `published_at`: czas z RSS z jawną strefą. Niepoprawna, pozbawiona strefy lub przyszła data daje `null` i stan częściowy. Dla dziennych CSV jest nieznana.
- `first_available_at`: w obu obecnych adapterach `null`. Data publikacji ani nagłówek serwera nie dowodzą momentu, od którego dany materiał faktycznie był dostępny.
- `first_seen_at` i pierwotne `fetched_at`: pierwsze pobranie tej wersji przez działający kolektor. Tabela `fetches` przechowuje wszystkie kolejne czasy i odnośniki do surowych odpowiedzi. Raport osobno pokazuje `last_fetched_at`.

Przykład: raport wydawcy o roku 2025 opublikowany w lipcu 2026, pobrany we wrześniu 2026, nie jest wrześniowym transportem ani dowodem, że system znał go w lipcu. Odtwarzanie stanu wiedzy nie korzysta z późniejszych pobrań ani ocen. Pierwszy pilotaż buduje historię pomiarów retrospektywnie, nie historię sprawdzonych prognoz.

## GPSJAM — działający dostęp i miary

Ścieżkę danych sprawdzono w publicznym kodzie mapy: `/_app/immutable/nodes/3.DCWEDE6g.js` i `/_app/immutable/chunks/CQxTLQls.js` (odczyt 23.09.2026). Kolektor czyta [manifest dzienny](https://gpsjam.org/data/manifest.csv) z datą, flagą `suspect` i dostawcą. Następnie czyta CSV `data/<dzień>-h3_4.csv` dla `adsbexchange` albo `data/<provider>/<dzień>-h3_4.csv` dla `merged` / `airplaneslive`. To pliki publicznej mapy, a nie API z gwarancją stabilności. Nie stosujemy cichego zastąpienia jednego dostawcy innym po błędzie.

W pobranym oknie 24.08–22.09.2026 pierwsze trzy dni mają dostawcę `adsbexchange`, pozostałe 27 `merged`. Zmiana przypada na **27.08.2026** według manifestu. Grupy pochodzenia zapisujemy osobno dla każdego dnia. Gdy źródło oznacza dzień jako `suspect`, raport pokazuje tę flagę i pomija dzień w roboczym zestawie odniesienia. Brak flagi nie jest dowodem kompletności odbioru.

Obszar roboczy: bbox `[14,49,29,60]` (zachód, południe, wschód, północ), 771 komórek H3 poziomu 4, wybieranych według środka komórki. To prostokąt badawczy obejmujący m.in. Polskę i Bałtyk, a nie dokładne granice państw. Graniczne komórki mogą wychodzić poza prostokąt. Publikacje logistyczne nie są filtrowane geograficznie przez ten prostokąt.

Zachowujemy liczby `good` i `bad`, ich sumę i wzór źródła `100 * (bad - 1) / (good + bad)`. Odejmowanie jednego samolotu jest korektą autora przeciw małym próbom. Wartość może być ujemna przy `bad=0`; zapisujemy ją bez cichej korekty. Nie oznacza ujemnego fizycznego poziomu zakłóceń. Suma próbek wielu komórek nie jest liczbą unikalnych lotów. [FAQ GPSJAM](https://gpsjam.org/faq), [pochodzenie danych](https://gpsjam.org/about).

Robocze minimum sumy `good+bad=5` służy tylko opisowi jakości. Nie jest skalibrowanym progiem detekcji. Udział komórek z wartością ≥10% obliczamy wśród komórek spełniających to minimum. Granicę ≥10% stosuje publiczny kod kolorowania mapy; FAQ opisuje czerwony kolor jako >10%. Nie interpretujemy kolorów jako kategorii RTB. Nieobserwowane komórki i próbki poniżej minimum są jawne; w GeoJSON brak pomiaru ma wartość `null`.

`gnss.comparison` porównuje oczekiwaną ostatnią dobę z wcześniejszymi dniami. Zmiana dostawcy, pochodzenia lub konfiguracji kończy serię odniesienia; nie łączymy rozdzielonych epok po powrocie dawnego dostawcy. Dni oznaczone przez wydawcę jako podejrzane są pomijane, braki pozostają jawne, a bieżący dzień nie wchodzi do mediany. W każdym wariancie wszystkie dni używają tych samych komórek. Działają warianty minimum próby 1, 5, 10 i 20, mediana, kwartyle oraz różnica w punktach procentowych.

Diagnostyka `prior_same_provider_days` i `common_eligible_cells` używa tej samej serii; dla minimum próby innego niż cztery badane warianty liczba wspólnych komórek jest `null`. Brak oczekiwanej doby lub jej flaga jakości blokuje bieżące porównanie. To opis zebranej historii, bez normalnego poziomu odniesienia, kalibracji, sezonowości, kontroli ćwiczeń i walidacji ostrzeżeń. Detektor ma `version=null`. [Dokładna metoda i przykład](gnss-reference-methodology.md).

## belzhd — publikacje, nie spis transportów

Kolektor używa [głównego RSS wydawcy](https://belzhd.info/feed/) odnalezionego w HTML strony. W rzeczywistym pobraniu kanał zawierał 10 publikacji od 2.07 do 16.09.2026, w tym cztery oznaczone rubryką przewozów wojskowych. Zachowujemy całe `content:encoded` po oczyszczeniu HTML, tytuł, kategorie i datę; braku pełnej treści nie ukrywamy, tylko oznaczamy `rss_summary` i stan częściowy.

Kanał RSS rubryki wojskowej zwrócił 403. Nie obchodzono tej blokady: główny RSS jest osobno publikowanym, działającym punktem dostępu i już zawiera materiały tej rubryki. Nie użyto Telegrama. Witryna i kanał mają jedną grupę pochodzenia `publisher:belzhd`. Nie wyprowadzamy liczby transportów z liczby postów, nie pobieramy obrazów załączników i nie uznajemy tekstowego opisu dokumentu za niezależną weryfikację jego autentyczności.

Stan `ok` mówi o pobraniu i parsowaniu aktualnego kanału, nie o prawdziwości doniesień ani kompletności aktywności kolei. Najstarszy wpis pozwala ocenić zasięg listy publikacji; `feed_reaches_window_start` nie dowodzi pełnej historii wydarzeń. Strukturalny import liczby wagonów, dat zdarzeń, lokalizacji i wieloźródłowych potwierdzeń jest dalszą pracą.

## Przegląd

Instrukcja: `agents/early-warning/reviewer.md`. Przykład zlecenia w Codex: „Przejrzyj bieżącą kolejkę sygnałów wczesnych według tej instrukcji, zachowaj niepewność i zapisz oceny agenta”. Następnie:

```sh
.venv/bin/python scripts/early_warning.py review data/early_warning/reviews/oceny.json
```

Plik przygotowuje analityk lub agent; nie powstaje z wywołania modelu w tle. Cytat musi występować w zapisanej wersji artykułu, a dowód liczbowy wskazuje konkretną komórkę, pole i zgodną wartość. Zmieniona publikacja wymaga nowej oceny. Pilny przegląd może mieć nieznaną atrybucję. Żaden status nie nalicza punktów RTB. `reviewed=true` oznacza wykonanie opisanej oceny, nie niezależne potwierdzenie wszystkich twierdzeń materiału.

<a id="kontrola-przed-odczytem"></a>

## Kontrola przed odczytem dobowym i tygodniowym — metodologia v0.3

Przed wyliczeniem i opisaniem nowego indeksu analityk wykonuje poniższą kontrolę. Dopóki adaptery i nowy kontrakt nie powstaną, jest to ręczny protokół uzupełniający raport v0.2, a nie deklaracja pełnej automatycznej kontroli. Zapisz go w nowym pliku `data/briefs/<czas-UTC>-preflight.md`, z odnośnikami do wersji dowodów. Nie edytuj ukończonego wydania.

1. **Ustal zakres i czas odcięcia.** Wybierz raport dobowy albo tygodniowy, ten sam zakres regionów i wersję reguł. Po zakończeniu kontroli zamroź `T`; dla odtworzenia historycznego używaj wyłącznie danych i ocen znanych do dawnego `T`. Odczyt wykonany teraz nie wypełnia wstecz luki dostępności.
2. **Sprawdź PAŻP u źródła.** Odczytaj [airspace.pansa.pl](https://airspace.pansa.pl/), obowiązujący AUP i jego UUP. Dla ADHOC/R/D/NPZ zapisz identyfikator, rewizję, planowany czas UTC, geometrię, wysokości, rzeczywisty status i czas zmiany, jeśli dostępny. Oddziel rezerwację od aktywacji, sprawdź odwołanie/dezaktywację i rutynowe ćwiczenia. Zachowaj treść/wersję, URL, datę odczytu i hash; nie wyprowadzaj statusu tylko z koloru mapy. Brak historii lub niejasny status oznacza `unknown`, bez bonusu PAŻP.
3. **Sprawdź RCB i RSO.** Przeczytaj pełną, aktualną treść [komunikatów RCB](https://www.gov.pl/web/rcb/komunikaty) oraz [obowiązujących komunikatów RSO](https://komunikaty.tvp.pl/komunikaty/wszystkie/wszystkie), z aktualizacjami i odwołaniami. Przypisz [L1/L2/L3](sources.md#rso-rcb-klasy), obszar adresatów, czas obowiązywania, nadawcę i identyfikator ostrzeżenia. Ćwiczenie ma osobny typ. Ten sam alert w obu systemach to jeden stan z kilkoma sposobami dystrybucji. Nie doliczaj automatycznie reakcji obronnej RP jako przygotowań RU/BY.
4. **Sprawdź dostępność i rozdzielczość czasu.** Zapisz status każdej rodziny: `ok`, `partial`, `unavailable`, `stale` lub `not_integrated`, rzeczywisty `checked_at` i zakres danych. Proponowany limit kontroli PAŻP i RCB/RSO dla korelacji taktycznej wynosi 5 minut względem `T`; to wymóg do zmierzenia, nie obecna gwarancja. Błąd odczytu nie oznacza braku aktywnych stref lub alertów. Najnowsza doba GPSJAM zachowuje rzeczywiste granice doby, jakość i [ograniczenia odniesienia](gnss-reference-methodology.md); nie przypisuj jej do 30-minutowego okna.
5. **Przeprowadź sanity check epizodów i pochodzenia** według procedury poniżej, włączając kanały UA i media bałtyckie. Przedziały czasu, regiony i negacje sprawdzaj w pełnej treści; polskie streszczenie nie zastępuje oryginalnego dowodu.
6. **Sprawdź przesłanki obliczenia.** Przed wyliczeniem v0.3 udokumentuj profil czasu, wagi, skład epizodów, źródła korelacji, najkrótsze drogi propagacji i bramkę czerwonego. Brak wymaganego pokrycia blokuje odpowiedni wynik, zamiast dawać zero. Adapter PAŻP obejmuje plan AUP, RSO bieżącą listę ogólną; nie dowodzą 216 godzin historii ani aktywacji. W głównym cyklu używaj `assessment_v03` i jawnego przeglądu historii. Pilotaż pozostaje bez punktacji.
7. **Dołącz protokół do interpretacji nowego wydania.** Powiąż go z identyfikatorem raportu i listą nierozstrzygniętych kwestii. Raport dobowy oraz tygodniowy wylicza stan na `T`, nie sumę wcześniejszych indeksów. Oficjalne zalecenia i odwołania prezentuj osobno od wygasającej wagi; sam spadek punktów nie odwołuje ostrzeżenia.

Minimalny protokół zawiera: wersję metody i źródeł, `T`, status i czas kontroli każdej rodziny, referencje/hash dowodów, stan stref i alertów, `event_key`/`episode_key`/`alert_key`, grupy pochodzenia, decyzje o duplikatach, brakujące dane i autora przeglądu. Kontrola wykonana przez agenta pozostaje oceną agenta.

<a id="sanity-check-epizodow"></a>

## Sanity check — jeden incydent, wiele doniesień

1. **Zacznij od materiału pierwotnego.** Zachowaj ID wpisu/raportu, wersję, cytat lub pomiar, jego czas, obszar i link do źródła cytowanego. Etykieta „radar ukraiński” w portalu nie dowodzi dostępu do radaru. Przy odrębnym, rzeczywiście udostępnionym pomiarze zachowaj identyfikator pomiaru; przy meldunku kanału UA zapisz typ `publication`.
2. **Rozwiąż tożsamość zdarzenia przed punktacją.** Porównaj przedziały czasu z niepewnością, lokalizację/obszar, klasę obiektu, sekwencję aktualizacji i odwołania. Wspólny oryginalny meldunek jest mocnym wskazaniem duplikatu. Sama bliskość czasu i miejscowości jest tylko kandydatem do połączenia. Przy niepewności liczby obiektów pozostaw grupę nierozstrzygniętą, bez mnożenia punktów lub wymyślania jednego pewnego toru.
3. **Przypisz stabilne klucze i pochodzenie.** Meldunek UA, artykuł powołujący się na niego i przedruk mają ten sam `event_key` i jedno pierwotne `origin_id`. Rzeczywiście niezależny pomiar może podnieść status potwierdzenia tego samego zdarzenia, ale nie tworzy kolejnego wkładu. Zmiana numeru śladu, języka albo koszyka czasowego nie tworzy nowego incydentu. Deduplikacja przechodzi przez granice próbek i dni.
4. **Oddziel synergię od powielania.** PAŻP, GNSS i doniesienie mogą wskazywać ten sam `episode_key`, zachowując odrębne rodzaje dowodów. Sprawdź trzy niezależne grupy pochodzenia, wspólny obszar i rozdzielczość czasu. Trzy teksty o jednym ostrzeżeniu nie są triadą. Wspólne dane ADS-B/GNSS oraz RCB rozpowszechnione przez RSO nie dają niezależności z samej różnicy nazw usług.
5. **Sprawdź falę i rewizje.** Minimum trzech składowych oznacza rozróżnione fizyczne obiekty/zdarzenia, nie posty. Każda składowa należy do jednej grupy w odczycie; punktowana jest grupa albo jej składowe, nigdy oba warianty. Przedruk nie odświeża czasu. Zakończenie alertu wygasza powiązane ostrzeżenie, lecz nie usuwa innego, nadal trwającego zdarzenia.
6. **Zachowaj decyzję audytową.** Zapisz połączenie albo odmowę połączenia wraz z uzasadnieniem, referencjami i rewizją. Porównaj liczbę publikacji, unikalnych epizodów i niezależnych grup pochodzenia przed obliczeniem. Obecny `event_key` i `campaign_id` pomagają w ręcznym przeglądzie, ale automatyczne grupowanie wieloźródłowe pozostaje do wdrożenia.

Przykład kontrolny: jeden meldunek ZSU o obiekcie, jego przekazanie przez kanał społecznościowy i dwa artykuły cytujące meldunek dają **jeden epizod i jedną grupę pochodzenia**. Wynik nie rośnie przy ponownym pobraniu ani po przejściu do następnej próbki. Osobny dowód PAŻP lub GNSS wymaga pełnego sprawdzenia warunków [metodologii v0.3](methodology.md#wygaszanie-regiony-i-korelacja).

## Polski język raportu

Instrukcja `agents/early-warning/translator.md` dotyczy wszystkich treści publikacji prezentowanych w raporcie: całego tytułu i zwięzłego streszczenia po polsku. Pełne teksty i rzeczywiste cytaty pozostają w oryginale w archiwum. Długie tabele nie są automatycznie tłumaczone ani weryfikowane przez przygotowanie streszczenia.

Agent czyta `translation_queue.json`, pomija niezmienione opisy i przygotowuje pakiet według `schemas/early-warning/translation.schema.json`. Każdy opis wskazuje wersję obserwacji, oryginalny tytuł, hash tekstu, cytaty źródłowe, zakres niepewności oraz rzeczywistego autora tłumaczenia. Import:

```sh
.venv/bin/python scripts/early_warning.py translate data/early_warning/translations/polskie-opisy.json
```

Polecenie importuje gotowy pakiet i zapisuje raport offline. Nie generuje tłumaczenia samoistnie. Błędny cytat, hash, wersja lub numer rewizji odrzucają cały pakiet. Korekta tworzy kolejną rewizję, nie zmienia źródła. Nowa treść wymaga własnego opisu. Nieprzetłumaczone pozycje mają polski komunikat oczekiwania i zwiększają licznik `pending_translations`.

Hash tekstu w kolejce jest liczony funkcją projektu `digest(text)` (SHA-256 kanonicznego JSON stringa), a nie bezpośrednio z bajtów tekstu. Należy przepisać wartość z kolejki. Kontrola cyrylicy chroni przed pozostawieniem oryginalnego tytułu w polu polskim; nie dowodzi poprawności językowej ani wierności tłumaczenia. To wymaga przeglądu semantycznego przez tłumaczącego.

## Kopie i granice wdrożenia

Dotychczasowe `scripts/backup.py` kopiuje bazę RTB, nie bazę tej warstwy. Przy zatrzymanych kolektorach i zamkniętych połączeniach wykonaj kopię całego `data/early_warning/` razem z wersją repozytorium i `requirements.lock`. Nie kopiuj samego pliku SQLite podczas aktywnego zapisu WAL. Odtwarzaj do nowego katalogu, potem wykonaj `--data-dir NOWY_KATALOG doctor` i `--data-dir NOWY_KATALOG replay ID`. Nie ma jeszcze automatycznej kopii na drugi nośnik.

Surowe dane, pełne teksty i materiały przeglądu są wyłączone z Git i nie trafiają do hostingu. Nie znaleziono w sprawdzonych stronach jawnej licencji zbiorczej na redystrybucję obu zbiorów; odczyt publicznych plików w lokalnym pilotażu nie ustala takich uprawnień. GPSJAM `robots.txt` zwracał 404; belzhd `robots.txt` nie blokował głównego kanału. Żadne z tych ustaleń nie jest licencją. Przed publicznym udostępnieniem danych należy ustalić zasady dostawców.

AUGUR pozostaje kandydatem do kontekstu GNSS; nie podłączono jego API. Osobny [pilotaż jakości ADSB.lol](aviation-runbook.md) działa od 24.09.2026 i ma własną bazę oraz ręczne próbkowanie. Uzupełnia go [audyt trzech półgodzinnych okien historii](aviation-history.md); odmienne formaty pozostają osobnymi seriami. Te moduły nie modyfikują obserwacji GNSS/logistyki. Nie uruchomiono Telegrama, nowych płatnych usług, ciągłego monitoringu, dashboardu ani alertów. Dalsza praca analityczna obejmuje porównywalną historię, definicje wyników i niezależne potwierdzenia; etap UI wymaga wcześniejszego wyboru spośród dwóch proponowanych kierunków wizualnych.
