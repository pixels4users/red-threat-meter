# Pilotaż jakości danych lotniczych ADSB.lol

Stan kontraktu: **24.09.2026**, `aviation-pilot-1`. Działa ręczny kolektor, lokalne archiwum odpowiedzi, SQLite, raport po polsku oraz przestrzenne agregaty GeoJSON. Wyniki rzeczywistych prób i identyfikator wydania są w [stanie realizacji](STATUS.md). To obserwacje nadajników; nie ma jeszcze katalogu lotów, zweryfikowanych operatorów ani detektora anomalii.

## Uruchomienie

Na przygotowanym Macu: **`Zbierz dane lotnicze.command`** w głównym katalogu projektu. Jedno uruchomienie pobiera jedną próbę i otwiera raport. Polecenia Python sprawdzono w Terminalu, a dla pliku `.command` zweryfikowano składnię. Dwuklik w Finderze nie był testowany interaktywnie.

Polecenia z katalogu projektu:

```sh
.venv/bin/python scripts/aviation.py collect
.venv/bin/python scripts/aviation.py report
.venv/bin/python scripts/aviation.py doctor
.venv/bin/python scripts/aviation.py replay
```

`collect` wykonuje najwyżej cztery odczyty regionalne. `report` tworzy nowe wydanie ze zgromadzonych próbek bez internetu, zachowując rzeczywisty czas pomiaru. `doctor` sprawdza SQLite, kontrakty i hashe wszystkich zapisanych odpowiedzi. `replay` odtwarza ostatnie wydanie, a `replay ID` — wskazane. Odtwarzanie wymaga tej samej wersji kodu; nie korzysta z sieci.

Konfiguracja: `config/aviation.json`. Opcje `--data-dir ŚCIEŻKA` i `--config PLIK` podaje się **przed** nazwą polecenia. Nie kieruj danych lotniczych do głównej bazy `data/` ani `data/early_warning/`; proces ma oddzielny katalog i blokadę zapisu. Testy używają katalogów tymczasowych, poza danymi rzeczywistymi.

## Dostęp i zakres zapytań

Sprawdzona specyfikacja jest pod adresem [api.adsb.lol/api/openapi.json](https://api.adsb.lol/api/openapi.json), wskazanym przez [stronę API](https://api.adsb.lol/docs). Dawniejsza próba domyślnego `/openapi.json` zwracała 404. Publiczny punkt `/v2/point/{lat}/{lon}/{radius}` ma maksymalny promień **250 mil morskich**. Kopię specyfikacji i metadane pobrania zachowano w `data/research/aviation-pilot-2026-09-24/`.

Region to prostokąt **14–29°E, 49–60°N**, zgodny z obszarem pilotażu GNSS. Cztery zapytania obejmują przypisane im ćwiartki; odpowiedzi mogą zawierać też obiekty poza prostokątem. W każdym cyklu najpierw usuwamy duplikaty, wybierając najnowszą znaną pozycję identyfikatora, a następnie przycinamy do regionu.

| Część regionu | Środek: szerokość, długość | Promień |
|---|---|---:|
| Południowy zachód | 51,75; 17,75 | 250 NM |
| Południowy wschód | 51,75; 25,25 | 250 NM |
| Północny zachód | 57,25; 17,75 | 250 NM |
| Północny wschód | 57,25; 25,25 | 250 NM |

Konfiguracja sprawdza konserwatywne ograniczenie odległości dla całej ćwiartki z marginesem 1 NM. Nie zakładamy, że cztery zapytania obejmą dowolny większy region. Dopuszczony adres źródła jest stały; kolektor nie podąża za przekierowaniem HTTP do innej usługi.

Dostawca stosuje dynamiczne limity. Używamy własnych ostrożnych ograniczeń: co najmniej **2 sekundy między początkami żądań**, **60 sekund od zakończenia poprzedniego cyklu**, 15 sekund timeoutu i 3 MB na odpowiedź. Nie są to gwarantowane limity ani SLA dostawcy. Błędy HTTP 3xx/4xx zatrzymują resztę cyklu; obowiązuje `Retry-After`, co najmniej 5 minut. Stan blokady zapisuje się na dysku, więc ponowne ręczne uruchomienie jej nie omija. Błąd 5xx lub połączenia daje jawny brak danego obszaru, bez ponowienia tego samego żądania. [Kod i zasady API](https://github.com/adsblol/api).

Brak zapętlonego procesu i harmonogramu. Instrukcja dostawcy prosi użytkowników produkcyjnych o kontakt w sprawie zmian API; mały lokalny pilotaż nie ustala warunków docelowej usługi.

## Czas, jednostki i pochodzenie

Adapter korzysta z formatu v2 opisanego w [readsb](https://github.com/wiedehopf/readsb/blob/dev/README-json.md). Nie utożsamia `type` z typem samolotu:

| Pole źródła | Znaczenie w pilotażu |
|---|---|
| `now` | Czas odpowiedzi dostawcy w **milisekundach** od epoki UNIX |
| `seen_pos` | Wiek pozycji w sekundach względem `now`; `position_at = now/1000 − seen_pos` |
| `seen` | Wiek ostatniej wiadomości; osobny czas `message_at` |
| `lat`, `lon` | Ostatnia pozycja; nie uzupełniamy jej z `lastPosition` ani szacunków `rr_lat/rr_lon` |
| `hex` | Identyfikator; przestrzenie z prefiksem `~` i bez niego pozostają odrębne |
| `type` | Sposób odbioru / rodzaj wiadomości, np. ADS-B lub MLAT |
| `t` | Kod typu statku powietrznego z bazy dostawcy |
| `alt_baro`, `alt_geom`, `gs` | Wysokości w stopach, prędkość względem ziemi w węzłach; `ground` zachowuje osobny status |
| `dbFlags & 1` | Oznaczenie wojskowe z bazy dostawcy, bez niezależnego potwierdzenia |

Każda próbka zachowuje czas rozpoczęcia i zakończenia, dla każdego żądania czas wysłania i odbioru, status HTTP, wybrane nagłówki, rozmiar oraz SHA-256 surowej odpowiedzi. Czasy są w UTC. Rekord przetworzony wskazuje identyfikator zapytania i indeks wiersza w tej odpowiedzi. Puste pola pozostają `null`; niewłaściwy format wiersza zwiększa licznik odrzuceń i daje częściową jakość próby.

Grupa pochodzenia to `adsb:adsblol`. Powtórzenie przez agregator nie jest niezależnym potwierdzeniem. Flaga nieustawiona i brak pola flag mają różne stany; żaden nie dowodzi operatora cywilnego. Operator i intencja pozostają nieustalone. Nie wyprowadzamy aktywności RU/BY albo NATO z kodu ICAO, typu lub flagi.

Rzeczywiste odpowiedzi zawierają także kody `TWR` i `GND` oraz oznaczenia naziemne. Zachowujemy je jawnie w jakości źródła; łącznego licznika identyfikatorów nie opisujemy jako liczby samolotów. Automatyczne rozpoznawanie i weryfikacja klas obiektów są dalszą pracą.

## Miary jakości i luki

Robocze granice jakości to **60 sekund wieku odpowiedzi i pozycji w chwili zakończenia cyklu**, a raport pokazuje ostatnią próbę jako bieżącą przez maksymalnie **15 minut**. To konfigurowalne reguły prezentacji, bez progu alarmowego. Czas w przyszłości nie kwalifikuje danych jako świeżych. Późniejsze `report` ujawnia starzenie próby, zamiast udawać ponowne pobranie.

Raport przedstawia liczbę poprawnych odpowiedzi, odrzucone wiersze, usunięte powtórzenia, świeże identyfikatory w regionie, braki i wiek pozycji (mediana i percentyl 95 metodą najbliższej rangi). Wiek obejmuje czas przetwarzania całej próby, a nie tylko `seen_pos` ze źródła.

Siatka obejmuje **165 pól 1° × 1°**. Każde pole odróżnia obecność świeżej obserwacji, brak obserwacji przy dostępnym zapytaniu oraz brak pełnego zakresu użytecznego zapytania. Przy ostatnim stanie liczba obserwacji bez dowodu wynosi `null`. Dostępny zakres zapytania oznacza geometrię żądania, **nie zmierzone pokrycie odbiornikami**. Pole bez punktów nie dowodzi pustej przestrzeni powietrznej.

Historia raportu obejmuje ostatnie 24 godziny i tylko próbki o identycznej konfiguracji; liczbę wyłączonych próbek zapisuje JSON. Brak użytecznej odpowiedzi daje `fresh_in_region=null`, poprawna odpowiedź bez świeżych rekordów — `0`. Odsetek prób bez danych ma za mianownik wykonane próby, nie wszystkie minuty doby. Przerwy między ręcznymi pomiarami są jawne i nie są okresem monitorowanym. Hash zestawu odpowiedzi ujawnia powtórzoną zawartość. Ten sam nadajnik w trzech chwilach nie oznacza trzech lotów.

## Pliki i kopie

| Ścieżka w `data/aviation/` | Zawartość |
|---|---|
| `raw/adsblol/` | Oryginalne odpowiedzi nazwane SHA-256, także dostępne treści błędów HTTP |
| `database/aviation.sqlite3` | Dopisywane próbki i wydania; zakaz aktualizacji i usuwania tabel audytu |
| `snapshots/av-…/` | Polski raport, JSON, agregaty `coverage.geojson`, zamrożone wejścia i manifest |
| `latest.json` | Wskazanie ostatniego opublikowanego wydania |
| `request-state.json` | Najwcześniejszy dozwolony czas kolejnego pobrania |
| `.mode.json` | Oddzielenie danych rzeczywistych od testowych |

Eksport powstaje w katalogu roboczym i dopiero potem zastępuje wskaźnik wydania. Błąd eksportu pozostawia wcześniejsze `latest.json`. Poprzednie raporty pozostają niezmienne. GeoJSON zawiera agregaty pól, nie ścieżki pojedynczych statków powietrznych. JSON diagnostyczny i surowe odpowiedzi pozostają lokalnie; nie wystawiaj całego `data/` serwerem WWW.

Dotychczasowe `scripts/backup.py` kopiuje bazę RTB, **nie** tę bazę. Przy zatrzymanych kolektorach i zamkniętych połączeniach skopiuj cały `data/aviation/` oraz zapisz wersję repozytorium i `requirements.lock`. Nie kopiuj samego pliku SQLite w trakcie aktywnego zapisu WAL; dla otwartej bazy użyj mechanizmu SQLite backup pod blokadą procesu, wraz z kopią surowych plików i wydań. Odtwarzaj do **nowego** katalogu, następnie wykonaj:

```sh
.venv/bin/python scripts/aviation.py --data-dir NOWY_KATALOG doctor
.venv/bin/python scripts/aviation.py --data-dir NOWY_KATALOG replay ID_WYDANIA
```

Nie ma automatycznej kopii na drugi nośnik. Nie usuwaj `request-state.json` przy przywracaniu działającego kolektora.

## Licencja i dalszy zakres

Dostawca publikuje dane API na [ODbL 1.0](https://www.adsb.lol/docs/open-data/api/); raport i GeoJSON zachowują atrybucję ADSB.lol oraz oznaczenie licencji. Warunki przekazania danych przez właścicieli odbiorników są odrębne od licencji wyniku API. Dostawca nie gwarantuje kompletności ani dokładności. [Zasady dostawcy](https://www.adsb.lol/privacy-license/).

24.09 wykonano osobny [audyt trzech półgodzinnych okien historii](aviation-history.md): 78,1 MB treści, 540 przedziałów po 10 sekund. Nie pobierano wielogigabajtowego archiwum dziennego. Próba wykazała różnice między historią mapy a API, dlatego nie dopisujemy jej do powyższej serii bieżącej. Historia nie zawiera kodów typu samolotu ani flag wojskowych i nie zachowuje dokładnego czasu każdej pozycji.

Kolejna walidacja danych powinna objąć różne pory i dni, stabilność źródła oraz osobny rejestr klas obiektów z datami obowiązywania. Porównania anomalii wymagają dłuższej porównywalnej serii oraz wyników do walidacji. Pilotaże nie zmieniają RTB, ocen GNSS ani publikacji logistycznych.
