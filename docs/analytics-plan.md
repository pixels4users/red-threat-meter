# GA4 — wdrożenie i odbiór

Stan: wdrożone na https://redthreatalert.pl 06.10.2026; test transmisji do Google zakończony. Pozostaje odbiór w panelu GA4 przez właściciela.
Identyfikator otrzymany od użytkownika: **G-3JHR8SCJ0Y**, strumień RTA-Home.
Konfiguracja: `config/analytics.json`, kontrakt JSON Schema 2020-12:
`schemas/analytics.schema.json`. Osobny worktree `codex/rta-analytics`
na bazie main 3c8d0ff; dotychczasowy worktree UI należy do innego czatu.

## Zakres i definicje

Bezpośredni Google tag, bez dodatkowego kontenera GTM. Ładowanie tylko po
zgodzie, na dwóch jawnie dozwolonych originach HTTPS. Localhost i podglądy
nie mogą uruchomić produkcyjnego tagu. W konfiguracji nie ma sekretów.

| Zdarzenie | Warunek | Parametry |
| --- | --- | --- |
| page_view | Pierwszy widok po zgodzie, faktyczne przejście, czytnik/druk raportu | view, oczyszczone page_location/page_title/page_referrer |
| newsletter_view | Co najmniej 50% sekcji przez 1 s w widocznej karcie, po zgodzie, raz na otwarcie strony | bez danych formularza |
| newsletter_submit | Poprawny formularz przyjęty przez API po rozpoczęciu akcji ze zgodą | bez danych formularza |
| newsletter_confirmed | API potwierdza nowy zapis przez newly_confirmed=true | bez identyfikatora subskrybenta |
| support_click | Kliknięcie linku BuyCoffee, również klawiaturą | placement: navigation/footer |
| filter_change | Jawna zmiana filtra | view, filter_name, filter_value z zamkniętego słownika |
| select_content | Otwarcie szczegółów sygnału | view, content_type=signal |

Powtórzenie renderowania albo zgody nie dodaje odsłony. Kategoria w tym samym
raporcie nie jest nową odsłoną. Zmiana filtra nie dodaje odsłony. Odsłona
czytnika mierzy wejście do niego, nie gwarantuje poprawnego pobrania raportu.

`newsletter_submit` to przyjęcie żądania, nie dowód wysyłki wiadomości:
API celowo nie ujawnia stanu istniejącego adresu ani ograniczenia ponownej wysyłki.
`newsletter_confirmed` jest głównym zdarzeniem kluczowym, nie generujemy go
na podstawie adresu strony sukcesu. Backend odróżnia nowe potwierdzenie od
idempotentnego powtórzenia. Publiczny proxy przepuszcza wyłącznie boolean
przy poprawnej odpowiedzi confirm. Starszy backend nie wywoła fałszywej
konwersji, ale nie dostarczy nowego pola — dlatego trzeba wdrożyć również Edge Function.
Przerwane połączenie po zapisie w bazie może oznaczać brak zdarzenia w GA.
Pełna liczba zapisów pochodzi z systemu newslettera, nie z GA4.

## Zgoda i dane

Zaakceptowany komunikat: „Pliki cookie”, „Tylko niezbędne”, „Akceptuj”,
„Ustawienia”, „Polityka prywatności”. Baner jest stałą dolną warstwą nad treścią; pozostawia dostęp do nawigacji.
„Akceptuj” ma neutralny styl primary. Szczegóły
obejmują niezbędne ustawienia oraz statystyki, domyślnie wyłączone.
Ustawienia są ponownie dostępne w stopce; Escape nie zapisuje zmian.

Podstawowy tryb zgody: przed zgodą brak skryptu, połączeń GA, cookies GA
i kolejki wcześniejszych interakcji. Zapis decyzji localStorage ma wersję
i termin 180 dni. Niedostępny storage oznacza wybór tylko w bieżącej karcie.
Wycofanie najpierw ustawia ga-disable, czyści kolejkę i cookies _ga/_ga_*,
następnie przeładowuje stronę, aby usunąć działającą bibliotekę i timery.
Wycofanie/wyczyszczenie pamięci w drugiej karcie jest synchronizowane.
Wygaśnięcie kontrolujemy przed zdarzeniem, przy powrocie do karty i co minutę.

Cookies GA mają 60 dni bez odnawiania. Google Signals i personalizacja reklam
są wyłączone w kodzie; trzeba sprawdzić również panel. Nie przekazujemy
e-maili, tokenów, pól formularza ani dowolnego tekstu źródłowego.
Adresy są wirtualne i tworzone z dozwolonych tras; nie kopiujemy query string.
Zewnętrzny referrer jest ograniczony do originu, wewnętrzny do poprzedniego
wirtualnego widoku. Parametry UTM nie są obecnie przekazywane — pomiar kampanii
wymaga osobnego słownika. Publiczny report_id identyfikuje publikację.
Google nadal otrzymuje dane techniczne połączenia. Nie nazywamy pomiaru anonimowym.

## Zadania właściciela w GA4 przed publikacją

1. Identyfikator: dostarczony i wpisany. Nie dodawać drugiej kopii skryptu.
2. Administracja → Strumienie danych → RTA-Home: wyłączyć Pomiar zaawansowany,
   w tym odsłony oparte o historię i interakcje formularza. `send_page_view:false`
   w kodzie wyłącza inicjalną automatyczną odsłonę, nie zastępuje tych ustawień.
3. Sprawdzić strefę Warszawa, wyłączyć Google Signals, funkcje reklamowe i
   zbieranie danych przekazywanych przez użytkowników. Nie łączyć Google Ads na tym etapie.
4. Retencja danych użytkowników/zdarzeń: **2 miesiące**, wyłączyć odnawianie
   okresu przy nowej aktywności. To musi odpowiadać tekstowi prywatności.
   Retencja nie usuwa wszystkich raportów zbiorczych.
5. Sprawdzić ustawienia udostępniania danych i warunki przetwarzania Google.
6. Po pierwszych zdarzeniach oznaczyć newsletter_confirmed jako zdarzenie
   kluczowe, liczenie raz na zdarzenie. Nie oznaczać samego kliknięcia lub
   page_view jako potwierdzonego zapisu.
7. Utworzyć wymiary niestandardowe o zakresie zdarzenia: view, placement,
   filter_name, filter_value, jeśli mają być używane w raportach/eksploracjach.

## Testy i publikacja

Lokalnie: `npm test`, `npm run test:newsletter`, `npm run test:site`,
`npm run build:site`, `npm run build:newsletter`. Testy korzystają z syntetycznych
raportów w katalogach tymczasowych i lokalnej bazy testowej; bez danych live.

Przeglądarka: brak zgody, odmowa, zgoda, ponowna wizyta, wycofanie, druga karta,
token w URL, wejście bezpośrednie do raportu, brak podwójnych odsłon, błędny
formularz, potwierdzenie/replay, obserwacja sekcji, klawiatura, 320 px,
jasny/ciemny wygląd, blokada skryptu, konsola i polityka CSP.
W symulatorze wszystkie żądania do Google i API są przechwycone lokalnie;
nie zasilamy prawdziwego strumienia i nie wysyłamy wiadomości.

Publikacja wymaga osobnej zgody i odbioru wyglądu oraz potwierdzenia powyższych
ustawień panelu. Wdrożyć Edge Function i stronę z tej samej sprawdzonej wersji.
Sprawdzić CSP i brak prywatnych danych w rzeczywistych żądaniach kolekcji.
Następnie właściciel sprawdza „Przetestuj instalację”, Czas rzeczywisty oraz
DebugView w kontrolowanej sesji z udzieloną zgodą. Nie pozostawiać debug_mode
w konfiguracji wszystkich użytkowników. Bez tego odbioru nie twierdzimy,
że GA4 odbiera dane. Odmowa, blokery i inne urządzenie zmniejszają widoczność
lejka; nie przeliczamy jej na pełną liczbę czytelników i subskrypcji.

## Źródła

- https://developers.google.com/analytics/devguides/collection/ga4/views
- https://developers.google.com/tag-platform/security/concepts/consent-mode
- https://developers.google.com/tag-platform/security/guides/csp
- https://support.google.com/analytics/answer/6366371
- https://support.google.com/analytics/answer/7667196
- https://support.google.com/analytics/answer/13128484

## Wynik odbioru lokalnego — 06.10.2026

- 63 testy dashboardu, 14 newslettera i 14 hostingu: **91/91**.
- Build frontend, strony z Workerem i Edge Function: poprawne.
  Pozostaje istniejące ostrzeżenie Vite o rozmiarze głównego bundla.
- Przeglądarka: zgoda/odmowa/pamięć wyboru/wycofanie, druga karta,
  bezpośredni raport i token newslettera, druk/powrót, niepoprawny formularz,
  przyjęcie zgłoszenia, nowe potwierdzenie i replay, sam adres sukcesu,
  błąd API, brak GA na localhost i działanie strony przy blokadzie tagu.
- Otwieranie sygnału i jego zamknięcie dają jedno select_content; wsparcie
  przekazuje footer; ponowna ekspozycja newslettera nie dodaje zdarzenia.
- 1350 px i 320 px, jasny/ciemny motyw, Tab/Escape i powrót fokusu:
  bez poziomego przepełnienia. Końcowy test interakcji: zero błędów JS i konsoli.
- Zrzuty i lokalne wyniki: output/playwright/analytics-*. Sieć Google była
  przechwycona; sprawdzono komendy tagu i moment ładowania, nie odbiór w GA4.
- Podgląd lokalny używa danych syntetycznych i symulatora newslettera,
  bez rzeczywistej wysyłki. Nie zmieniono danych live ani produkcyjnej strony.

Właściciel zaakceptował wygląd oraz zgłosił zakończenie konfiguracji GA4.
06.10.2026 wyraził zgodę na wdrożenie po końcowej weryfikacji testów.
Pozostaje sprawdzenie rzeczywistych żądań i odbioru zdarzeń w panelu GA4.
Skrypt pakujący Sites uwzględnia publiczną konfigurację analityki.
Końcowy przebieg przed publikacją: 91/91 testów Node oraz 5/5 testów
Python dla bramek wydawcy newslettera; build strony i Edge poprawne.

Korekta UI: baner przypięty na dole nad treścią, „Akceptuj” primary.
Sprawdzono stałe położenie przy przewijaniu, 1350×1000, 320×780,
390×844 (ciemny) i 667×375, brak przepełnienia i kolizji z nawigacją,
akceptację i ponowne otwieranie ustawień. Build frontend poprawny.


## Wdrożenie produkcyjne — 06.10.2026

- Akceptacja publikacji: użytkownik, po końcowej weryfikacji testów.
- GitHub `main`: `553e058c9245d7ee3037e09e5b254d2e803759b3`.
  Drzewo Git jest identyczne ze sprawdzonym lokalnym kodem. Zapis obejmuje
  także wcześniej wdrożony kompaktowy newsletter, który nie był jeszcze
  zsynchronizowany z GitHubem. Prywatne dane i inne lokalne zmiany pominięto.
- Sites: wersja **30**, źródło `54ee684098e82320ff59f5c99de325a5f445dc46`,
  deployment `appgdep_6ac5217901ec8191a3d09576a41650b1`, status **succeeded**.
  Zachowano publiczny dostęp oraz domenę redthreatalert.pl.
- Supabase `rta-newsletter`: wersja **3**, ACTIVE, dotychczasowe sekrety
  i autoryzacja bez zmian; bez migracji i wysyłki wiadomości.
  Pobraną funkcję porównano z buildem: identyczny SHA256
  `eeb0ecdfc68388721cc2b5ba4d464685706608b58f4ec6c74c91ebb36304077f`.
- Na publicznej domenie: przed zgodą oraz po odmowie zero żądań do GA/tagu
  i zero cookies GA. Po zgodzie gtag HTTP 200 oraz trzy odpowiedzi kolekcji
  HTTP 204: page_view Przegląd, newsletter_view, page_view Mapa.
  ID pomiaru G-3JHR8SCJ0Y, oczyszczone adresy widoków, npa=1.
  Powtórne kliknięcie Mapy nie dodało odsłony.
- Wycofanie: zapis analytics=false, przeładowanie, zero skryptów GA i cookies;
  liczba żądań pozostała bez zmian po wycofaniu zgody.
- Newsletter status HTTP 200/enabled. Brak błędów JS aplikacji.
  Konsola odnotowała blokadę przez CSP skryptu inline mechanizmu Cloudflare
  challenge dodanego przez hosting. Nie jest to skrypt GA; pomiar otrzymał 204.
  Nie poszerzano polityki skryptów o unsafe-inline.
- Dowody lokalne (poza Git): output/playwright/analytics-production-result.txt.
  Test dodał dwie odsłony oraz newsletter_view do rzeczywistego strumienia.
  Nie wysłano maila ani nie utworzono testowej subskrypcji na produkcji.

HTTP 204 potwierdza odpowiedź endpointu kolekcji Google, nie widoczność danych
w raportach. Właściciel sprawdza Czas rzeczywisty i później listę zdarzeń;
newsletter_confirmed oznacza jako kluczowe po jego pierwszym odbiorze.
