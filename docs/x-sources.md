# Konta X — odczyt Codexa i import do raportu

Stan: 30.09.2026. Wskazane przez użytkownika konta
[OSINT Defender](https://x.com/sentdefender) i
[OSINT Technical](https://x.com/osinttechnical) są opcjonalnymi źródłami
wtórnymi w `config/sources.json`. Parametry śledzące linków nie są zachowywane.

## Dostęp i rola skillu

`skills/x-research/SKILL.md` jest instrukcją pracy agenta, nie kolektorem.
Nie dostarcza `x_search`, sesji ani klucza. Codex korzysta z dostępnej
przeglądarki, zachowuje faktycznie odczytane treści, a Python importuje paczkę
według `schemas/x-capture.schema.json`. `analysis_cycle.py prepare` nie otwiera
samodzielnie przeglądarki. Pełne zadanie Codexa wykonuje odczyt przed `prepare`,
zgodnie z `agents/analysis-cycle.md`; sam harmonogram nie został włączony.

Pierwsza próba: czytnik WWW zwrócił 403; przeglądarka pokazała tożsamość kont,
po pięć wpisów i ograniczenie dostępu do dalszej historii. Trzy regionalne
wpisy OSINT Technical odczytano również pod ich bezpośrednimi adresami.
Nie zastępujemy ograniczenia pośrednikiem ani nie obchodzimy logowania.
[API osi czasu X](https://docs.x.com/x-api/users/get-posts) wymaga tokena;
nie jest częścią tej integracji. Nie uruchomiono płatnego dostępu.

## Procedura przed cyklem

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
