# Dashboard — publikowanie i obsługa

Stan: 01.10.2026. Interfejs **B — Chronologia**, kontrakt `dashboard-v1`.
Stan chmurowej migracji i połączenia: `supabase/README.md`.
Właściwy dashboard jest [online](https://red-threat-alert.michalomski.chatgpt.site)
z prywatnym dostępem Sites. [Hosting i domena](hosting-runbook.md).

## Co uruchamia raport

Analizę można zlecić ręcznie; aktywny jest też lokalny harmonogram Codexa
codziennie o 09:00 czasu Warszawy. [Warunki i kontrola](automation-runbook.md).
Przycisk „Odśwież” na stronie tylko pobiera
ostatnią publikację. Otwarta strona sprawdza nowy raport co 30 sekund; nie
uruchamia kolektorów ani modelu. Publikacja danych nie wymaga przebudowy strony.
Harmonogram nie wymaga otwartej strony. Pierwszy przebieg zaplanowany na
02.10 wymaga potwierdzenia wykonania i publikacji.

Pełną analizę zleca się Codexowi według `agents/analysis-cycle.md`.
[Instrukcja silnika](analysis-runbook.md) opisuje oceny i przegląd komentarza.
Nie jest potrzebne osobne API modelu.

Na tym Macu dostęp jest skonfigurowany. **`Opublikuj raport.command`**
wykonuje pobranie i publikację bez przeglądu Codexa. Dotychczasowy
`Zbierz dane.command` nadal tworzy wyłącznie raport lokalny.

Proces RTB nadal wymaga przeglądu nowych materiałów. Od 30.09 domyślny silnik
używa `rtb-v0.4`: wynik jest liczbowy 0–100, a braki ocen, źródeł i historii
216 godzin obniżają osobną pewność. Zero nie oznacza bezpieczeństwa.
Historyczne wydania v0.2/v0.3 zachowują własne wyniki, także null.
Awaria programu nie publikuje zastępczego zera. Szczegóły: [v0.4](v0.4-implementation.md).

## Przygotowanie

Na bieżącym komputerze poniższe kroki zostały wykonane 27.09.2026.
Służą również odtworzeniu konfiguracji na innym, uprawnionym komputerze.

1. `.venv/bin/python` korzysta z istniejącego środowiska projektu.
2. `npm ci` instaluje zależności frontendu; `npm run build` tworzy tylko `dist/`.
3. Lokalny operator loguje CLI przez `supabase login`. Token podaje w terminalu,
   bez kopiowania do rozmowy. Sama sesja panelu WWW nie loguje CLI.
4. Prywatny `.env.dashboard` zawiera `SUPABASE_URL` wskazanego projektu i
   `SUPABASE_SECRET_KEY` (klucz serwerowy, ewentualnie dawny `service_role`).
   Nadaj plikowi tryb `600`. Wzór bez sekretu jest w `.env.example`.
5. Przed migracjami porównaj bazę z `supabase/README.md`. Pierwszą migrację
   wykonano już w SQL Editor i oznaczono w historii CLI; nie wykonuj jej drugi
   raz. `supabase migration list --linked` potwierdza zgodność obu stron.

Klucz jest używany wyłącznie przez serwer Python lub Worker Sites, nie przez Vite. Nie dodawaj
prefiksu `VITE_`, nie wysyłaj `.env.dashboard` do hostingu statycznego i nie
serwuj całego repozytorium przez HTTP. Adres docelowej bazy jest przypięty w
`config/dashboard.json`; pomyłka projektu zatrzymuje wydawcę.

## Eksport, sprawdzenie i publikacja

Eksport istniejącego zamrożonego wydania nie pobiera danych i nie wymaga klucza:

```sh
.venv/bin/python scripts/publish_dashboard.py export \
  --snapshot-dir data/snapshots/IDENTYFIKATOR_WYDANIA \
  --output data/dashboard/exports/raport.json
```

Wydawca weryfikuje sumy kontrolne manifestu i kontrakt. Eksportowane pola są
ograniczone; `replay_input.json` i surowe źródła zostają lokalnie. Samodzielny
eksport nie zna poprzedniej publikacji, więc nie dopisuje trendu.

Po skonfigurowaniu dostępu:

```sh
.venv/bin/python scripts/publish_dashboard.py status
.venv/bin/python scripts/publish_dashboard.py publish \
  --input data/dashboard/exports/raport.json
```

Zapis jest atomowy: raport, incydenty i źródła pojawiają się razem. Ponowienie
tego samego pakietu zwraca `created=false`, bez duplikatu. Przerwane połączenie
nie uzasadnia zmiany identyfikatora — ponów identyczną publikację.

Cały ręczny cykl, z pobraniem i eksportem:

```sh
.venv/bin/python scripts/publish_dashboard.py cycle \
  --output data/dashboard/exports/ostatni.json
```

Po osobnym przeglądzie materiałów można użyć `--offline --review
data/reviews/oceny.json`. Offline nie odnawia wieku źródeł. `--type weekly`
oznacza wydanie tygodniowe tej samej metody, nie nowy algorytm ani średnią.
`cycle` dobiera wcześniejszy raport do porównania trendu. Nie uruchamia osobnych
pilotaży GNSS i ADS-B; zachowują własne limity i instrukcje.

## Lokalna strona z odczytem Supabase

```sh
npm run build
.venv/bin/python scripts/serve_dashboard.py
```

Otwórz `http://127.0.0.1:8765`. Serwer słucha wyłącznie lokalnie. Przeglądarka
czyta `/api/latest`, `/api/reports` i `/api/reports/IDENTYFIKATOR`; Python
pobiera opublikowane pakiety z Supabase. Port `8765` jest domyślny.

Nie ma automatycznego przełączania z Supabase na demonstrację. Brak połączenia
zostawia ostatni dostępny raport z jawnym komunikatem; pierwsza awaria nie
udaje pustej bazy. Pusta baza pokazuje oczekiwanie na pierwszą publikację.
Opóźnienie powyżej 30 godzin jest opisane oddzielnie; próg jest w konfiguracji.

## Izolowany test bez Supabase

```sh
mkdir -p data/demo/dashboard-test
.venv/bin/python scripts/publish_dashboard.py cycle \
  --fixture tests/fixtures/demo.json \
  --data-dir data/demo/dashboard-test/analysis \
  --local-store data/demo/dashboard-test/releases.sqlite
.venv/bin/python scripts/serve_dashboard.py \
  --local-store data/demo/dashboard-test/releases.sqlite
```

Gotowy generator pełnego i niepełnego odczytu używany przez testy to
`tests/dashboard/make_fixture.py`; tworzy pełny i niepełny pakiet w katalogu
tymczasowym. Dane `fixture` nie mogą trafić do live ani zmienić trybu istniejącej
bazy testowej. Ekran oznacza dane syntetyczne.

## Historia, korekty i uprawnienia

`dashboard_reports` przechowuje pełny oczyszczony pakiet oraz metadane.
`dashboard_report_incidents` i `dashboard_report_sources` zachowują jego
wersjonowane elementy. `dashboard_readers` jest listą dopuszczonych tożsamości
Supabase Auth, początkowo pustą. Nie dodajemy użytkowników automatycznie.

Anonim nie odczyta raportów bezpośrednio z Supabase. Samo założenie konta również nie wystarcza.
Dopuszczony użytkownik może tylko czytać; RPC publikacji jest dostępne dla
serwera. RLS i wycofanie uprawnień zapisu chronią tabele, a triggery blokują
zmianę/usunięcie opublikowanej historii. Nie używamy `upsert` do korekt.

Korekta otrzymuje nowy identyfikator i `supersedes` wskazujące wcześniejszy
raport tego samego rodzaju oraz czasu odcięcia. Zmiana oceny w nowym cyklu
z nowym czasem jest kolejnym wydaniem, nie podmianą dawnego. Archiwum pokazuje
obie publikacje, najnowszą wybiera czas analizy, następnie publikacji.

## Weryfikacja i granica wdrożenia

```sh
.venv/bin/python -m pytest
npm test
npm run build
```

Test PostgreSQL działa w PGlite (w pamięci), z rzeczywistą migracją. Sprawdza
role, RLS, atomowość, idempotencję i blokowanie danych testowych; nie zapisuje
nic do chmury. Test HTTP korzysta z portu loopback i może wymagać uprawnienia
środowiska do otwierania lokalnych gniazd.

01.10 wdrożono serwerowy adapter Sites w osobnym projekcie dashboardu.
Strona i API korzystają z prywatnego dostępu Sites. Sekret Supabase jest
w runtime serwera; frontend go nie otrzymuje. Design System pozostaje
osobną wizualizacją. [Obsługa wdrożenia](hosting-runbook.md).

Pełny odbiór danych wykonano 27.09.2026: prawdziwy raport z procesu live →
Supabase → lokalny odczyt → automatyczne odświeżenie ekranu. Potwierdzenie
znajduje się w `data/dashboard/cloud-verification.json`. Harmonogram
aktywowano 01.10; pierwsze zaplanowane wykonanie pozostaje do sprawdzenia.
Komentarz przygotowuje Codex w pełnym cyklu analizy; wydawca sprawdza prywatny
rekord jego przeglądu powiązany z dokładnym wydaniem i tekstem. Komentarz bez
takiego rekordu nie przejdzie publikacji. Aktualny silnik to v0.4;
zakres osobnych pilotaży opisują ich instrukcje.

29.09.2026 sprawdzono dodatkowo rzeczywisty cykl z przeglądem Codexa: 46
rozstrzygniętych materiałów, 4 wstrzymane pozycje OSW, 9 nowych obserwacji.
Nowe wydanie jest w Supabase i na lokalnym ekranie; RTB oraz komentarz są
nieobecne z powodu niepełnego materiału. Potwierdzenie odczytu i ponowienia:
`data/analysis/current-verification.json`. Test pełnego komentarza pozostaje
odseparowany od rzeczywistych raportów.
