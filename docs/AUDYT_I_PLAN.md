# OSINT Threat Dashboard — audyt i proponowany plan

> Dokument historyczny z 22.09.2026, zachowany jako ślad decyzji. Stan implementacji opisuje obecnie STATUS.md, a zaakceptowaną specyfikację metodologia v0.3 w methodology.md; działający silnik nadal wykonuje v0.2. Wątki majątkowe i osobiste z pierwotnego planu zostały wycofane z zakresu projektu; poniższy tekst nie jest aktualną instrukcją wykonania.

Data oceny: 22 września 2026. Status: propozycja do dalszej realizacji.

Dokument obejmuje przegląd lokalnych materiałów, punktowe testy istniejącego kodu i rekomendowaną architekturę. Nie jest raportem o aktualnym zagrożeniu. Liczby z testów poniżej pochodzą wyłącznie z danych syntetycznych. Podczas audytu dodano ten dokument; istniejących materiałów nie przebudowano ani nie uruchomiono monitoringu cyklicznego.

**Rekomendacja**

Rozwijać jeden projekt z dwiema oddzielnymi częściami: przetwarzaniem danych i dashboardem. Najpierw ustalić format danych oraz reguły RTB i przeprowadzić mały przebieg od rzeczywistych źródeł do raportu. Po tym można równolegle rozwijać zbieranie danych i interfejs, korzystając z tego samego kontraktu JSON. Rozbudowane scenariusze majątkowe dodać po sprawdzeniu jakości pomiaru.

Robocze założenie do planowania: jeden użytkownik, lokalny Mac, Polska jako obszar decyzji, CEE jako obszar obserwacji, Warszawa i Łódź jako osobne rynki nieruchomości. Horyzont majątkowy 6–24 miesięcy jest propozycją, a nie potwierdzoną preferencją użytkownika. Operacyjny monitoring wymaga krótszych okien niezależnie od tego horyzontu.

**Co jest dostępne**

| Materiał | Ustalenie | Proponowane wykorzystanie |
|---|---|---|
| `agents/OSINT-threat-barometer.md` | Definiuje cel, siedem kategorii punktowych, bazę 10 i próg ponad 60. Nie definiuje usuwania duplikatów, ograniczenia sumy do 100 ani walidacji progu. | Przepisać na instrukcję analityka pracującego na ustalonym schemacie i zasadach dowodowych. |
| `scripts/ingest.py` | Importuje lokalne dokumenty do Chroma z użyciem embeddingów. Nie pobiera wiadomości OSINT. Odwołuje się do nieobecnego w projekcie `constants.py`. | Zachować jako materiał referencyjny; stworzyć właściwy proces pobierania. Baza wektorowa nie jest potrzebna do pierwszego RTB. |
| `skills/rss-feeds` | Zawiera rzeczywisty skrypt Python czytający RSS, Atom i JSON Feed. Nie pobiera pełnych artykułów i nie utrwala historii pobrań. | Najlepszy punkt wyjścia do pierwszego kolektora; dodać obsługę błędów, stan źródeł i zapis surowych odpowiedzi. |
| `skills/x-research` | Sam dokument wprost mówi, że nie dostarcza narzędzia wyszukiwania, poświadczeń ani modułu wykonawczego. Jest zorientowany na analizę opinii. | Późniejszy, opcjonalny kanał wykrywania doniesień po zapewnieniu dostępu; wymaga adaptacji do incydentów. |
| `skills/browser-automation` | Ogólne wskazówki; brak scraperów dla konkretnych źródeł. | Pomoc przy wybranych stronach wymagających JavaScript, po sprawdzeniu dostępu i stabilności. |
| `skills/geopandas` | Instrukcja biblioteki GIS; brak lokalnego procesu rozpoznawania nazw miejsc i rozstrzygania niejednoznaczności. | Opcjonalna analiza przestrzenna. Osobno przygotować ekstrakcję miejsc, geokoder i ocenę dokładności. |
| `skills/expo-sqlite` | Instrukcja dla środowiska Expo/React Native, również z obsługą web wymagającą dodatkowej konfiguracji. | W tym projekcie wybrać zwykłe SQLite obsługiwane z Pythona. |
| `skills/worldthreatmodel` | Opisuje środowisko LifeOS, zewnętrzne ścieżki, 11 dokumentów modeli i dodatkowe skills. Tych modeli nie ma w tym projekcie. | Inspiracja do późniejszych przeglądów strategicznych; nie jest gotowym modelem RTB. Nie sprawdzano, czy zależności istnieją poza projektem. |
| `skills/geopolitical-risk` | Obszerny materiał ogólny z przykładami rynkowymi i kodem wewnątrz Markdown. Brak wdrożonego modelu nieruchomości dla Warszawy i Łodzi. | Wybrać odpowiednie mechanizmy wpływu; dane liczbowe i twierdzenia historyczne zweryfikować przed wykorzystaniem. |
| `skills/soft-predict-future`, `skills/hard-predict-future` | Ogólne procesy scenariuszowe o znacznie dłuższych horyzontach. Wersja hard ma osiem skryptów, ale zawiera błędy integracji i niewalidowane heurystyki. | Nie używać bezpośrednio do alarmów lub decyzji kapitałowych. Zachować elementy struktury scenariuszy po adaptacji. |

Katalogi `data/raw` i `data/database` są puste. Brakuje dashboardu, schematów danych, konfiguracji źródeł, zarządzania zależnościami, migracji, harmonogramu, testów integracyjnych i instrukcji uruchamiania. Nie ma repozytorium Git ani plików `AGENTS.md`, `design.md`, `guidelines.md`, `theme.css` w projekcie. Sam plik `SKILL.md` jest instrukcją; wykonanie wymaga podłączonych narzędzi i procesu, który je wywołuje.

**Wyniki sprawdzeń kodu**

W Pythonie 3.13.7 sprawdzono składnię wszystkich 10 plików `.py`: bez błędów składni. Wykonano poniższe próby offline przez import funkcji. Nie instalowano zależności, nie uruchamiano całych workflow predykcyjnych i nie potwierdzano działania produkcyjnego kolektorów.

| Próba | Zaobserwowany wynik | Znaczenie |
|---|---|---|
| RSS, Atom, JSON Feed: po jednym poprawnym wpisie | Wszystkie trzy formaty sparsowane, czas przeliczony do UTC. | Parser RSS można wykorzystać jako podstawę. |
| Niepoprawna data wpisu + filtr `--since` | `ValueError: Invalid isoformat string: 'unknown-date'`. | Jeden wadliwy wpis może przerwać przetwarzanie kanału; potrzebna kwarantanna rekordu. |
| `probable_score=90`, `plausible_score=5` przekazane do `compute_guidance` | Wniosek o zbyt mieszanych sygnałach. Te same wartości pod nazwami `probable_pct`, `plausible_pct` dają wniosek o podążaniu za scenariuszem. | Producent i odbiorca używają innych nazw pól; odbiorca cicho zastępuje wynik wartościami domyślnymi. |
| Jedno syntetyczne doniesienie, następnie 20 kopii tego samego doniesienia | `probable_score` rośnie z 24 do 100. | Kalkulator nie chroni się przed powtórzeniami. Brak wcześniejszego usuwania duplikatów w projekcie. |
| 20 syntetycznych sygnałów oznaczonych wyłącznie `OPPOSING` | `probable_score=89`. | Intensywność komórki macierzy podnosi wynik także przy sygnałach przeciwnych; nie wolno interpretować wyniku jako prawdopodobieństwa tezy. |
| Źródło `https://example.org/post`, następnie ten sam adres z `?tag=government` | Waga wiarygodności rośnie z 0.4 do 1.0. | Waga zależy od fragmentu tekstu adresu, a nie sprawdzonej tożsamości wydawcy. |

Miejsca wymagające uwagi: `probability_calc.py:323` emituje pola `*_score`, a `decision_guidance.py:118` czyta `*_pct`; `signal_scorer.py:233` sprawdza podciągi tekstu; `probability_calc.py:63` wykorzystuje intensywność komórki niezależnie od kierunku sygnałów; `feed.py:194` zakłada poprawny format daty. Nazwy tych plików odnoszą się do odpowiednich katalogów `skills/*/scripts/`.

Instrukcja hard wymaga narracji bez wyrażania niepewności (`SKILL.md:211`). Dla tego zastosowania należy zastąpić ją scenariuszami warunkowymi z jawnymi założeniami. Arytmetyka w Pythonie zapewnia powtarzalność obliczeń, lecz sama nie potwierdza trafności prognoz.

**Znaczenie RTB i reguły wiarygodności**

RTB powinien początkowo oznaczać eksperymentalny indeks nasilenia określonych sygnałów, w skali 1–100. Wynik 68 nie oznacza 68% szans na wojnę, eskalację ani spadek cen. Obecny próg 60 i wagi 2–10 punktów są założeniami autora instrukcji, bez przedstawionej walidacji.

Przed kodowaniem scoringu trzeba opisać:

1. **Zakres.** Jakie państwa i zdarzenia należą do indeksu; które są tylko kontekstem. Zdarzenie po ukraińskiej stronie granicy nie jest samo w sobie naruszeniem przestrzeni NATO. Wzrost aktywności obronnej nie dowodzi przygotowania ataku.
2. **Oddzielne twierdzenia.** Wystąpienie pożaru, celowy sabotaż i przypisanie go Rosji/Białorusi to trzy osobne ustalenia. Potwierdzenie pierwszego nie potwierdza pozostałych. Do komponentu przypisanego RU/BY potrzebne są dowody atrybucji; zdarzenia nieprzypisane zachowujemy jako osobną warstwę obserwacji.
3. **Zdarzenie i publikacje.** Dziesięć tekstów o jednym pożarze nie daje dziesięciu incydentów. Dwa portale cytujące ten sam komunikat nie są dwoma niezależnymi potwierdzeniami.
4. **Stany dowodowe.** Osobno: niezweryfikowane, potwierdzone jednym źródłem pierwotnym, potwierdzone niezależnie, sprzeczne, obalone. Brak potwierdzenia nie jest dowodem dezinformacji; zamiar wprowadzenia w błąd wymaga dodatkowego uzasadnienia.
5. **Trzy informacje obok wyniku.** Nasilenie sygnałów, jakość dowodów i kompletność monitoringu. Niedostępne źródła nie mogą automatycznie obniżać poziomu zagrożenia.
6. **Czas.** Data zdarzenia, publikacji, pobrania i moment wiedzy analityka są oddzielne. Powrót starego artykułu do obiegu nie tworzy nowego zdarzenia.
7. **Geografia.** Zapisać miejsce wraz z dokładnością i podstawą lokalizacji. „W pobliżu Łasku” nie uprawnia do wskazania dokładnego obiektu. Dopuszczać obszar, punkt orientacyjny oznaczony jako przybliżony albo brak współrzędnych.
8. **Powiązania.** Zdarzenia dotyczące jednej operacji lub kampanii mają wspólny identyfikator. Reguły określają, kiedy wolno liczyć oddzielne skutki, a kiedy byłoby to wielokrotne naliczenie tej samej informacji.

Pierwszą wersję punktowania powinien liczyć kod na podstawie jawnej, wersjonowanej tabeli. Można zacząć od dotychczasowych wag jako hipotezy roboczej, ale dopiero po zdefiniowaniu kwalifikacji zdarzeń, limitów kategorii, okna czasowego i sposobu wygasania sygnałów. Należy przechowywać także surową sumę, aby widzieć nasycenie skali po ograniczeniu do 100. AI proponuje klasyfikację i wskazuje dowody; nie zmienia samodzielnie wzoru ani progów.

Główny odczyt: ostatnie 7 dni wobec poprzednich 7 dni, według jednej strefy i ustalonego momentu odcięcia. Archiwum tygodniowe: stałe tygodnie kalendarzowe w Europe/Warsaw. Trend miesięczny może pokazywać średnią i maksimum dziennych odczytów 7-dniowych. „All-time” służy przeglądaniu historii, a nie sumowaniu wszystkich punktów od początku projektu. Zmiana 55 → 68 to przede wszystkim +13 pkt indeksu; procentowa zmiana jest informacją pomocniczą, nie zmianą prawdopodobieństwa.

Gdy brak minimalnego pokrycia źródeł, bieżący wynik ma status „dane niepełne” albo nie jest publikowany. Ostatni prawidłowy odczyt pozostaje widoczny z datą ważności. Przy zmianie zestawu źródeł lub metodologii zaznaczyć nieporównywalność; nowych i starych odczytów nie łączyć bez wyjaśnienia w jednolity trend.

**Architektura lokalna**

Przepływ: źródła → zapis surowych materiałów → ekstrakcja doniesień → łączenie duplikatów i dowodów → weryfikacja oraz lokalizacja → scoring → SQLite → wersjonowany eksport JSON/GeoJSON → dashboard i raport.

Rekomendowany zestaw:

- Python do kolektorów, walidacji, obliczeń i raportów.
- SQLite jako trwała lokalna baza. Python udostępnia moduł `sqlite3`; osobny serwer bazy nie jest wymagany. [Dokumentacja Pythona](https://docs.python.org/3/library/sqlite3.html).
- Lekka strona HTML/CSS/JS. Mapa w Leaflet, które obsługuje GeoJSON, znaczniki i warstwy. [Dokumentacja Leaflet](https://leafletjs.com/).
- Eksport danych do statycznych plików; lokalny serwer HTTP udostępnia wyłącznie katalog dashboardu. Przeglądarka nie otwiera automatycznie roboczej bazy SQLite z dysku.
- Późniejsze lokalne API tylko wtedy, gdy potrzebne będą zapisywane w przeglądarce korekty i zatwierdzenia. Filtry, mapa i odczyt historii nie wymagają takiego API.

`expo-sqlite` ma zastosowanie w środowisku Expo. Aktualna dokumentacja opisuje obsługę web jako alpha i wymaga konfiguracji WASM oraz nagłówków dla `SharedArrayBuffer`; to niepotrzebny koszt złożoności dla tego wariantu. [Dokumentacja Expo](https://docs.expo.dev/versions/latest/sdk/sqlite/).

GeoPandas może wykonywać geokodowanie przez geopy i wybranego dostawcę. Nie zastępuje jednak ekstrakcji miejsc z tekstu, rozróżnienia miejscowości o tej samej nazwie ani oceny dokładności. Na początek wystarczy kontrolowany słownik miejsc oraz kolejka niejednoznaczności. [Dokumentacja geokodowania GeoPandas](https://geopandas.org/en/stable/docs/reference/api/geopandas.tools.geocode.html).

Dashboard będzie lokalny, ale pozyskiwanie nowych informacji wymaga internetu. Zewnętrzne modele AI i dostawcy map oznaczają dodatkowe połączenia. Jeśli potrzebne jest odczytywanie archiwum bez sieci, trzeba lokalnie dostarczyć biblioteki i legalnie dostępny podkład mapy lub uproszczone granice. Klucze API należą do procesu zbierania, poza katalogiem udostępnianym przeglądarce.

**Kontrakt danych i historia**

| Obiekt | Minimalna zawartość |
|---|---|
| Źródło | Identyfikator, wydawca, URL, metoda dostępu, język, region, częstotliwość, ograniczenia, status sprawdzenia dostępu. |
| Materiał źródłowy | Stabilny identyfikator, URL kanoniczny, identyfikator dostawcy, daty publikacji/pobrania, hash treści, ścieżka kopii lub dozwolonego fragmentu, wynik pobrania. |
| Zdarzenie | Identyfikator, rewizja, data lub przedział czasu, kraj, opis, kategoria, status, powiązana kampania, czas pierwszego rozpoznania. |
| Dowód | Zdarzenie, konkretne twierdzenie, materiał, fragment uzasadnienia, kierunek: potwierdza/przeczy, pierwotne pochodzenie i niezależność. |
| Lokalizacja | Nazwa, geometria albo null, metoda ustalenia, dokładność/obszar niepewności, materiał potwierdzający. GeoJSON: WGS84, kolejność długość/szerokość. |
| Atrybucja | Wskazany sprawca lub brak ustalenia, status dowodowy, uzasadnienie i dowody. |
| Przegląd | Autor typu człowiek/agent, czas, decyzja, uzasadnienie, wersja instrukcji; nie oznaczać przeglądu AI jako ludzkiej weryfikacji. |
| Przebieg | Identyfikator, czas odcięcia, wersja kodu i reguł, użyte wersje danych, statusy źródeł, błędy, użycie usług i koszty, jeśli dostępne. |
| Odczyt RTB | Okno czasu, wynik albo null, wkłady kategorii i zdarzeń, surowa suma, kompletność, metoda, identyfikator przebiegu. |
| Raport | Data publikacji, okres, wersja, odczyt RTB, cytowane rewizje zdarzeń, scenariusze oddzielone od obserwacji. |

SQLite samo nie zapewnia nienaruszalnej historii. Potrzebne są wersje zdarzeń i raportów, ograniczenia zapisu oraz kopie zapasowe. Korekta tworzy nową rewizję, zachowując poprzednią. Rozróżniamy historię „jak wiedzieliśmy wtedy” od historii przeliczonej z dzisiejszą wiedzą.

Przy eksporcie najpierw powstaje kompletny katalog nowego przebiegu. Dopiero po sprawdzeniu spójności zmienia się wskaźnik najnowszego wydania. Wykres, mapa i tabela odwołują się do tego samego identyfikatora przebiegu. Błąd jednego źródła lub przerwanie programu nie może opublikować mieszanki różnych wersji danych.

**Źródła i etapy zbierania**

Pierwszy przebieg: 3–5 sprawdzonych źródeł obejmujących komunikaty pierwotne oraz analizę regionalną. Kandydaci to właściwe komunikaty MON/Dowództwa Operacyjnego, RCB, Straży Granicznej, CERT Polska i OSW. To propozycja listy do sprawdzenia, nie potwierdzenie działających integracji. Istniejący agent ma niespójność: wspomina komunikaty ministerstw w workflow, a jego późniejsza zamknięta lista źródeł ich nie obejmuje. Należy ją ujednolicić w konfiguracji.

Komunikaty RCB są dostępne na stronie instytucji. Są przydatne również do rozróżniania ćwiczeń, aktualizacji i odwołań ostrzeżeń. Dostępność strony nie potwierdza jeszcze RSS ani niezawodności przyszłego kolektora. [RCB — komunikaty](https://www.gov.pl/web/rcb/komunikaty).

War on the Rocks, The War Zone, Defense One, Breaking Defense i Naval News mogą dostarczać kontekstu. Nie zakładamy, że pokrywają komplet lokalnych zdarzeń w Polsce. Zasięg tematyczny i geograficzny każdego źródła powinien być widoczny w rejestrze.

Każdy kolektor potrzebuje ograniczonego czasu żądania, ponowień z odstępami, obsługi limitów, kontrolowanego nadrabiania przerw, stanu ostatniego udanego pobrania i ochrony przed ponownym naliczeniem wpisów. Surowy materiał zapisujemy przed ekstrakcją, w zakresie dozwolonym przez źródło. Nie zakładamy, że skrót RSS zawiera wszystkie informacje artykułu. Teksty z internetu traktujemy jako materiał dowodowy, nie jako instrukcje dla narzędzi.

X należy dodać po osobnym sprawdzeniu dostępu i kosztu. Oficjalne API jest płatne za użycie; plik `x-research/SKILL.md` tego dostępu nie zapewnia. Nie opierać pierwszej działającej wersji na założeniu bezpłatnego, kompletnego monitoringu X. [Dokumentacja cen X](https://docs.x.com/x-api/getting-started/pricing).

FIRMS jest późniejszym źródłem pomocniczym. Anomalie termiczne mogą pochodzić m.in. z przemysłu i spalania gazu, więc sama detekcja nie rozstrzyga o eksplozji lub sabotażu. API wymaga klucza MAP_KEY. [NASA — FAQ](https://www.earthdata.nasa.gov/data/tools/firms/faq), [NASA — API obszarowe](https://firms.modaps.eosdis.nasa.gov/api/area/).

Liveuamap, DeepStateMap i ADS-B Exchange: przed implementacją zweryfikować dozwolony sposób automatycznego dostępu, zakres danych i koszty. Dostępna mapa internetowa nie jest równoznaczna z darmowym API lub pełnym dostępem do historii. Brak odczytów nie jest dowodem braku aktywności. Anomalie wymagają poziomu odniesienia; większa liczba widocznych lotów sama nie stanowi potwierdzonego incydentu.

**Proponowane pliki do stworzenia**

Nazwy poniżej oznaczają planowane elementy, nie pliki już wdrożone. Zachować obecne katalogi i materiały. Skrypty powinny być cienkimi punktami uruchamiania; wspólna logika w jednym pakiecie `src/osint_dashboard/`.

| Plik lub grupa | Zadanie | Etap |
|---|---|---|
| `README.md`, `pyproject.toml`, `.gitignore`, `.env.example` | Uruchamianie, zależności, wyłączenie danych roboczych i sekretów z Git, przykładowa konfiguracja bez kluczy. | 1 |
| `AGENTS.md`, `docs/methodology.md` | Zasady pracy, granice automatyzacji, definicja RTB, dowody, korekty, horyzonty i kryteria publikacji. | 1 |
| `config/sources.yaml`, `config/scoring-v0.yaml` | Rejestr faktycznie podłączonych źródeł i jawne reguły naliczania. | 1 |
| `schemas/incident.schema.json`, `schemas/snapshot.schema.json` | Jeden kontrakt walidowany przez proces danych i używany przez frontend. | 1 |
| `migrations/001_initial.sql` | Baza materiałów, zdarzeń, dowodów, przeglądów, przebiegów i odczytów. | 1 |
| `scripts/collect_sources.py` | Pobranie i archiwizacja materiałów, statusy źródeł; adaptacja parsera RSS. | 2 |
| `scripts/extract_incidents.py` | Z materiałów tworzy kandydatów na zdarzenia, z cytowanymi dowodami i walidacją schematu. | 2 |
| `scripts/resolve_incidents.py` | Łączenie powtórzeń, pochodzenie dowodów, lokalizacja, atrybucja, rozbieżności i kolejka przeglądu. | 2 |
| `scripts/score_rtb.py` | Deterministyczny odczyt z zatwierdzonego zbioru rewizji i jawnej daty odcięcia. | 2 |
| `scripts/export_dashboard.py`, `scripts/build_report.py` | Spójny eksport danych, raport źródłowy, manifest wydania. | 2 |
| `scripts/run_pipeline.py`, `scripts/doctor.py` | Kolejność etapów, blokada równoczesnych uruchomień, wznawianie, limity kosztu i diagnoza braków. | 2 |
| `agents/incident-extractor.md`, `agents/evidence-reviewer.md` | Wąskie role AI o ustalonych wejściach i wyjściach; mogą być wykonywane kolejno przez jeden model. | 2 |
| Zmiana `agents/OSINT-threat-barometer.md` | Synteza z zatwierdzonych danych, bez swobodnego liczenia, wymyślania współrzędnych i progów. | 2 |
| `design.md`, `guidelines.md`, `theme.css` | Wybrany kierunek wizualny, dostępność i reguły prezentowania niepewności. | 3 |
| `dashboard/`, `scripts/serve_dashboard.py` | Strona lokalna z RTB, mapą, historią, dowodami i stanem źródeł; podanie wyłącznie katalogu strony. | 3 |
| `tests/fixtures/`, testy integracji | Przypadki duplikatów, sprzeczności, błędnych dat, braków danych i korekt. | 2–3 |
| `ops/`, instrukcja kopii i odtwarzania, lokalny launcher | Harmonogram, logi, kopie, odzyskiwanie po awarii, proste otwieranie aplikacji. | 4 |
| `agents/scenario-analyst.md`, konfiguracja danych rynkowych, `scripts/evaluate_history.py` | Scenariusze i ocena na danych historycznych oraz z pilotażu. | 5 |

Docelowe role katalogów danych: `data/raw/` — materiały; `data/database/` — SQLite; `data/runs/` — wyniki przebiegów; `data/reports/` — raporty; `data/snapshots/` — utrwalone odczyty. Eksport dostępny w przeglądarce jest osobną, ograniczoną kopią danych. Demonstracyjne przypadki należą do `tests/fixtures/`, nie do historii realnych zdarzeń.

W pierwszej wersji wystarczy jeden proces koordynujący i kolejne wywołania modelu do jasno opisanych zadań. Większa liczba agentów może później pomagać w rozwiązywaniu sprzeczności, ale ich zgodność nie stanowi niezależnego potwierdzenia faktów.

**Kolejność prac i warunki odbioru**

| Etap | Konkretny rezultat | Kiedy uznajemy etap za ukończony |
|---|---|---|
| 1. Fundament | Metodologia v0, lista źródeł, schemat danych, konfiguracja projektu i Git. | Jedno zdarzenie da się opisać od źródła do wkładu w RTB; wiadomo, co oznaczają brak danych, korekta i nieznany sprawca. |
| 2. Pierwszy pełny przebieg | 3–5 podłączonych źródeł, lokalna baza, obliczenie i raport z realnymi odnośnikami. | Dwa uruchomienia na tych samych materiałach nie tworzą nowych incydentów ani dodatkowych punktów. Wynik można odtworzyć ze zapisanych danych. |
| 3. Dashboard | Lokalna mapa, filtry, karta RTB, trend, tabela dowodów, stan aktualizacji i źródeł. | Mapa, tabela i raport pokazują ten sam przebieg; dane testowe są jawnie oznaczone; niepełne dane i przybliżone lokalizacje są czytelne. |
| 4. Automatyzacja i pilotaż | Harmonogram, nadrabianie przerw, kopie, logi, kolejka przeglądu. | Awaria źródła nie udaje spadku ryzyka, przerwany zapis nie psuje wydania, kopię da się odtworzyć. |
| 5. Scenariusze majątkowe | Oddzielne analizy Warszawy i Łodzi z danymi rynkowymi, warunkami scenariuszy i uzasadnieniem. | Wnioski mają powiązanie z dowodami i jawnymi założeniami; opisano granice dostępnych danych i oceniono błędy pilotażu. |

Po zamknięciu schematów w etapie 1 frontend może powstawać na oznaczonych danych demonstracyjnych równolegle z etapem 2. Pierwszym kamieniem milowym pozostaje jednak rzeczywisty przebieg od pobrania do eksportu. Nie trzeba czekać na pełną automatyzację wszystkich źródeł, aby uzyskać użyteczny dashboard.

Przed budową UI przygotować dwa kierunki wizualne, następnie zapisać wybrany w materiałach projektowych. Docelowo ważniejsze od dekoracyjnego wskaźnika są: źródło zmiany wyniku, data ostatniej aktualizacji, jakość dowodów i kompletność monitoringu.

Na mapie domyślnie pokazać incydenty i skupiska punktów, z kształtem oznaczającym kategorię i osobnym oznaczeniem wiarygodności. Warstwa cieplna może przedstawiać gęstość zaobserwowanych zdarzeń; nie nazywać jej mapą prawdopodobieństwa ataku. Filtr listy lub kategorii nie powinien po cichu zmieniać znaczenia głównego RTB. Wykres pozwala wskazać wydarzenia towarzyszące wzrostowi, ale sam nie dowodzi cykliczności ani związku przyczynowego.

**Jak ma działać automatyzacja**

Propozycja startowa: pobieranie co 6 godzin, bieżący odczyt 7-dniowy po udanym przebiegu i utrwalony raport raz w tygodniu. To częstotliwość pilotażu, nie obietnica wykrywania zdarzeń w czasie rzeczywistym. Ważne nowe doniesienia trafiają do kolejki przeglądu poza terminem raportu tygodniowego. Przegląd pilnych informacji i awarie mają osobne statusy; nie każdy nowy artykuł jest alertem.

Na macOS można wykorzystać `launchd`; pliki konfiguracji pozostają w projekcie, a instalacja harmonogramu jest osobnym etapem. Dokumentacja Apple opisuje wywołania okresowe i kalendarzowe. [Apple — launchd](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html).

Wyłączony komputer nie zbiera danych. Po uruchomieniu system musi nadrabiać dostępne publikacje, oznaczając luki, których nie dało się uzupełnić. Ciągła praca wymaga stale działającego urządzenia; serwer można rozważyć później. Automatyczne działanie wymaga również wybranego, skonfigurowanego sposobu wywoływania AI. Obecne pliki nie dostarczają takiego połączenia. Wariant API i wariant modelu lokalnego wymagają osobnej próby jakości, kosztu i czasu działania.

Koszt oszacować po próbnym przetworzeniu reprezentatywnego pakietu: liczba materiałów × rozmiar tekstu × wywołania modelu, plus płatne źródła i mapy. Wprowadzić cache, analizę nowych/zmienionych treści i limit wydatków na przebieg oraz miesiąc. Nie zakładać, że dostęp do stron lub posiadanie skills obejmuje opłaty API.

**Powiązanie z decyzjami majątkowymi**

Obok RTB potrzebna jest druga warstwa: ceny transakcyjne i ofertowe, czynsze, koszty finansowania, podaż oraz dostępne miary płynności. Warszawa i Łódź wymagają osobnych danych. NBP publikuje szeregi cen obejmujące oba miasta; raporty są przykładem danych o innej częstotliwości niż wiadomości OSINT. Nie należy interpolować kwartalnych publikacji i przedstawiać ich jako nowych dziennych obserwacji. [NBP — przykładowy raport kwartalny i opis BaRN](https://nbp.pl/wp-content/uploads/2025/02/Informacja-o-cenach-mieszkan-i-sytuacji-na-rynku-nieruchomosci-mieszkaniowych-i-komercyjnych-w-Polsce-w-I-kwartale-2024-r.pdf).

Dodatkowo potrzebne będą założenia właściciela: horyzont sprzedaży, zadłużenie, przepływy z najmu, rezerwa gotówkowa, koncentracja majątku i koszty zmiany alokacji. W pierwszym etapie nie są potrzebne adresy konkretnych mieszkań.

Scenariusz powinien zawierać: opis warunkowy, sygnały wspierające i przeciwne, mechanizm wpływu na dany rynek, założenia, co zmieni ocenę i jakie informacje warto uzupełnić. Początkowo służy do przeglądu planu finansowego. Nie wprowadzać automatu „RTB ponad 60 → sprzedaj mieszkanie”. Brak lokalnego modelu pozwalającego rzetelnie przeliczyć indeks na zmianę ceny lub optymalny termin sprzedaży.

Zewnętrzny GPR Caldary i Iacoviella może być punktem porównania dla ogólnej presji informacyjnej: jest konstruowany z udziału artykułów spełniających określone kryteria. Nie jest etykietą prawdy ani dowodem kalibracji naszego RTB. [Autorzy — metodologia i dane GPR](https://www.matteoiacoviello.com/gpr.htm).

**Sprawdzenia, których wymaga gotowa pierwsza wersja**

- Pięć kopii jednego artykułu i pięć niezależnych incydentów dają różne wyniki zgodnie z regułami.
- Cytowanie jednej agencji przez różne portale nie daje statusu niezależnego potwierdzenia.
- Potwierdzony pożar o nieznanej przyczynie nie staje się automatycznie rosyjskim sabotażem.
- Zdarzenie na Ukrainie nie dostaje kategorii naruszenia NATO bez dowodu przekroczenia granicy.
- Stare zdarzenie opisane ponownie nie otrzymuje dzisiejszej daty zdarzenia.
- Niejasna lokalizacja pozostaje niejasna w danych i na mapie.
- Brak internetu, puste źródło i brak nowych incydentów mają różne statusy.
- Awaria modelu nie tworzy pozornie poprawnego pustego raportu.
- Zmiana źródeł lub reguł zostaje oznaczona w historii i ogranicza porównywalność trendu.
- Korekta tworzy nową rewizję; wcześniejszy raport da się odtworzyć.
- Ponowne liczenie na zamrożonych wejściach, zapisanych ocenach i tej samej konfiguracji daje ten sam RTB bez ponownego pytania modelu.
- Każdy punkt RTB da się prześledzić do zdarzenia, reguły i dowodu; wartości mieszczą się w skali lub jawnie wynoszą null.
- Frontend pokazuje spójne wydanie, poprawne odnośniki, stan danych i tekstowe odpowiedniki oznaczeń kolorystycznych.
- Odtworzenie SQLite i raportów z kopii zostaje faktycznie przeprowadzone.

Przed poleganiem na alarmach porównać wyniki z ręcznie opisanymi przypadkami spokojnymi, głośnymi medialnie, rzeczywiście istotnymi i później obalonymi. Do oceny historycznej używać informacji dostępnych na daną datę, a nie późniejszych wyjaśnień. Kilkutygodniowy pilotaż może ujawnić błędy procesu i fałszywe alarmy; nie wystarcza do udowodnienia zdolności przewidywania rzadkich eskalacji ani cen nieruchomości.

**Najbliższy rekomendowany zakres realizacji**

Etapy 1–2: metodologia v0, kontrakt zdarzenia i odczytu, 3–5 sprawdzonych źródeł, SQLite, prosty kolektor oraz pierwszy raport, w którym każdy naliczony punkt ma dowód. Po ustaleniu kontraktu rozpocząć dashboard. Ten zakres daje podstawę do rzeczywistej oceny jakości przed rozszerzaniem źródeł, agentów i scenariuszy.
