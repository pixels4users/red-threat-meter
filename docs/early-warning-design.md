# Wczesne ostrzeganie — doprecyzowanie projektu

Aktualizacja: 25.09.2026. Status: **dotychczasowy plan zaakceptowany; kontrakt obserwacji, pilotaż GPSJAM/belzhd, pilotaż jakości ADSB.lol i ograniczony audyt historii wdrożone**. Rozszerzenie o źródła pierwotne i metodologię v0.3 zostało zaakceptowane 25.09.2026; obliczenia v0.3 oraz PAŻP/AUP i RSO/ogólne wdrożono 29.09.2026. Pozostałe adaptery i detektor minutowy GNSS wymagają dalszej pracy. Strażnik jest odniesieniem architektonicznym, a dane pozyskujemy od wskazanych instytucji i wydawców. Wykonywalny zakres opisują [instrukcja GNSS/logistyki](early-warning-runbook.md), [instrukcja lotnictwa](aviation-runbook.md) i [audyt historii](aviation-history.md). Wagi RTB v0.3 pozostają osobne wobec pilotaży; nie uruchomiono harmonogramu, usług AI ani detektora anomalii.

Kolejna dostawa z 23.09 dodaje polskie tytuły i streszczenia, [porównanie GNSS na wspólnej siatce](gnss-reference-methodology.md) oraz [ocenę dostępu lotniczego](aviation-access.md). Mediana historii nie jest ustalonym poziomem normalnej aktywności. Przegląd agentowy obejmuje już wszystkie 10 pobranych publikacji; niezależne potwierdzenie twierdzeń pozostaje odrębne.

## Decyzja projektowa

Rozbudować system o osobną warstwę sygnałów wczesnych. Obecny RTB celowo wymaga mocnego potwierdzenia i przypisania RU/BY; dlatego sam nie wystarcza do wczesnego ostrzegania. Brak takiej atrybucji nie może ukrywać anomalii przed analitykiem. Warstwa wczesna powinna przyjąć sygnał o nieznanym sprawcy i kierować go do sprawdzenia, zachowując jego niepewność.

| Wynik dla użytkownika | Co opisuje | Warunek |
|---|---|---|
| Sygnały wczesne | Zaobserwowane odchylenia i doniesienia wymagające uwagi | Jawne źródło, czas dostępności, jakość i uzasadnienie; atrybucja może być nieznana |
| RTB | Potwierdzone, kwalifikujące się działania i przygotowania | Domyślny silnik v0.3; wcześniejsze odczyty zachowują v0.2 |
| Jakość pokrycia | Co rzeczywiście obserwujemy i gdzie brakuje danych | Aktualność, liczebność próby, kompletność i zależności źródeł |

Na początek sygnały wczesne otrzymują statusy: „nowe doniesienie”, „anomalia do sprawdzenia”, „pilny przegląd”, „wyjaśnione” albo „brak podstaw do oceny”. Nie dodajemy drugiej nieskalibrowanej liczby 0–100. „Pilny przegląd” jest priorytetem analitycznym, nie prognozą ataku. Sam raport o dużej możliwej wadze może trafić do pilnego przeglądu mimo pojedynczego źródła; etykieta nie zmienia się wtedy na „potwierdzone”.

**Wyprzedzający/opóźniony jest konkretny sygnał względem zdefiniowanego zdarzenia, nie cały serwis.** Telemetria pokazuje stan obecny i może poprzedzać inne zdarzenie; zdolność przewidywania wymaga pomiaru. Komunikat oficjalny może zawierać zapowiedź ćwiczeń lub ograniczeń, a publikacja społecznościowa opisywać transport sprzed miesięcy. Żadna z tych kategorii nie jest automatycznie ground truth.

## Weryfikacja propozycji źródeł

### GPSJAM i GNSS

GPSJAM publikuje agregaty 24-godzinne według UTC, aktualizowane raz na dobę. Czerwony obszar oznacza podwyższony udział samolotów raportujących niską dokładność nawigacji, nie identyfikację sprawcy ani dowód ciągłego zagłuszania. Kilka czerwonych dni nie potwierdza samoistnie `duration_over_24h`. Brak komórki może oznaczać brak obserwacji. [FAQ projektu](https://gpsjam.org/faq).

GPSJAM korzysta z raportów ADS-B z airplanes.live i ADS-B Exchange. **Wniosek projektowy:** wspólne pochodzenie pomiarów trzeba zapisać; dwóch produktów z tych danych nie uznajemy z góry za niezależne potwierdzenia. [Opis projektu](https://gpsjam.org/about).

Cel pilotażu: zmiana zasięgu i intensywności zakłóceń przy porównywalnym pokryciu. Potrzebne są dane liczbowe i liczebność próby, nie rozpoznawanie czerwieni ze zrzutu ekranu. **Wdrożenie:** sprawdzono publiczny manifest i CSV używane przez mapę; pobrano 30 dób z liczebnościami i flagami jakości. Manifest wskazuje zmianę zestawu dostawców 27.08.2026; porównania zachowują tę granicę. Nie jest to stabilne kontraktowe API ani ustalona licencja redystrybucji. Uzupełnieniem do sprawdzenia pozostaje **EUROCONTROL AUGUR**: oficjalny opis wymienia advisories, NOTAM-y GNSS, warunki kosmiczne i API; samego API nie testowano. [AUGUR](https://www.eurocontrol.int/online-tool/augur).

### Lotnictwo

Aktywność transportowa RU/BY i zmiany aktywności wsparcia NATO warto obserwować osobno. Przelot cysterny lub AWACS nie ujawnia zadania misji ani przyczyny decyzji dowódczej. NATO dokumentuje udział AWACS i KC-135 w ćwiczeniach, a także regularne patrole oraz ochronę wydarzeń. To konkretne alternatywy wobec hipotezy przygotowań do ataku. [Ćwiczenia Formidable Shield 2025](https://awacs.nato.int/media-center/press-releases/2025/nato-awacs-participates-in-largest-atsea-livefire-exercise-in-europe), [patrole i ochrona szczytu](https://www.nato.int/cps/en/natohq/news_215106.htm).

Mierzyć można zagregowaną obserwowaną aktywność według klas samolotów, regionu i czasu, przy stałej metodzie i kontroli pokrycia. Liczba wiadomości ADS-B nie jest liczbą lotów. Zanik odbioru lub brak nadawania oznacza brak obserwacji, nie brak lotu. E-3 i RC-135 pozostają odrębnymi klasami o innych zadaniach; z samej trasy żadnego z nich nie wyprowadzamy natężenia komunikacji przeciwnika. Nazwy typów z załącznika są kandydatami do klasyfikacji, a nie potwierdzeniem ich aktualnego rozmieszczenia lub dostępności.

ADS-B Exchange ma udokumentowane API. Oferta hobbystyczna podaje 10 USD/miesiąc i 10 000 zapytań; warunki historii, archiwizacji i konkretnego zastosowania trzeba potwierdzić przed wyborem. Nie zakupiono dostępu. [Developer Hub](https://adsbexchange.com/community/developer-hub/), [dokumentacja API](https://www.adsbexchange.com/api/aircraft/v2/docs).

**Wdrożenie 24.09:** kolektor ADSB.lol zapisuje cztery odpowiedzi regionalne na ręczną próbę, usuwa powtórzenia identyfikatorów i pokazuje jakość oraz luki w siatce 1°. Rozdziela czas pomiaru i pobrania, nie uznaje kodów typów ani flag wojskowych za zweryfikowanego operatora. Zasięg zapytania nie mierzy pokrycia odbiornikami. Historia jest na razie krótką serią prób; bez odniesienia dla aktywności RU/BY i NATO. [Kontrakt i obsługa](aviation-runbook.md).

**Audyt historii 24.09:** trzy okna po 30 minut, z dni 22–24.09, zachowano w osobnej serii. Zmierzono rozmiar, kompletność przedziałów, odrzucenia rekordów i różnice zbiorów identyfikatorów wobec trzech próbek API. Format historii nie zawiera dokładnego czasu każdej pozycji, kodów typu samolotu ani flag wojskowych. Próbki historii oraz API nie tworzą wspólnego trendu; nie uzupełniamy historycznych klas dzisiejszymi oznaczeniami. [Metoda i ograniczenia](aviation-history.md).

### Logistyka i Telegram

**Hajun nie jest aktualnym strumieniem do podłączenia:** projekt ogłosił zatrzymanie pracy w lutym 2025. To kandydat na archiwum do badań historycznych, z zachowaniem pierwotnych dat dostępności. [Komunikat projektu](https://t.me/Hajun_BY/8378), [archiwum](https://hajun.info/).

**belzhd.info działa w pilotażu przez główny RSS:** pobrano 10 publikacji, w tym cztery z rubryki przewozów wojskowych. Kanał tematyczny zwrócił 403; osobno publikowany główny RSS jest dostępny. Nie podłączono Telegrama ani nie potwierdzono prawdziwości wszystkich doniesień i pełności obserwacji kolei. Część materiałów opisuje długie, zakończone okresy: data publikacji nie oznacza świeżego transportu. Strona i kanał mają wspólnego wydawcę. [Publikacje wydawcy](https://belzhd.info/category/news/), [RSS](https://belzhd.info/feed/), [kanał](https://t.me/s/belzhd_live).

Integracja Telegram → LLM ma dwa konkretne warunki. Bot odbiera posty kanałów, których jest członkiem, a `messages.getHistory` jest metodą dla kont użytkowników. Dostęp techniczny nie oznacza prawa do dowolnego użycia treści. [Bot FAQ](https://core.telegram.org/bots/faq), [getHistory](https://core.telegram.org/method/messages.getHistory).

Aktualne warunki Telegrama ograniczają zbieranie i wykorzystanie treści do wdrażania AI; opisują wyjątki wymagające odpowiednich zgód. Dlatego nie zakładamy, że wystarczy klucz API, aby uruchomić proponowany automat. Najpierw ustalić dozwolony sposób pozyskiwania i przetwarzania. W przypadku belzhd można zacząć od osobno publikowanych materiałów WWW, sprawdzając warunki wydawcy. Nie jest to zgoda na kopiowanie Telegrama przez pośrednika. [Warunki API, pkt 1.5](https://core.telegram.org/api/terms), [Content Licensing](https://telegram.org/tos/content-licensing).

LLM może proponować tłumaczenie i strukturyzację dopuszczonych materiałów. Zachowujemy oryginał, wersję tłumaczenia, niepewność liczby i miejsca; nie zamieniamy „wiele wagonów” na liczbę. Geokodowanie nazwy bez rozstrzygnięcia niejednoznaczności daje region/nieznaną geometrię, nie pozornie dokładny punkt. Pilotaż dotyczy publikacji i agregatów; nie wymaga identyfikowania informatorów ani wysyłania wiadomości do nich.

### FIRMS / Sentinel

NASA opisuje FIRMS jako detekcje pożarów i anomalii termicznych; VIIRS ma piksel około 375 m, MODIS około 1 km, a chmury ograniczają obserwację. Małe, intensywne źródło może być wykryte wewnątrz piksela — rozdzielczość nie oznacza minimalnej powierzchni pożaru. **Wniosek projektowy:** detekcja nie rozpoznaje namiotu, kuchni polowej czy silnika; nie budujemy na niej automatycznego detektora obozów. Potrzebna jest kontrola źródeł przemysłowych, pogody i innych obrazów. [Opis NASA](https://firms.modaps.eosdis.nasa.gov/map2/).

Sentinel Hub jest usługą dostępu, a znaczenie pomiaru zależy od sensora. Sentinel-2 ma pasma widzialne, NIR i SWIR; nie jest kamerą TIR mierzącą temperaturę namiotów. Sentinel-3 SLSTR ma termalne piksele rzędu 1 km. Dane satelitarne proponujemy jako późniejszą warstwę weryfikacji zmian przestrzennych. [Sentinel-2 MSI](https://step.esa.int/main/wp-content/help/versions/12.0.0/snap-toolboxes/eu.esa.opt.opttbx.s2msi.reader/Sentinel2Overview.html), [Sentinel-3 SLSTR](https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-3/Instruments).

FIRMS ma API wymagające bezpłatnego MAP_KEY. Nie utworzono klucza ani kolektora. [Area API](https://firms.modaps.eosdis.nasa.gov/api/area/).

### Doniesienia lokalne, morze i alarmy lotnicze

Publiczne doniesienia o pożarach, awariach, zakłóceniach transportu, cyberincydentach i aktywności morskiej mogą inicjować przegląd. Rejestr powinien zawierać konkretne wydawnictwa i kanały, historię oraz sposób pozyskania. Ogólne „lokalne grupy VK/Telegram” lub „porty Skandynawii” nie są jeszcze specyfikacją źródła.

Trzy pożary w trzech państwach uzasadniają sprawdzenie wspólnego wzorca. Nie wystarczają do automatycznego skoku RTB ani przypisania RU/BY. Trzeba uwzględnić częstość zwykłych zdarzeń, zwiększenie liczby monitorowanych portali, duplikaty i alternatywne przyczyny. Analogicznie sam statek w pobliżu kabla lub start bombowca nie dowodzi planu sabotażu ani przyszłego naruszenia polskiej przestrzeni. Sygnały dotyczące Ukrainy zachowują osobny obszar i hipotezę skutków dla Polski.

### Rozszerzenie inspirowane Strażnikiem — źródła pierwotne

W [rejestrze z 25.09.2026](sources.md#rozszerzenie-zrodel-25-09-2026) wskazano bezpośrednie źródła i rzeczywisty zakres ich sprawdzenia. Strażnik jest odniesieniem architektonicznym; nie pobieramy jego punktacji, front-endu ani NEPTUN jako danych. Bezpośredni ADSB.lol pozostaje jedynym działającym strumieniem lotniczym tego pilotażu.

| Rodzina | Kandydaci / rozszerzenie | Fakt, który wolno wyprowadzić |
|---|---|---|
| PAŻP | `pansa_airspace`: ADHOC, R, D, NPZ z AUP/UUP i statusów wykorzystania | Zmiana planu albo potwierdzona aktywacja, z rozróżnieniem obu; hipoteza przygotowań obronnych wymaga kontekstu i odniesienia |
| Ukraińskie OSINT | `ua_air_force_public`, `ua_monitor_public`, `ua_vanek_public` | Publikacja o zagrożeniu lub odwołaniu, z czasem i niepewnością; priorytet dla obwodów lwowskiego i wołyńskiego, bez domniemanej telemetrii radarowej |
| Ostrzeżenia ludności | `rso_public` i `rcb_alert_semantics`, rozszerzające istniejący kolektor `rcb` | Treść, obszar i stan oficjalnego komunikatu; RSO/gov.pl/media mogą dystrybuować ten sam alert |
| Bałtyk | LRT, LSM, ERR oraz komunikaty sił zbrojnych LT/LV/EE | Własne ustalenia wydawcy albo wskazane źródło pierwotne o zdarzeniu lotniczym, morskim, infrastrukturalnym lub GNSS |

Nazwy i klasy nie zastępują dowodów. NPZ dotyczy ograniczeń planowania; strefa nie musi mieć celu wojskowego. Sygnał PAŻP dostaje status `routine_status=unknown`, dopóki nie ma odpowiedniej historii. Media bałtyckie powtarzające ten sam komunikat mają wspólne pochodzenie. „Baltic Jammer” jest hasłem wyszukiwania, nie ustaleniem sprawcy.

Każda integracja przechodzi osobno: ustalenie bezpośredniego dostępu → małe pobranie → pomiar opóźnienia i kompletności → zachowanie rewizji/odwołań → przegląd pochodzenia → polski opis. Nie uruchamiać adaptera na podstawie wpisu w rejestrze. Obecny odczyt LRT jest zablokowany; nie zastępuje go pośrednik. Dostęp i przetwarzanie Telegrama podlegają opisanym wyżej warunkom.

## Specyfikacja nowego przepływu

**Pozyskanie → zapis obserwacji → kontrola jakości i duplikatów → odniesienie → anomalia → przegląd → ewentualna kwalifikacja do RTB.**

W zaakceptowanej v0.3 po przeglądzie dochodzą: **ustalenie epizodu i zależności → waga zależna od wieku → ograniczony bonus korelacji/fali → ograniczenie kampanii → osobna projekcja regionalna → limity kategorii i indeksów → bramka priorytetu**. Wzory, parametry i kolejność są zdefiniowane w [metodologii](methodology.md#wygaszanie-regiony-i-korelacja), bez drugiej, rozbieżnej tabeli wag w tym dokumencie.

Dane sensorowe powinny dostać osobną tabelę obserwacji i własny kontrakt. Nie udajemy, że pomiar liczbowy jest cytatem z artykułu. Proponowany rekord zawiera:

- czas pomiaru/zdarzenia, czas publikacji, pierwszy moment dostępności i czas pobrania; daty nieustalone pozostają jawne;
- źródło, wersję surowych danych, identyfikator dokumentu/pomiaru i jego pierwotne pochodzenie;
- obszar oraz dokładność lokalizacji; wartość, jednostkę i mianownik pomiaru;
- pokrycie, liczebność próby, brakujące interwały, opóźnienie i status integralności źródła;
- definicję i wersję odniesienia oraz detektora, wynik porównania i jawne ograniczenia;
- alternatywne wyjaśnienia, status przeglądu, grupę zależności źródeł i powiązany event_key, jeśli ustalono;
- osobny status atrybucji oraz odnośniki do późniejszego potwierdzenia lub sprostowania.

Rozszerzenie kontraktu v0.3 powinno zachować również `episode_key`, składowe `event_key`, `origin_id` i grupy zależności, identyfikator/rewizję strefy lub alertu, `valid_from/until`, `supersedes`/odwołanie, przedział niepewności czasu, rozróżnienie planu i wykonania, profil wygaszania oraz wersje odniesienia, korelacji i grafu. Wyjście zawiera `base_weight`, `decay_factor`, przesłanki i składniki `synergy_factor`, wagę przed/po limitach, wkład bezpośredni/przeniesiony i powody wstrzymania czerwonego. Import przyjmuje `assessment_v03` i `official_warning`; dokładne nazwy pól i rozbicie wyniku podaje [wdrożenie v0.3](v0.3-implementation.md).

Sygnał istnieje także wtedy, gdy RTB jest `null`. Brak bieżącego odczytu jednej rodziny danych nie usuwa poprawnych obserwacji z innych rodzin; obok pokazujemy brak pokrycia. Nowe źródła początkowo działają jako obserwacyjne, bez dodawania wszystkich do globalnej bramki kompletności RTB.

Reguły przeglądu muszą umożliwiać pojedynczy pilny sygnał o wysokich potencjalnych skutkach, ale wymagają jawnego oznaczenia niepotwierdzenia. Zbieżność różnych rodzin pomiarów może zwiększać priorytet dopiero po sprawdzeniu czasu, obszaru i wspólnego pochodzenia. Reakcja NATO i wiadomości o tym samym uderzeniu mogą być skutkami jednego zdarzenia; nie są automatycznie dwoma dowodami przygotowań.

### Trzy mechanizmy i granice zastosowania

- **Wygaszanie:** profil taktyczny 30 minut pełnej wagi i 30 minut spadku; strukturalny 48 godzin pełnej wagi i 168 godzin spadku. Dobowy lub tygodniowy rytm raportu nie jest nowym okresem liczenia tego samego incydentu. Odwołania i rzeczywisty czas dostępności mają pierwszeństwo przed samym upływem czasu.
- **Regiony:** przeniesienie 40% na pierwszy i 16% na drugi krąg dotyczy potwierdzonego bezpośredniego zagrożenia kinetycznego. Najkrótsza droga, jeden wkład epizodu na region, brak sumowania ścieżek i powrotnego zwiększania indeksu ogólnego. Warszawa ma widok mazowieckiego, Łódź łódzkiego; role decyzyjna i logistyczna są kontekstem, bez stałego bonusu lub rabatu miasta.
- **Korelacja i fala:** pełna triada GNSS/PAŻP/OSINT zwiększa wagę epizodu o 50%, a rozpoznana fala co najmniej trzech odrębnych obiektów o 25%; łączny mnożnik nie przekracza 1,75. Trzy portale, które powielają jeden meldunek, nie spełniają żadnego z tych warunków. Bonus nie nadaje atrybucji RU/BY ani nie obchodzi progów jakości.

**Bieżący pilotaż nie może uruchomić triady taktycznej.** [GPSJAM](gnss-reference-methodology.md) ma krok dobowy i nie ma zatwierdzonego detektora; brak pomiaru pozwalającego powiązać GNSS z 30-minutowym epizodem. Czas pobrania nie naprawia tej luki. Do tego czasu wynik korelacji to `not_assessed`, bez bonusu, z dobowym GNSS w kontekście strukturalnym. Podobnie nie łączymy historii mapy ADSB.lol z bieżącymi próbkami API w jeden trend.

Sam wynik ponad 60 nie wystarczy do czerwonego w metodologii v0.3: wymagana jest dodatkowa bramka niezależnych, bezpośrednich dowodów. Trzy klasy RCB/RSO opisują treść oficjalnej instrukcji, a nie kolor modelu. Autentyczne zalecenie ochronne i jego odwołanie pozostają widoczne także przy niewyliczonym RTB. Dokładną regułę zawiera metodologia.

## Odniesienie i ocena skuteczności

Roboczy pilotaż: zebrać 30–90 dni dostępnej historii, a przy sezonowości również dłuższe porównanie. To zakres zbierania materiału do oceny, nie gwarancja wystarczającej próby. Rzadkie zdarzenia mogą wymagać znacznie dłuższej obserwacji. Porównywać te same regiony, pory, pokrycie i definicje miar, uwzględniając ćwiczenia. Można sprawdzić mediany, kwantyle lub odchylenia odporne na wartości skrajne; progów nie ustalamy przez intuicyjne dopasowanie do głośnego przypadku.

Przed testem określić wynik, który chcemy przewidywać, np. potwierdzone naruszenie przestrzeni NATO, istotne zakłócenie infrastruktury lub udokumentowaną zmianę aktywności wojskowej. Te wyniki mają osobne definicje; żaden nie jest równoznaczny z rozpoczęciem wojny. Horyzonty 24 godziny, 72 godziny, 7 dni i 28 dni są **propozycjami okien badania**, nie ustalonym czasem wyprzedzenia danych. Brief strategiczny może nadal obejmować 14–42 dni.

Oceny tworzyć wyłącznie z informacji dostępnych w chwili prognozy. Raport o przygotowaniach z 2022 r. opublikowany później nie dowodzi, że system mógł ostrzec w 2022 r. Zapisać hipotezę i czas jej wygaśnięcia przed wynikiem. Oddzielić materiał do strojenia od późniejszego okresu sprawdzenia.

Mierzyć: opóźnienie źródła i całego procesu; wyprzedzenie względem czasu zdarzenia, nie tylko oficjalnego komunikatu; odsetek trafnych ostrzeżeń, przeoczonych zdarzeń, fałszywych alarmów i nieocenialnych przypadków. Okna, które jeszcze nie minęły, pozostają otwarte. Brak komunikatu nie daje automatycznej etykiety „nic się nie wydarzyło”. Późniejsze dowody mogą zmienić ocenę wyniku z zachowaniem historii.

## Kolejność wdrożenia i stan

1. **Kontrakt obserwacji i lista sygnałów wczesnych — wdrożone.** Oddzielono pomiar od oceny; zachowano niepewność, źródła, czas obserwacji/publikacji/dostępności/pozyskania. Nieustalone czasy są jawne. Działa historia, kontrola jakości, ręczny import ocen i raport.
2. **Dwa strumienie pilotażowe — GPSJAM i RSS belzhd działają.** Historia 30 dób i 10 publikacji, powtórny przebieg bez duplikatów. Dostępne dane nie stanowią pełnej obserwacji regionu; prawa redystrybucji są nieustalone, API AUGUR nadal niepodłączone. Nadal potrzebne są niezależne źródła potwierdzające.
3. **ADS-B: pilotaż API i ograniczony audyt historii wdrożone.** Rzeczywiste regionalne próbki, trzy półgodzinne okna historyczne, archiwa, odtwarzanie offline i polskie raporty. Historia i API pozostają oddzielne z powodu odmiennych reguł próbkowania. Kolejne badanie obejmie różne pory i dni, zmienność źródła oraz historycznie poprawną klasyfikację; ta próba nie kalibruje alarmu. Jednorazowy test OpenSky i oceny płatnych wariantów są osobne; nie zakupiono dostępu. [API](aviation-runbook.md), [historia](aviation-history.md).
4. **Porównanie GNSS wdrożone; detektory i rejestr hipotez pozostają dalszą pracą.** Działa opisowa zmiana na wspólnych komórkach w bieżącej epoce dostawców oraz cztery warianty minimum próby. Wciąż potrzebne są etykiety wyników, kalibracja i walidacja czasowa przed automatycznym priorytetem. Nie stroić systemu do samego wzrostu liczby postów.
5. **Kolejne domeny:** konkretne media lokalne, źródła morskie/AIS i weryfikacja satelitarna po próbnym sprawdzeniu jakości. Ograniczyć początkową liczbę strumieni, aby każdy miał kontrolowany zakres i opóźnienie.

Rozszerzenie z 25.09 zostało zaakceptowane. W zakresie przyszłego wdrożenia danych: sprawdzić małe próbki PAŻP i RSO oraz wykorzystać istniejące materiały RCB do klasyfikacji; następnie testować bezpośrednich wydawców bałtyckich i dopuszczony dostęp do kanałów ukraińskich. Wdrożenie heurystyk wymaga wersjonowanego kontraktu i trybu obliczeń porównawczych, testów przypadków z metodologii oraz walidacji czasowej. Minutowa korelacja GNSS pozostaje zależna od odpowiedniego źródła i detektora. Nie tworzymy jej przez sztuczne zwiększenie częstotliwości danych dobowych.

Osobny następny krok uzgodniony z użytkownikiem to projekt dashboardu i sposobu zasilania frontendu. Akceptacja metodologii nie rozpoczyna tego etapu ani nie oznacza uruchomienia wymienionych integracji.

Do wyboru przed płatnym wdrożeniem pozostają budżet dostępu i oczekiwana szybkość powiadomień. Obecny wariant to działający lokalny pilotaż bez nowych opłat; dzienny produkt nie obsłuży ostrzegania w ciągu minut, a ręczne próbki lotnicze nie są ciągłym monitoringiem. Dalsza praca obejmuje porównywalną historię, detekcję i walidację oraz kolejne domeny. Szczegóły kontraktów: `docs/early-warning-runbook.md` i `docs/aviation-runbook.md`.

## Nowe materiały lokalne

Podczas przeglądu pojawiły się `skills/track-military-flights/SKILL.md` oraz `skills/geostrategy-skills/skill.md`. Sprawdzono ich treść jako materiały projektu; nie uruchamiano opisanych usług i nie zmieniano tych plików.

- `track-military-flights` opisuje dostęp przez WorldMonitor i wymóg klucza. Późniejszy przegląd OpenAPI wykazał, że filtry operatora i typu są oznaczone jako ignorowane; opis dostawców także wymaga aktualizacji względem dokumentacji serwisu. Wyniki zapisano osobno w `docs/aviation-access.md`, bez modyfikowania dostarczonego skilla. Nie jest to działająca integracja ani zweryfikowany detektor zagrożeń.
- `geostrategy-skills` jest instrukcją analityczną. Wymóg przypisywania prawdopodobieństw scenariuszom trzeba dostosować do eksperymentalnego statusu projektu; nie wprowadza on skalibrowanych prognoz. Ogólne paradygmaty strategiczne pozostają hipotezami pomocniczymi, bez automatycznych punktów RTB.
