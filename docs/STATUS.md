# Stan realizacji — 01.10.2026

## Zmiana doby i odbiór harmonogramu — 01.10.2026, 12:12

Cykl `2026-10-01T100253Z-e71de236` obejmuje 17 źródeł i **91 materiałów do
przeglądu**. Rozstrzygnięto 80, 11 pozostawiono do wyjaśnienia. Codex wykonał
ocenę, drugi krytyczny przegląd 29 decyzji oraz osobny przegląd komentarza.
Wszystkie oceny mają `reviewer.type=agent`. **RTB 3/100, pewność 22%** wobec
wczorajszych 25%; częściowy odczyt RCB obniżył pokrycie. Nie zablokował indeksu.

Nowy biuletyn ZSU opisuje noc 30.09/01.10: 107 dronów, w tym 63 odrzutowe.
Nie ustala lokalizacji wszystkich trafień; pozostaje kontekstem bez nowych
punktów. Nakładający się bilans dzienny odroczono, bez sumowania obu liczników.
Serie alarmów Wołynia i Równego zaktualizowano w istniejących zdarzeniach.
Nowy alarm nie dowodzi trafienia. Aktualizacje X dotyczące Nowej Dęby
połączono; uwzględniono późniejsze wykluczenie zagrożenia chemicznego,
biologicznego i radiologicznego, bez automatycznej kwalifikacji sabotażu.

Sprawdzono 34 rekordy bieżącej listy RSO oraz plan PAŻP na 01–02.10
z 411 wierszami. Ćwiczenia RCB/RSO i planowane strefy nie otrzymują punktów.
Brak pełnego artykułu RCB z 30.09 pozostaje odroczeniem; skrót o wcześniejszym
zagrożeniu nie staje się bieżącym ostrzeżeniem. Komentarz zawiera datowany
nalot i zapowiedziane przez MON wsparcie szwedzkich Gripenów w misji NATO.

GPSJAM: jedna nowa doba, **30/30 od 01 do 30.09**. Dla 30.09 kwalifikuje się
572 z 642 komórek, 125 ma podwyższony udział niskiej dokładności. Na wspólnej
siatce **492 komórek: 15,65%**, wobec mediany **16,26%** z wcześniejszych
29 dób. To porównanie opisowe; skład siatki różni się od wczorajszego.
Zaakceptowany pomiar daje 50% pokrycia domeny GNSS i zero punktów RTB.

Wkład trzech punktów nadal pochodzi z tego samego epizodu 29/30.09.
Rewizja i przedział wystąpienia nie zmieniły się. Najstarszy możliwy wiek
wynosi 43,21 godziny, więc zgodnie z metodologią nie rozpoczęło się jeszcze
wygaszanie po 48 godzinach. Osobna kontrola granic potwierdziła pełną wagę
po 48 h, 6/7 po 72 h i zero po 216 h, bez publikowania scenariuszy testowych.

Raport `rpt_c78f0e37f01bf51f50f00d9e32095896f9f0717e525a077b51618f0da582bd4c`
zapisano w Supabase z `verified_readback=true`. Lokalny odczyt i pobierany JSON
są identyczne z eksportem. Strona pokazuje datę **01.10.2026, 12:12**, RTB 3,
pewność 22% i polski komentarz. 74 wpisy obejmują zdarzenia i kontekst,
nie 74 zagrożenia. Pełne siatki GNSS pozostają prywatne. Replay ze 142
zamrożonych plików dał identyczny wynik bez sieci; baza i klucze obce są poprawne.
Dowód: `data/analysis/cycles/2026-10-01T100253Z-e71de236/verification.json`.

**51 testów cyklu, v0.4, GNSS i publikacji przeszło**, w tym dwa nowe przypadki:
awaria przed zapisem i utrata odpowiedzi po zapisie. Ponowienie zachowuje
eksport i nie tworzy duplikatu. W izolowanej przeglądarce sprawdzono także
HTTP 503: wynik i data pozostają widoczne, a powrót połączenia przywraca
odświeżanie. Nie wprowadzono danych testowych do Supabase.

X: dwa żądania, 18 wpisów, pięć wybranych do przeglądu; szacowany koszt
**0,090 USD**, łącznie **0,165 USD** w lokalnym rejestrze. Oba konta nadal
mają zaległe strony. Limity bez zmian; koszt wymaga uzgodnienia z rozliczeniem X.

Aktywowano **RTB — codzienna analiza i raport**, codziennie o **09:00 czasu
Warszawy**, w istniejącym wątku Codexa. Pierwszy zaplanowany przebieg 02.10
pozostaje do sprawdzenia. Wymaga włączonego Maca i działającego Codexa;
[warunki i odzyskiwanie](automation-runbook.md). Nie zmieniono wag, kodu
silnika ani UI. Hosting produkcyjnego dashboardu i domena pozostają niewłączone.

## Zachodnia Ukraina i zweryfikowane pomiary GNSS — 30.09.2026, 15:11

`sources-pilot-8` dodaje publiczne kanały administracji obwodów wołyńskiego,
lwowskiego i rówieńskiego, z tożsamością potwierdzoną w serwisach instytucji.
Pobrano odpowiednio 20, 11 i 20 tekstów w czterech żądaniach. Odczyt jest
ograniczony, a przekazania zachowują pierwotnego autora i URL. Alarm,
odwołanie alarmu i potwierdzone trafienie są rozpatrywane osobno.

Lokalny komunikat Wołynia potwierdził odrzutowy dron Shahed i uszkodzenie
punktu kontrolnego przy Jagodzinie 28 września. Uzupełniono istniejący wpis
OSW, bez drugiego incydentu i bez automatycznego potwierdzania sprawcy.
Przekazany przez administrację rówieńską komunikat prezydenta Ukrainy
potwierdził rosyjski nalot i uderzenia w infrastrukturę Rówieńszczyzny.
Uzupełnia on jeden istniejący epizod nocy 29/30 września. Liczba 188 dronów
dotyczy całego nalotu na Ukrainę, nie tego obwodu. Późniejsze doniesienie
lokalne pozostaje do dopasowania, aby nie podwoić liczby zdarzeń.

GPSJAM odświeżono raz: siedem nowych dób, łącznie **30/30 od 31.08 do 29.09**.
Główny cykl importuje zamrożoną obserwację bez kolejnego pobrania, odtwarza
liczby z CSV i kontroluje pochodzenie. Dla 29.09: 111 z 550 kwalifikujących
się komórek ma podwyższony udział niskiej dokładności; na wspólnej siatce
490 komórek jest to 15,71%, wobec mediany 16,53% z poprzednich 29 dób.
To porównanie opisowe, bez kalibrowanego progu, sprawcy ani dowodu ciągłości
zakłóceń. Zaakceptowany pomiar daje **50% pokrycia domeny GNSS i 0 punktów
RTB**. Samo pobranie, odroczenie oceny lub nieaktualna doba nie poprawiają
pewności. [Kontrakt i obsługa](gnss-review-integration.md).

Cykl `2026-09-30T125639Z-e3352267`: 100 materiałów do przeglądu, 93
rozstrzygnięte i siedem pozostawionych do wyjaśnienia. **RTB 3/100,
pewność 25%, bez blokad indeksu**. Trzy punkty pochodzą z jednego epizodu
na zachodniej Ukrainie; GNSS, plan PAŻP i serie alarmów nie dodają punktów.
Publikacja zawiera 63 zdarzenia i obserwacje kontekstowe, nie 63 zagrożenia.
Nie poświadczono pełnej historii. Zmiana konfiguracji pokrycia rozdziela
serie porównawcze; nie pokazujemy jej jako trendu zagrożenia.

Raport `rpt_cf911e27f78cbd90dff98f808a4ca39a68005e4504220d355f22a2ec02b4f917`
zapisano w Supabase z `verified_readback=true`. Lokalny odczyt i pobierany
JSON są identyczne z eksportem. Przeglądarka pokazuje datę 15:11, wynik,
pewność oraz polski komentarz; pełne siatki pomiarowe pozostają prywatne.
Replay ze 142 zamrożonych plików daje identyczny wynik bez żądań sieciowych.
Baza i klucze obce są poprawne. Dowód:
`data/analysis/cycles/2026-09-30T125639Z-e3352267/verification.json`.

**351 testów Python przeszło.** Nie wykonano płatnego żądania X, nie zmieniono
limitów kosztów, UI ani wag punktacji. Harmonogram, hosting produkcyjnego
dashboardu i domena pozostają niewłączone.

## Źródła pierwotne i cykl v0.4 — 30.09.2026, 13:58

Włączono `sources-pilot-7`: bezpośrednie biuletyny CERT/NASK i Podlaskiej
Straży Granicznej oraz szerszy odczyt oficjalnego kanału Sił Powietrznych
Ukrainy. Rzeczywiste pobranie obejmuje 20 artykułów CERT, 18 artykułów SG,
20 materiałów RCB, 28 MON oraz 60 wpisów ukraińskich. Publiczne podsumowania
ukraińskie zawierają datowane bilanse z 15–30 września. To ograniczony odczyt,
nie kompletne archiwum kanału. Kolektory nie korzystają z interfejsu Strażnika.

RCB i MON odzyskały pełne treści; obsługa chwilowego zerwania połączenia ma
jedną ograniczoną próbę ponowienia i respektuje limit żądań oraz Retry-After.
403 nie jest omijane. CERT korzysta z własnego publicznego serwisu biuletynów,
a nie z niedostępnego archiwum `cert.pl/posts`. Datę bez godziny zachowujemy
osobno; nie tworzymy fikcyjnej północy ani czasu zdarzenia. Regionalne
biuletyny SG mają maksymalnie 50% pokrycia domeny granicznej i nie zastępują
statystyk potrzebnych do rozpoznania wzrostu presji.

Cykl `2026-09-30T114359Z-efc75e41` objął **105 materiałów do przeglądu**.
Rozstrzygnięto 99, sześć pozostawiono do wyjaśnienia: zbiorcze wzmianki
OSW/VDD oraz cztery ukraińskie bilanse z niejasnym rozdzieleniem epizodów
lub nakładającymi się oknami. Wpis X o akademii nauk w Kijowie połączono
z pierwotnym komunikatem ukraińskim, zachowując tożsamość zdarzenia.
Aktualizacje tego samego nalotu, plan PAŻP i ćwiczenia syren nie tworzą
dodatkowych punktów. Przejrzano wszystkie 42 rekordy bieżącej listy RSO.

**RTB: 0/100; pewność: 22%; brak globalnych blokad.** Wynik oznacza brak
zakwalifikowanych wkładów według przyjętych kryteriów, nie ocenę bezpieczeństwa.
Ogólnokrajowe bilanse Ukrainy nie ustalają lokalizacji wszystkich trafień
w obwodach lwowskim, wołyńskim i rówieńskim. Ostrzeżenia o podatnościach CERT
nie dowodzą dużego cyberataku RU/BY na polską lub litewską infrastrukturę.
GNSS nadal pozostaje poza pokryciem indeksu; historia zdarzeń nie została
poświadczona jako kompletna. Nie dodano komentarza zapewniającego o spokoju.

Raport `rpt_0b513c71de73fa5627ec6007644f28512f3ead40ef0ad9c203058ef3cfe018d9`
zapisano w Supabase z `verified_readback=true`. Eksport i lokalne API są
identyczne. Przeglądarka potwierdza datę 13:58 i pewność 22%; publikacja
zawiera 58 zdarzeń i obserwacji kontekstowych, nie 58 naliczonych zagrożeń.
Replay ze 139 zamrożonych plików daje identyczny wynik bez żądań sieciowych.
Baza i klucze obce przeszły kontrolę integralności. Dowód:
`data/analysis/cycles/2026-09-30T114359Z-efc75e41/verification.json`.

Poprawiono też oznaczanie lokalnego pominięcia X z powodu budżetu: zachowuje
ostatni rzeczywisty odczyt i jego datę, bez udawania awarii lub odświeżenia.
Etap nie wykonał żadnego płatnego żądania X; limity kosztowe są bez zmian.
Kontrola pełnej ścieżki oceny wykryła brak dwóch kryteriów zachodniej Ukrainy
w schemacie propozycji. Poprawka została sprawdzona po zamrożeniu raportu,
w izolowanym pełnym cyklu; nie zmienia opublikowanego obliczenia.
**347 testów Python przeszło.** Harmonogram, produkcyjny hosting dashboardu
i domena pozostają kolejnymi etapami.

## Przegląd historii i pełny cykl — 30.09.2026, 11:33

Wykonano cykl `2026-09-30T091940Z-3171f42e`: pobranie źródeł, przegląd
dowodów, drugi przegląd tego samego agenta, dopisanie ocen, obliczenie,
archiwizacja i publikacja do Supabase. To **ósme rzeczywiste wydanie**.
Wszystkie oceny mają `reviewer.type=agent`; drugi przegląd nie oznacza
niezależnego potwierdzenia źródeł.

Przegląd objął pełne teksty **59 materiałów**: 32 znane materiały RCB,
16 publikacji MON od 21 września oraz 11 publikacji OSW od 21 września.
Porównano zapisane rewizje zdarzeń i 32 przejścia między wersjami materiałów.
Uzupełnienie skrótu RSS pełnym tekstem nie jest automatycznie korektą wydawcy
ani nowym incydentem. Lista przejrzanych wersji, dowody i dalsze zadania są
w prywatnym `data/analysis/cycles/2026-09-30T091940Z-3171f42e/history-gap-audit.json`.

Nowy odczyt PAŻP zawiera identyczny multizbiór 541 wierszy; zmienił się tylko
znacznik aktualizacji. RSO dodało jeden komunikat o zakończeniu ataku na
Ukrainę, bez zmian pozostałych 42 rekordów. Dopisano trzy rewizje istniejących
wpisów i jeden zapis komunikatu, zachowując wspólne pochodzenie RCB/RSO.
Komunikatu nie potraktowano jako dowodu nowego ataku. Baza zawiera teraz
35 zdarzeń i 47 rewizji, także kontekstowych; nie są to liczniki zagrożeń.

**RTB pozostaje niewyliczony.** Dwa wstrzymane materiały to zbiorcze wzmianki
OSW o incydentach na Łotwie oraz komunikat VDD o pojedynczych próbach
dezinformacji. Brakuje identyfikacji i dat poszczególnych zdarzeń.
Przejrzane dokumenty łotewskie opisują konkretne starsze sprawy, ale nie
poświadczają kompletności tych wzmianek. Nie utworzono `history-review.json`
ani komentarza zapewniającego o bezpieczeństwie. Dalsza praca dotyczy
konkretnych komunikatów i sprostowań, a nie ponownego odczytu tego samego RSS.

X: dwa żądania, cztery nowe wpisy poza zakresem regionalnym, bez nowych
kandydatów. Szacowany koszt odczytu **0,020 USD**, łącznie **0,075 USD**
w lokalnym rejestrze; kwoty wymagają porównania z rozliczeniem dostawcy.

Publikacja ma `verified_readback=true`. Supabase, lokalne API i pobierany
JSON są identyczne, a przeglądarka pokazuje datę **30.09.2026, 11:33**.
Replay z osobnej kopii 131 plików kodu, obejmującej parser RSS, dał identyczny
wynik przy zablokowanej sieci. Baza, klucze obce i kopia sprzed cyklu przeszły
kontrolę integralności. Dowód:
`data/analysis/cycles/2026-09-30T091940Z-3171f42e/verification.json`.
Harmonogram pozostaje wyłączony; nie zmieniano hostingu, domeny ani UI.

Ikonę strony wyeksportowano do `artifacts/branding/`: PNG 1024 × 1024
na białym i przezroczystym tle, z marginesem do okrągłego kadrowania na X.
Zachowano kształt znaku Lucide Radar, kolor z `theme.css` oraz licencję.

## API X — 30.09.2026, 09:19

Podłączono token aplikacji i bezpośrednie pobieranie OSINT Defender / OSINT
Technical. `sources-pilot-6`, `source-candidates-11`, limity `x-api-pilot-1`:
do 20 postów i czterech żądań na przebieg, 0,12 USD dziennie i na przebieg,
4,50 USD łącznie w lokalnym pilotażu. Sekret jest w prywatnym `.env.x`, poza
Git, raportami i frontendem. Częstotliwość i koszt są sprawdzane przed
żądaniem; przerwanie pozostawia rezerwację. Kolejny odczyt korzysta z zapisanego
kursora, a zaległa paginacja nie przesuwa granicy przed ukończeniem przedziału.
Nie pobieramy automatycznie mediów, cytowanych postów ani przedruków.

Test: **cztery odpowiedzi HTTP 200**, siedem postów Defender, zero Technical
w zadanym oknie ostatnich 24 h. Siedem postów było poza regionem; nie dodano
z nich incydentów. Szacowany koszt zasobów: **0,055 USD**, do potwierdzenia
w rozliczeniu dostawcy. Ponowne wywołanie wykonało zero żądań. Wcześniejsze trzy
regionalne materiały Technical pozostają niezmienione z oryginalną metodą
odczytu; pusta odpowiedź API nie jest dowodem ich usunięcia ani braku zdarzeń.

Import do kolektora sprawdzono bez kolejnego zapytania. API ma osobny kontrakt
i archiwum odpowiedzi, tekstów, dat oraz pochodzenia. Limit kosztów, wznowienie,
awarie, blokada równoległych pobrań, integralność i brak odświeżania dat w trybie
offline są objęte testami. Łącznie **316 testów Python**; test lokalnego HTTP
wymagał uruchomienia poza blokadą portów sandboxa. Dowód rzeczywistego odczytu
i importu: `data/x-api/runs/16063d05cc1f491d8da16964390a55b2.verification.json`.

Przed przyszłym cyklem Codex wykonuje `scripts/collect_x.py collect` w tych
limitach; samo `prepare` tylko importuje paczki, bez opłat X. [Instrukcja](x-sources.md).
Harmonogram pozostaje niewłączony. Brak nowych regionalnych postów w tej próbie
nie uzasadnia nowej oceny zagrożenia — ostatni opublikowany raport pozostaje
z godziny 08:52. Nie publikowano nowego wydania ani nie zmieniano frontendu.

## Uzupełnienie OSW, konta X i dokumenty łotewskie — 30.09.2026, 08:52

`sources-pilot-5` obejmuje ograniczone archiwum OSW, odczyty kont
OSINT Defender / OSINT Technical oraz sześć wybranych dokumentów MON Łotwy
i VDD. [Instrukcja X](x-sources.md) wykorzystuje dostarczony skill
`x-research`; skill nie zapewnia narzędzia ani uprawnień do X. Odczyt wykonuje
Codex w przeglądarce przed `prepare`, bez płatnego API. Import zachowuje
oryginały, pochodzenie, ograniczenie zasięgu i filtr Europy Wschodniej/Niemiec.

Rzeczywisty odczyt pokazał po pięć wpisów obu kont. Trzy regionalne wpisy
OSINT Technical odczytano w całości i uwzględniono po polsku w raporcie;
pozostałe siedem było poza zakresem. Nie poświadczamy pełnej historii kont.
Źródła X są opcjonalne, stale oznaczone jako niepełne. Ponowne czytanie pliku
nie odświeża czasu dostępu. Zmiana tekstu lub cytowanego pochodzenia wymaga
nowej oceny, a kopie komunikatu nie zwiększają liczby niezależnych dowodów.

OSW zwróciło 20 pełnych publikacji; dwie strony archiwum przekroczyły granicę
216 godzin. Usunięto brak pokrycia listy publikacji, nie poświadczono przez to
historii wszystkich zdarzeń. Łotewskie źródła odświeżają wyłącznie wskazane
URL-e — nie są pełnymi strumieniami wiadomości. PAŻP zwróciła 541 wierszy
planu, a RSO 43 komunikaty; wiersz planu nie oznacza incydentu ani aktywacji.

Cykl `2026-09-30T063135Z-45abcfda` obejmował 24 materiały do oceny:
22 rozstrzygnięto, dwa wstrzymano. Powstało dziewięć nowych obserwacji i trzy
rewizje wcześniejszych zdarzeń. Wpis X o Milrem i komunikat VDD połączono
w jeden sierpniowy epizod, bez potwierdzania nowej atrybucji Rosji. Dwa
komunikaty o dronie w Balvi dotyczą jednego zdarzenia z 14 sierpnia; późniejsza
identyfikacja obiektu jako ukraińskiego nie ustala operatora ani zamiaru.

Kontrola przeglądarki ujawniła przesunięcie dziennej daty publikacji po
konwersji łotewskiej północy. Poprawiono parser: zapisuje dzień w
`source_record.published_on`, a bez podanej godziny zachowuje `published_at=null`.
Nowy cykl `2026-09-30T064935Z-4e7846c9` ponownie pobrał dokumenty, zachował
identyczne treści i dopisał ich oceny, nie nadpisując historii. Aktualizacja
PAŻP zmieniła kolejność wierszy i znacznik aktualizacji, nie ich treść ani
liczbę incydentów. W dashboardzie wpis bez znacznika czasu pozostaje dostępny
w dzienniku; nie otrzymuje wymyślonej godziny na osi czasu.

**RTB pozostaje niewyliczony:** nierozstrzygnięte są ogólne wzmianki OSW o
łotewskich incydentach i VDD o pojedynczych próbach dezinformacji. Nadal brak
podstaw do poświadczenia pełnej historii zdarzeń/rewizji w horyzoncie 216 h.
Nie wygenerowano zapewnienia o bezpieczeństwie ani pozornego wyniku 10/100.

Wydanie z **30.09.2026, 08:52 czasu Warszawy** zapisano w Supabase. Eksport,
odczyt chmury i lokalne API są identyczne; ponowienie nie dodało duplikatu.
Historia zawiera siedem rzeczywistych wydań. Przeglądarka automatycznie
wyświetliła nową datę; filtr OSINT Technical pokazuje trzy polskie wpisy.
Dowód: `data/analysis/cycles/2026-09-30T064935Z-4e7846c9/verification.json`.

Weryfikacja: **293 testy Python** (test HTTP wymagał dostępu do lokalnego portu
po blokadzie sandboxa); odtworzenie z osobnej kopii 125 plików, wraz z parserem
RSS, dało identyczny wynik przy zablokowanej sieci. Dwa nowe wydania zachowują
własne kopie kodu. Dane robocze i klucze pozostają poza Git. Frontendu nie
zmieniano; wcześniejsze sześć testów JS/PostgreSQL i build sprawdzono w punkcie
kontrolnym. Harmonogram, domena i hosting nowej aplikacji pozostają osobne.

## Punkt kontrolny Git — 30.09.2026

Na prośbę użytkownika zapisano i wypchnięto dotychczasowy silnik v0.3, dashboard,
publikowanie do Supabase i dostarczone materiały na gałęzi
`codex/dashboard-publication` — commit `d840c66`. Kontrola przed commitem: 267 testów Python,
6 testów JavaScript/PostgreSQL i build zakończone poprawnie. Dane robocze,
lokalne klucze i artefakty kompilacji pozostają poza Git. Kolejny etap obejmuje
uzupełnienie danych i dodanie wskazanych kont OSINT na X.

## Silnik v0.3 i pierwsze źródła — odbiór 29.09.2026, 19:27

Domyślny silnik wykonuje teraz `rtb-v0.3`: wygaszanie, regionalną propagację
na grafie PRG (16 województw, 34 krawędzie), grupowanie epizodów, efekt fali
oraz bramki korelacji i czerwonego priorytetu. Bonus GNSS pozostaje wyłączony
z powodu braku zatwierdzonego detektora o odpowiedniej rozdzielczości.
Opis kontraktów i procedury: [wdrożenie v0.3](v0.3-implementation.md).

Pierwsze kolektory: bezpośredni current AUP PAŻP (422 wiersze planu) i ogólna
lista XML RSO (42 komunikaty). Plan nie potwierdza aktywacji; bieżące listy
nie poświadczają historii. Oba pobrania zakończyły się poprawnie, po jednym
żądaniu. Pozostałe cztery źródła także odpowiedziały; RSS OSW nie objął już
pełnego horyzontu 216 godzin, choć pełne teksty dostępnych pozycji pobrano.

W cyklu `2026-09-29T172300Z-57d7b9f6` przejrzano sześciu kandydatów:
pięciu rozstrzygnięto, jeden materiał OSW o Łotwie pozostaje wstrzymany.
Do wcześniejszego incydentu dotyczącego Ustki dołączono RSO jako dystrybucję
tego samego komunikatu RCB, bez podwójnego zliczania. Dodano obserwację planu
PAŻP i zapowiedź ćwiczeń syren. Nie naliczono z nich punktów.

**RTB pozostaje niewyliczony:** brak potwierdzenia kompletnej historii zdarzeń
z 216 godzin, niepełny horyzont OSW i nierozstrzygnięta pozycja o Łotwie.
Nie utworzono fikcyjnego poświadczenia historii ani komentarza o bezpieczeństwie.
To ograniczenie danych, odrębne od wykonanej implementacji obliczeń.

Migrację numeric zastosowano w Supabase, bez zmiany dawnych payloadów i RLS.
Nowe rzeczywiste wydanie odczytano z chmury i lokalnego API: są identyczne
z eksportem. Historia zawiera pięć raportów. Przeglądarka pokazała stan na
19:27 i sześć dzisiejszych sygnałów, w tym PAŻP oraz ćwiczenie RCB/RSO.
Potwierdzenie: `data/analysis/cycles/2026-09-29T172300Z-57d7b9f6/verification.json`.

Weryfikacja: **267 testów Python, 6 testów JavaScript/PostgreSQL i poprawny
build**. Test numeric=12,5 wykonano wyłącznie w pamięci PGlite. Oddzielne
kopie kodu odtworzyły identycznie raporty v0.2 i v0.3 przy zablokowanej sieci.
Wykonano kopię SQLite przed pobraniem. Syntetyki nie trafiły do live.

Następny krok danych: uzupełnienie archiwum OSW do co najmniej 216 godzin
zdarzeń/rewizji i rozwiązanie wzmianki o łotewskich incydentach u pierwotnych
wydawców. Dalej: aktywacja PAŻP/UUP, UA, Bałtyk i kalibracja. Harmonogram,
domena oraz hosting nowej aplikacji pozostają osobnymi etapami.
Kod jest lokalnie na `codex/dashboard-publication`, bez nowego commita/pusha.

## Pełne treści OSW — odbiór 29.09.2026, 18:22

Kolektor OSW pobiera teraz pełne artykuły HTML i tekst raportów PDF bezpośrednio
od wydawcy. Wraca również do znanych nierozstrzygniętych publikacji, które
wypadły z RSS. Rejestr źródeł ma wersję `sources-pilot-3`; obliczenia nadal
wykonują **`rtb-v0.2`**. Szczegóły: [źródła](sources.md#pełne-treści-osw--rozszerzenie-29092026),
[obsługa](runbook.md). Nowe treści mają własne wersje i oceny; poprzednie
materiały, oceny i raporty pozostają w historii.

Rzeczywisty cykl `2026-09-29T161625Z-e468a958` pobrał **12 pełnych publikacji
OSW: 11 artykułów HTML i jeden 67-stronicowy PDF**, wykonując 15 żądań do OSW.
Dwie publikacje odzyskano spoza bieżącego RSS. Uzupełniono wszystkie cztery
braki pełnej treści z poprzedniego cyklu. RCB, MON i OSW odpowiedziały poprawnie;
opcjonalny Naval News zwrócił HTTP 503, zachowany jako jawna niedostępność.

Przegląd agenta rozstrzygnął 11 materiałów: osiem wykluczeń oraz pięć obserwacji
kontekstowych z trzech analiz wojennych. Jedna nowa publikacja pozostaje do
wyjaśnienia: analiza wyborów na Łotwie wspomina o naruszeniach przestrzeni
powietrznej bez dat i szczegółów pozwalających rozdzielić zdarzenia. Jej pełny
tekst jest już dostępny; dalsza weryfikacja wymaga komunikatów pierwotnych.
**RTB pozostaje niewyliczony z powodu tej jednej nierozstrzygniętej pozycji.**
Nowe obserwacje kontekstowe nie otrzymały punktów; komentarz główny pominięto.

Raport ze stanem na **29.09.2026, 18:22 czasu Warszawy** opublikowano do
Supabase. Eksport, odczyt chmury i lokalne API są identyczne; historia zawiera
cztery rzeczywiste wydania. Otwarty dashboard sam zaktualizował datę i pokazał
cztery sygnały z bieżącego dnia. Potwierdzenie:
`data/analysis/cycles/2026-09-29T161625Z-e468a958/verification.json` (poza Git).
Poprzednie potwierdzenie zachowano w katalogu wcześniejszego cyklu.

Weryfikacja: **227 testów Python**, w tym dziesięć nowych testów kolektora OSW.
Sprawdzono PDF, zaległości, zmiany treści, limity, przekierowania i utrwalanie
`Retry-After`. Odtworzenie z zamrożonych wejść i osobnej kopii 92 plików kodu
dało identyczny wynik przy zablokowanej sieci. Przed pobraniem wykonano kopię
bazy; dane testowe pozostały w katalogach tymczasowych.

Ten etap zamyka uzupełnianie treści OSW. Dalszy zaakceptowany zakres obejmuje
źródła pierwotne i wykonanie metodologii v0.3. Harmonogram, domena i wdrożenie
nowej aplikacji pozostają osobnymi zadaniami. Kod jest lokalnie na gałęzi
`codex/dashboard-publication`, bez nowego commita/pusha.

## Silnik analityczny Codexa — wcześniejszy cykl 29.09.2026, 17:41

Wykonawcą AI jest Codex pracujący w tym repozytorium, bez osobnego API modelu.
`scripts/analysis_cycle.py` prowadzi cykl: pobranie → zamrożony pakiet →
propozycja ocen → kontrola dowodów → drugi przegląd agenta → obliczenie RTB →
opcjonalny komentarz po przeglądzie → niezmienne wydanie → Supabase → kontrola
odczytu. Zmiana materiałów lub kodu zatrzymuje korzystanie ze starego pakietu.
Instrukcja: [obsługa silnika](analysis-runbook.md),
[zadanie dla Codexa](../agents/analysis-cycle.md).

Przeprowadzono rzeczywisty cykl `2026-09-29T153254Z-d3ca4c60`. Kolektory pobrały
54 publikacje; wszystkie cztery źródła odpowiedziały poprawnie. Kolejka z
zaległościami liczyła 50 materiałów. Przegląd rozstrzygnął 46: 36 wykluczeń
kontekstu spoza punktacji oraz 9 obserwacji z 10 materiałów. Dwa nakładające się
komunikaty RCB połączono w jeden zapis dziennej sekwencji ostrzeżeń. Oceny
oznaczono `reviewer.type=agent`; drugi przegląd nie jest weryfikacją człowieka.

**W tym cyklu RTB pozostał niewyliczony:** cztery publikacje OSW miały pusty skrót RSS albo
sam spis treści. Zachowano wstrzymanie, bez uzupełniania treści z tytułu. Nowe
obserwacje są kontekstem cywilnym i obronnym; nie otrzymały punktów działań
RU/BY. Komentarz główny jest pominięty z powodu niepełnej analizy. Metodologia
wykonywana nadal ma wersję `rtb-v0.2`.

Raport ze stanem na **29.09.2026, 17:41 czasu Warszawy** opublikowano do
Supabase. Pakiety eksportu, chmury i lokalnego API są identyczne. Ponowienie
zwraca `created=false`, historia ma trzy rzeczywiste wydania. Przeglądarka
wyświetliła nową datę, obserwację w osi czasu i nowe wydanie w archiwum.
Replay dał identyczny wynik bez sieci. Potwierdzenie:
`data/analysis/cycles/2026-09-29T153254Z-d3ca4c60/verification.json` (poza Git).
Zachowano także 90 plików kodu i instrukcji z manifestem w
`data/analysis/code/<code_hash>/`; odtworzenie z tej kopii jest identyczne.

Weryfikacja kodu: **217 testów Python i 5 testów JavaScript/PostgreSQL**,
poprawny build frontendu. Pełna ścieżka komentarza została sprawdzona na
odseparowanych danych syntetycznych, bez publikowania ich do live.
Skorygowano także istniejący kontrakt snapshotu: obsługuje kategorię
`military_preparation` i kontekst strategiczny, już obecne w metodologii v0.2.

Harmonogram nie został włączony; lokalne zadanie będzie potrzebować włączonego
Maca i działającej aplikacji Codex. Hosting nowej aplikacji w Sites pozostaje
osobnym wdrożeniem. Zaplanowano wtedy: archiwizowanie pełnych treści brakujących
publikacji OSW, ustawienie harmonogramu Codexa oraz produkcyjny adapter WWW.
Wagi, kalibracja i wdrożenie v0.3 pozostają odrębnym zakresem. Kod tego etapu
jest lokalnie na gałęzi `codex/dashboard-publication`, bez nowego commita/pusha.

## Dashboard i publikacje — odbiór 27.09.2026

Użytkownik wybrał opcję 2, **B — Chronologia**, oraz zaakceptował kontrakt,
publikowanie i frontend. Design System 0.2 zapisuje tę decyzję w `design.md`,
`guidelines.md` i `theme.css`. `web/` zawiera działający interfejs, a
`schemas/dashboard/report.schema.json` kontrakt `dashboard-v1`.

Gotowe są weryfikacja zamrożonych wejść, ograniczony eksport, atomowy i
idempotentny wydawca, historia oraz lokalne API odczytu. Frontend sprawdza nowe
wydania co 30 sekund bez przebudowy. Zachowuje daty, niewyliczony RTB, braki
źródeł i brak skalibrowanej pewności. Wersji v0.2 nie oznacza jako v0.3.

Migrację czterech tabel i reguł RLS zastosowano w Supabase przez SQL Editor;
schemat potwierdzono zapytaniem kontrolnym. **CLI jest zalogowane, repozytorium
powiązane z projektem, historia migracji zgodna.** W Supabase są dwa rzeczywiste
wydania; syntetyczne dane pozostały lokalnie. Nowy raport z 27.09, 20:20 czasu
Warszawy, został zapisany, odczytany i automatycznie wyświetlony przez otwarty
dashboard. Wszystkie trzy wymagane źródła są gotowe; RTB pozostaje niewyliczony,
bo 32 materiały wymagają przeglądu. Ponowienie publikacji nie dodało duplikatu.
Eksport, pakiet Supabase i odpowiedź lokalnego API są identyczne. Szczegóły:
[stan Supabase](../supabase/README.md).

Sprawdzono lokalny cykl analiza → przegląd → eksport → publikacja → odczyt,
na odseparowanych danych syntetycznych. Ekran sam zmienił brak wyniku na 15 po
kolejnej publikacji. Testy PostgreSQL/PGlite potwierdzają atomowość, brak
duplikatów, niezmienność historii i role dostępu. Przeglądarka potwierdziła
mapę i szczegóły, zoom, duży widok, skalę osi czasu, oba filtry dziennika,
odczyt/pobranie raportu, menu mobile przy 320 px, stan awarii i powrót połączenia.

Nie wdrożono nowej aplikacji w Sites ani harmonogramu. Komentarz pozostaje
neutralnym brakiem podsumowania do czasu integracji rejestru zatwierdzonych
ustaleń. Dane osobnych pilotaży wymagają osobnych adapterów prezentacyjnych.
[Kontrakt](dashboard-data-contract.md), [uruchamianie](dashboard-runbook.md).

## Fundament pilotażu — wcześniejsze etapy

Etapy 0–2 mają działającą pierwszą wersję. Proces został uruchomiony na rzeczywistych źródłach i zakończony raportem z jawnym brakiem odczytu RTB. To fundament pilotażu, bez kompletnego pokrycia regionu i bez autonomicznego monitoringu.

## GitHub i Supabase — połączenie zweryfikowane 26.09.2026

Repozytorium [pixels4users/red-threat-meter](https://github.com/pixels4users/red-threat-meter/tree/main) ma gałąź `main`. Pierwsze opublikowane wydanie kodu `8a6ec9e` obejmuje 153 pliki, których drzewo Git porównano z przetestowanym stanem lokalnym; przed publikacją przeszło 140 testów. To weryfikacja istniejącego pilotażu, nie implementacja obliczeń v0.3. Wcześniejsza historia pozostaje lokalnie na `codex/foundation-pipeline` i `archive/local-main-before-github`; dane robocze oraz sekrety nie trafiły do GitHub.

Po zalogowaniu przez użytkownika sprawdzono panel Supabase: projekt `dubhsimiblpfcaudbvjb` (`red-threat-meter`) ma status **Healthy**, a integracja jest już połączona z właściwym repozytorium. Katalog roboczy to `.`, **Deploy to production** i **Automatic branching** są wyłączone. Pole gałęzi GitHub dla wdrożeń jest puste i nieaktywne; docelowe `main` ustawimy przy późniejszym uruchamianiu wdrożeń. W tym przeglądzie odczytano stan bez zmiany ustawień chmury, uprawnień ani planu.

Logowanie do panelu nie stanowi uwierzytelnienia lokalnego CLI ani testu połączenia PostgreSQL. Nie wykonano migracji, zapisu wyników do Supabase ani wdrożenia strony. Do zaprojektowania pozostają model udostępnianych danych, uprawnienia, publikowanie wyników z procesu Python oraz dashboard. Szczegóły i dalsza kolejność: [stan integracji Supabase](../supabase/README.md).

## Metodologia v0.3 — zaakceptowana specyfikacja

25.09.2026 użytkownik zaakceptował rozszerzenie o źródła pierwotne i aktualizację metodologii. [Metodologia v0.3](methodology.md) zastępuje dotychczasową specyfikację: określa wygaszanie, propagację 40% / 16%, korelację, efekt fali oraz dodatkowe warunki czerwonego priorytetu. Parametry pozostają eksperymentalne i nieskalibrowane. Ujednolicono instrukcje projektu, opis źródeł i procedury operacyjne.

**Pochodzenie danych:** bezpośrednio PAŻP, wydawcy ukraińscy, RSO/RCB oraz media i siły zbrojne państw bałtyckich. Strażnik jest odniesieniem architektonicznym, bez integracji jego agregatów lub interfejsu. ADS-B pozostaje w istniejącym strumieniu ADSB.lol; RCB rozszerza dotychczasowy kolektor. Rejestr `source-candidates-8` zapisuje akceptację 12 pozycji jako `accepted_for_integration` i datę decyzji, niezależnie od niezmienionej daty oceny dostępu. Pozostałych 26 pozycji zachowano bez zmian.

**Stan wdrożenia:** działający silnik, konfiguracja `config/scoring-v0.json` i instrukcje przeglądu w `agents/` nadal wykonują v0.2. Nowe kolektory, kontrakty i obliczenia v0.3 wymagają implementacji oraz walidacji. Dzienne GPSJAM nie spełnia wymogu korelacji w oknie 30 minut. Nie utworzono odczytu oznaczonego jako v0.3. Dokładną poprzednią metodologię i parametry zachowano w `docs/archive/methodology-v0.2.md` i `config/archive/scoring-v0.2.json` z kodu `2bccbb2`.

Weryfikacja tej aktualizacji: poprawny JSON, unikalne identyfikatory, lokalne odnośniki i kotwice oraz diff bez błędów formatowania. Archiwum v0.2 odpowiada oryginałowi bajt po bajcie. Raport RTB `2026-09-22T234233Z-c41c5e05` odtworzono identycznie bez sieci, z zachowaniem `RTB=null`. To sprawdzenie ciągłości istniejącego procesu; nie test nowego silnika. Zachowano wcześniejsze zmiany użytkownika w `aviation-access.md` i dostarczone skills. Zmiany pozostają lokalne, bez nowego commita.

**Następny uzgodniony krok:** osobno zaprojektować dashboard i sposób zasilania frontendu danymi. W tej aktualizacji nie rozpoczęto UI ani eksportu dla przeglądarki. Przed implementacją interfejsu pozostaje wybór spośród dwóch kierunków wizualnych; prezentowane wersje modelu, źródła i braki muszą odpowiadać rzeczywistym wydaniom danych.

## Historia lotnicza — bieżący wynik z 24.09.2026

Wydanie: **`ah-20260924T173557Z-a782c71a`**, stan analizy **24.09.2026, 19:35 czasu Warszawy**. [Raport lokalny](../data/aviation_history/snapshots/ah-20260924T173557Z-a782c71a/report.md). Kod odtworzenia: **`524e033`**. [Metoda, dostęp i obsługa](aviation-history.md).

Dodano `scripts/aviation_history.py`, konfigurację `config/aviation-history.json`, walidację binarnego formatu, raport po polsku, agregaty GeoJSON i odtwarzanie bez sieci. Dane są w osobnym `data/aviation_history/`; pobranie ma stały plan najwyżej trzech półgodzinnych plików i limit 96 MB, bez automatycznych ponowień. Zapisano oryginalne treści, czasy, nagłówki, statusy HTTP oraz sumy kontrolne. Przegląd faktycznie serwowanego kodu mapy i kodu producenta ustalił znaczenie pól; kopie dowodów są w `data/research/aviation-history-2026-09-24/`.

Rzeczywiste pobranie trwało od **17:20:44 do 17:20:52 UTC**. Zebrano okna **16:30–17:00 UTC z 22, 23 i 24.09.2026**, dla regionu `[14,49,29,60]`. Wszystkie trzy odpowiedzi miały HTTP 200. To **78 108 013 bajtów treści (78,1 MB)** i **88 119 536 bajtów po rozpakowaniu**. Nie pobierano wielogigabajtowych archiwów dziennych.

| Dzień | Przedziały po 10 s | Min / mediana / max identyfikatorów na przedział | Unikalne identyfikatory w 30 minutach | Pola z obserwacją |
|---|---:|---:|---:|---:|
| 22.09 | 180/180 | 125 / 160 / 193 | 418 | 117/165 |
| 23.09 | 180/180 | 108 / 196,5 / 226 | 480 | 124/165 |
| 24.09 | 180/180 | 141 / 162 / 181 | 429 | 123/165 |

Odczytano **540/540 przedziałów**, bez luk na osi czasu. W pliku 23.09 odrzucono jeden rekord z niedopuszczalną ujemną prędkością (poza naszym regionem); okno ma stan częściowy, pozostałe dwa — poprawny. JSON zachowuje indeks rekordu, przedział i przyczynę odrzucenia. Obserwacje w każdym z trzech okien występowały w 107 polach, a w co najmniej jednym — w 135. **Nie jest to pomiar zasięgu odbiorników ani kompletności wszystkich lotów.**

Porównanie z trzema zachowanymi próbkami API wybiera ostatni pełny przedział historii zakończony przed rozpoczęciem danego pobrania API. Odstęp wynosił 2,7–4,8 sekundy. Liczniki API / historia / wspólne identyfikatory to kolejno **231 / 168 / 167**, **223 / 163 / 162** i **225 / 161 / 159**. Historia ma odmienne reguły doboru pozycji; nie zawiera dokładnego czasu każdej pozycji, kodów typu samolotu ani flag wojskowych. Oba produkty pochodzą z tej samej grupy ADSB.lol, bez niezależnej prawdy referencyjnej.

**Decyzja: zachowujemy dwie osobne serie.** Łączenie ich liczników mogłoby wywołać pozorną anomalię wynikającą z formatu. Z trzech krótkich okien nie wyznaczamy normalnego poziomu, alarmu ani aktywności RU/BY lub NATO. Dzisiejsze etykiety nie uzupełniają historycznej klasyfikacji. Dane pozyskane wieczorem nie udają wiedzy dostępnej w chwili wcześniejszych pomiarów; pierwotna dostępność u dostawcy pozostaje nieustalona.

Weryfikacja: **140 testów poprawnych, w tym 16 nowych przypadków historii**. Sprawdzono strukturę gzip i indeksów, jednostki i znaczniki, duplikaty i konflikty, odróżnienie braków od zer, błędy i limity transportu, chronologię porównania, odtwarzanie i wykrywanie zmiany dowodów. Replay raportu jest identyczny i nie używa sieci. Dotychczasowe wydania API, GNSS/logistyki i RTB v0.2 także nadal odtwarzają się identycznie; **RTB pozostaje `null`**.

Pełna kopia danych i kodu: `data/aviation_history/backups/backup-20260924T174126Z/`. Zweryfikowano **14 plików manifestu**, odtworzono dane i całe archiwum kodu do osobnego katalogu tymczasowego. Raport odtworzono identycznie z zablokowaną siecią i bez katalogu bieżących danych API. Potwierdzenie: `data/research/aviation-history-2026-09-24/restore-verification.json`. Instrukcja kopii uwzględnia również parser RSS importowany przez wspólny moduł procesu. To lokalna kopia, bez drugiego nośnika.

Rejestr ma wersję `source-candidates-6`. Nie dodano harmonogramu, opłat, alertów ani UI. Kolejna walidacja danych obejmie różne pory i dni, stabilność źródła i rejestr klas obiektów z datami obowiązywania. Można ją prowadzić obok następnego etapu produktu: wyboru spośród dwóch kierunków dashboardu, który pokaże osobno rodziny danych i ich aktualność.

## Pilotaż jakości ADSB.lol — wcześniejszy wynik z 24.09.2026

Wydanie: **`av-2026-09-24T164929Z-d612456c`**, stan wiedzy **24.09.2026, 18:49 czasu Warszawy**. [Raport lokalny](../data/aviation/snapshots/av-2026-09-24T164929Z-d612456c/report.md). Kod odtworzenia wszystkich trzech wydań lotniczych: **`60851cb`**. [Instrukcja obsługi i metodologii](aviation-runbook.md).

Wdrożono osobny kolektor `scripts/aviation.py` i uruchamianie przez `Zbierz dane lotnicze.command`. Konfiguracja `config/aviation.json` wyznacza bbox `[14,49,29,60]`, cztery koła po 250 NM i limity zapytań. Dane trafiają do `data/aviation/`, z archiwum odpowiedzi, bazą SQLite, polskim raportem, JSON i agregatami siatki GeoJSON. Prawidłowy adres specyfikacji to `/api/openapi.json`; wcześniejszy 404 dotyczył innej ścieżki.

Przeprowadzono **trzy ręczne próby**, od 16:45:04 do 16:49:29 UTC. **12/12 zapytań HTTP 200**, bez niezgodnych wierszy; 0 prób częściowych i niedostępnych. To krótki test dostępu i jakości formatu, bez dowodu niezawodności całodobowej.

| Koniec próby UTC | Wiersze przed usunięciem powtórzeń | Usunięte powtórzenia | Świeże identyfikatory w regionie | Pola siatki z obserwacją | Mediana / P95 wieku pozycji |
|---|---:|---:|---:|---:|---:|
| 16:45:15 | 507 | 105 | 231 | 73/165 | 9,104 / 26,326 s |
| 16:46:59 | 514 | 108 | 223 | 76/165 | 6,967 / 26,080 s |
| 16:49:29 | 520 | 111 | 225 | 78/165 | 5,655 / 16,718 s |

Pozostałe identyfikatory ostatniej próby (184) miały najnowszą pozycję poza prostokątem. **87/165 pól nie miało świeżej obserwacji**, choć zapytania obejmowały ich obszar; nie uznajemy ich za przestrzeń bez ruchu. Zasięg odbiorników pozostaje nieustalony. Przerwy pomiędzy końcem a początkiem prób wyniosły 97,083 i 143,489 sekundy — nie były okresem monitorowanym. Najmniejszy zmierzony odstęp między początkiem żądań wyniósł 2,003 sekundy.

W ostatniej próbie 42 identyfikatory miały oznaczenie naziemne, a 183 liczbową wysokość barometryczną. Źródło zawiera też kody `TWR` i `GND`; **225 identyfikatorów nie oznacza 225 lotów ani samolotów**. Dostawca ustawił flagę wojskową dla 4 identyfikatorów; dla 6 bit był nieustawiony, w 215 rekordach brak pola flag. Nie potwierdzono niezależnie operatorów ani zadań. Zmiana między trzema próbkami nie jest skalibrowaną anomalią.

Archiwum: **3 próbki, 3 wydania, 12 surowych odpowiedzi, 934 677 bajtów odpowiedzi**. Każdy odczyt zachowuje czasy, źródło, status i hash. Osobny wstępny odczyt jednego koła oraz kopia specyfikacji znajdują się w `data/research/aviation-pilot-2026-09-24/`; nie dodają czwartej regionalnej próby do bazy. Nie pobierano wielogigabajtowej historii.

Weryfikacja: **124 testy poprawne, w tym 25 nowych przypadków lotniczych**. Sprawdzono duplikaty, jednostki, nieaktualne i przyszłe dane, brak pozycji, niezgodne wiersze, puste odpowiedzi, częściową awarię, limit 429/Retry-After, przekierowania, zbyt dużą odpowiedź, zmianę konfiguracji, granicę czasu, niezmienność archiwum, atomowy eksport i oddzielenie danych testowych. `doctor` potwierdził integralność bazy i 12 plików. Bieżący replay jest identyczny bez sieci.

Pełną kopię zapisano w `data/aviation/backups/backup-2026-09-24T165036Z/`, używając SQLite backup pod blokadą. Sprawdzono 31 plików manifestu; kopię odtworzono do osobnego katalogu tymczasowego. Liczniki i integralność są zgodne, **wszystkie trzy raporty odtworzono identycznie bez sieci**. Potwierdzenie: `data/research/aviation-pilot-2026-09-24/restore-verification.json`. To kopia lokalna, nie kopia na drugim nośniku.

Dotychczasowe raporty GNSS/logistyki (`ew-2026-09-23T133506Z-41e96c7e`) oraz RTB v0.2 (`2026-09-22T234233Z-c41c5e05`) nadal dają identyczny replay; **RTB pozostaje `null`**. Nie zmieniono ich baz, ocen ani dat pozyskania. Rejestr integracji ma wersję `source-candidates-5`.

Kolektor działa po ręcznym uruchomieniu, bez harmonogramu, nowych opłat, modelu klasyfikującego misje i alertów. Sprawdzono polecenia Python i składnię `.command`; nie testowano dwukliku w Finderze. Nie zmieniono UI. Zapowiedziany wówczas dobór ograniczonej historii wykonano w opisanym wyżej audycie; przygotowanie dashboardu pozostaje osobnym etapem z dwoma kierunkami wizualnymi do wyboru.

## Polskie treści, porównanie GNSS i ocena lotnictwa — wynik z 23.09.2026

Wydanie: `ew-2026-09-23T133506Z-41e96c7e`, stan wiedzy **23.09.2026, 15:35 czasu Warszawy**. Raport: `data/early_warning/snapshots/ew-2026-09-23T133506Z-41e96c7e/report.md`. Kod odtworzenia: **`4137138`**. Nie pobierano ponownie GPSJAM ani RSS; źródła zachowują rzeczywiste czasy kontroli około 14:15.

- **10/10 publikacji ma polski tytuł i streszczenie**, 0 oczekujących tłumaczeń. Oryginały i cytaty pozostają nienaruszone. Opisy są przypisane do konkretnych wersji i zachowują osobne rewizje; nowa treść wymaga nowego tłumaczenia. Brak automatycznego API tłumaczącego — kolejka jest obsługiwana w przeglądzie agenta.
- Przejrzano wstępnie pozostałe pięć publikacji. Łącznie **11 ocen agenta**: 10 publikacji i najnowsza doba GNSS. Nie jest to niezależne potwierdzenie wszystkich twierdzeń ani weryfikacja wszystkich tabel i załączników.
- **Działa opisowe porównanie GNSS** na wspólnych komórkach. Przy minimum próby 5: 491 komórek, 26 wcześniejszych dób, 13,85% wobec mediany 18,33%, różnica −4,48 pkt proc. Raport pokazuje też warianty minimum 1, 10 i 20. Odniesienie nie jest skalibrowanym poziomem normalnym; brak automatycznego progu alarmowego. [Metoda](gnss-reference-methodology.md).
- [Ocena danych lotniczych](aviation-access.md): jednorazowy odczyt OpenSky HTTP 200, 303 rekordy stanu; wymóg osobnej umowy dla stałego użycia operacyjnego. Sprawdzono dokumentację ADSB.lol i metadane dziennego archiwum oraz ograniczenia oferty ADS-B Exchange i OpenAPI WorldMonitor. ADSB.lol jest proponowanym źródłem następnego małego pilotażu, po ustaleniu kontraktu odpowiedzi i pomiarze jakości. Brak kolektora lotniczego i nowych opłat.

Stan bazy obserwacji: **40 wersji, 53 odczyty, 4 kontrole źródeł, 11 ocen, 10 tłumaczeń, 5 wydań**. Migracja do wersji 2 dodała tłumaczenia; przed migracją wykonano kopię SQLite. Porównano wszystkie wcześniejsze wiersze obserwacji, pobrań, kontroli i ocen z kopią — pozostały identyczne. Surowe archiwum nadal zawiera 32 sprawdzone pliki.

Weryfikacja: **99 testów poprawnych**, w tym 16 nowych przypadków tłumaczeń i porównania GNSS. Sprawdzono odrzucanie niezgodnego dowodu i wersji, atomowy import, rewizje, granicę czasu, migrację, zmianę pokrycia i dostawcy, brak najnowszej doby oraz flagi jakości. Bieżący raport nie zawiera nieprzetłumaczonej cyrylicy; źródła dowodowe ją zachowują. Replay nowego wydania jest identyczny i nie używa sieci; taki sam wynik uzyskano po odtworzeniu bazy, surowych danych i wydania do osobnego katalogu tymczasowego. Dotychczasowy replay RTB v0.2 nadal jest identyczny (`rtb=null`).

Dla roboczego wydania `ew-2026-09-23T131458Z-80ddeb12` zachowano dokładną kopię kodu w `data/early_warning/backups/code-ew-2026-09-23T131458Z-80ddeb12/` i także zweryfikowano identyczne odtworzenie. Nie zmieniano historycznych raportów. Nie wykonano przebudowy UI ani uruchomienia harmonogramu.

## Pierwsze wdrożenie sygnałów wczesnych — wcześniejszy stan z 23.09.2026

Po zaakceptowaniu planu uruchomiono osobną warstwę `early-warning-1`: kontrakt obserwacji, dzienne CSV GPSJAM, RSS belzhd, SQLite, historię pobrań i wersji, raport jakości, GeoJSON oraz przegląd z dowodami. Konfiguracja: `config/early-warning.json`. Uruchomienie: `Zbierz sygnały wczesne.command` albo `scripts/early_warning.py`. [Pełna instrukcja](early-warning-runbook.md).

Rzeczywisty wynik:

| Miara | Wynik |
|---|---:|
| Dobowe siatki GNSS | 30/30, od 24.08 do 22.09.2026 |
| Publikacje belzhd | 10, w tym 4 z rubryki przewozów wojskowych |
| Unikalne wersje obserwacji | 40 |
| Ponowne pobranie 3 dni + RSS | 0 nowych wersji; 13 kolejnych odczytów |
| Wstępne oceny agenta | 6: najnowsza doba GNSS, 4 materiały wojskowe, 1 publikacja okolicznościowa |
| Pozostałe publikacje oczekujące na przegląd | 5 |
| Najnowsza siatka: komórki obserwowane / w obszarze | 643 / 771 |
| Komórki bez obserwacji / poniżej roboczego minimum próby 5 | 128 / 93 |

Manifest wskazuje zmianę `adsbexchange` → `merged` od 27.08.2026. W oknie jest 26 wcześniejszych dób z takim samym zestawem dostawców jak ostatnia doba, bez flagi suspect; wspólne minimum próby spełnia 491 komórek. To diagnostyka pokrycia, a nie skalibrowane odniesienie. Wskaźnik dobowy nie dowodzi ciągłości zakłóceń ani sprawcy. Stany ocen nie zmieniają RTB.

RSS rubryki belzhd zwrócił 403; działa główny, publiczny RSS. Nie podłączono Telegrama. Wstępny przegląd odróżnia niedobór wagonów opisany pod koniec sierpnia, prace nad rezerwowym zarządzaniem, planowaną infrastrukturę, retrospektywne zestawienie i treść okolicznościową. Nie potwierdzono niezależnie twierdzeń wydawcy, nie sprawdzono wszystkich tabel ani załączników.

Raport po ocenach: `data/early_warning/snapshots/ew-2026-09-23T122426Z-f3c0f43b/report.md` (14:24 czasu Warszawy). Odczyty źródeł pozostają z rzeczywistego pobrania około 14:15. Pierwsze dwa wydania zachowano; odpowiadają kodowi `a3848e1`.

Weryfikacja: **83 testy**, w tym 21 nowych przypadków dotyczących braków danych, pochodzenia, dat, błędnych pomiarów, duplikatów, zmiany treści, cofnięcia do starszej wersji, przeglądu i atomowego eksportu. Rzeczywista baza i 32 pliki surowego archiwum przeszły kontrolę integralności. Odtwarzanie nowych danych i istniejącego RTB v0.2 daje identyczne wyniki bez sieci. Kopię SQLite wraz z materiałami odtworzono do osobnego katalogu tymczasowego; liczniki, integralność i replay były zgodne. Brak frontendowych mocków i nowych danych syntetycznych w bazach live.

Nie podłączono API AUGUR ani ADS-B, nie skalibrowano detektora, nie dodano harmonogramu, płatnych usług, alertów ani strony WWW. Kod przetestowano lokalnie. Obsługę dwuklikiem w Finderze pozostawiono bez testu interaktywnego.

## Aktualizacja metodologii v0.2

Ujednolicono instrukcje trzech agentów, konfigurację, kontrakty JSON, metodologię i dokumentację obsługi. Obecny cel to OSINT / I&W dla Polski i flanki NATO. Dawne cele osobiste pozostały wyłącznie w oznaczonym archiwum.

- Dodano `military_preparation` (15 pkt, limit 30), z wymogiem dowodów zmiany, odniesienia, znaczenia operacyjnego i sprawdzenia rutynowego wyjaśnienia. Białoruś oraz obwód królewiecki mają jawne kryteria zakresu.
- Rozdzielono wkłady działań i przygotowań. Ponad 60 punktów oznacza przegląd analityczny; próg nie jest skalibrowaną prognozą.
- Dodano obszary strategiczne jako priorytet, bez bonusu punktowego, i szablon scenariuszy warunkowych na 14–42 dni.
- Oddzielono kolektory, kandydatów na źródła oraz bibliotekę doktryny. Nowe źródła operacyjne są opisane, ale nie podłączone.
- Zarejestrowano materiały użytkownika i oba linki. Lokalny indeks obejmuje **2295 stron tekstu z 10 dostępnych PDF-ów**; dwa wcześniejsze pliki Romera są oznaczone jako nieobecne. Indeksacja nie jest pełną analizą treści ani semantycznym RAG.

Kontrolny eksport offline v0.2: `2026-09-22T234233Z-c41c5e05` (23.09.2026, 01:42 czasu Warszawy). Nie pobierano nowych informacji. RTB pozostaje `null` z powodu dwóch nieocenionych materiałów i kontroli RCB/MON/OSW starszych niż osiem godzin. `alert.status=not_assessed`; brak delty. Daty pobrań zachowano. Raport: `data/snapshots/2026-09-22T234233Z-c41c5e05/report.md`.

Weryfikacja tej aktualizacji: **62 testy poprawne**, w tym nowa kategoria, zakres regionalny, progi, brak punktów za priorytet geograficzny, odrzucenie doktryny jako dowodu oraz integralność i numeracja stron indeksu. Nowy replay dał identyczny wynik bez sieci. Pliki pierwszego wydania v0.1 pozostają zgodne z pierwotnym manifestem. Sprawdzono rzeczywiste wyszukiwanie i hashe wszystkich dostępnych PDF-ów. Biblioteka i dane live pozostają poza Git.

## Fundament dostarczony 22.09.2026

- Repozytorium Git: oryginalne materiały zachowane w commicie `759ccd3`, implementacja na gałęzi `codex/foundation-pipeline`. Brak skonfigurowanego zdalnego repozytorium.
- Python 3.13.7 w `.venv`, przypięte zależności, konfiguracja źródeł i metodologii, JSON Schema dla oceny, zdarzenia i odczytu.
- Kolektory RCB, MON i RSS, zachowanie surowych odpowiedzi, kontrola dostępu, ponowienia i rejestrowanie braków.
- SQLite z migracją, blokadami zmian tabel audytu, wersjami materiałów i ocen oraz spójną kopią bazy.
- Kolejka przeglądu, instrukcje ekstraktora i analityka, import ocen z walidacją cytatów i deklarowanej niezależności źródeł.
- Deterministyczny scoring z oknem czasu, deduplikacją zdarzeń, limitami kategorii i blokowaniem odczytu przy niepełnych danych.
- Wersjonowany raport Markdown, JSON i GeoJSON, atomowa zmiana wskaźnika wydania, odtwarzanie obliczeń bez sieci.
- Polecenia do obsługi oraz plik `Zbierz dane.command` dla macOS. Skrypt `scripts/ingest.py` i dostarczone skills pozostają zachowanymi materiałami; parser RSS jest używany przez nowy moduł.

## Pierwszy rzeczywisty wynik — archiwum v0.1

Wydanie: `2026-09-22T141737Z-326ba3f8`; stan wiedzy 22.09.2026, 16:17 czasu Warszawy.

Raport lokalny: `data/snapshots/2026-09-22T141737Z-326ba3f8/report.md`.

| Miara | Wynik |
|---|---:|
| Unikalne wersje publikacji | 44 |
| RCB / MON / OSW | 20 / 14 / 10 |
| Nowe materiały przy powtórnym pobraniu | 0 |
| Publikacje z oceną agenta | 42 |
| Zachowane obserwacje kontekstowe | 9 |
| Wykluczenia z uzasadnieniem | 33 |
| Publikacje wymagające pełnej treści | 2 |
| Kwalifikujące się punkty | 0 |
| Główny RTB | `null`, przegląd niepełny |

Naval News zwróciło 503 w obu przebiegach i jest jawnie niedostępne. CERT pozostaje wyłączony po próbie 403. Dwie nierozstrzygnięte pozycje OSW to „Najsilniejsza armia w Europie”? (w kanale tylko spis treści) oraz „Rosjanie uderzają przy granicy z Polską. 1665. dzień wojny” (pusty skrót). Nie zastąpiono braku informacji oceną 10/100.

Oceny dotyczą zapisanych treści: oficjalnych komunikatów RCB/MON i skrótów RSS OSW. Nie oznaczają niezależnego potwierdzenia wszystkich twierdzeń wydawców. Żaden punkt nie otrzymał zgadywanych współrzędnych; w pierwszym GeoJSON geometrie są `null`.

## Weryfikacja pierwszej dostawy z 22.09.2026

Wówczas 40 testów zakończonych poprawnie. Sprawdzono m.in. zachowanie aktualizacji komunikatu, błędne i przyszłe daty, awarie źródeł, powielanie materiałów i zdarzeń, wspólne pochodzenie kopii, brak dowodu sprawcy, korekty i przywracanie kwalifikacji, ograniczenia kategorii, zmianę konfiguracji źródła, granicę czasu, przerwany eksport, współbieżną blokadę, oddzielenie fixture/live i wykrywanie zmiany wydania.

Potwierdzono także na danych rzeczywistych:

- ponowny odczyt trzech źródeł bez tworzenia duplikatów;
- integralność SQLite i brak błędów powiązań;
- identyczny replay pierwszego wydania, bez żądań sieciowych;
- odtworzenie kopii bazy, materiałów i wydania do osobnego katalogu tymczasowego, zgodne liczniki i identyczny replay.

Sprawdzono składnię skryptów Python oraz skryptów powłoki. Samo otwarcie `Zbierz dane.command` dwuklikiem w Finderze nie było testowane. Dane demonstracyjne uruchomiono osobno w `data/demo/`; są oznaczone jako syntetyczne i nie weszły do bazy live.

## Wcześniejszy plan kolejnych prac — 22.09.2026

1. Po zakończonych pilotażach API i historii badać różne pory i dni oraz stabilność źródła, z budżetem opartym na zmierzonym rozmiarze. Opracować rejestr klas obiektów z datami obowiązywania; zachować oddzielne serie historii i API. Rozwinąć niezależną weryfikację publikacji oraz rejestr wyników do przyszłej kalibracji GNSS. Wszystkie 10 publikacji ma już wstępny przegląd i polskie opisy. Uzupełnić nierozstrzygnięte pozycje OSW i źródła weryfikujące. Krótkie próby nie kalibrują zdolności przewidywania.
2. Etap 3, obok dalszej walidacji danych: przedstawić dwa kierunki wizualne, zapisać wybór w `design.md`, `guidelines.md`, `theme.css` i zbudować dashboard. Rozdzielić rodziny danych i ich aktualność. Mapa musi obsługiwać brak geometrii, a wykres brak odczytu. Delta pozostaje pusta do uzyskania porównywalnych okresów.
3. Etap 4: wybrać sposób automatycznego przeglądu AI, zmierzyć jakość i koszt, dodać harmonogram oraz kopie na osobnym nośniku. Skrypty działają obecnie po ręcznym uruchomieniu.
4. Walidacja: opisać historyczne przypadki, kontrprzykłady i sprostowania; sprawdzić wagi oraz próg przeglądu, zbudować serie odniesienia dla anomalii. Rozwijać scenariusze bezpieczeństwa z jawną niepewnością.

Nie uruchomiono płatnych API, modelu predykcyjnego, publicznego hostingu ani wysyłania alertów.

Wcześniejsze uzupełnienie dokumentacyjne po komentarzu o wskaźnikach wyprzedzających: sprawdzono dokumentację dostawców i aktualność źródeł, zapisano projekt warstwy wczesnej oraz rejestr `source-candidates-2`. Nie uruchamiało kolektorów. Kolejne wdrożenie podłączyło osobny pilotaż i rejestr `source-candidates-3`. Ocena dostępu lotniczego dała `source-candidates-4`, pilotaż API ADSB.lol — `source-candidates-5`, a ograniczony audyt historii — `source-candidates-6`. Wagi i dane RTB pozostają bez zmian.
