# Metodologia RTB v0.3

**Wersja `rtb-v0.3`, zaakceptowana 25.09.2026.** To obowiązująca specyfikacja analityczna dla dalszego rozwoju projektu, eksperymentalna i bez kalibracji prognostycznej. Akceptacja obejmuje źródła pierwotne i reguły poniżej; nie oznacza zakończenia integracji ani wdrożenia nowych obliczeń.

| Element | Wersja / stan |
|---|---|
| Obowiązująca metodologia | `rtb-v0.3`, zaakceptowana specyfikacja |
| Działający silnik i wydania | `rtb-v0.2` w `config/scoring-v0.json`; nowe heurystyki jeszcze niewdrożone |
| Reguły dotychczasowych obliczeń | [Metodologia v0.2](archive/methodology-v0.2.md) i `config/archive/scoring-v0.2.json` |
| Rozszerzenie źródeł | Zaakceptowane do integracji; dostęp i wdrożenie każdego adaptera mają osobny status |

Źródła i status dostępu: [rejestr kandydatów](sources.md#rozszerzenie-zrodel-25-09-2026). Dane pozyskujemy bezpośrednio od instytucji i wydawców; Strażnik jest odniesieniem architektonicznym, nie dostawcą danych. ADS-B pozostaje w istniejącym strumieniu ADSB.lol. Wersja i hash reguł w każdym wydaniu opisują faktycznie użyty silnik; sama akceptacja dokumentacji nie zmienia etykiety wcześniejszych ani nowych wyników v0.2.

## Cel i znaczenie

RTB opisuje nasilenie potwierdzonych działań RU/BY oraz sygnałów przygotowań wojskowych istotnych dla Polski i wschodniej flanki NATO. Wspiera przegląd Indicators & Warnings. Nie mierzy prawdopodobieństwa wojny ani zamiaru ataku. Zdolność, intencja i wystąpienie zdarzenia są osobnymi ustaleniami. Baza i punkty nie mają empirycznej interpretacji procentowej.

Wynik rozdziela dwa wkłady: `hostile_activity` (pozostałe kategorie) i `preparation` (logistyka/medycyna oraz aktywność lotnicza RU/BY). Wkłady pokazuje się po limitach kategorii, bez bazy. Przy limicie całego indeksu 100 suma wkładów plus baza może przewyższać wynik. Przy niekompletnych danych wkłady służą wyłącznie diagnostyce.

Podstawowy zakres punktacji obejmuje PL, LT, LV, EE, CZ, SK, HU, RO, BG, DE, FI, SE. Szczególne zakresy kategorii podano niżej. Obserwacje mogą obejmować szerszy region, w tym Ukrainę i zachodnią Rosję, bez automatycznego naliczania punktów. To roboczy zakres; obecne kolektory skupiają się na Polsce i nie zapewniają pełnego pokrycia tych państw.

## Czas i scenariusze

W v0.3 wkład zależy od wieku zdarzenia w chwili odcięcia, według [funkcji wygaszania](#wygaszanie-regiony-i-korelacja). Profil taktyczny utrzymuje pełną wagę przez 30 minut i wygasa przez kolejne 30 minut; strukturalny ma 48 godzin pełnej wagi i 168 godzin spadku. Czasy pobrań i ocen zapisujemy w UTC. Data publikacji nie zastępuje daty zdarzenia, a ponowne pobranie nie odświeża jego wieku. Dotychczasowe siedem dni kalendarzowych pozostaje wyłącznie regułą wykonywaną przez silnik v0.2.

Dla trwałej aktywności nowy rekord wymaga odrębnej udokumentowanej zmiany, własnej daty oraz związku z wcześniejszą kampanią. Kontynuację bez nowego faktu opisujemy jako kontekst. Raport tygodniowy jest docelowym rytmem analizy; harmonogram nie jest jeszcze uruchomiony.

Interpretacja strategiczna używa roboczego horyzontu 14–42 dni. Scenariusz zawiera warunki, dowody, kontrargumenty i sygnały rozstrzygające. Nie generujemy z RTB liczbowej prognozy ani automatycznej oceny szczebla eskalacji. Skrypt tworzy raport danych; interpretację uzupełnia analityk według `docs/templates/analytical-brief.md`.

## Punktacja i kryteria

`RTB = min(100, 10 + suma wkładów po limitach kategorii)`, wyłącznie po przejściu kontroli kompletności. W v0.3 wkład obejmuje wygaszanie i kwalifikowany mnożnik epizodu; wynik regionalny również współczynnik propagacji. Dokładna kolejność jest podana [niżej](#wygaszanie-regiony-i-korelacja). Zero zakwalifikowanych punktów daje bazę 10, co nie dowodzi bezpieczeństwa.

W każdej kategorii wymagamy potwierdzenia wystąpienia, daty, kraju i atrybucji RU/BY. Dla przygotowań atrybucja identyfikuje operatora sił lub infrastruktury, a nie zamiar ataku. Nieustalony sprawca oznacza obserwację poza punktacją, nawet gdy samo zdarzenie zostało potwierdzone.

| Kategoria / klucz | Punkty bazowe / limit w odczycie | Zakres i dodatkowe kryteria |
|---|---:|---|
| Logistyka lub medycyna wojskowa / `military_preparation` | 15 / 30 | Białoruś albo obwód królewiecki; `logistics_or_medical_change`, `baseline_anomaly`, `operational_relevance`, `routine_explanation_checked`; dla RU także `kaliningrad_oblast` |
| Sabotaż / `sabotage` | 10 / 30 | Zakres podstawowy; `intentional_action`, `critical_infrastructure` |
| Eksplozja w zakładzie zbrojeniowym / `arms_explosion` | 8 / 24 | Zakres podstawowy; `explosion_confirmed`, `arms_facility` |
| Naruszenie przestrzeni NATO / `airspace_breach` | 5 / 25 | Zakres podstawowy; `nato_airspace_breach` |
| Anomalia lotnicza RU/BY / `air_activity` | 4 / 12 | Zakres podstawowy, Białoruś, obwód królewiecki; `baseline_anomaly`, `military_activity`; dla RU także `kaliningrad_oblast` |
| Cyberatak / `cyberattack` | 3 / 12 | Wyłącznie Polska/Litwa; `large_scale`, `target_banking_or_government` |
| Presja graniczna / `border_pressure` | 3 / 9 | Polska/Białoruś i granica PL–BY; `baseline_increase`, `pl_by_border` |
| Zakłócenia GPS / `gps_jamming` | 2 / 8 | Zakres podstawowy; `duration_over_24h` |

Każde spełnione kryterium wskazuje własne dowody typu `criterion`; jeden fragment może uzasadniać kilka kryteriów, jeśli rzeczywiście zawiera odpowiednie ustalenia. Sam szpital, transport lub pożar nie wystarcza. Uderzenie w obwodzie lwowskim nie jest naruszeniem przestrzeni NATO. Ćwiczenia lub loty obronne NATO pozostają kontekstem.

Dla anomalii analityk podaje miarę, okres odniesienia, wartości porównania, źródło i ograniczenia obserwacji. Powinien sprawdzić ćwiczenia, rotację, sezonowość i zmianę dostępności danych. Gdzie jest to możliwe, warto zacząć od co najmniej 30 dni danych i porównania ze zbliżonymi ćwiczeniami; to zalecenie badawcze, nie automatyczny próg. Brak podstawy porównania oznacza niespełnione kryterium. System nie oblicza jeszcze anomalii z danych telemetrycznych.

`routine_explanation_checked` oznacza zapisanie konkurencyjnego wyjaśnienia i powodów, dla których pozostaje istotna zmiana ponad zwykłą aktywność. Nie oznacza dowiedzionego zamiaru ataku. Sama etykieta „sprawdzono” bez treści dowodu jest niewystarczająca analitycznie.

Jedno zdarzenie ma stabilny `event_key`, jedną kategorię i najwyżej jedną aktualną rewizję. Wiele publikacji może wskazywać to samo zdarzenie; jedna publikacja może opisywać kilka odrębnych zdarzeń. Tożsamość ustala analityk. Tego samego lotu nie punktujemy raz jako logistyki, a drugi raz jako anomalii lotniczej. Powtórzenie pobrania identycznej treści nie tworzy nowego materiału.

Wspólny `campaign_id` ogranicza punktowanie do jednego epizodu w danej kategorii. V0.3 wybiera najwyższy aktualny wkład po wygaszaniu i synergii, przed projekcją regionalną; remis rozstrzyga `event_key`. Działający kod v0.2 nie rozpoznaje automatycznie wspólnego zdarzenia pod różnymi kluczami lub kategoriami. Limity kategorii ograniczają nadmierny wkład jednej kategorii, lecz nie naprawiają błędnego przeglądu. Surowa suma, wkłady i wykluczenia pozostają dostępne do audytu.

## Próg i priorytet geograficzny

Wynik **ściśle ponad 60** kieruje do pilnego przeglądu analitycznego. Czerwony priorytet v0.3 wymaga dodatkowo opisanej niżej bramki niezależnych, bezpośrednich dowodów. Próg pozostaje roboczy, z `calibrated=false`, bez przypisywania wysokiego prawdopodobieństwa wojny. Wynik 60 nie przekracza progu. Przy `score: null` status wynosi `not_assessed`; brak oceny nie jest sygnałem uspokojenia. Działający silnik v0.2 zapisuje samo `alert.status=analyst_review_required`, bez nowej bramki koloru. Nie działa wysyłanie powiadomień.

Obszary w `config/strategic-areas.json` nadają priorytet przeglądowi, bez własnego mnożnika punktów ani arbitralnego promienia bliskości. `strategic_context`, jeśli występuje, wymaga identyfikatorów obszarów, uzasadnienia i dowodów lokalizacji. Samo skojarzenie nazwy miejsca z ważną bazą nie wystarcza. Regionalna propagacja v0.3 ma osobne reguły 40% / 16% i nie nadaje punktów za samą obecność obiektu strategicznego. Silnik v0.2 nadal nie oblicza wyników regionalnych.

GeoJSON używa WGS84 i kolejności `[długość, szerokość]`. Punkt wymaga dowodu lokalizacji i jawnej dokładności. W przeciwnym razie geometria ma wartość `null`; nazwa regionu nie staje się jego środkiem. Aktualna implementacja nie ma automatycznego geokodera. Lokalną bazą jest SQLite, bez wymogu PostGIS.

## Standard dowodowy

Oddzielnie dokumentujemy wystąpienie, przypisanie operatora/sprawcy, czas, lokalizację i kryteria. Wnioski o intencji, kontroli refleksyjnej i maskirowce są hipotezami do sprawdzenia, a nie domyślną kwalifikacją.

| Status | Znaczenie |
|---|---|
| `unverified` | Brak wystarczającego potwierdzenia |
| `confirmed_primary` | Potwierdzenie danego twierdzenia w źródle pierwotnym |
| `corroborated` | Co najmniej dwa źródła o niezależnym pochodzeniu |
| `disputed` | Zapisane dowody sprzeczne |
| `refuted` | Twierdzenie uznane za obalone, z uzasadnieniem |

Punktacja przyjmuje `confirmed_primary` lub `corroborated` dla wystąpienia i atrybucji. Komunikat o zatrzymaniu lub zarzutach nie jest automatycznie dowodem wszystkich zarzucanych czynów. Dwa portale cytujące MON lub tę samą agencję mają wspólny `origin_id`. Ocena niezależności pozostaje zadaniem analityka. Brak potwierdzenia nie oznacza dezinformacji.

Walidator sprawdza obecność cytatu w zapisanym materiale, identyfikatory i typy referencji, źródła oraz deklarowane statusy. Nie rozstrzyga semantycznego znaczenia cytatu, prawdziwości niezależności, skali anomalii ani intencji. Przegląd pozostaje nadzorowany; wykonanie przez model jest oznaczane `reviewer.type=agent`.

Biblioteka `data/doctrine_rag` ma osobny rejestr i indeks lokalny. Pomaga formułować hipotezy oraz kontrhipotezy. Nie jest podłączona do kolektora incydentów; walidator odrzuca materiał oznaczony `doctrine` lub `reference` jako dowód incydentu. Nie wolno obchodzić tej granicy przez zmianę etykiety dokumentu. Artykuły analityczne mogą dostarczać aktualnych ustaleń tylko po sprawdzeniu konkretnych faktów i ich pierwotnego pochodzenia. Zasady cytowania i katalog: `docs/doctrine.md`.

## Kompletność i brak odczytu

Wynik pozostaje pusty, gdy wymagane źródło jest niedostępne, częściowe, nie obejmuje wymaganego horyzontu lub przekracza limit świeżości; gdy definicja źródła zmieniła się od pobrania; albo gdy pozostały nieprzejrzane aktualne wersje materiałów. Stara publikacja również może zawierać nową aktualizację. Działający v0.2 sprawdza siedem dni kalendarzowych publikacji i osiem godzin od pobrania. V0.3 wymaga co najmniej 216 godzin historii zdarzeń i rewizji oraz osobnych limitów dla warstwy taktycznej; opisano je w warunkach wdrożenia. Akceptacja kandydata nie zmienia automatycznie listy źródeł wymaganych przez bieżący silnik.

Nierozstrzygnięta data potencjalnego incydentu, błędne dowody i użycie nieaktualnej wersji materiału również mogą blokować odczyt. Zdarzenia kontekstowe, poza zakresem lub niespełniające kryteriów mają uzasadnienie wykluczenia. Nie przedstawiamy ich jako potwierdzonych punktów. Błąd źródła opcjonalnego jest widoczny, lecz nie blokuje liczby.

Stan braku to `score: null`, `status: incomplete` i lista `blockers`. Suma przejrzanych punktów nie zastępuje RTB. „Pełne okno publikacji” jest kontrolą chronologicznej listy kolektora, nie dowodem pełnego pokrycia wydawcy ani regionu. Skrót RSS nie oznacza przeczytania artykułu. Nowe wydanie offline zachowuje prawdziwe daty pobrania.

## Historia, wersje i porównania

Materiały, oceny i wydania dopisujemy. Aktualizacja publikacji wymaga oceny nowej wersji; korekta incydentu tworzy rewizję. Raportów historycznych nie przepisujemy. SQLite blokuje aktualizacje/usunięcia tabel audytu; pliki mają manifesty hashy. Kopie pozostają potrzebne, ponieważ administrator dysku może zmienić pliki.

Wydanie zachowuje wejścia, wersję i hash metodologii, konfigurację źródeł oraz hash kodu, schematów i instrukcji agentów. Replay nie pyta ponownie modelu i wymaga tego samego kodu. Wydania v0.1 odtwarza się z kodu `cc98b68` w osobnym katalogu; nowy kod celowo nie udaje zgodności z ich hashem. Dawne reguły są w `config/archive/scoring-v0.1.json` i `docs/archive/methodology-v0.1.md`.

Zmiana na v0.2 dodaje kategorię przygotowań, uściśla zakres lotnictwa i cyberataków, dodaje próg przeglądu, dwa wkłady oraz kontekst obszarów strategicznych. Odczyty v0.1 i v0.2 nie są bezpośrednio porównywalne. `delta_points` i `comparison_run_id` pozostają `null` do wdrożenia porównywania zgodnych okresów, źródeł i kompletności. Nie oznaczamy braku porównania jako „stabilnie”.

Akceptacja v0.3 zastępuje specyfikację v0.2 w tym dokumencie. Jej dokładny poprzedni tekst i parametry zachowano w `docs/archive/methodology-v0.2.md` oraz `config/archive/scoring-v0.2.json` z kodu `2bccbb2`. Nowy model wymaga osobnych wydań z identyfikatorem `rtb-v0.3`; nie wolno przemianować odczytów v0.2 ani łączyć wersji w jeden trend. Do czasu wdrożenia i sprawdzenia nowego silnika `config/scoring-v0.json` nadal deklaruje `rtb-v0.2`.

<a id="projekt-v03--wygaszanie-regiony-i-korelacja"></a>
<a id="wygaszanie-regiony-i-korelacja"></a>

## Wygaszanie, regiony i korelacja — v0.3

**Status: specyfikacja zaakceptowana 25.09.2026, `calibrated=false`; implementacja pozostaje do wykonania.** Inspiracją są opisane przez [Strażnika](https://straznik.eu/) wygaszanie taktyczne i propagacja regionalna. Publiczna [konfiguracja autora](https://github.com/cukierrro/Straznik/blob/main/backend/app/config.py), sprawdzona 25.09.2026, wskazuje 30 minut pełnej wagi, koniec po 60 minutach i współczynnik sąsiedztwa 0,4. To sprawdzenie opublikowanych reguł, nie audyt działającego serwera ani dowód trafności modelu. Profil strukturalny, współczynniki korelacji i warunki poniżej są **naszymi roboczymi założeniami badawczymi**, nie potwierdzonymi parametrami Strażnika.

RTB nadal obejmuje sabotaż, cyberataki, logistykę, presję graniczną, zakłócenia i zdarzenia kinetyczne. Nowe źródła nie zmieniają automatycznie kryteriów wystąpienia ani atrybucji. Aktywacja PAŻP, lot obronny NATO i ostrzeżenie RCB są kontekstem lub potwierdzeniem konkretnego twierdzenia; nie stają się samodzielnymi zdarzeniami `military_preparation` RU/BY. Niezweryfikowany sygnał pozostaje widoczny w warstwie wczesnej, bez punktów RTB.

### Wygaszanie zamiast sztywnego okna

Niech `T` oznacza czas odcięcia, `t_e` — udokumentowany czas zdarzenia lub nowego pomiaru, a `a = T - t_e` jego wiek. Dla profilu z pełną wagą przez `H` i spadkiem przez kolejne `F`:

```text
D(a; H, F) = 1                       dla 0 <= a <= H
            (H + F - a) / F          dla H < a < H + F
            0                       dla a >= H + F
```

| Profil | Zastosowanie po kwalifikacji dowodowej | H | F | Waga zerowa od |
|---|---|---:|---:|---:|
| `tactical` | Krótkotrwałe zagrożenie powietrzne, aktywny alert, krótkie naruszenie przestrzeni | 30 min | 30 min | 60 min |
| `structural` | Sabotaż i jego skutki, zdarzenie kinetyczne ze skutkami infrastrukturalnymi, potwierdzone zakłócenia GNSS, ruchy wojsk, cyberatak, presja graniczna | 48 h | 168 h | 216 h, czyli 9 dni |

Siedem dni spadku w profilu strukturalnym liczymy **po** 48 godzinach pełnej wagi. Wariant taktyczny `F=60 min` daje zanik po 90 minutach; jest wariantem testu wrażliwości wymagającym osobnej wersji parametrów, bez przełączania go zależnie od pożądanego wyniku. Profil przypisuje analityk na podstawie charakteru i czasu trwania faktu, nie nazwy wydawcy. Ten sam fakt nie otrzymuje jednocześnie obu profili.

Wiek ujemny wyklucza punktację. Nieznany czas albo sama data dzienna, która nie pozwala jednoznacznie wyliczyć wagi, daje stan częściowy i brak pojedynczego odczytu; nie podstawiamy północy ani czasu pobrania. Najnowsza rewizja tego samego zdarzenia zastępuje jego wkład. Ponowny post, odczyt lub potwierdzenie starego faktu nie zeruje wieku. Nowy udokumentowany pomiar trwającego zjawiska może zmienić `t_e`, ale wymaga dowodu nowego stanu i zachowania związku z tym samym epizodem.

Odwołanie alertu lub dezaktywacja strefy kończy ich aktywny wkład od znanego czasu zakończenia; późniejsza wiedza nie zmienia dawnych raportów. Zakończenie akcji ratowniczej nie usuwa historycznego faktu sabotażu — jego wkład nadal wygasa profilem strukturalnym. Wygaśnięcie wagi modelu nie jest odwołaniem oficjalnego ostrzeżenia: jego treść i status obowiązywania pokazujemy osobno.

Przed obliczeniem dopuszczamy tylko wersje materiałów, pomiarów i ocen rzeczywiście znane systemowi do `T`. Obliczenia wieku używają czasu UTC i upływu sekund, niezależnie od zmiany czasu letniego. Odczyt dobowy i tygodniowy używa tego samego wzoru w chwili `T`; rytm raportu nie zmienia wagi i **nie sumujemy siedmiu dziennych indeksów**. Przyszły kolektor musi zapewnić co najmniej 216 godzin historii istotnych zdarzeń oraz ich rewizji; obecnej kontroli siedmiu dni publikacji nie uznajemy za spełnienie tego wymogu. Historyczne piki można zestawić tylko z zapisanych, kompletnych odczytów, z jawnymi lukami.

### Wkład i kolejność obliczeń

Dla unikalnego zakwalifikowanego epizodu `e` z kategorii `c`:

```text
w_e(T) = B_c * D_e(T) * S_e(T)
RTB_v03(T) = min(100, 10 + sum_c min(L_c, sum_e_in_c w_e(T)))
```

`B_c` i `L_c` to wagi oraz limity z tabeli powyżej, przejęte z v0.2 jako punkt wyjścia do porównania modeli. Najpierw rozstrzygamy pochodzenie, tożsamość, bieżącą rewizję i kryteria, potem wygaszanie i synergię. Dla wspólnego `campaign_id` i kategorii wybieramy najwyższy aktualny `w_e`, z rozstrzyganiem remisu po `event_key`; to wspólny wybór przed projekcją regionalną. Sumy we wzorach obejmują już tylko epizody po tym ograniczeniu. Następnie stosujemy niezależnie limity kategorii dla indeksu ogólnego oraz dla każdego regionu, na końcu limit 100. Nie zaokrąglamy wkładów przed zsumowaniem. Niekompletność nadal daje `null`; mnożnik nie zastępuje dowodu ani brakujących danych.

### Propagacja regionalna i widoki Warszawy oraz Łodzi

Graf sąsiedztwa województw jest nieskierowany, wersjonowany i sprawdzany na granicach [PRG GUGiK](https://www.gov.pl/web/gugik/dane-centralnego-zasobu-geodezyjnego-i-kartograficznego3). Krawędź oznacza wspólny odcinek granicy, a `d(e,v)` najmniejszą liczbę krawędzi od udokumentowanego regionu zdarzenia do regionu docelowego. Nie używamy odległości między umownymi środkami województw.

```text
P(e,v) = 1       dla d = 0
         0.40    dla d = 1
         0.16    dla d = 2
         0       dla d > 2
w_e,v(T) = w_e(T) * P(e,v)
RTB_v03,v(T) = min(100, 10 + sum_c min(L_c, sum_e_in_c w_e,v(T)))
```

Jest to hipoteza regionalnej istotności, nie model toru lotu ani fizycznego rozchodzenia się zagrożenia. W pierwszym wariancie dwa kręgi stosujemy wyłącznie do **potwierdzonego, bezpośredniego zagrożenia kinetycznego**. Dla cyberataku, GNSS, sabotażu o lokalnych skutkach i logistyki liczymy udokumentowany zasięg oddziaływania (`P=1` w tym zasięgu), bez automatycznej dyfuzji; zależności sieciowe wymagają odrębnych dowodów. Alerty RCB/RSO zachowują oficjalny obszar adresatów. Strefa PAŻP nie rozszerza sama zasięgu zagrożenia kinetycznego.

Każdy epizod dociera do danego regionu **raz, najkrótszą drogą**. Jeśli ma kilka potwierdzonych regionów bezpośrednich, wybieramy największe `P`, nie sumę tras. Niejasna lokalizacja daje `regional_score=null` dla nierozstrzygniętego zakresu; nie zamieniamy jej w brak zagrożenia. Wkłady przeniesione nie stają się kolejnymi zdarzeniami i nie służą jako dowody korelacji. Indeks ogólny liczy oryginalne epizody raz, a nie sumę indeksów województw. Raport rozdziela wkład bezpośredni i przeniesiony, także po limitach: przy przekroczeniu limitu skaluje je proporcjonalnie.

| Widok | Obszar obliczenia | Przykład: epizod o wkładzie 10 pkt w lubelskim albo podlaskim | Kontekst analityczny |
|---|---|---:|---|
| Warszawa | mazowieckie | 4 pkt przeniesionego wkładu, jeden krąg | Ciągłość funkcji decyzyjnych i administracji |
| Łódź | łódzkie | 1,6 pkt przeniesionego wkładu, dwa kręgi | Ciągłość transportu, magazynowania i dostaw |

To widoki wojewódzkie z kontekstem miasta, bez pozornej dokładności punktowej. Role miast nie dodają mnożnika. Potwierdzone lokalne zdarzenie w łódzkim ma tam pełny wkład; Łódź nie ma stałego rabatu. Parametry 40% i 16% są robocze i wymagają walidacji, podobnie jak pozostałe wagi. Nie przywracamy osobistego celu majątkowego projektu.

### Korelacja wieloźródłowa i efekt fali

Przyjęty ograniczony mnożnik dla jednego epizodu:

```text
S_e(T) = 1 + 0.50 * C_e(T) + 0.25 * F_e(T)       zakres 1.00–1.75
```

`C=1` wymaga łącznie: zweryfikowanej anomalii GNSS względem wersjonowanego odniesienia, potwierdzonej nierutynowej aktywacji PAŻP oraz doniesienia OSINT o tym samym epizodzie. Trzy rodziny muszą mieć **trzy rozdzielone, sprawdzone grupy pochodzenia**. GNSS nie może być streszczeniem tego doniesienia, a dwa portale cytujące ten sam komunikat nie tworzą dwóch grup. Wspólna przyczyna jest dopuszczalna; wspólny materiał pierwotny nie daje niezależności.

Wymagamy udokumentowanego wspólnego obszaru przed propagacją oraz czasu wystąpienia anomalii, zmiany aktywacji i zdarzenia opisanego w OSINT w jednym przedziale najwyżej 30 minut, zakończonym nie później niż `T`. Niepewność czasu też musi mieścić się w tym przedziale. Jest to przedział współwystąpienia w epizodzie, nie koszyk czasu publikacji lub pobrania; jego późniejszy wkład maleje przez `D_e`. Strefa ma być wówczas aktywna, a związek z epizodem i odrzucenie rutynowego wyjaśnienia muszą mieć uzasadnienie. Publikacja zapowiedzi ćwiczeń i późniejszy alert nie tworzą zbieżności przez samą bliskość czasu pobrania. Brak czasu, niezależności lub jakości oznacza brak bonusu i jawne `correlation_status=not_assessed`, a nie potwierdzenie braku korelacji. Korekta lub odwołanie przesłanki usuwa odpowiadający jej bonus w nowym odczycie, bez przepisywania archiwum.

**Obecne GPSJAM nie spełnia tej rozdzielczości:** agregat dobowy nie lokalizuje anomalii w oknie 30 minut, a [porównanie GNSS](gnss-reference-methodology.md) nie jest skalibrowanym detektorem. Wynik dobowy pozostaje kontekstem strukturalnym; nie wolno rozciągać go na każdą minutę ani używać daty pobrania do bonusu. Do aktywacji `C` potrzebny będzie dopuszczony pomiar GNSS o odpowiedniej rozdzielczości i zwalidowana reguła anomalii. Do tego czasu `C=0`, z przyczyną braku oceny, także przy dostępnych PAŻP i OSINT.

`F=1` wymaga co najmniej trzech **rozróżnionych i potwierdzonych fizycznych obiektów lub zdarzeń kinetycznych** w tym samym epizodzie, których czasy wraz z niepewnością mieszczą się w przedziale 15 minut zakończonym do `T`. Liczba postów, nazw kanałów i zmieniających się identyfikatorów nie wystarcza. Epizod grupujemy od pierwszej rozpoznanej składowej, nie dopiero po pojawieniu się trzeciej; przy jednej lub dwóch `F=0`. Składowe zachowują własne identyfikatory, ale grupa ma jeden `episode_key`, jedną kategorię i bazę tej kategorii; jej składowych nie doliczamy drugi raz. Każda składowa może należeć tylko do jednej grupy w danym odczycie. Wiek grupy wyznacza najstarsza zaliczona składowa, więc fala również wygasa przez `D_e`. Korekta obalająca warunek liczby lub spójności czasowej usuwa bonus. Nie sumujemy równoległych wersji grupy i jej składowych.

Pełna triada bez fali daje `S=1,50`, sama fala `1,25`, oba warunki `1,75`. Bonus stosujemy raz do epizodu, nigdy do całego indeksu, każdej publikacji, pary źródeł ani kolejnej próbki. Surowe dowody, skład grupy i rozbicie bonusu są audytowalne. Brak bonusu nie ukrywa pojedynczego pilnego sygnału w kolejce przeglądu.

### Poziom czerwony i oficjalne ostrzeżenia

Roboczy próg liczbowy pozostaje ściśle ponad 60. W v0.3 czerwony **priorytet analityczny** dodatkowo wymaga kompletności, co najmniej dwóch niezależnych grup pochodzenia dla punktowanych dowodów bezpośrednich oraz przynajmniej jednego bezpośredniego zdarzenia w ocenianym obszarze ze statusem wystąpienia `corroborated`. Samo przeniesienie punktów nie otwiera czerwonego. Przy przekroczeniu sumy bez bramki pokazujemy wartość i powód wstrzymania czerwonego; pozostaje przegląd analityczny. Jedna relacja medialna i dowolna liczba jej kopii nie przechodzą bramki.

Trzy klasy treści RCB/RSO z [rejestru źródeł](sources.md#rso-rcb-klasy) są osobnym statusem oficjalnego komunikatu, bez przelicznika 1:1 na RTB. Autentyczne polecenie szukania bezpiecznego miejsca jest prezentowane wraz z obszarem i czasem także wtedy, gdy RTB jest `null` lub brakuje drugiego źródła. Model nie odwołuje, nie rozszerza i nie zastępuje zaleceń służb. Brak alertu nie jest dowodem braku zagrożenia.

### Warunki wdrożenia i przypadki kontrolne

Zaakceptowano specyfikację z identyfikatorem `rtb-v0.3`; parametry pozostają nieskalibrowane. Wdrożenie wymaga konfiguracji obliczeń i schematów v0.3, wersji grafu oraz rejestru źródeł, tłumaczeń, reguł grupowania i bramek jakości. Nie wystarczy zmiana pola `version` w konfiguracji v0.2. Uruchomić najpierw obliczenia porównawcze na osobnych danych, zachowując v0.2 i replay. Osiem godzin świeżości źródeł RTB i 36 godzin pilotażu GNSS nie są dopuszczalnymi limitami dla minutowego ostrzegania. Dla taktycznej korelacji przyjęto wymóg kontroli PAŻP i RCB/RSO nie starszej niż 5 minut względem `T`; jej osiągalność musi zostać zmierzona przed użyciem.

| Przypadek syntetyczny / warunek | Oczekiwany wynik przyszłej implementacji |
|---|---|
| Taktyczny: wiek 0, 30, 45, 60 min | `D=1; 1; 0,5; 0` |
| Strukturalny: wiek 48, 132, 216 h | `D=1; 0,5; 0` |
| Ten sam meldunek UA, jego przedruk i kopia na drugim portalu | Jeden epizod; brak nowych grup pochodzenia, fali i resetu wieku |
| Wkład 10 w lubelskim; dwie drogi do łódzkiego | Mazowieckie 4; łódzkie 1,6, bez sumowania dróg; indeks ogólny nadal jeden wkład 10 |
| Ten sam Alert RCB w RSO i na gov.pl; późniejsze odwołanie | Jedna aktualna instrukcja dla obszaru, zachowane rewizje |
| Dobowe GPSJAM + PAŻP + OSINT w bieżącej godzinie | Bonus korelacji wyłączony; brak rozdzielczości czasowej / detektora |
| Pełna, niezależna triada z dopuszczonym pomiarem GNSS; baza 10, `D=0,5`, bez fali | Wkład 7,5 przed limitami i propagacją, `S=1,5` |
| Suma >60 z jednej grupy pochodzenia albo wyłącznie z propagacji | Czerwony wstrzymany; powód widoczny |
| Dane pobrane dopiero po czasie odcięcia, brak lub błąd źródła | Bez późniejszej wiedzy; brak nie staje się zerem |

Wyniki trzeba sprawdzić na odseparowanym okresie historycznym, z ćwiczeniami, odwołaniami, awariami odbioru, przedrukami i rzeczywistymi incydentami. Samo przejście przypadków syntetycznych potwierdza rachunek, nie jakość ostrzegania.

## Ustalenia robocze i dalsza walidacja

Po komentarzu użytkownika wdrożono osobne pilotaże GNSS/logistyki, API ADSB.lol i historii lotniczej, opisane w `docs/early-warning-design.md`. Obserwacje mogą trafiać do przeglądu bez potwierdzonego sprawcy; detektor alarmowy i nowe heurystyki nie są jeszcze wdrożone. Wagi, kryteria i odczyty działającej v0.2 pozostają bez zmian do wdrożenia zaakceptowanej specyfikacji v0.3. Kontrola pokrycia i ocena wyprzedzenia muszą zachować wiedzę dostępną w chwili prognozy.

Przyjęte w v0.3: Polska i flanka NATO jako cel; wygaszanie według profilu zdarzenia; 14–42 dni dla scenariuszy; propagacja regionalna 40% / 16%; korelacja i fala z ograniczonym mnożnikiem; ponad 60 jako wezwanie do przeglądu z osobną bramką czerwonego; biblioteka doktryny oddzielona od zdarzeń. Żadna nowa integracja nie korzysta z danych agregowanych przez Strażnika.

Dalsze dane są potrzebne do kalibracji wag, limitów i progu, pomiaru fałszywych alarmów, zbudowania baz odniesienia dla anomalii oraz oceny pokrycia państw. „Wiarygodność” oznacza obecnie status dowodowy, bez pozornie precyzyjnego procentu. Pierwszy krok to opisane historyczne przypadki wraz z kontrprzykładami i późniejszymi sprostowaniami; dopiero potem porównanie wariantów wag i alarmów. Te luki nie wymagają zgadywania liczb przez użytkownika.
