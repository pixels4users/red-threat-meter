# Codzienny cykl Codexa

Stan: 01.10.2026. Zadanie **RTB — codzienna analiza i raport** jest aktywnym
harmonogramem w tym wątku Codexa. Start: codziennie o **09:00 czasu lokalnego
Europe/Warsaw**. Identyfikator: `rtb-codzienna-analiza-i-raport`. Pierwszy
zaplanowany przebieg po konfiguracji przypada 02.10; jego wykonanie wymaga
osobnego potwierdzenia. Ręczny odbiór pełnego cyklu zakończono 01.10 o 12:12.

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

## Kolejność wykonania

1. Przeczytaj `AGENTS.md` i [instrukcję agenta](../agents/analysis-cycle.md).
   Sprawdź lokalne potwierdzenia publikacji i datę `as_of` w Europe/Warsaw.
   Jeśli istnieje poprawny raport dobowy z dzisiaj i `verified_readback=true`,
   zakończ bez ponownego pobrania. Sam plik projektu raportu nie wystarcza.
   Nie uruchamiaj drugiego cyklu podczas trwającego przeglądu.
2. Zachowaj spójną kopię bazy: `.venv/bin/python scripts/backup.py`.
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
