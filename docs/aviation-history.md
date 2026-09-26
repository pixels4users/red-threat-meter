# Historia lotnicza — ograniczony audyt jakości

Stan: **24.09.2026**, `aviation-history-1`. Działa pobranie wybranych półgodzinnych plików mapy ADSB.lol, walidacja formatu, polski raport, agregaty GeoJSON i odtwarzanie bez sieci. Audyt ma własne archiwum `data/aviation_history/`. Bieżące próbki API, GNSS/logistyka oraz RTB zachowują swoje dotychczasowe wersje.

## Zakres i wynik decyzji

Wybrano **16:30–17:00 UTC w dniach 22, 23 i 24.09.2026**, dla prostokąta `[14,49,29,60]`. Wybór jednakowej pory pozwala sprawdzić format w kilku dniach; 24.09 obejmuje czasy trzech zachowanych próbek API. Jest to celowa mała próba techniczna, bez losowania i bez reprezentatywności dla całych dób, pór tygodnia czy aktywności wojskowej. Wyniki oraz identyfikator raportu są w [stanie realizacji](STATUS.md).

**Historii mapy nie dopisujemy do szeregu bieżącego API.** Oba produkty mają inne reguły wyboru pozycji i dostępność pól. Zachowujemy opisowe miary historii jako odrębną serię. Nie tworzymy z trzech okien poziomu normalnego, progu alarmowego ani miary trafności ostrzeżeń. Kod jawnie zapisuje `baseline_eligible=false` i `rtb_effect=none`.

## Dostęp i pochodzenie

Dokumentacja dostawcy opisuje codzienne [archiwa na ODbL 1.0](https://www.adsb.lol/docs/open-data/historical/). [Repozytorium archiwum](https://github.com/adsblol/globe_history_2026) rozróżnia ślady pojedynczych obiektów i pliki odtwarzania mapy, a także instancje produkcyjne oraz zapasowe. Dzienne archiwum nie jest jedną tabelą zdarzeń. Nie pobierano części dziennego TAR liczących gigabajty.

Publiczna mapa czyta `https://adsb.lol/globe_history/YYYY/MM/DD/heatmap/NN.bin.ttf`. Indeks `NN = 2 × godzina UTC + (minuta >= 30)` wskazuje pół godziny. Ścieżkę i sposób odczytu sprawdzono w faktycznie serwowanym [kodzie mapy](https://adsb.lol/script_25c7773ecdd90f0174ac8a506f50c4ca.js), funkcje `replayGetChunk`, `initReplay`, `replayStep`. Plik ma treść binarną gzip, mimo rozszerzenia `.ttf`. To punkt dostępu mapy, bez kontraktu stabilności API.

Kopię strony, kodu mapy, aktualnego kodu producenta i metadanych dostępu zachowano w `data/research/aviation-history-2026-09-24/` wraz z czasami oraz hashami. Sam adres nie ujawnia instancji dostawcy; `provider_instance` pozostaje `null`. Nie uznajemy wybranej instancji dziennego wydania GitHub za dowód pochodzenia pliku mapy. Grupa zależności to `adsb:adsblol` — wspólna z naszym kolektorem bieżącym.

## Uruchamianie

```sh
.venv/bin/python scripts/aviation_history.py plan
.venv/bin/python scripts/aviation_history.py collect
.venv/bin/python scripts/aviation_history.py report
.venv/bin/python scripts/aviation_history.py replay
```

`plan` pokazuje daty, adresy i budżet bez używania internetu. `collect` wykonuje do trzech GET i zapisuje potwierdzenia, także dla błędów. **Konfiguracja zawiera stałe daty pilotażu** — nie przesuwa automatycznie okna do dzisiaj. Ponowne `collect` ponownie pobiera treści; do pracy na już zapisanych danych używaj `report` lub `replay`. `report` analizuje ostatni zapisany pakiet i tworzy nowe, niezmienne wydanie. `replay ID` sprawdza manifest, surowe odpowiedzi, kod i ponownie liczy wskazane wydanie.

Opcje globalne `--data-dir`, `--config` i `--live-data-dir` podaje się przed poleceniem. Nowy plan przygotuj jako osobny plik według `schemas/aviation/history/config.schema.json`; źródło, liczba plików i limity mają ograniczenia w walidacji. Domyślny plan wskazuje trzy istniejące wydania API; przy tworzeniu raportu sprawdzany jest ich pełny replay. Odwołania i zbiory identyfikatorów są potem zamrażane w wejściach raportu historii, aby samo odtwarzanie nie wymagało ponownego pobrania ani zmieniających się referencji.

Brak harmonogramu i nowej usługi AI. Limit pilotażu: **32 MB na odpowiedź, 96 MB na przebieg, 160 MB po rozpakowaniu jednego pliku**, co najmniej 3 sekundy między początkami żądań oraz godzina od końca poprzedniego pobrania. Timeout połączenia/odczytu: 25 sekund, kontrola czasu całego transferu między blokami: 90 sekund. Nie ma automatycznych ponowień ani przekierowań. HTTP 3xx/4xx zatrzymuje dalsze żądania i respektuje `Retry-After`; wyjątkiem jest 404 dla brakującego okna, po którym można sprawdzić pozostałe daty. Blokada jest zapisywana na dysku. Dane z okna, które nie zakończyło się co najmniej dwie minuty wcześniej, są odrzucane przed pobraniem.

## Znaczenie formatu

Sposób zapisu sprawdzono w funkcji `handleHeatmap` w [readsb/globe_index.c](https://github.com/wiedehopf/readsb/blob/dev/globe_index.c) oraz porównano z kodem czytającym go na mapie. Odczytany kod producenta nie dowodzi konkretnej wersji uruchomionej u dostawcy; rzeczywiste pliki przechodzą osobną walidację zgodności.

Parser obsługuje rekordy po 16 bajtów, kolejność bajtów little-endian, tablicę indeksów i znaczniki początku przedziałów. Weryfikuje integralność gzip, rozmiar, wyrównanie, indeksy, datę okna, kolejność i krok czasowy. Współrzędne są w mikrostopniach, prędkość w dziesiątych częściach węzła, wysokość w krokach 25 stóp, z osobnymi oznaczeniami naziemnym i nieznanym. Dane callsign/squawk są rozpoznawane jako metadane i nie są liczone jako pozycje.

Najważniejsze różnice wobec bieżącego API:

| Właściwość | Bieżące API | Historia mapy |
|---|---|---|
| Czas | Czas odpowiedzi oraz wiek wiadomości i pozycji | Znacznik przedziału; dokładny czas punktu nie jest zapisany |
| Dobór | Ostatnia znana pozycja; lokalny filtr wieku do 60 s | Wybrane punkty śladu przypisane do przedziałów, według reguł producenta |
| Typ odbioru | Pole `type`, np. ADS-B/MLAT | Kod typu odbioru w rekordzie; nie typ samolotu |
| Klasa obiektu | Opcjonalne `t` i `dbFlags`, nadal niezweryfikowane | Brak tych pól; nie uzupełniamy ich dzisiejszą bazą etykiet |
| Wysokość | Oddzielne pola barometryczne i geometryczne | Możliwy zapis jednej albo drugiej, bez rozróżnienia w rekordzie |
| Pokrycie | Obserwowane identyfikatory; zasięg odbiorników nieznany | Obserwowane identyfikatory; zasięg odbiorników i instancja także nieznane |

Przegląd kodu pokazuje, że historia nie jest pełnym obrazem stanu API w każdej sekundzie. Nie kopiujemy ustawianego przez odtwarzacz mapy `seen_pos=0` do naszych danych: byłoby to udawanie znanego wieku pozycji. Brak per-pozycyjnego czasu utrudnia przypisanie różnic konkretnej przyczynie. Historyczny operator, misja i intencja pozostają nieustalone.

## Miary, duplikaty i braki

Każde okno ma osobno: dostępność, liczbę i krok przedziałów, brakujące znaczniki czasu, puste przedziały globalne i regionalne, odrzucone rekordy oraz miary liczby obserwowanych identyfikatorów. Brak pliku oznacza `unavailable` i brak miar aktywności; poprawny pusty przedział ma licznik zero. Nie wstawiamy zer za brakujące przedziały. Kompletna oś czasu nie dowodzi pełnego odbioru ruchu.

W obrębie przedziału identyczne rekordy identyfikatora są scalane; sprzeczne pozycje tego samego identyfikatora są wykluczane, ponieważ nie ma czasu każdego punktu pozwalającego wybrać najnowszy. Przestrzenie adresów z `~` i bez niego są odrębne. Po rozstrzygnięciu duplikatów stosujemy bbox. Nie sumujemy kolejnych obserwacji jako lotów. Złe rekordy dają stan częściowy i licznik; JSON zachowuje do 100 przykładów z zerowym indeksem rekordu w rozpakowanym pliku, czasem przedziału i przyczyną odrzucenia.

Siatka 1° × 1° ma 165 pól. Liczba przedziałów z obserwacją, unikalne identyfikatory i wspólne pola między oknami opisują obecność zebranych danych. Nie są mapą zasięgu odbiorników. Wyniki częściowe można czytać opisowo; nie dostają automatycznie statusu skalibrowanego odniesienia.

## Porównanie z wcześniejszym API

Dla każdego zapisanego pomiaru API wybieramy ostatni przedział historii, którego koniec przypada **przed rozpoczęciem pobrania API**, a odstęp jest mniejszy od jednego kroku historii. Brak takiego przedziału, częściowa jakość albo niezgodny obszar wykluczają porównanie. Nie wybieramy wygodniejszej późniejszej pozycji. Przedziały i odstęp są jawne w JSON.

Porównujemy zbiory identyfikatorów: wspólne, występujące tylko w API i tylko w historii. To diagnostyka dwóch zależnych produktów w zbliżonym czasie. Nie wyznaczamy na tej podstawie czułości, odsetka przeoczonych lotów ani błędu dostawcy. Nowo pozyskana historia nie udaje danych, którymi system dysponował w czasie wcześniejszego pomiaru: raport zachowuje rzeczywisty czas pobrania i osobno czas źródła. Nagłówek `Last-Modified` pozostaje metadanymi serwera, a `first_available_at` jest nieustalone.

## Archiwizacja i odtwarzanie

| Ścieżka w `data/aviation_history/` | Zawartość |
|---|---|
| `raw/<sha>.bin` | Oryginalna treść odpowiedzi, identyfikowana SHA-256 |
| `collections/ahc-….json` | Zamrożony plan, czasy, nagłówki, statusy i odnośniki do treści |
| `latest-collection.json` | Wskazanie ostatniego pobrania z hashem jego metadanych |
| `snapshots/ah-…/` | Polski raport, agregaty JSON i GeoJSON, wejścia odtworzenia i manifest |
| `latest.json` | Ostatnie kompletne wydanie raportu, także gdy przedstawia brak danych |
| `request-state.json`, `.mode.json` | Blokada kolejnego pobrania i oddzielenie danych rzeczywistych od testowych |

Wynik powstaje w katalogu roboczym i dopiero po udanym zapisie zmienia wskaźnik wydania. Zmiana surowej treści albo wejścia wykryta podczas replay jest błędem integralności. GeoJSON zawiera agregaty siatki; raport nie publikuje śladów ani identyfikatorów obiektów. Surowe pliki i wejścia diagnostyczne pozostają lokalnie i poza Git.

Kopiuj dane przy zatrzymanym kolektorze: `raw/`, `collections/`, `snapshots/`, oba wskaźniki, `request-state.json` i `.mode.json`. Kopii zapisywanej wewnątrz `backups/` nie kopiuj rekurencyjnie do samej siebie. Zachowaj pełną wersję repozytorium, w tym `requirements.lock` i parser `skills/rss-feeds/scripts/feed.py`, importowany przez wspólny moduł procesu. Sama kopia `src/` i `scripts/` nie wystarcza do uruchomienia.

Odtwarzaj do nowego katalogu, następnie użyj `--data-dir NOWY_KATALOG replay ID`. Ta warstwa używa niezmiennych plików i manifestów; nie dopisuje historycznych punktów do tabel bieżących obserwacji SQLite. Test pełnej kopii obejmuje dane, archiwum kodu i blokadę sieci; wynik znajduje się w [stanie realizacji](STATUS.md). Lokalna kopia nie zastępuje kopii na innym nośniku.

Kolejne badanie danych powinno objąć różne pory i dni oraz stabilność źródła, z budżetem ustalonym na podstawie zmierzonego rozmiaru. Klasyfikacja wojskowa wymaga osobnego rejestru etykiet z datą obowiązywania i dowodem. Te prace mogą rozwijać się obok dashboardu, który już teraz powinien jasno rozdzielać rodziny danych i ich aktualność.
