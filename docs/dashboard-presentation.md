# Prezentacja dashboardu

Status: zaakceptowany układ B i działający lokalnie frontend, 29.09.2026.
Gotowe są kontrakt, eksporter, wydawca i adapter Supabase. Stan wdrożenia
chmurowego opisuje `supabase/README.md`, a uruchomienie `dashboard-runbook.md`.
Komentarz przygotowuje Codex według `agents/analysis-cycle.md`; prywatny
rekord przeglądu jest połączony z wydawcą. Nie ma osobnego API modelu. Działający
silnik nadal wykonuje rtb-v0.2; te zmiany nie wdrażają punktacji rtb-v0.3.

## 1. Oś czasu

- Domyślny dzień: grupy godzinowe od północy do chwili odcięcia odczytu.
- Bieżący tydzień: grupy dobowe, od poniedziałku do chwili odcięcia.
- Bieżący miesiąc: grupy tygodni ISO, przycięte do granic miesiąca i odczytu.
- Wszystkie etykiety i granice okresów korzystają z Europe/Warsaw. Tydzień
  zaczyna się w poniedziałek. Nie należy grupować według czasu komputera widza.
- Liczniki i podziały kategorii pochodzą z tych samych wpisów. Przy remisie
  dominanty pokazujemy wszystkie najczęstsze kategorie. Rozwinięcie grupy
  ujawnia konkretne wpisy; powrót ze szczegółów zachowuje skalę i rozwinięcia.
- Oś pokazuje **czas publikacji**, nie domniemaną datę wystąpienia. Liczba
  sygnałów nie jest liczbą niezależnych źródeł ani lotów. Wydawca dostarcza
  jeden wpis na identyfikator incydentu, z powiązaniami materiałów źródłowych.
- „Brak wpisów” oznacza wyłącznie pusty zbiór. Nie oznacza braku zagrożeń.
- Podgląd A/B używa wyłącznie danych syntetycznych poza bazą live. Frontend
  pokazuje punkty z wybranego wydania; przełącznik skali zmienia tylko oś czasu.
  W dniu pomijamy puste godziny, a brak wpisów opisujemy jednym komunikatem.

## 2. Język i niepełne dane

Wynik RTB, pewność danych i treść analityczna pozostają odrębnymi informacjami.
Wartości demonstracyjne nie mogą zastępować niewyliczonego wyniku silnika.
Nie wolno traktować procentu pewności jako prawdopodobieństwa eskalacji.

Szczegóły sygnału zachowują istotną niepewność: „Pojedyncze doniesienie”,
„Przyczyna nieustalona”. Krótki komentarz na stronie głównej pomija niepewne
sygnały i nie opisuje procesu ich weryfikowania. Przy braku podstaw do pełnej
oceny pokazuje neutralne „Podsumowanie niedostępne”. Szczegóły implementacji, ostrzeżenia
parserów, wersje konfiguracji i komunikaty o przyszłych integracjach pozostają
w dokumentacji lub logach. Nie wyświetlamy nieaktywnych przycisków pobierania.
Tekst „Brak istotnych anomalii” jest wnioskiem i wymaga zakończonej analizy;
nie jest zastępczym komunikatem dla awarii lub brakujących danych.

Nagłówek nie zawiera banera „Projekt · dane przykładowe”. Osobny tryb testowy
zachowuje oznaczenie danych syntetycznych. Odczyt live nie otrzymuje tej etykiety.

Mapa ma przyciski przybliżania, oddalania, powrotu do całego obszaru oraz
powiększenia. Przeciąganie i gest dwoma palcami zmieniają położenie widoku;
zwykłe przewijanie strony nie przybliża mapy. Punkty i podkład korzystają z tej
samej transformacji. Duży widok zachowuje wybrany obszar i otwiera szczegóły
punktu. Pełny ekran przeglądarki jest używany, gdy dostępny; podgląd osadzony
w rozmowie zachowuje działającą dużą warstwę bez tego uprawnienia.

Podpisy mapy: „Lokalizacje orientacyjne” i „Podkład mapy:
naturalearthdata.com”, bez linku do repozytorium. Frontend nie dopisuje
współrzędnych zdarzeniom. Flaga w stolicy reprezentuje cały kraj, jest kotwicą
interfejsu z odrębnego katalogu i nie trafia do GeoJSON jako miejsce incydentu.
Na telefonie hamburger otwiera dużą warstwę menu. Wybór sekcji, krzyżyk
i Esc zamykają ją; fokus wraca do przycisku otwierającego. Menu boczne
pozostaje widoczne na dużych ekranach.

## 3. Granica publikacji komentarza

`prompts/dashboard-commentary-system.md` definiuje prompt `dashboard-commentary-v2`
(zmiana zaakceptowana 02.10.2026). Komentarz ma chłodny, bezpośredni ton i 1–3
zwięzłe zdania o sprawdzonych wydarzeniach. Trend i praktyczne znaczenie dla
mieszkańców Polski lub gospodarki dodajemy tylko przy osobnych podstawach;
ich brak nie blokuje podsumowania. Nie zawiera opisu procesu analitycznego. Przykłady w prompcie
uczą stylu; nie są ustaleniami o bieżącej sytuacji. Sprawstwo, intencja,
„rutynowość” działań i ocena bezpieczeństwa wymagają osobnej podstawy.
Nie wyprowadzamy ich z samego RTB, zakłóceń GPS ani aktywacji strefy PAŻP.

`scripts/build_dashboard_commentary_request.py` czyta prywatny kontekst zgodny
z `schemas/dashboard/commentary-context.schema.json`. Kontekst przygotowuje
zaufany proces przeglądu: wynik RTB, jego wersja, identyfikator odczytu i ustalenia
z rolami (`situation`, `action`, `impact`) i odnośnikami do dowodów. Role opisują
treść; nie wymagamy kompletu, ustalonej kolejności ani unikalności ról.
Skrypt usuwa ustalenia `uncertain` i `rejected` **przed** przygotowaniem wiadomości
dla modelu. Niezakończone obliczenie, brak wyniku lub brak zaakceptowanych
ustaleń opartych na dowodach innych niż sam indeks zwracają `null`.
Nie zastępujemy brakującej oceny bezpieczeństwa interpretacją liczby RTB.

Funkcja `build_generation_request` ładuje rzeczywistą treść promptu jako
wiadomość `system` i dołącza jego wersję, SHA-256 oraz schemat odpowiedzi.
Pozostałe ustalenia trafiają do wiadomości `user` jako dane. Wyjściem jest
prywatny pakiet dla wykonawcy analizy; skrypt nie wykonuje połączeń
sieciowych. Przykład przygotowania pakietu:

```sh
.venv/bin/python scripts/build_dashboard_commentary_request.py \
  --input /private/tmp/commentary-reviewed-context.json \
  > /private/tmp/commentary-private-request.json
```

Pole `status=accepted` nie jest samodzielnym dowodem prawdziwości. Moduł
`analysis/commentary.py` rozwiązuje odnośniki w zamrożonych danych: potwierdza
wersje materiałów, powiązania aktualnych ocen oraz zakres czasu. Drugi przegląd
Codexa bada znaczenie twierdzeń; nie jest niezależnym źródłem ani kontrolą
człowieka. Dane `mode=fixture` pozostają poza publikacją live.

`src/osint_dashboard/dashboard_commentary.py` i
`scripts/prepare_dashboard_commentary.py` przygotowują osobny publiczny obiekt
`{"text": "…"}` albo `{"text": null}`. Nie zmieniają raportów audytowych,
zamrożonych wejść, oryginalnych materiałów ani historii ocen.

Prywatny kandydat jest zgodny ze schematem JSON Schema 2020-12
`schemas/dashboard/commentary-candidate.schema.json`: identyfikator odczytu,
język `pl` i 1–3 zdania prozą, do 220 znaków każde i do 600 znaków łącznie.
Każdy element zawiera jedno zdanie; prompt wyklucza skróty z kropką.
Bieżący identyfikator, zakończenie analizy
i zatwierdzenie są informacjami wydawcy, a nie polami kontrolowanymi przez LLM.

Filtr odrzuca cały tekst przy błędnym kontrakcie, znanych meta-komentarzach,
logach, znacznikach, adresach URL lub ukrytych znakach sterujących. Nie usuwa
pojedynczych zdań ani negacji, żeby nie zmienić sensu. Diagnostyka zawiera
wyłącznie stały kod przyczyny, bez surowej odpowiedzi i wyjątku walidatora.
Kontrola obejmuje także frazy „zbieżność czasu publikacji”, „doniesienia
pozostają niepotwierdzone”, „wymaga przeglądu”, „dane wskazują na” i „jako
model AI”, bez względu na wielkość liter oraz wariant polskich znaków.

Sam wykaz zakazanych fraz nie gwarantuje poprawności dowolnego tekstu. Dlatego
publikacja wymaga również osobnego przeglądu języka, każdego zdania, dowodów
i braku meta-komentarzy. Zatwierdzenie wiąże się przez `candidate_digest`
z dokładną treścią oraz identyfikatorem odczytu. Zmieniony tekst wymaga nowego
przeglądu. Jeśli przegląd wykonuje model, zapisujemy `reviewer.type=agent`.
Sam plik kandydata nie jest zatwierdzeniem. Cykl wymaga osobnego audytu
powiązanego z całym kontekstem i dokładnym tekstem. Wydawca odczytuje go
z prywatnego `commentary-review.json` w zamrożonym wydaniu. Polecenie
pomocnicze poniżej sprawdza tekst, ale nie zastępuje tej ścieżki publikacji.

Przykład lokalnego uruchomienia po osobnym przeglądzie:

```sh
.venv/bin/python scripts/prepare_dashboard_commentary.py \
  --input /private/tmp/commentary-candidate.json \
  --snapshot-id IDENTYFIKATOR_ODCZYTU \
  --analysis-complete \
  --approved-sha256 SKROT_ZATWIERDZONEGO_KANDYDATA
```

Publiczny JSON trafia na stdout; kody diagnostyczne na stderr. Brak
zatwierdzenia lub nieczytelne wejście zwraca `text: null`, bez surowego błędu.
Wywołujący powinien obserwować prywatne logi, a nie traktować kodu wyjścia 0
jako dowodu dostępności komentarza. Frontend używa `textContent` i neutralnego
stanu dla `null`; nie wyświetla surowej odpowiedzi, wyjątków ani pól logowania.
Podgląd ma dodatkową kontrolę znanych fraz oraz możliwość sprawdzenia pustej
i odrzuconej odpowiedzi w ustawieniach projektu.

## 4. Design System i warianty układu

`design.md`, `guidelines.md` i `theme.css` tworzą Design System 0.2. Wspólna
paleta jest neutralna; czerwień oznacza zagrożenie lub wzrost indeksu i może
być użyta w znaku aplikacji. Akcje, nawigacja, wybór punktu, tematy sygnałów
i pewność danych pozostają neutralne. Sam czerwony wzrost RTB nie klasyfikuje
zagrożenia jako wysokiego. Podgląd nie dodaje progów ani nowych ocen.

`ui/dashboard-fragment.html` zawiera jeden szablon powłoki i komponentów,
używany w dwóch propozycjach: A — Mapa i kontekst oraz B — Chronologia.
Stan interakcji jest niezależny dla każdego wariantu; geometria i fikcyjne
rekordy są wspólne. Zmiana wariantu nie może zmieniać liczby sygnałów.
Użytkownik zaakceptował opcję 2, **B — Chronologia**; implementacja jest w `web/`.

`scripts/build_dashboard_preview.py` osadza `theme.css` w wynikowym fragmencie
podglądu. Dzięki temu kolory i odstępy mają jedno źródło. Istniejące podglądy
z wcześniejszych etapów pozostają historycznymi wersjami projektu. Nowy ekran
czyta wyłącznie oczyszczony kontrakt `dashboard-v1`. Skrypt publikacji i API
odczytu mają adapter Supabase oraz osobną bazę testową; brak połączenia
chmurowego nigdy nie włącza automatycznie danych testowych.
