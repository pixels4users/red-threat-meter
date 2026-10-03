# UX: spójny Przegląd i Mapa Operacyjna

Status: interaktywny prototyp do oceny, 02.10.2026. Ten plan zastępuje wcześniejszą propozycję osobnych sekcji regionalnych ponad osią czasu i mapą. Aktualny podgląd: `ui/experiments/rta-overview-prototype.html`. Makiety `ui/experiments/rta-ux-directions.html` są zapisem wcześniejszego eksperymentu, nie docelową specyfikacją.

## Zakres

Cel: odpowiedzieć na pytania „co się dzieje”, „czy dotyczy mnie” i „co powinienem zrobić”, zachowując minimalizm obecnej strony.

Zachowujemy siatkę Przeglądu: oś czasu po lewej, mapa po prawej; na telefonie oś przed mapą. Nie dokładamy pomiędzy podsumowaniem a siatką kolejnej kolekcji kart. Przebudowa dotyczy zawartości obecnego obszaru indeksu i komentarza, etykiet osi oraz osobnej Mapy Operacyjnej. RTA pozostaje największą liczbą i występuje tylko w Przeglądzie. Szczegółowy zakres źródeł nadal jest poniżej osi i mapy, skrót pewności przy wyniku. Zachowujemy neutralne kontrolki i skalę odstępów 4 px. Powiadomienia są poza zakresem.

## Sprawdzone ustalenia

Sprawdzono lokalny dashboard, kod frontendu i publikacji oraz eksport `data/analysis/commentary-revisions/2026-10-02-verified-events-v2/publication-daily.json` (02.10.2026, 09:25 czasu Warszawy, raport `rpt_eac9ac1f8145fa0820288abc21e8782c545d0dd185733af4431b9a4dad94fb2f`).

- „Polska / flanka wschodnia” w menu to opis, nie działający wybór regionu. Przełącznik będzie nową funkcją.
- Raport ma 83 wpisy, w tym 80 z kategorią punktacji `context`. Filtr tematu Dziennika korzysta z tej kategorii, dlatego wiele informacji lotniczych, cyber i GNSS trafia do „Sytuacji w regionie”.
- Wpis CERT „Fałszywe wiadomości podatkowe instalują Remcos” (`evt_7393684f1cbcc37946935635`) jest widoczny przy „Wszystkich tematach”. Filtr „Cyberbezpieczeństwo” daje 0 z 83 wpisów. Nie pochodzi on z osobnego zbioru; wcześniejsza makieta dodatkowo użyła innej nazwy tego samego wpisu.
- Eksport zawiera **0 punktów GeoJSON**. Flagi krajowe tworzy frontend; nie są lokalizacjami incydentów. Część lokalnych wpisów, np. Świnoujście i powiat pyrzycki, ma nadal obszar „Polska”.
- Silnik ma 16 wyników wojewódzkich; w tym raporcie wszystkie wynoszą 0. To nie liczba lokalnych wpisów: zapowiedź formowania brygady w Łowiczu ma 0 punktów, choć jest użyteczną informacją regionalną. Przy nieustalonym przypisaniu istotnych zdarzeń obecny kod może również zwrócić regionalne `null`.
- Eksport nie ma osobnej pewności wojewódzkiej ani wskaźników odchylenia w dziedzinach. `confidence.domains[].percent` opisuje pokrycie źródeł, nie nasilenie zagrożenia.
- GNSS ma opisowe porównanie historyczne w pilotażu, ale nie zweryfikowaną normę. Nie ma ogólnego automatycznego detektora anomalii dla lotnictwa i cyber.
- Mapa i Dziennik korzystają z wpisów najnowszego raportu. Archiwum udostępnia raporty, nie gotowy, scalony zbiór sygnałów za kwartał lub rok.
- Komentarz jest jednym zatwierdzonym tekstem. Generator dopuszcza 1–3 zdania, ale nie eksportuje trzech nazwanych pól.

## Ocena propozycji

| Zmiana | Ocena | Warunek |
| --- | --- | --- |
| Trzy krótkie wiersze komentarza | Zalecana; niewielka zmiana widoku, średnia procesu publikacji | Nazwane pola, dowody dla treści, regionalna wersja i proste stany braku danych |
| Makro / województwo obok indeksu | Wykonalne; większa zmiana danych niż wyglądu | Przypisania, wynik i pewność regionalna oraz wspólny wybór sygnałów |
| Liczniki sygnałów: ostatnie 7 dni vs poprzednie 7 dni | Rekomendowana prosta wersja początkowa | Wspólne tematy, odrębne sygnały i dostępna historia obu okresów; bez wyznaczania norm |
| Etykiety regionów na osi | Mała zmiana widoku po uzupełnieniu danych | Zweryfikowane obszary i jedna reguła dla wszystkich widoków |
| Filtry → mapa → lista | Średnia zmiana widoku; większa dla długiej historii | Jeden zbiór wyników dla mapy, listy i liczników; usuwanie powtórzeń |
| Spójne pojęcie sygnału | Pierwszy etap i warunek reszty | Rozdzielenie tematu, rodzaju, zasięgu i wkładu do indeksu |

## Jeden zbiór sygnałów

**Sygnał** to opublikowany po przeglądzie zapis zdarzenia, pomiaru, ostrzeżenia lub istotnej zapowiedzi. Materiał źródłowy jest dowodem; artykuł lub przedruk nie tworzy automatycznie kolejnego sygnału. Stopień potwierdzenia pozostaje osobny.

Każdy sygnał ma stały identyfikator, wspólny tytuł i opis, źródła, daty oraz:

- **Temat:** np. lotnictwo, cyberbezpieczeństwo, nawigacja, infrastruktura, granica; niezależny od kategorii punktacji, możliwe kilka tematów.
- **Rodzaj:** zdarzenie, ostrzeżenie, zapowiedź/ćwiczenia, pomiar. Ćwiczenia nie są atakiem, a ostrzeżenie cyber nie jest automatycznie wykonanym incydentem.
- **Obszar, którego dotyczy:** kraj, województwa lub obszar zagraniczny, ewentualnie nieustalony. Miejsce zdarzenia i zasięg skutków/instrukcji są różnymi danymi.
- **Wkład do RTA:** osobna ocena. Użyteczny dla mieszkańca wpis może mieć 0 punktów. Etykieta „Cyberbezpieczeństwo” nie nadaje punktów ani rosyjskiej atrybucji.

Dziennik zawiera cały opublikowany zbiór, oś grupuje jego wybrany podzbiór, mapa przedstawia rekordy z możliwą do pokazania lokalizacją. Przegląd podsumowuje te same rekordy. Wyróżnione wydarzenie lub zalecenie prowadzi do odpowiednich szczegółów; nie powstaje osobna lista „innych informacji”. Krótszy tytuł, jeśli potrzebny, jest wspólnym polem używanym wszędzie, a nie doraźną przeróbką na jednym ekranie.

Bez współrzędnych wpis pozostaje w Dzienniku i liście pod mapą. Nie wstawiamy fikcyjnego punktu w środku województwa. Flaga stolicy oznacza zasięg krajowy, nie lokalne zdarzenie. Liczba markerów/klastrów nie zastępuje liczby sygnałów. Tematy i regiony wymagają przeglądu; korekty tworzą nową wersję bez zmieniania starego raportu. Zasięg wydawcy „Polska” sam nie dowodzi ogólnopolskiego zasięgu konkretnego komunikatu.

## Przegląd: obecna siatka, nowa treść górnej sekcji

### Trzy wiersze komentarza

Proponowane etykiety: **Sytuacja:**, **Twój region:**, **Co zrobić:**. Trzy krótkie wiersze, bez osobnych kart, najwyżej jedno zdanie w każdym. W trybie makro drugi wiersz dotyczy Polski i regionu analizy. Nazwane pola i odwołania do sygnałów są przygotowywane i sprawdzane razem z raportem. Przegląd redakcyjny obejmuje treść, region, terminy i źródła. Frontend nie rozcina obecnego tekstu ani nie interpretuje Markdown wygenerowanego przez model.

Nie wymuszamy trzech twierdzeń, kiedy znamy tylko jedno. Miejsca w układzie są stałe, a brakujące dane mają prosty opis, np. „Brak lokalnych danych dla łódzkiego”. Brak aktualnych instrukcji i sprawdzone niewydanie nowych instrukcji to różne stany; tylko w drugim można napisać „Brak nowych zaleceń w tym raporcie”. Brak danych nie prowadzi do komunikatu „Nie musisz nic robić”.

Zalecenia ochronne wynikają z komunikatu właściwej instytucji i zachowują jego obszar oraz czas. LLM nie tworzy nakazu ewakuacji, zapewnienia o bezpieczeństwie ani decyzji finansowej z samego indeksu. Istotna aktywna instrukcja służb zachowuje pierwszeństwo także przy niskim RTA. Plan ma przyszły termin; odwołanie zastępuje instrukcję w bieżącym widoku bez kasowania historii.

### Region obok indeksu

Przełącznik `[Skala makro] [Region: łódzkie ▾]` jest wykonalny. Dla cywilów można zamiast „Skala makro” użyć „Cały obszar”, z opisem Polski i dotychczasowego regionu analizy. Nie przemianowujemy dotychczasowego wyniku na węższy indeks samej Polski.

Wybór województwa aktualizuje razem podpis i wynik RTA, pewność, komentarz, wskaźniki dziedzin, oś oraz mapę. Trend porównuje ten sam obszar. Indeks pochodzi z silnika, nie z sumowania punktów widocznych na mapie: obejmuje także wygaszanie, limity i przenoszenie wpływu między regionami.

Obliczenia regionalne istnieją, ale przed ich prezentacją trzeba uzupełnić przypisania i informację o kompletności. Krajowych 25% nie kopiujemy jako pewności każdego województwa. Przed udostępnieniem przełącznika trzeba ustalić zachowanie obecnego regionalnego `null` i ewentualne rozszerzenie zasady 0–100 z osobną pewnością na regiony. Krajowy v0.4 pozostaje liczbowy i nie jest blokowany przez tę pracę. Zero nie jest potwierdzeniem bezpieczeństwa.

Region może być zapamiętany lokalnie, bez konta i geolokalizacji. Komunikaty ogólnopolskie pozostają widoczne z taką etykietą. Nieustalonego zasięgu nie przypisujemy do wszystkich województw. Sygnał z sąsiedniego obszaru nie dostaje etykiety wybranego województwa tylko dlatego, że punktacja uwzględnia wpływ pośredni.

### Liczba sygnałów według tematu — uproszczona wersja początkowa

„Działania / Przygotowania” przenosimy do rozwijanych szczegółów indeksu. W ich miejscu: Lotnictwo, Cyber, Nawigacja — ikona i krótka wartość, bez kart. Układ zawija się na telefonie; odstępy 8/12/16 px. Rozbicie punktów nadal istnieje w metodyce i danych.

Uproszczenie zaproponowane przez użytkownika: w pierwszej wersji liczymy sygnały w danym temacie i wybranym obszarze. Rekomendacja: **ostatnie 7 dni do chwili raportu vs bezpośrednio poprzednie 7 dni**. Dwa równe okna po 168 godzin kończą się na zamrożonym `as_of`; ponowne otwarcie strony nie przesuwa ich względem danych. Daty i godziny prezentujemy w Europe/Warsaw. Nie porównujemy rozpoczętego tygodnia kalendarzowego z całym poprzednim tygodniem. Widok dzień do dnia można dodać później jako dwa analogiczne okna po 24 godziny.

Wspólna etykieta paska: **„Sygnały · ostatnie 7 dni”**. Pod liczbą pokazujemy zmianę liczbową względem poprzednich 7 dni, bez procentów. Przykłady demonstracyjne: „Lotnictwo: 12 · ↑ 3”, „Cyber: 5 · ↓ 2”, „Nawigacja: 7 · bez zmian”. Rozwinięcie pokazuje poprzednią liczbę, oba przedziały czasu i odnośniki do odpowiednich wpisów w Dzienniku. Indeks RTA pozostaje dobowy; pasek ma wyraźnie opisany własny okres.

Zasady liczenia:

1. Liczymy odrębne opublikowane sygnały z Dziennika, według tematu niezależnego od kategorii punktacji. Każdy wspólny identyfikator/epizod występuje najwyżej raz w danym temacie i okresie. Przedruk, kolejne źródło, aktualizacja i powtórzenie wpisu w następnym raporcie nie są nowym sygnałem.
2. O przypisaniu do okna decyduje `published_at`, czyli data publikacji materiału przyjęta dla sygnału, zgodnie z obecną osią czasu. Nie nazywamy tego liczbą ataków, które wydarzyły się w danym tygodniu. Oba okna liczymy według wiedzy i przejrzanych rewizji dostępnych w chwili raportu; nowy odczyt nie edytuje starych eksportów. Przedziały są rozłączne: poprzedni `[as_of−336h, as_of−168h)`, bieżący `[as_of−168h, as_of)`.
3. Sygnały bez daty pozostają w Dzienniku i są wskazane w szczegółach licznika jako „Bez daty”; nie dopisujemy im daty pobrania. Przy wielu tematach wpis może należeć do kilku liczników, dlatego sumy tematów nie przedstawiamy jako liczby odrębnych sygnałów całego raportu.
4. Oba okresy stosują te same reguły tematu i obszaru, w tym jawne traktowanie komunikatów ogólnopolskich. Przypisania lokalizacji nie powstają z domyślnego adresu wydawcy.
5. Zero po poprawnym odczycie to prawidłowa liczba. Przy poprzednim zerze działa zwykła różnica, np. `3 − 0 = +3`; nie potrzebujemy procentu. Brak historii porównawczej daje „Brak danych do porównania”, ale nie ukrywa znanej liczby z bieżącego okresu ani nie blokuje RTA.
6. Niepełne pobrania oznaczamy krótko: „Dane częściowe”. Gdy zmiana źródeł lub brakujące dni uniemożliwiają porównanie, zachowujemy dostępny licznik i nie pokazujemy strzałki sugerującej porównywalny spadek/wzrost. Szczegóły mogą wyjaśniać np. „W poprzednim okresie brakowało danych”. Nie jest potrzebna kalibracja norm ani zgodność klucza porównania wyniku RTA; potrzebna jest zgodność zbioru i reguł zliczania.

Pasek opisuje liczbę zarejestrowanych sygnałów. Regularny pomiar GNSS jest wpisem pomiarowym, nie kolejnym potwierdzonym atakiem; zmiana liczby pomiarów nie jest zmianą siły zakłóceń. Strzałki są neutralne kolorystycznie. Nie nadajemy etykiet „Anomalia”, „Rutynowe” ani „Poniżej normy” i nie zmieniamy punktacji. Pomiar natężenia poszczególnych zjawisk oraz badanie norm pozostają poza pierwszą wersją.

### Etykiety osi czasu

Neutralne etykiety: „Zachodniopomorskie”, „Cała Polska”, „Obwód lwowski”, „Obszar nieustalony”. Dla wielu obszarów najwyżej dwa i „+2 regiony” ze szczegółami. Zagregowana godzina lub dzień może dotyczyć wielu miejsc; nie nadajemy całej grupie obszaru pierwszego wpisu. Nazwy są wspólne z mapą i Dziennikiem.

Etykieta wskazuje obszar, nie kierunek zbliżania się zagrożenia. Nie narusza siatki ani czytelności tytułu. Oś nadal grupuje publikacje; data zdarzenia jest osobną informacją.

## Mapa Operacyjna: filtry → mapa → lista

Nagłówek, zwarty wiersz filtrów zawijany na telefonie, mapa, liczba wyników i lista tych samych sygnałów. Bez indeksu na tym ekranie.

**Obszar:** Flanka wschodnia, Cała Polska i wszystkie 16 województw. Flanka oznacza jawnie zdefiniowany zakres projektu z istotnym sąsiedztwem, nie zgadywany promień od użytkownika. Identyfikatory województw już są w `config/regions-v0.3.json`.

Liczba przy województwie dotyczy lokalnych sygnałów w wybranym okresie i temacie, np. `Łódzkie (0)`. Komunikaty ogólnopolskie pokazujemy dodatkowo, z osobną liczbą, aby „0 lokalnych” nie kolidowało z widocznym ostrzeżeniem dla całej Polski. Liczniki obejmują wpisy bez punktu na mapie; nie liczą powielonych raportów ani klastrów. Wszystkie województwa pozostają dostępne przy zerze. Nieudany odczyt nie tworzy zera.

**Okres:** Dzisiaj, Ten tydzień, Ten miesiąc, Ten kwartał, Ten rok. Tydzień od poniedziałku; miesiąc, kwartał i rok kalendarzowe; Europe/Warsaw. Rozpoczęty okres kończy się na dostępnych danych, pokazujemy przedział i datę raportu. Zachowujemy podstawę „Według daty publikacji”; dat nie dopowiadamy. Bezdatowe wpisy pozostają dostępne osobno jako „Bez daty”.

Mapa i lista używają identycznego zbioru po filtrowaniu. Podsumowanie może brzmieć „10 sygnałów · 7 z lokalizacją”. Kliknięcie wiersza wskazuje odpowiadający punkt, a punkt ten sam wpis. Brak współrzędnych nie usuwa wiersza z listy. Nie wracamy do kolorowania całych państw jako mapy zagrożenia.

Przejście z Przeglądu ustawia obszar Mapy zgodnie z wybranym regionem. Dalej filtry Mapy są jawne; powrót zachowuje wybór Przeglądu i nie zmienia po cichu indeksu krajowego. Przejście do Dziennika przenosi filtry. Okres Mapy filtruje sygnały, nie tworzy „rocznego RTA”. Archiwalny raport zachowuje swój wynik i datę.

Kwartał i rok wymagają odczytu historii, wyboru właściwych rewizji i usunięcia powtórzeń sygnału obecnego w wielu raportach. `/api/reports` jest katalogiem raportów, nie takim zbiorem. Krótsza historia otrzymuje informację np. „Dane dostępne od 10 września”; wcześniejsze miesiące nie są przedstawiane jako okresy bez zdarzeń. Uwzględniamy korekty, odwołania ostrzeżeń i połączenia epizodów. Aktywna instrukcja ochronna potrzebuje osobnego oznaczonego miejsca, jeśli filtr czasu ukrywa jej pierwotną publikację.

## Język

| Unikamy | Pokazujemy |
| --- | --- |
| „Brak oceny zmiany” | „Brak danych do porównania” |
| „Ten widok nie zawiera porównania pomiarów dla wspólnego obszaru i okresu…” | „Brak danych do porównania” |
| „To aktualizacja wiedzy o konkretnej kampanii; raport nie ustala wzrostu liczby ataków” | „CERT ostrzega przed fałszywymi wiadomościami podatkowymi” |
| „Normalnie” wywnioskowane z pustego zbioru | „Brak nowych sygnałów w wybranym okresie” — tylko po poprawnym odczycie |
| „Zagrożenie 0%” | „RTA 0/100” z informacją o pewności |

Nie dokładamy do każdej informacji zdania o procesie analizy. Opis mówi o wydarzeniu; metodyka jest dostępna w szczegółach, logi poza publicznym UI.

## Kolejność po akceptacji

1. **Wspólne dane i słownik.** Temat, rodzaj, obszar i daty. Przejrzeć reprezentatywne wpisy: CERT, Świnoujście, Łowicz, plan PAŻP, pomiar GNSS i ostrzeżenie z odwołaniem. Uzupełnić nowe oceny, nie zmieniając punktów dla naprawy filtra.
2. **Kontrakt publikacji.** Wersjonowane pola tematów, obszarów, komentarza, regionalnej kompletności i porównań. Zmiany obejmują `schemas/dashboard/report.schema.json`, `src/osint_dashboard/dashboard/contract.py`, generator komentarza i przegląd redakcyjny. Zachować odczyt starych raportów; nie dopisywać luźnych pól do ścisłego schematu.
3. **Jedna makieta na obecnej siatce.** Trzy wiersze komentarza, przełącznik, pasek dziedzin i etykiety; te same rekordy w każdym miejscu, bez nowych sekcji nad osią i mapą. Po wyborze zaktualizować `design.md`, `guidelines.md` i ewentualnie `theme.css`.
4. **Frontend i mapa.** `web/index.html`, `web/app.js`, `web/data.js`, `web/map.js`, `web/styles.css`: wspólne filtrowanie i prezentacja wpisu. Historia w warstwie publikacji i `hosting/worker.mjs` wymaga stronicowania i deduplikacji. Liczbowy widok regionalny udostępnić razem z ukończeniem danych regionalnych, nie wcześniej.
5. **Proste porównanie tygodniowe.** Wyliczyć liczbę odrębnych sygnałów tematu w dwóch kolejnych oknach po 7 dni, pokazać bieżącą liczbę i różnicę bez procentów. Sprawdzić powtórzenia, granice okien, zero i brak historii. Nie czekamy na kalibrację norm; ich badanie i pomiary natężenia zjawisk są poza pierwszą wersją.
6. **Odbiór → akceptacja → publikacja.** Sprawdzić eksport i odczyt, stare raporty, puste stany, okresy, regiony i mobile. Dopiero potem publikacja, bez powiadomień.

## Kryteria odbioru

- CERT jest widoczny pod Cyberbezpieczeństwem i otwiera ten sam wpis z każdego widoku; może nadal mieć 0 punktów.
- Łowicz otrzymuje obszar łódzkiego; źródło MON nie czyni go wydarzeniem w Warszawie.
- Wynik, pewność, komentarz i trend dotyczą tego samego obszaru i raportu. Pewności krajowej nie kopiujemy do województw.
- Brak zdarzeń, brak odczytu, brak porównania i odwołanie ostrzeżenia mają różne, krótkie komunikaty. Plan nie staje się wykonanym atakiem.
- Liczniki, mapa i lista używają jednego zbioru. Komunikaty krajowe, bezdatowe wpisy i brak współrzędnych nie giną bez informacji. Jeden sygnał w dziesięciu raportach nie staje się dziesięcioma zdarzeniami.
- „0” przy regionie oznacza zero pasujących wpisów, nie poziom bezpieczeństwa. Kwartał i rok pokazują rzeczywisty zakres historii.
- Pasek ma etykietę „ostatnie 7 dni”; oba okresy są równe i rozłączne. Aktualizacja starego sygnału nie tworzy nowego, a brak daty nie jest uzupełniany datą pobrania. Różnica działa również przy poprzednim zerze. Brak historii lub nieporównywalne pobrania nie są przedstawiane jako spadek; znana liczba nadal jest widoczna. Liczba pomiarów GNSS nie jest opisywana jako liczba ataków ani siła zakłóceń.
- Oś i mapa zachowują siatkę i proporcje. Przy 320 px kontrolki zawijają się, etykiety nie zasłaniają tytułów, działa klawiatura i dolna nawigacja.
- Nowy kontrakt nie psuje archiwum, zatwierdzania komentarza ani publikacji w Supabase.

## Stan wykonania oceny

Pierwsza ocena obejmowała kod, kontrakty, eksport i odtworzenie problemu filtra w przeglądarce. Następnie, na prośbę użytkownika, przygotowano jeden spójny prototyp na gałęzi `codex/ux-regional-context`.

### Prototyp — 02.10.2026

`ui/experiments/rta-overview-prototype.html` jest samodzielnym fragmentem do podglądu w rozmowie. Zachowuje układ Chronologia: duży indeks i komentarz, zwarty pasek trzech tematów, oś po lewej i mapa po prawej. Dane oraz wyniki regionalne są wyłącznie przykładami do testowania interakcji, opisanymi w interfejsie; nie pochodzą z publikacji live i nie dowodzą gotowości kontraktu regionalnego.

- Działają: wybór regionu, wspólny komentarz i indeks, liczniki dwóch kolejnych okien 7-dniowych, przejście do właściwych wpisów Dziennika i poprzedniego okresu, grupowanie osi, etykiety regionów, filtry mapy i lista tych samych sygnałów.
- Jeden zbiór przykładowych rekordów zasila wszystkie widoki. Przykładowe porównanie lotnictwa: 12 vs 9 wpisów; cyber: 5 vs 7; nawigacja: 7 vs 7. Odrębne identyfikatory reprezentują odrębne przykładowe sygnały. To nie pomiar rzeczywistego wzrostu aktywności.
- Wszystkie województwa są dostępne. Łódzkie pokazuje zero lokalnych wpisów w krótkim okresie i osobny komunikat ogólnopolski. Wpis bez daty jest dostępny przez filtr „Bez daty”; brak punktu nie usuwa wpisu z listy.
- Podkład i katalog stolic pochodzą z istniejących zasobów Natural Earth w `web/assets/`. Mapa korzysta z osadzonego D3 7.9.0 i geometrii 25 państw. Flagi krajowe nie udają lokalizacji incydentów. Nie ma żądań do zewnętrznych API ani połączenia z Supabase.
- Kontrolka projektowa pozwala obejrzeć stan „Brak danych do porównania”. Bieżące liczby pozostają widoczne. Raporty zawierają jedynie przejście do przykładowego podsumowania; pobierania i historii produkcyjnej nie przebudowywano.
- Sprawdzono w przeglądarce szerokości treści 320, 736 i 1024 px (bez przewijania w poziomie), jasny i ciemny wygląd, liczniki i listy porównywanych okresów, filtr CERT, wybór szczegółów z mapy i z Dziennika, skupisko dwóch wpisów, zamknięcie przez Escape, puste filtry, brak daty, brak historii oraz odtworzenie wyboru województwa po przeładowaniu. Indeks nie pojawia się jako główny element na Mapie, w Dzienniku ani Raportach. Nie zaobserwowano błędów JavaScript.

Podgląd jest do akceptacji. Pliki `web/`, metodologia, baza, publikowanie, harmonogram i hosting pozostają bez zmian. Nie pobierano nowych źródeł. Produkcyjnego Design Systemu nie przemianowano na zaakceptowaną nową wersję; aktualizacja wzorców nastąpi po wyborze użytkownika. Walidacja dotyczy prototypu, nie integracji nowych pól z silnikiem ani Supabase.

## Realizacja zaakceptowanego prototypu — 03.10.2026

Użytkownik zaakceptował koncepcję i poprosił o usunięcie podkreślenia
rekomendacji. Implementacja jest na `codex/ux-regional-context`, w `web/`,
z rzeczywistym odczytem opublikowanych raportów i bez danych demonstracyjnych
w interfejsie produkcyjnym. Zachowany prototyp w `ui/experiments/` nadal
oznacza wszystkie swoje dane jako przykładowe.

Dodano wspólny model sygnału, kotwiczoną historię, filtry obszaru i okresu,
liczniki tygodniowe, regionalny wynik i etykiety, listę pod mapą oraz nazwane
części nowych komentarzy. Krajowa pewność nie jest kopiowana do regionów;
regionalny null pozostaje brakiem oceny. Nie zmieniono punktacji ani progów.
Starsze komentarze pozostają pełnym tekstem w polu Sytuacja; ich brakujących
części nie dopisuje frontend. Rekomendacja jest zwykłą prozą bez podkreślenia.

Metadane geograficzne starszych raportów są niepełne: część wpisów pozostaje
bez przypisanego województwa lub punktu. Nowy przegląd może nadać jawne
`dashboard_context` z dowodami. Nie wykonano automatycznego przeglądu starej
historii ani jej publikacji. Obecna krótka/częściowa historia nie daje
wiarygodnych strzałek tygodniowych; stan ten jest obsłużony w interfejsie.

Publikacja tej zmiany jest osobnym krokiem po lokalnym odbiorze. Nie zmieniano
hostingu, domeny, harmonogramu ani danych w Supabase.

### Odbiór implementacji

- 369 testów Pythona, 17 testów JS/PostgreSQL i 14 testów warstwy hostingu
  przeszło. Sprawdzają między innymi dowody przypisań regionalnych, zatwierdzone
  części komentarza, rozłączne okna tygodniowe, korekty dat, deduplikację,
  stronicowanie historii, częściowy odczyt i zgodność starych raportów.
- Przeglądarka: 1440/736/390/320 px, jasny i ciemny wygląd, filtr regionu,
  liczniki i te same wpisy w dzienniku, CERT w Cyber, mapa z listą, powiększanie,
  szczegóły i Escape, brak daty, puste filtry, powrót fokusu oraz czytnik raportów.
- Rekomendacja nie jest przyciskiem ani linkiem i nie ma podkreślenia.
  Indeks nadal występuje tylko w Przeglądzie, a na telefonie działa dolna nawigacja.
- Nie wykonano ponownego przeglądu historycznych materiałów, więc m.in.
  przypisania Świnoujścia i Łowicza wymagają osobnych, udokumentowanych ocen.
  Nie oznaczamy ich jako ukończonych na podstawie samego tytułu publikacji.
