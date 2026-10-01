# Konta X — API, odczyt Codexa i import do raportu

Stan: 01.10.2026. Wskazane przez użytkownika konta
[OSINT Defender](https://x.com/sentdefender) i
[OSINT Technical](https://x.com/osinttechnical) są opcjonalnymi źródłami
wtórnymi w `config/sources.json`. Parametry śledzące linków nie są zachowywane.

## API X — pilotaż od 30.09.2026

Użytkownik uruchomił dostęp i kredyty X. `scripts/collect_x.py collect` pobiera
dane bezpośrednio z `api.x.com`, z tokenem aplikacji w prywatnym `.env.x`.
Token pozostaje poza Git, logami, raportami i frontendem; plik wymaga uprawnień
0600. `status` oraz przygotowanie raportu nie odczytują tokenu. Skrypt nie
korzysta z płatnego API modelu AI. Analizę nadal wykonuje Codex.

```sh
.venv/bin/python scripts/collect_x.py status
.venv/bin/python scripts/collect_x.py collect
.venv/bin/python scripts/analysis_cycle.py prepare
```

`collect` to jawne uruchomienie płatnego pobrania. `prepare` tylko importuje
zapisane paczki X i nie zamawia kolejnych odczytów. Od 01.10 polecenie collect
wchodzi do [codziennego harmonogramu Codexa](automation-runbook.md), z tymi
samymi limitami. Konfiguracja: `config/x-api.json`; kontrakty: JSON Schema 2020-12.
Domyślne ograniczenia pilotażu:

- Tylko dwa wskazane konta; po jednej stronie, maksymalnie 10 wpisów na konto
  i cztery żądania łącznie. Identyfikatory kont są zachowane po sprawdzeniu
  nazw przez API; następne pobrania nie odczytują profili ponownie.
- Maksymalnie 0,12 USD na przebieg i dzień UTC oraz 4,50 USD łącznie w tym
  lokalnym pilotażu. Ponowne wywołanie przed upływem godziny nie odpytuje API.
  Licznik używa całkowitych tysięcznych USD; nie jest odczytem salda X ani
  ochroną wydatków innych aplikacji korzystających z tego konta.
- Rezerwacja maksymalnego kosztu jest zapisywana **przed** żądaniem. Awaria
  pozostawia rezerwację; odpowiedź sukcesu rozlicza liczbę zasobów. Kwoty są
  konserwatywnym oszacowaniem według cennika, bez zakładania rabatu za powtórny
  odczyt. Rozliczenie dostawcy potwierdza jego konsola. Nie kasuj dziennika
  kosztów ani nie uruchamiaj pobierania w drugim katalogu live.
- Pominięcie żądania z powodu budżetu nie jest awarią X ani nowym odczytem.
  Import zachowuje poprzednią rzeczywistą datę obserwacji. Dawne paczki
  oznaczające wyłącznie taki lokalny limit pozostają w audycie, ale nie
  zastępują ostatniej obserwacji. Błąd HTTP/uwierzytelnienia nadal daje niedostępność.
- Brak ponowień, przekierowań i automatycznego doładowania. Błąd dostępu lub
  parsera zatrzymuje kolejne zapytania. HTTP 429 / Retry-After zachowuje termin
  blokady także po restarcie. Odpowiedź ma limit 500 KB i 20 sekund.

Pierwsze zapytanie obejmuje poprzednie 24 h, do 30 sekund przed odczytem.
Kolejne używa `since_id`. Przy `next_token` zachowuje dokładne granice i
kontynuuje zaległą stronę w następnym przebiegu; nie przesuwa `since_id`, dopóki
nie dojdzie do końca. Duże zaległości mogą opóźniać dostęp do najnowszych
wpisów. Pusta strona zachowuje koniec przedziału, bez wymyślania ID.
Nie poświadczamy historii 216 h ani kompletności X: timeline ma ograniczenia
dostawcy, pomijamy reposty, nie pobieramy osobno mediów i cytowanych wpisów.
Przyrostowy odczyt nie sprawdza ponownie usunięć ani korekt dawnych postów;
zwrócona przez API historia edycji scala dostępne wersje pod pierwotnym ID.

Pełny tekst długiego wpisu pochodzi z `note_post` (starszy format:
`note_tweet`). Timestamps są polami API, nie wynikiem dekodowania ID.
Odnośniki i informacja o cytowaniu przechodzą do przeglądu; cytowane źródło
wciąż wymaga osobnego sprawdzenia. Filtr regionalny działa po pobraniu, więc
odłożone wpisy również zużywają kredyty. Zapis surowej odpowiedzi i paczki jest
niezmienny, z kontrolą hasha oraz zgodności tekstu z odpowiedzią.

Test 30.09.2026, 09:19 czasu Warszawy: cztery odpowiedzi HTTP 200, siedem
wpisów OSINT Defender i zero OSINT Technical w zadanym oknie. Wszystkie siedem
było poza filtrem regionu; nie powstały z nich incydenty. Pusta odpowiedź API
nie podważa wcześniejszych odczytów przeglądarkowych ani nie dowodzi braku
publikacji. Trzy wcześniejsze regionalne wpisy Technical pozostają dostępne
z oryginalną datą obserwacji i metodą dostępu. Szacowany koszt: 0,055 USD
(7 × 0,005 + 2 × 0,01); dowód: `data/x-api/runs/16063d05cc1f491d8da16964390a55b2.json`.

Dokumentacja sprawdzona 30.09.2026: [timeline](https://docs.x.com/x-api/users/get-posts),
[token aplikacji](https://docs.x.com/fundamentals/authentication/oauth-2-0/application-only),
[cennik](https://docs.x.com/x-api/getting-started/pricing). Przed zmianą limitów
sprawdź stawki i widoczne saldo w konsoli X.

## Dostęp i rola skillu

`skills/x-research/SKILL.md` jest instrukcją pracy agenta, nie kolektorem.
Nie dostarcza `x_search`, sesji ani klucza. Codex korzysta z dostępnej
przeglądarki jako alternatywnego sposobu odczytu, zachowuje faktyczne treści,
a Python importuje paczkę według `schemas/x-capture.schema.json`. API ma osobny
kontrakt `schemas/x-api-capture.schema.json`. `analysis_cycle.py prepare` nie
otwiera przeglądarki. Pełne zadanie Codexa wykonuje pobranie API przed `prepare`,
zgodnie z `agents/analysis-cycle.md`; harmonogram jest aktywny od 01.10.

Pierwsza próba: czytnik WWW zwrócił 403; przeglądarka pokazała tożsamość kont,
po pięć wpisów i ograniczenie dostępu do dalszej historii. Trzy regionalne
wpisy OSINT Technical odczytano również pod ich bezpośrednimi adresami.
Nie zastępujemy ograniczenia pośrednikiem ani nie obchodzimy logowania.
Była to próba przed podłączeniem API; oryginalne paczki pozostają zachowane.

## Alternatywa: odczyt przeglądarkowy przed cyklem

1. Odczytaj oba profile i dostępne wpisy, z limitem 30 postów na paczkę.
   Zachowaj tekst głównego autora oddzielnie od cytowanego wpisu. Otwórz pełną
   treść regionalnych pozycji, jeśli jest dostępna. Nie odtwarzaj uciętych zdań.
2. Zapisz rzeczywisty odczyt w prywatnym JSON: `synthetic=false`, konto,
   `captured_at`, `access_status`, opis zasięgu, transkrypcja strony i posty.
   Każdy post ma URL, oryginał, `text_complete`, `post_kind`, cytowane URL,
   `published_at` i oryginalną etykietę czasu. Bez jawnej daty ze strefą pozostaw
   `published_at=null`; nie dekoduj ID ani nie wyliczaj godziny z „2 h”.
3. Zaimportuj paczkę przed zamrożeniem materiałów:

   ```sh
   .venv/bin/python scripts/import_x_capture.py PACZKA.json --source x_osinttechnical
   .venv/bin/python scripts/analysis_cycle.py prepare
   ```

4. Przejrzyj wybrane materiały razem z innymi źródłami. Tytuł i streszczenie
   zdarzenia napisz po polsku; cytaty dowodowe zachowaj w oryginale. Skillowy
   brief jest notatką roboczą, nie decyzją o punktacji ani gotowym komentarzem.
5. Gdy odczyt się nie uda, zapisz paczkę `access_status=unavailable` z pustą
   listą postów i opisem rzeczywistej przeszkody. Nie odświeżaj poprzedniej
   paczki. Odczyt starszy niż 24 h jest niedostępny dla bieżącego importu.

## Filtr i kontrola duplikatów

Konfiguracja zawiera terminy dla Polski, Niemiec, Ukrainy, Białorusi, Mołdawii,
państw bałtyckich, Europy Środkowo-Wschodniej i europejskiej części Rosji.
Tematy: aktywność wojskowa, infrastruktura, cyber, GNSS, granice, sabotaż,
polityka bezpieczeństwa i logistyka. Nazwa Rosji/NATO bez lokalizacji trafia
do kontroli geografii; geografia bez tematu — do kontroli tematu. Jednoznaczny
kontekst spoza regionu jest odkładany w archiwum. To szeroki filtr słów,
nie ustalenie miejsca zdarzenia. Nietypowe nazwy, ironia i brak kontekstu mogą
wymagać ręcznego doboru lub rozszerzenia reguł.

Tożsamość dokumentu wynika z konta i URL postu. Nowa treść lub zmiana cytowanych
źródeł tworzy nową wersję do oceny. Korekta wcześniejszego regionalnego wpisu
dociera do przeglądu również po usunięciu regionalnych słów. Usunięcie wpisu
z krótkiej osi czasu nie dowodzi jego skasowania. Ten sam komunikat przytoczony
przez oba konta i media pozostaje jednym pochodzeniem twierdzenia. Deduplikacja
fizycznego incydentu następuje przez `event_key`, dowody i przegląd agenta;
samo podobieństwo tekstów nie scala różnych incydentów.

## Granice i przechowywanie

Paczkę zachowujemy niezmiennie pod hashem w `data/social/`, poza Git.
Oryginalny czas odczytu przechodzi do kontroli źródła; ponowne czytanie pliku
nie odświeża danych. Import nie zastępuje przeglądu, nie daje potwierdzenia
atrybucji i nie przyznaje punktów RTB. Źródła zawsze mają niepełny horyzont,
a brak nowych wybranych postów nie oznacza braku zagrożeń. W jednym odczycie
adapter obsługuje do 200 paczek i 100 unikalnych postów z ostatnich 216 h;
przekroczenie limitu jest błędem, bez cichego pomijania. Dłuższe archiwum wymaga
późniejszego indeksowania, z zachowaniem oryginałów.
