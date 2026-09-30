# Dane lotnicze — wynik oceny dostępu

**Aktualizacja 24.09.2026:** wdrożono ręczny regionalny pilotaż ADSB.lol i potwierdzono rzeczywiste odpowiedzi. Właściwa specyfikacja znajduje się pod adresem [api.adsb.lol/api/openapi.json](https://api.adsb.lol/api/openapi.json). Kolektor, ograniczenia zapytań i interpretację danych opisuje [instrukcja pilotażu](aviation-runbook.md); wyniki pomiarów są w [stanie realizacji](STATUS.md). Nie uruchomiono ciągłego monitoringu, katalogu lotów wojskowych ani detektora aktywności.

**Uzupełnienie historii 24.09:** pobrano trzy półgodzinne pliki odtwarzania mapy, łącznie 78 108 013 bajtów. Zmierzone różnice formatu i doboru pozycji wymagają utrzymania historii oraz API w osobnych seriach. To odrębny produkt od pełnego dziennego archiwum śladów; rozmiaru tej próby nie ekstrapolujemy na wszystkie doby. [Metoda i dostęp](aviation-history.md).

**Poniżej zachowano ocenę z 23.09.2026**, sprzed wdrożenia kolektora. Obejmowała dokumentację, jeden ograniczony odczyt OpenSky oraz metadane jednego archiwum ADSB.lol. Dawny status ADSB.lol „kandydat” i nieudane szukanie domyślnego `/openapi.json` są zapisem historycznym.

## Wybór do następnego pilotażu

**Proponuję zacząć od technicznego pilotażu ADSB.lol**, ponieważ publikuje API i historię na jawnej licencji. Najpierw trzeba potwierdzić aktualny kontrakt odpowiedzi oraz zmierzyć jakość w naszym regionie. OpenSky zachowujemy jako sprawdzony technicznie wariant wymagający uzgodnienia użycia operacyjnego. Nie ma jeszcze podstaw do zakupienia planu ADS-B Exchange ani WorldMonitor.

|  | Dokumentacja publicznego API i archiwum, aktualne metadane wydania | Dostawca deklaruje otwarte dane na ODbL 1.0; jeden sprawdzony zestaw dzienny ma ok. 3,84 GB | Kandydat na pilotaż; odpowiedzi pomiarowej jeszcze nie testowano |
| OpenSkyWariant | Sprawdzone | Historia i koszt | Stan integracji |
|---|---|---|---|
| ADSB.lol | Anonimowy odczyt regionalny HTTP 200 | Dostęp techniczny bez klucza; stałe użycie operacyjne wymaga osobnej umowy | Jednorazowy test badawczy, bez podłączenia do procesu |
| ADS-B Exchange | Dokumentacja API i oferta | Plan hobbystyczny: 10 USD/miesiąc, 10 000 zapytań; historii nie zakładamy w tej cenie | Klucz i plan nieuruchomione |
| WorldMonitor | Dokumentacja, uwierzytelnianie i OpenAPI | Nie potwierdzono ceny potrzebnego API ani dostępności długiej historii | Nie testowano endpointu wymagającego klucza |

## ADSB.lol — otwarta historia, koszt przetwarzania do zmierzenia

Dostawca udostępnia publiczne [API](https://www.adsb.lol/docs/open-data/api/) oraz [dzienne archiwa](https://www.adsb.lol/docs/open-data/historical/) z licencją ODbL 1.0. Dokumentacja opisuje pliki JSON gzip dla poszczególnych statków powietrznych, w wydaniach GitHub dla różnych instancji zbierających dane. Nie należy sumować instancji jako niezależnych lotów ani dowodów.

Metadane wydania `v2026.09.22-planes-readsb-staging-0` opublikowanego 23.09 o 04:40 UTC wskazują dwie części o rozmiarach 2 000 000 000 i 1 841 244 672 bajtów. To **3,84 GB dla jednej sprawdzonej doby jednej instancji**, bez rozpakowania. Nie ekstrapolujemy tej próby na stały rozmiar każdej doby. Nie pobierano tych dużych plików. [Repozytorium archiwum](https://github.com/adsblol/globe_history/releases).

Próba odczytu `https://api.adsb.lol/openapi.json` zwróciła 404; nie traktujemy domyślnej ścieżki specyfikacji jako potwierdzonego kontraktu API. Następny krok to ustalenie kontraktu według aktualnej dokumentacji i mała próba regionalna, dopiero potem selektywne przetwarzanie historii. Trzeba zmierzyć dysk, czas, pokrycie, luki oraz jakość klasyfikacji operatora. Otwartość danych nie oznacza kompletności odbioru. Warunki licencji zachowujemy przy dalszym wykorzystaniu i ewentualnym eksporcie.

## OpenSky — dostęp potwierdzony, użycie operacyjne odrębne

23.09 o 13:08:33 UTC zapytanie `states/all` dla bbox `[14,49,29,60]` zwróciło **HTTP 200 i 303 rekordy bieżącego stanu**, wszystkie z pozycją. Nagłówek limitu wskazał 397 pozostałych kredytów. To jedna chwila pomiaru, nie liczba lotów wojskowych, liczba operacji dobowych ani pomiar pełności pokrycia. Odpowiedź i potwierdzenie odczytu zachowano lokalnie w `data/research/aviation-access-2026-09-23/opensky-{response,probe}.json`.

Dokumentacja opisuje anonimowe stany bieżące, limit 400 kredytów/dobę i koszt 3 kredytów dla prostokąta 100–400 stopni kwadratowych. Nasz prostokąt ma 165 takich jednostek. Obliczenie planistyczne: 96 odczytów co 15 minut kosztowałoby 288 kredytów/dobę, bez powtórek i innych zapytań z tego samego IP. Nie uruchomiono takiego harmonogramu. `origin_country` wynika z adresu ICAO, nie potwierdza operatora wojskowego. Dostęp do historycznych stanów po uwierzytelnieniu sięga godziny; inne endpointy lotów i tras mają inne ograniczenia i nie zastępują automatycznie porównywalnej serii regionalnej. [REST API](https://openskynetwork.github.io/opensky-api/rest.html).

Aktualne warunki wymagają pisemnej umowy dla operacyjnego użycia REST API w działającym produkcie lub automatycznym systemie, również wewnętrznym. Dlatego udany test techniczny nie oznacza gotowej podstawy stałego monitoringu. Nie wysyłano zapytania do dostawcy ani nie tworzono konta. [Warunki OpenSky](https://opensky-network.org/about/terms-of-use).

## ADS-B Exchange — cena API nie rozstrzyga dostępu do historii

Oferta hobbystyczna obejmuje 10 000 zapytań za 10 USD/miesiąc. Historia jest wymieniona w ofercie Enterprise; nie uznajemy jej za część najtańszego planu. Przy jednej prośbie o dane co 15 minut wychodzi 2880 zapytań przez 30 dni, a co minutę — 43 200; dodatkowe regiony, strony i powtórki zwiększają tę liczbę. To obliczenie, nie pomiar przyszłych rachunków. [Developer Hub](https://adsbexchange.com/community/developer-hub/).

Przed zakupem trzeba potwierdzić zakres regionu, archiwizację, historię i prawo do użycia w tym systemie. ADS-B Exchange jest też dostawcą GPSJAM; wspólnego pochodzenia nie liczymy jako dwóch niezależnych potwierdzeń. Nie zakupiono subskrypcji.

## WorldMonitor — sprawdzić rzeczywisty zakres usługi

API wymaga klucza i odpowiedniego uprawnienia. Dostęp do interfejsu użytkownika nie potwierdza uprawnień API. [Uwierzytelnianie](https://www.worldmonitor.app/docs/usage-auth).

W pobranej specyfikacji `ListMilitaryFlights` parametry `operator` i `aircraft_type` są opisane jako przyjmowane, lecz obecnie ignorowane. Nie można opierać filtrowania na przykładzie z lokalnego skilla bez sprawdzenia odpowiedzi. Zachowano kopię specyfikacji i wyciąg w `data/research/aviation-access-2026-09-23/worldmonitor-{openapi,assessment}.json`. [OpenAPI](https://www.worldmonitor.app/openapi.json).

Dokumentacja opisuje obecnie ADSB.lol jako podstawę zbierania, Wingbits jako uzupełnienie i dodatkowych dostawców awaryjnych; zawiera też starsze odniesienia do OpenSky. Nie testowano tego łańcucha na odpowiedzi live. Krótki ślad pozycji i gotowe klasyfikacje nie są dowodem dostępności porównywalnej historii 30–90 dni ani sprawdzonym detektorem zagrożenia. [Opis modułu lotniczego](https://www.worldmonitor.app/docs/military-tracking).

## Kryteria odbioru kolektora lotniczego

Kolejny etap powinien dostarczyć małą serię pomiarową z jawnymi brakami i pochodzeniem, bez kopiowania niezweryfikowanych alertów dostawcy:

1. Zachowane odpowiedzi, daty pomiaru i pobrania, wersja parsera, jednostki i limit zapytań; brak pozycji pozostaje `null`.
2. Stały region i próbki czasu, rozdzielone zmiany dostawcy, kontrola duplikatów. Pojedynczy transponder w wielu próbkach nie jest wieloma lotami.
3. Klasyfikacja operatora i typu z osobnym źródłem oraz niepewnością. Państwo przypisane adresowi ICAO nie wystarcza do identyfikacji operatora.
4. Raport jakości: odsetek próbek bez danych, wiek pozycji, obszary bez odbioru i zgodność formatów. Bez twierdzenia, że obserwujemy wszystkie loty.
5. Dłuższa historia przetwarzana po pomiarze rozmiaru i kosztu; znane opóźnienia oraz pierwotna dostępność. Wspólny dostawca z GPSJAM lub WorldMonitor jest jawną zależnością.

Ten etap nie wymaga wyboru progu alarmowego ani zakupu planu. Oddzielne szeregi aktywności RU/BY i wsparcia NATO mają sens dopiero po sprawdzeniu klasyfikacji i reprezentatywności próby. Wzrost liczby widocznych maszyn sam nie określa zadania misji ani zamiaru ataku.
