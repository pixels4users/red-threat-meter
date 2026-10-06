# Codzienny cykl Codexa

Stan: 06.10.2026. Zadanie **RTB — codzienna analiza i raport** jest aktywnym
harmonogramem w tym wątku Codexa. Start: codziennie o **09:00 czasu lokalnego
Europe/Warsaw**. Identyfikator: `rtb-codzienna-analiza-i-raport`. Pierwszy
zaplanowany przebieg 02.10 zatrzymała blokada sieci; ręczne wznowienie
zakończyło się publikacją. Odbiór wykonania bez interwencji pozostaje otwarty.

03.10 po naprawie reguł wykonano ręczny pełny cykl
`2026-10-03T080200Z-4df15c35`: RTA 2,2597/100, pewność 22%, 10 odroczeń,
szacowany koszt X 0,10 USD. Publikację potwierdzono w Supabase, publicznym
API i przeglądarce; odtworzenie z archiwum kodu zwróciło identyczny wynik.
Dowód: `data/analysis/cycles/2026-10-03T080200Z-4df15c35/verification.json`
(prywatny, poza Git). Ten przebieg używał zatwierdzonego dostępu sieciowego;
reguły z pliku wymagają jeszcze restartu Codexa i odbioru kolejnego
uruchomienia harmonogramu.

06.10 po zgodzie użytkownika do tego samego harmonogramu dołączono newsletter.
Wysyłka korzysta wyłącznie z już opublikowanego raportu dobowego, po zgodnym
publicznym odczycie i identycznym replay. Zachowano godzinę, wątek, preflight
i wszystkie limity; nie utworzono osobnego harmonogramu. Formularz, pełny
mail oraz wypis i ponowny zapis sprawdzono na produkcji. Nowa reguła skryptu
wymaga restartu Codexa, a pierwszy przebieg automatycznej wysyłki pozostaje
do odbioru. [Obsługa newslettera](newsletter-runbook.md).

## Warunki pracy

Mac musi być włączony, Codex uruchomiony, a projekt i jego dane dostępne w
`/Users/milosz/Documents/Codex/OSINT Dashboard`. Jest to lokalne zadanie
agenta, nie usługa działająca niezależnie od komputera. Nie potrzebuje
otwartej strony ani osobnego API modelu. Warunki:
[dokumentacja automatyzacji](https://learn.chatgpt.com/docs/automations?surface=app).

Używaj istniejącego katalogu, `.venv/bin/python` i prywatnej konfiguracji
ładowanej przez skrypty. Nie drukuj sekretów, nie twórz worktree ani drugiej
bazy live. Zadanie korzysta z uprawnień Codexa; blokada sieci lub zapisu jest
błędem wykonania do zgłoszenia, nie powodem do samodzielnego poszerzania
uprawnień. Dzisiejsza kontrola ręczna nie potwierdza przyszłego wykonania
bez nadzoru.

### Dostęp sieciowy do ustalonych poleceń

03.10 porównano ten sam odczyt w ograniczonym środowisku i po zatwierdzeniu
dostępu: DNS działał tylko w drugim przypadku, a istniejące dane logowania
Supabase były poprawne. To ograniczenie wykonania Codexa, nie awaria DNS domeny.

Na prośbę użytkownika o naprawę zapisano pięć wąskich reguł, a 06.10 po
osobnej zgodzie dodano szóstą dla newslettera w
`~/.codex/rules/rtb-network.rules`; ich wersja do przeglądu jest w
[docs/examples/rtb-network.rules](examples/rtb-network.rules).
Reguły dopuszczają uruchomienie poza sandboxem wyłącznie wskazanego interpretera
i skryptu/podpolecenia. Nie nadają ogólnego zezwolenia na Python ani powłokę.
Ręczne dodanie reguł wymaga ponownego uruchomienia Codexa
([dokumentacja reguł](https://learn.chatgpt.com/docs/agent-configuration/rules)).
Sam zapis pliku i poprawny test dopasowania nie potwierdzają ich załadowania.

W harmonogramie używaj poniższych poleceń **pojedynczo, z pełnymi ścieżkami**,
bez opakowania w dodatkowy skrypt powłoki, `cd`, zmienne lub `python -c`:

```sh
'/Users/milosz/Documents/Codex/OSINT Dashboard/.venv/bin/python' '/Users/milosz/Documents/Codex/OSINT Dashboard/scripts/check_network.py'
'/Users/milosz/Documents/Codex/OSINT Dashboard/.venv/bin/python' '/Users/milosz/Documents/Codex/OSINT Dashboard/scripts/early_warning.py' collect
'/Users/milosz/Documents/Codex/OSINT Dashboard/.venv/bin/python' '/Users/milosz/Documents/Codex/OSINT Dashboard/scripts/collect_x.py' collect
'/Users/milosz/Documents/Codex/OSINT Dashboard/.venv/bin/python' '/Users/milosz/Documents/Codex/OSINT Dashboard/scripts/analysis_cycle.py' prepare
'/Users/milosz/Documents/Codex/OSINT Dashboard/.venv/bin/python' '/Users/milosz/Documents/Codex/OSINT Dashboard/scripts/analysis_cycle.py' publish --cycle CYKL --type daily
'/Users/milosz/Documents/Codex/OSINT Dashboard/.venv/bin/python' '/Users/milosz/Documents/Codex/OSINT Dashboard/scripts/dispatch_newsletter.py' --cycle CYKL --send
```

Pierwsze polecenie jest tylko odczytem: sprawdza DNS, najnowszy raport Supabase
i publiczny odczyt strony. Nie odpytuje płatnego X ani nie zmienia danych.
Nie zastępuj go osobnym testem DNS w `python -c`: takie polecenie nie jest
objęte regułami. Po publikacji uruchom je z `--expected-report-id RAPORT`.
Kontrola weryfikuje oryginalny hash raportu Supabase, schemat odczytu strony
oraz zgodność całej zawartości; uwzględnia równoważny zapis liczb `0.0` i `0`
po serializacji JSON w JavaScript.

Ostatnie polecenie wykonuj dopiero po zakończeniu kontroli publikacji i replay
dla tego samego cyklu. Nie pobiera źródeł ani nie publikuje raportu.
`dispatch_newsletter.py --status` to osobny odczyt gotowości, bez wysyłki.

Wynik nieudanego testu rozpatruj według usługi. Błąd DNS wszystkich adresów
lub niedostępność Supabase zatrzymuje zależne kroki. Sama awaria odczytu
strony nie oznacza awarii Supabase ani pozwolenia na zmianę hostingu.
Reguł nie instaluj ani nie rozszerzaj podczas cyklu. Zgłoś blokadę zamiast
przestawiać globalne uprawnienia. Kontrole, audyty i obliczenia offline
pozostają w zwykłym środowisku projektu.

### Stały dostęp do zapisu i kontrola przed pobraniem

04.10 harmonogram zatrzymał się na `data/.pipeline.lock`: jego lista katalogów
do zapisu obejmowała dawny katalog wizualizacji tego wątku, ale nie projekt.
DNS i odczyt Supabase działały. To blokada sandboxa, nie uszkodzenie bazy
ani brak tokenu.

Na prośbę użytkownika dodano lokalną `.codex/config.toml` w projekcie oraz
w pierwotnym katalogu tego samego wątku:
`~/.codex/visualizations/2026/09/22/01a0c92c-80ab-7692-8b52-c09cc44cedab`.
Obie konfiguracje jawnie dodają katalog OSINT Dashboard do `writable_roots`,
zachowując `workspace-write` i wyłączoną sieć w sandboxie. W konfiguracji
użytkownika oznaczono jako zaufany wyłącznie ten dodatkowy katalog wątku;
przed zmianą zachowano prywatną kopię konfiguracji. Wersja bez sekretów:
[rtb-project-config.toml](examples/rtb-project-config.toml).
Nie nadawano dostępu do całego dysku ani ogólnego zezwolenia na Python.

Nowa kontrola, wykonywana **w zwykłym sandboxie, bez eskalacji**, przed
kopią i pobieraniem:

```sh
'/Users/milosz/Documents/Codex/OSINT Dashboard/.venv/bin/python' '/Users/milosz/Documents/Codex/OSINT Dashboard/scripts/check_project_access.py'
```

Wymaga `ready=true`. Sprawdza rzeczywiste utworzenie, atomową zmianę nazwy,
odczyt i usunięcie plików w katalogach wyjściowych, blokady obu pipeline'ów
oraz SQLite WAL w usuwanej bazie testowej. Nie zmienia rekordów live,
nie ładuje sekretów i nie wysyła żądań. Blokada innego procesu również
zwraca błąd. Ta kontrola nie rezerwuje blokady na cały czas analizy.
Nie powtarzaj jej poza sandboxem, aby uzyskać pozorny wynik pozytywny.

W testach odtworzono poranną odmowę i potwierdzono poprawny zapis po dodaniu
projektu. Świeży proces Codexa wczytuje obie konfiguracje; kontrola przez
`command/exec` z zapisanymi ustawieniami domyślnymi przechodzi. Wymuszenie
starej, niepełnej polityki nadal powoduje odmowę — istniejący harmonogram
wymaga osobnego odbioru. Dowody prywatne: `data/diagnostics/write-access-repair-*.json`.
Wykonano też spójną kopię bazy `osint-2026-10-04T074133+0000.sqlite3`.

## Kolejność wykonania

1. Przeczytaj `AGENTS.md` i [instrukcję agenta](../agents/analysis-cycle.md).
   Sprawdź lokalne potwierdzenia publikacji i datę `as_of` w Europe/Warsaw.
   Jeśli istnieje poprawny raport dobowy z dzisiaj i `verified_readback=true`,
   nie powtarzaj pobierania ani publikacji. Można przejść wyłącznie do kroku 9
   z pełnymi dowodami tego samego cyklu. Sam plik projektu raportu nie wystarcza.
   Nie uruchamiaj drugiego cyklu podczas trwającego przeglądu.
2. Uruchom `scripts/check_project_access.py` i wymagaj `ready=true`.
   Przy odmowie zapisu zatrzymaj pobieranie i zgłoś konkretną ścieżkę;
   nie zmieniaj uprawnień w cyklu. Następnie zachowaj spójną kopię bazy:
   `.venv/bin/python scripts/backup.py`.
   Sprawdź kopię kodu `data/analysis/code/<code_hash>/code-manifest.json`.
   Wszystkie hashe muszą się zgadzać. Brakującą wersję zachowaj przed
   pobraniem, wraz z konfiguracją, schematami, instrukcjami, zależnościami
   i używanym `skills/rss-feeds/scripts/feed.py`. Nie nadpisuj starszej kopii.
3. Raz wykonaj `scripts/early_warning.py collect`, raz
   `scripts/collect_x.py collect`, następnie `scripts/analysis_cycle.py prepare`
   przez lokalny interpreter. Dalsze kroki używają tego samego zamrożonego
   pakietu. Nie wykonuj pilotażu ADS-B.
4. Przeczytaj pełne materiały i rozstrzygnij wszystkich kandydatów. Wykonaj
   `check`, osobny krytyczny audyt, `apply`, `history-context`, `calculate`.
   Każdy przegląd ma `reviewer.type=agent`. Kopie i wspólne źródło nie są
   niezależnymi potwierdzeniami; aktualizacja nie tworzy nowego ataku.
5. Sprawdź RTB i pewność oddzielnie. W v0.4 niepełne źródło lub decyzja
   `defer` nie blokują liczby. Nie udawaj pełnej historii. GNSS po przeglądzie
   liczbowym zasila kontekst i pokrycie, bez punktów ani atrybucji.
6. Przygotuj 1–3 zdania o sprawdzonych wydarzeniach i osobny przegląd redakcyjny.
   Trend oraz skutki dla Polski dodawaj tylko przy własnych podstawach; ich
   brak nie blokuje komentarza. Pomiń tekst wyłącznie przy braku użytecznych
   sprawdzonych ustaleń. Następnie `finish` i `publish --type daily` z identyfikatorem
   tego cyklu. Wymagaj `verified_readback=true`; zachowaj identyczny eksport.
7. Wykonaj replay z właściwej kopii kodu, kontrolę integralności bazy oraz
   zgodności odczytanego raportu. Zapisz dowód w prywatnym `verification.json`
   tego cyklu. Lokalna strona nie musi działać podczas publikacji; po
   otwarciu pobierze najnowszy pakiet z Supabase.
8. Po publikacji sprawdź publiczny `https://redthreatalert.pl/api/latest`:
   wymagaj HTTP 200 i zgodności `report.report_id` z opublikowanym wydaniem.
   Ten odczyt nie wymaga klucza ani lokalnego serwera. Zapisz wynik w dowodzie
   cyklu. Awarię hostingu zgłoś oddzielnie od udanej publikacji w Supabase;
   nie twórz ponownie analizy ani nie zmieniaj ustawień hostingu w harmonogramie.
9. Uruchom `scripts/dispatch_newsletter.py --cycle CYKL --send` przez pełne
   ścieżki wskazane wyżej. Wymagaj kompletnego `verification.json`, zgodności
   identyfikatorów i hasha eksportu, publicznego odczytu oraz replay. Raport
   musi mieć dzisiejszą datę w Europe/Warsaw. Brak dowodów zatrzymuje newsletter;
   nie uzupełniaj ich deklaracją ani nie zastępuj raportu starszym.
   `sent` oznacza przyjęcie wysyłki przez Resend, nie dostarczenie każdej
   wiadomości. `already_handled` z kodem zakończenia 0 oznacza, że skrypt
   potwierdził wcześniejsze `delivery_status=sent`; nie wysyłaj ponownie.
   `disabled`, `ineligible` i `superseded` pomijają wysyłkę. Błąd, `needs_review`
   lub nieznany wynik wymagają zgłoszenia, bez ślepego ponawiania, drugiego
   Broadcast czy usuwania blokady dnia. Dodaj wynik do podsumowania cyklu.

Analiza nie zmienia kodu, wag, limitów ani źródeł. Opis oceny i dokładne
argumenty poleceń pozostają w instrukcji agenta, bez drugiej konkurencyjnej
metody w harmonogramie.

## Limity, przerwy i awarie

X zachowuje limity `config/x-api.json`: do 0,12 USD na przebieg i dobę UTC,
4,50 USD łącznie w lokalnym pilotażu. Są to szacunki i rezerwacje, nie saldo
dostawcy. Nie kasuj licznika i nie doładowuj konta. Limit, błąd lub Retry-After
nie upoważniają do ponownego odpytania; analiza korzysta z zachowanych
odczytów z ich rzeczywistymi datami. [Szczegóły X](x-sources.md).

Po przerwie nie twórz raportów wstecz z datą wcześniejszej wiedzy. Pobierz
bieżący zakres zgodnie z limitami; zaległości, brakujące doby i niepełny
przegląd pozostają jawne. Przekroczenie limitu pakietu wymaga interwencji,
bez cichego pomijania kandydatów.

Jeśli publikacja została przerwana, ponów **ten sam** zamrożony eksport i
`report_id` bez ponownego pobierania. Dotyczy to także utraty odpowiedzi po
skutecznym zapisie w Supabase. W razie zmiany kodu użyj zachowanej wersji,
nie wyłączaj kontroli integralności. Niedokończona ocena z nieaktualnymi
wejściami wymaga nowego `prepare`, nie zmiany dat w starym pakiecie.

Nie usuwaj poprzedniego raportu i nie zmieniaj jego daty. Otwarta strona
zachowuje go przy błędzie odświeżania; po ponad 30 godzinach wskazuje brak
aktualnego obrazu sytuacji. Awaria procesu nie jest odczytem RTB=0.

## Odbiór i dalszy etap

01.10 sprawdzono nową dobę GPSJAM, zachowanie tożsamości istniejącego ataku
i jego wagi przed upływem 48 godzin, odczyt Supabase, pobierany JSON oraz
replay bez sieci. Dwa izolowane testy publikacji obejmują awarię przed zapisem
i utratę odpowiedzi po zapisie; ponowienie nie tworzy duplikatu. W osobnej
przeglądarce sprawdzono utrzymanie wyniku i daty przy HTTP 503 oraz powrót
odświeżania po usunięciu awarii. Dane testowe nie trafiły do Supabase.

Po pierwszym wykonaniu z harmonogramu sprawdź rzeczywisty czas uruchomienia,
koszt X i potwierdzenie publikacji. Harmonogram można wstrzymać lub zmienić
w Codexie, wskazując jego nazwę. Właściwy dashboard wdrożono online 01.10
w osobnym projekcie Sites. Nowy raport w Supabase zasila go bez ponownego
wdrożenia strony. Domena `redthreatalert.pl` jest aktywna z HTTPS od 01.10;
[hosting i domena](hosting-runbook.md). Hosting nie przenosi lokalnego
harmonogramu analizy do chmury.
