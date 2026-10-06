# RTB — Design System

Wersja: **0.5 — Przegląd, Mapa i Dziennik po odbiorze; Raporty do odbioru**, 04.10.2026. Żywy dokument aktualizowany razem z interfejsem.
Przegląd i Mapa Operacyjna zaakceptowane przez użytkownika 04.10.2026. Po korekcie Dziennika
użytkownik zlecił przejście do Raportów. Ten ekran jest teraz do odbioru lokalnego
na `codex/ux-index-history`. Audyt całości z dostarczonymi skillami będzie osobnym krokiem. Nie opublikowano tej iteracji. Wcześniejsza
wersja 0.4 została opublikowana 03.10.2026. Układ repozytorium: `docs/git-workflow.md`.
Stan połączenia z chmurą: `supabase/README.md`. Silnik od 30.09.2026 wykonuje rtb-v0.4.

## Kierunek i decyzje

Odbiorca ma szybko zrozumieć sytuację w Polsce i regionie. Najpierw widzi RTB,
kierunek zmiany i krótki komentarz; potem położenie oraz chronologię sygnałów.
Dokumentacja techniczna nie jest częścią tego przepływu.

Zaakceptowane wymagania: neutralne akcje i nawigacja; czerwony tylko przy
zagrożeniach lub jako kolor ikony aplikacji; duży RTB; komentarz obok wyniku;
cztery sekcje nawigacji; mapa punktowa; oś czasu dzień/tydzień/miesiąc;
hamburger na telefonie. **Użytkownik wybrał opcję 2: B — Chronologia**.

Inspiracja: [Dovetail w Refero Styles](https://styles.refero.design/style/108e2695-6970-47d5-b5b0-eea8fc34e048),
obejrzana 27.09.2026. Adaptujemy oszczędność koloru, stopniowanie szarości,
typografię i neutralne przyciski. To interpretacja referencji, nie oficjalny
system Dovetail. Nie kopiujemy marketingowego układu, siatki dekoracyjnej
ani niebieskiego akcentu. Nasza skala odstępów ma bazę 4 px.

## Wybór układu

- **A — Mapa i kontekst (wcześniejsza propozycja):** mapa jako główna powierzchnia po
  lewej, pionowa oś czasu po prawej; spokojne odstępy. Wspiera szybki ogląd
  regionu i przejście od punktu do szczegółów.
- **B — Chronologia (zaakceptowany):** pionowa oś czasu po lewej, szersza mapa po prawej;
  zwartsza nawigacja i odstępy. Czytanie zaczyna się od ostatnich publikacji.
  Na telefonie oś poprzedza mapę. Wartość RTB nadal dominuje typograficznie.

Historyczny podgląd zachowuje obie propozycje. Frontend `web/` implementuje B;
nie oferuje użytkownikowi przełącznika projektu ani danych demonstracyjnych.

## Kolory i znaczenie

Źródło wartości: `theme.css`. Motywy jasny i ciemny korzystają z tych samych
ról. Domyślnie podgląd podąża za wyglądem hosta; wymuszenie motywu służy QA.

- Powierzchnie, teksty, separatory, przyciski i fokus są neutralne.
- Główna akcja: grafit na jasnym tle lub jasny na ciemnym; druga akcja:
  neutralny obrys albo sam tekst z czytelną reakcją na wskazanie.
- `--color-threat`: ocena zagrożenia lub wzrost indeksu. Strzałka i tekst
  wyjaśniają sens czerwieni. Czerwony wzrost nie jest etykietą „wysokie ryzyko”.
- `--color-brand-mark`: wyłącznie znak/ikona aplikacji; bez czerwonego słowa
  w nazwie, zaznaczenia menu, linku, przełącznika ani tła przycisku.
- Temat sygnału rozróżniamy ikoną i polską nazwą, nie barwą. Cyberatak nie
  staje się czerwony tylko dlatego, że należy do kategorii cyberbezpieczeństwa.
- Wysoki poziom zagrożenia wymaga jawnej oceny i etykiety tekstowej. Nie
  wyliczamy go z rodzaju źródła, numeru kategorii czy stałego progu w CSS.
- Brak danych, niepewna atrybucja i pewność danych nie korzystają z czerwieni
  zagrożenia. Brak alertu nie jest zielonym zapewnieniem bezpieczeństwa.

## Typografia i rytm

Inter, z systemowym fontem bezszeryfowym jako fallback. Bez fontu monospace
w zwykłych opisach. Wagi 400/500/600; cyfry RTB i czasu mają stałą szerokość.
RTB: historycznie 112 px w A i 104 px w B; Przegląd 0.5 używa 90 px,
72 px na mniejszym desktopie i 64 px na telefonie. Tytuł strony: 28/36 px;
sekcje: 18/24 px; proza: 16/24 px; etykiety i metadane: 12/16 px.

Odstępy: 4, 8, 12, 16, 24, 32, 48, 64 i 96 px, nazwane semantycznie w CSS.
Powiązane elementy mają 8–12 px, sekcje 32–48 px. Strukturalne kolumny
korzystają z Grid, szeregi przycisków z Flexbox i `gap`. Nie otaczamy każdej
sekcji kartą. Zaokrąglenie kontrolek i dużych powierzchni wynosi 8 px.
Warstwy wynikają z kontrastu powierzchni; cienie nie dekorują ekranu.

## Komponenty v0.3

- Indeks RTA (01.10.2026): nowa nazwa publiczna; kontrakt `rtb`, identyfikatory
  metodologii i archiwalne dane zachowują nazwy. Liczba i opis poziomu mają
  kolor: (0,20] zielony, (20,60] bursztynowy, >60 czerwony tylko przy
  `red_priority.eligible=true`; bez tej bramki pozostaje podwyższony/bursztynowy.
  To robocza skala prezentacji, bez kalibracji i wpływu na punktację.
  Zero i brak wyniku są neutralne; aktywne/nieustalone ostrzeżenie oficjalne
  wyłącza zieleń niskiego wyniku. Pewność pozostaje osobną informacją.
- Stopka (01.10.2026): podpis „RedThreatAlert by Pixels4Users” oraz informacja
  o indeksie po lewej; ikona X z linkiem do x.com/redthreatalert i „Postaw kawę”
  po prawej. Na wąskim ekranie grupa przechodzi poniżej tekstu i pozostaje
  wyrównana do prawej. Ikona ma etykietę dostępną, cel dotykowy 44 px
  i otwiera nową kartę; jest lokalnym SVG bez skryptu śledzącego.
- Zakres obserwacji (01.10.2026): rozwijana sekcja „Pewność danych…” znajduje
  się po treści widoku, przed stopką. W Przeglądzie poprzedzają ją oś czasu
  i mapa, również na telefonie. Mały wskaźnik pewności pozostaje przy RTB.
- Wsparcie (01.10.2026): na prośbę użytkownika zielony, oficjalny przycisk
  BuyCoffee w nawigacji desktop i stopce; prowadzi do
  buycoffee.to/red-threat-meter w nowej karcie. Lokalna kopia dostarczonego
  PNG primary, szerokość do 176 px i cel dotykowy co najmniej 44 px.
  To wyjątek od neutralnych akcji; zieleń marki nie oznacza poziomu indeksu.
- Nagłówek bez przycisku „Odśwież”: zachowuje datę raportu. Odczyt co 30 s
  i po powrocie do karty działa automatycznie; nie uruchamia nowej analizy.
- Powłoka (01.10.2026): sidebar desktop; do 620 px dolny pasek czterech
  zakładek (Przegląd, Mapa, Dziennik, Raporty), zamiast hamburgera.
  Bezpieczny odstęp pod treścią i safe-area; BuyCoffee pozostaje w stopce.
- Indeks i komentarz tylko w Przeglądzie. Pozostałe widoki zaczynają się
  od nagłówka i własnej treści; powiększona mapa również bez indeksu.
  Zmiana widoku przewija na początek i przenosi fokus na nagłówek.
- RTB: wartość, delta ze strzałką, okres porównania, pewność danych i dwa
  wkłady: działania oraz przygotowania. To odrębne informacje.
- Komentarz: miejsce na trzy zdania, ciasno powiązane z RTB; filtr pozostaje
  w `src/osint_dashboard/dashboard_commentary.py`. Do czasu połączenia z
  rejestrem zatwierdzonych ustaleń publikujemy `null`, bez automatycznej prozy.
- Mapa: neutralny podkład, ikony punktów, flaga dla zasięgu krajowego,
  kontrolki powiększenia i panel szczegółów. Zaznaczenie ma neutralny obrys.
- Oś czasu: grupy godzinowe/dobowe/tygodniowe, rozwijanie wpisów i powrót.
- Dziennik: tematy, źródła, wiersz sygnału i szczegóły.
- Raporty: stronicowana historia, odczyt, pobieranie tekstu, JSON i GeoJSON.
  Od 02.10.2026 „Czytaj” przewija do początku podglądu i ustawia fokus na
  tytule raportu; tak samo widoczny jest komunikat nieudanego odczytu.
  Zamknięcie podglądu zwraca fokus do przycisku otwierającego.
- Kontrolki: przycisk neutralny, link, pole wyboru, przełącznik okresu,
  stany hover/pressed/disabled/focus. Cel dotykowy co najmniej 44 × 44 px.
- Selektory (03.10.2026): wspólny chevron 16 px, odsunięty o 16 px od
  prawej krawędzi, z rezerwą 12 px między tekstem i ikoną. Dotyczy
  wyboru regionu, filtrów Mapy i Dziennika oraz rodzaju raportu.
  Wszystkie instancje korzystają z `.r-field > .r-select` w `web/styles.css`
  i tokenów `--select-*` w `theme.css`. Ikona dziedziczy
  neutralny kolor etykiety w obu motywach; wybór opcji i klawiatura pozostają
  natywne. Wymuszone kolory korzystają ze strzałki systemowej.

## Pliki i utrzymanie

- `design.md` — kierunek, decyzje, komponenty i historia zmian.
- `guidelines.md` — reguły użycia i odbioru UI.
- `theme.css` — jedyne źródło wspólnych tokenów.
- `ui/components/card.css` — wspólna karta `.r-card`; importowana przez
  frontend. API i przykład użycia: `ui/components/README.md`.
- `web/` — działający interfejs B; importuje tokeny z `theme.css`, czyta `/api/`.
- `schemas/dashboard/report.schema.json` — kontrakt danych, niezależny od układu.
- `ui/dashboard-fragment.html` — wspólny szablon, układy i interakcje A/B;
  zawiera wyłącznie dane syntetyczne.
- `scripts/build_dashboard_preview.py` — osadza bieżące tokeny w podglądzie.
  Pliku wynikowego nie edytujemy ręcznie.

Przed większą zmianą czytamy te trzy pliki systemu. Nowy wzorzec dodajemy
do wspólnych zasad i pokazujemy w podglądzie przed rozszerzaniem go na kolejne
widoki. Zmianę koloru lub odstępu wykonujemy w tokenie, nie w kopii komponentu.
Nie przenosimy danych przykładowych do publikacji live.
Poprawka wspólnego komponentu obejmuje wszystkie jego instancje w danej
wersji kodu. Osobne gałęzie mają własne kopie; przed odbiorem przenosimy
również przyjęte poprawki Design Systemu z pozostałych gałęzi.

## Przegląd regionalny — zaakceptowany 02–03.10.2026

Użytkownik zaakceptował `ui/experiments/rta-overview-prototype.html`.
To rozwinięcie B — Chronologia, z zachowaniem osi po lewej i mapy po prawej.
Metodologia indeksu pozostaje rtb-v0.4; numer 0.3 dotyczy Design Systemu.

- Jeden dropdown „Obszar” obok nagłówka „Przegląd”: domyślnie „Cały obszar”, następnie
  wszystkie województwa. Bez widocznej etykiety nad polem; nazwa „Obszar”
  pozostaje dostępna dla czytników ekranu przez `aria-label`. Wariant
  `.r-field-unlabeled` nie rezerwuje pustego wiersza po etykiecie.
  Bez osobnego przycisku resetującego i pustej opcji
  „Wybierz województwo”. Zachowujemy lokalne zapamiętanie wyboru.
  Wynik regionalny pochodzi z raportu; brak oceny pozostaje brakiem.
  Pewność krajowa jest podpisana jako dotycząca całego obszaru, bez kopiowania
  jej do województw. Przy regionie: „Nieustalona dla regionu”.
- Komentarz: Sytuacja / Wpływ na Polskę lub Twój region / Co zrobić.
  Nowe komentarze mogą mieć zatwierdzone nazwane części; stare pozostają
  pełnym tekstem w „Sytuacja”. **Rekomendacja jest prozą bez podkreślenia,
  klikalności i kursora linku** — poprawka użytkownika z 02.10.
- Trzy neutralne liczniki Lotnictwo / Cyber / Nawigacja, ostatnie 7 dni
  względem poprzednich 7. W wersji 0.5 kliknięcie rozwija trzy najnowsze wpisy; osobna akcja
  prowadzi do tego samego, pełnego zbioru w Dzienniku.
  Brak porównania zachowuje znaną liczbę, bez strzałki i bez etykiety normy.
  Zmianę i opis porównania pokazujemy dopiero, gdy jest ono dostępne;
  nie zastępujemy ich komunikatem o braku danych. Porównujemy same zapisane
  sygnały: częściowe źródło, zmiana konfiguracji i kolejka przeglądu nie
  blokują różnicy. Nieodczytana lub nieistniejąca historia nie udaje zera.
  Tak samo ukrywamy pusty
  trend indeksu i jego podpis — doprecyzowanie użytkownika z 03.10.
- „Skąd ten wynik?” ujawnia wkłady Działania / Przygotowania.
- Każdy wpis osi i listy ma etykietę obszaru; nieustalone przypisanie nie
  zmienia się automatycznie w zasięg ogólnopolski.
- Mapa Operacyjna: Obszar / Okres / Temat, mapa, lista. W filtrach są też
  województwa z zerem. Liczba lokalna jest oddzielona od komunikatów krajowych.
  Dziennik dodaje filtr źródła oraz dostęp do sygnałów bez daty.
- Znaczenie flagi krajowej wyjaśnia legenda mapy. Nie powtarzamy tego
  objaśnienia w szczegółach sygnału — doprecyzowanie użytkownika z 03.10.
- Indeks pozostaje tylko w Przeglądzie. Górna sekcja przewija się z treścią,
  aby dłuższy komentarz nie zasłaniał mapy ani osi. Dolna nawigacja mobilna
  nadal pozostaje przy dolnej krawędzi ekranu.
- Kolory i bazowe tokeny nie zmieniają się; nowe kontrolki mają cel 44 px,
  skala odstępów 4 px. Brak nowej palety i powiadomień.

## Historia indeksu — pierwotny kierunek 0.4 z 03.10.2026

Poniższy opis dokumentuje 0.4. Zmiany kompozycji i ruchu w 0.5 opisano dalej;
reguły historycznych danych nadal obowiązują.

- Nagłówek Przegląd i istniejący dropdown tworzą jeden szereg. Data raportu
  pozostaje po prawej. Usuwamy powtórzony tekst zakresu z góry strony.
- Główna sekcja zastępuje wcześniejszy układ: około 3/4 na wartość i wykres,
  1/4 na komentarz (minimum 280 px). Przy szerokości do 1120 px komentarz
  przechodzi pod wykres, a na telefonie jego części ustawiają się pionowo.
  Siatka osi czasu i mapy pozostaje bez zmian.
- Cała grupa indeks + historia + komentarz używa wspólnej `.r-card`.
  Karta jest neutralną powierzchnią bez cienia i dodatkowej ramki; jej tło,
  promień 8 px oraz odstępy pochodzą z tokenów. Odstęp wewnętrzny: 32 px,
  do 900 px szerokości 24 px, do 620 px 16 px. Komponent nie narzuca kolumn.
  Nie dodajemy kart do liczników, osi ani mapy. To decyzja użytkownika
  z 03.10.2026, po pierwszym podglądzie historii.
- Komentarz ma własną neutralną powierzchnię wewnątrz wspólnej karty:
  wariant `.r-card.r-card--inset`, biały w jasnym wyglądzie i jaśniejszy
  grafitowy w ciemnym. Odstęp 24 px, na telefonie 16 px, promień 8 px;
  bez cienia i dodatkowej ramki. Na desktopie panel zajmuje wysokość grupy,
  na telefonie przechodzi pod wykres. To rozwinięcie zaakceptowane
  03.10.2026 na wzór wydzielonego komentarza w wizja-koncept.
- Poziom zagrożenia, pewność i „Skąd ten wynik?” są po prawej stronie liczby.
  Na telefonie przechodzą pod nią. Wkłady Działania / Przygotowania,
  objaśnienie indeksu i opis częściowych obserwacji są wewnątrz rozwinięcia.
  Objaśnienie zera, brak wyniku oraz potrzeba pogłębionego przeglądu nadal
  pozostają widoczne bez otwierania szczegółów.
- Wspólna karta jest zdefiniowana wyłącznie w `ui/components/card.css`,
  a używający jej widok ustala tylko układ. Wykres odczytuje odziedziczone
  `--surface-background`, aby jego stała oś i obrysy punktów miały tło karty.
- Wykres obejmuje 14 dni kalendarzowych Europe/Warsaw, kończących się datą
  najnowszego raportu. Każdy dzień wskazuje ostatni dobowy raport z tego dnia;
  korekty tego samego momentu rozstrzyga czas publikacji. Dawnych wydań nie usuwamy.
- Liczba zachowuje swój kolor poziomu zagrożenia. Linia, wybór dnia i fokus
  są neutralne. Stała skala 0–100 nie wyolbrzymia małych różnic. Brak wyniku
  nie staje się zerem; dostępny raport bez wyniku można otworzyć przez datę.
  Linia łączy tylko sąsiednie dni spełniające dotychczasowe reguły porównywalności.
- Kliknięcie/Enter/Spacja otwiera raport; strzałki przenoszą fokus między
  dostępnymi dniami, Home/End do krańców. Hover podgląda wartość i nie zmienia
  wybranego dnia. Dotykowe pola mają co najmniej 44 px; w wąskim widoku sam
  wykres przewija się poziomo, bez poszerzania strony.
- Wartość, pewność, komentarz, mapa, oś i liczniki korzystają z jednego
  zapisanego raportu. Okna liczników kończą się jego `as_of`. Odczyt starszych
  sygnałów jest ograniczony czasem publikacji tego raportu; późniejsze korekty
  nie dopisują wiedzy do historycznego widoku. Nie generujemy nowej prozy.
- Przy województwie odczytujemy jego historyczny wynik; brak takiej oceny
  nie jest zastępowany wynikiem kraju. Wybór regionu nie resetuje daty.
- „Wróć do najnowszego” jest widoczne tylko podczas oglądania historii.
  Mapa i Dziennik zachowują wybraną datę oraz jawnie nazywają okres jako
  „Wybrany dzień” / „Tydzień raportu”. W Raportach nadal dostępne jest całe archiwum.
- Nieudany odczyt zachowuje poprzedni, spójny widok; szybkie wybory stosują
  wyłącznie ostatnie żądanie użytkownika. Odświeżanie najnowszego raportu
  w tle nie wyrywa użytkownika z historii.

Prototyp czyta wyłącznie istniejące publikacje przez dotychczasowe API.
Nie zmienia wag, bazy, raportów, kolektorów ani harmonogramu. Wyjaśnianie
przyczyn zmian indeksu pozostaje osobnym następnym rozszerzeniem.

## Przegląd 0.5 — zaakceptowany 04.10.2026

Użytkownik odrzucił warianty ograniczone do przekolorowania interfejsu.
Przyjęty kierunek zachowuje tło podsumowania i osobną powierzchnię komentarza,
ikony tematów oraz hierarchię danych. Referencja Modern Treasury dotyczy
czytelności kompozycji i reakcji na interakcje. Nie kopiujemy jego strony.

- Desktop: około 55/45 na indeks z historią oraz komentarz. Wykres ma 104 px
  wysokości, stałą skalę 0–100 i 14 dni; małe zmiany nie są wyolbrzymiane.
- Telefon: wynik i opis obok siebie, komentarz niżej, potem zwinięta historia.
  Przy 320 px opis wyniku przechodzi pod liczbę. Rozwinięta historia przewija
  się we własnym obszarze, z celami dotykowymi minimum 44 px.
- Każdy punkt ma kolor historycznej oceny, z ostrzeżeniami i bramką czerwieni
  z dokładnie tego raportu. Przed odczytem pełnej treści punkt jest neutralny.
  Tylko wybrany dzień ma pulsujący zewnętrzny pierścień (2,2 s). To wskazanie
  wyboru, nie alarm ani informacja o odczycie na żywo. Linia i fokus są neutralne.
  `prefers-reduced-motion` wyłącza puls, pozostawiając stały obrys.
- Liczniki są bez kart, z ikonami 30 px i liczbą 30 px. Rozwinięcie pokazuje
  maksymalnie trzy najnowsze rzeczywiste sygnały; pełna lista zachowuje filtr
  obszaru, tematu, daty raportu i siedmiodniowego okna.
- Szczegóły sygnału rozwijają się przy wpisie. Lista oraz kontekst mapy pozostają
  widoczne. Esc i przycisk zamykają szczegóły i zwracają fokus.
- Ruch: hover 160 ms, rozwinięcie 280 ms; animacja nie zmienia liczb ani treści.
  Tło podsumowania i mapy używa spokojniejszych neutralnych tokenów 0.5.
  Czerwone logo i semantyczne barwy wyniku pozostają punktami odniesienia.
- Zakres tego odbioru: wyłącznie Przegląd. Mapa Operacyjna, Dziennik i Raporty
  czekają na osobne propozycje. Kolejność: lokalny ekran → poprawki/akceptacja
  → weryfikacja danych → commit i push → publikacja → następny ekran.

## Odbiór techniczny Przeglądu 0.5 — 04.10.2026

- Rzeczywisty raport z 04.10, 11:28: RTA 1,8; pewność 22%; liczniki 39/3/5.
  Wybór 03.10 przełącza wynik na 2,2, komentarz i liczniki na 36/3/4.
  Raport 23.09 zachowuje brak wyniku i brak komentarza.
- Sprawdzono region z wynikiem 0 i bez wyliczonej pewności regionalnej,
  wybór dat klawiaturą, powrót do najnowszego, podgląd tematu i filtr Dziennika,
  rozwijanie wpisu, powiązanie z punktem mapy, zoom, duży widok i powrót fokusu.
- Motywy jasny i ciemny; szerokości 320, 390, 1024 i 1440 px. Izolowany
  test UI: 100/100, długi komentarz, oficjalna instrukcja, pusta publikacja,
  pusty komentarz oraz błąd odczytu. Dane testowe pozostają w katalogu tymczasowym.
- 32 testy frontendu, 14 testów hostingu oraz build Vite i Sites przechodzą.
  Redukcja ruchu jest obsłużona w CSS i JS; bez zmiany systemowych preferencji
  użytkownika podczas QA.
- Zmiany nie są jeszcze zapisane w commicie ani opublikowane; czekają na
  ocenę wyglądu tego ekranu. Główny podgląd czyta prawdziwe publikacje przez API.

## Historia

- **0.4 / 03.10.2026 — prototyp lokalny:** główny wynik razem z wyborem dnia
  na wykresie, komentarz po prawej oraz wspólna data wszystkich widoków.

- **0.3 / 03.10.2026:** zaakceptowany Przegląd regionalny, nazwane części
  komentarza, liczniki sygnałów i filtry mapy. Wdrożenie na gałęzi, przed publikacją.

- **0.2 / 27.09.2026:** użytkownik zaakceptował B — Chronologia. Frontend czyta
  wersjonowane raporty, zachowuje brak wyniku i odświeża odczyt co 30 sekund.
  Dostępność źródeł jest oddzielona od nieskalibrowanej pewności danych.
- **0.1 / 27.09.2026:** wspólna paleta neutralna, semantyka czerwieni,
  tokeny jasne/ciemne, skala 4 px, dwa warianty istniejącego dashboardu.
  Wybór był wtedy otwarty; decyzję zapisano w 0.2.

## Weryfikacja podglądu 0.1

Sprawdzono oba układy przy szerokościach 320, 736 i 1024 px oraz oba motywy.
Bez przewijania w poziomie i kolizji identyfikatorów. Działają zmiana skali osi
czasu, rozwijanie grup, przejście do szczegółów i powrót, zoom, duży widok mapy,
Esc, menu telefonu, utrzymanie fokusu w menu i filtr tematyczny dziennika.
Liczby sygnałów w podglądzie: 6 / 27 / 64; zmiana układu nie zmienia zbioru.

Zmierzony kontrast podstawowego tekstu, podpisów i czerwonego wskaźnika na tle
ekranu wynosi co najmniej 5,8:1, a granicy kontrolki mapy na jej tle 3,67:1.
To kontrola wymienionych par i scenariuszy, nie pełny audyt dostępności.
W sprawdzonych akcjach nie wystąpił kolor chromatyczny ani błąd JavaScript.
Nie podłączono publikacji ani danych live; wartości pozostają syntetyczne.

## Weryfikacja frontendu 0.2

Sprawdzono lokalny cykl publikacji na oddzielnej bazie fixture: nowy raport
zmienił ekran bez przeładowania. Odbiór UI obejmuje szerokości 1440, 736 i
320 px, jasny i ciemny motyw, znaczniki krajowe, szczegóły, zoom i duży widok
mapy, dzień/tydzień/miesiąc, filtry tematu i źródła, historię, pobieranie oraz
menu telefonu z powrotem fokusu. Nie stwierdzono poziomego przepełnienia.
Awaria pierwszego odczytu, przerwane odświeżenie, pusta baza i odzyskanie
połączenia mają odrębne stany. Przeszły 204 testy Python, 5 testów JS/PostgreSQL
oraz build. Następnie sprawdzono pełny cykl na rzeczywistych raportach:
Supabase → lokalne API → automatyczna aktualizacja otwartego ekranu.
Witryna Sites pozostaje osobną wizualizacją do czasu wdrożenia aplikacji.

## Ciągły wynik — 30.09.2026

Układ B pozostaje bez zmian. Nowe raporty pokazują RTB 0–100 i liczbową pewność według jawnej heurystyki. Zero ma neutralne wyjaśnienie i nie komunikuje bezpieczeństwa. Rozwijana sekcja opisuje osiem obszarów obserwacji. Historia zachowuje null i przerwy pomiędzy nieporównywalnymi seriami. Oficjalne ostrzeżenia pozostają nad indeksem.

## Weryfikacja frontendu 0.3 — 03.10.2026

Lokalny podgląd czyta rzeczywiste, opublikowane raporty. Sprawdzono szerokości
1440, 736, 390 i 320 px, jasny i ciemny wygląd, bez poziomego przepełnienia.
Odbiór obejmuje wybór województwa, wspólne filtrowanie osi i mapy, przejście
z licznika Cyber do obu wpisów CERT, obszary z zerem lokalnych sygnałów,
filtry okresu i tematu, szczegóły, zoom i powiększenie mapy, Escape oraz
powrót fokusu. Czytnik raportu nadal przewija do treści i zwraca fokus
do przycisku „Czytaj”. Rekomendacja jest elementem tekstowym bez podkreślenia.

Przeszły 369 testów Pythona, 17 testów JS/PostgreSQL i 14 testów warstwy
hostingu oraz oba buildy: lokalny i docelowy pakiet Sites. Dane testowe
pozostały odizolowane od bazy live. Nowe pola są opcjonalne, a stare raporty
i ich komentarze pozostają czytelne. Brakująca historia porównań oraz pewność
regionalna są opisane wprost. To odbiór lokalny, bez zmiany publicznej wersji,
harmonogramu ani danych Supabase.

## Weryfikacja prototypu 0.4 — 03.10.2026

Podgląd na `codex/ux-index-history` korzysta z rzeczywistych publikacji przez
odczyt istniejącego API. Wybór 2 października przywraca indeks 2,7, ówczesny
komentarz i liczniki 16 / 2 / 3; powrót do raportu z 3 października przywraca
indeks 2,2 i liczniki 36 / 3 / 4. Sprawdzono również 1 października,
wybór łódzkiego, przejście do Mapy z zachowaniem daty oraz powrót do
najnowszego raportu z fokusem na nagłówku.

Przeszło 31 testów JS/PostgreSQL i build frontendu. Testy obejmują brakujące
daty, zero i null, korekty publikacji, granice doby Europe/Warsaw, paginację,
wybór regionu, nieudany odczyt oraz wyścig szybkich wyborów. Potwierdzają też,
że późniejsze korekty nie zmieniają komentarza, mapy ani liczników w dawnym
raporcie. Testy PostgreSQL korzystają z odizolowanej bazy PGlite.

Sprawdzono szerokości 1440, 390 i 320 px, jasny i ciemny wygląd, strzałki,
Enter oraz widoczność wybranego dnia po zmianie szerokości. Strona nie ma
poziomego przepełnienia; na telefonie przewija się wyłącznie historia.
Przywrócono automatyczny wybór wyglądu. Konsola bez ostrzeżeń i błędów.
Nie opublikowano prototypu ani nie zmieniono danych, silnika i harmonogramu.

### Wspólna karta i opis obok wyniku — druga iteracja

Karta jest komponentem `ui/components/card.css`, importowanym przez frontend,
z tokenami w `theme.css` i przykładem użycia w `ui/components/README.md`.
Reguły widoku ustalają wyłącznie układ. Na dużym ekranie zachowano proporcję
840 / 280 px dla dwóch kolumn przy szerokości 1440 px. Opis indeksu przechodzi
pod liczbę również wtedy, gdy sam panel ma mniej niż 440 px szerokości.

Sprawdzono szerokości 1440, 736, 621 i 320 px, oba motywy, rozwijanie klawiszem
Enter i kliknięciem oraz odstęp między rozwinięciem a wykresem. Bez poziomego
przepełnienia strony. Zero w łódzkim i historyczny niewyliczony wynik mają
nadal widoczne wyjaśnienie przy zamkniętych szczegółach. Częściowe obserwacje
dla dodatniego indeksu są opisane w rozwinięciu; procent pewności jest widoczny.
Kontrast tekstów podstawowych, pomocniczych i trzech kolorów poziomu indeksu
na tle karty wynosi co najmniej 5,37:1 w jasnym i 7,22:1 w ciemnym motywie.
To sprawdzenie wymienionych par, nie pełny audyt dostępności.

Przeszło 31 istniejących testów JS/PostgreSQL oraz build. Wersja nadal jest
lokalnym prototypem bez publikacji; automatyczny wygląd został przywrócony.

## Publikacja 0.4 — 03.10.2026

Po akceptacji użytkownika wdrożono historię i wspólną kartę w istniejącym
projekcie Sites, wersja 18. Stan publikacji: `succeeded`; strona pozostała
publiczna pod `https://redthreatalert.pl`. Minimalne repozytorium hostingu
zawiera także `ui/components/card.css`, importowane przez wspólny arkusz.

W publicznym widoku potwierdzono raport z 3 października 13:05: indeks 2,2,
pewność 22%, liczniki 36 / 3 / 4. Wybór 2 października przywraca 2,7,
25%, liczniki 16 / 2 / 3 oraz ówczesny komentarz, mapę i oś. Działa powrót
do najnowszego raportu; konsola bez ostrzeżeń i błędów. Nie zmieniono
punktacji ani sposobu publikowania kolejnych raportów. Szczegóły wdrożenia:
`docs/hosting-runbook.md`.

## Mapa Operacyjna 0.5 — zaakceptowana, 04.10.2026

- Stały układ około 65/35: mapa po lewej, przewijana lista po prawej.
  Wybór sygnału rozwija jego szczegóły we wpisie, bez zmniejszania mapy.
  Telefon: mapa nad listą; cała strona przewija się naturalnie. Filtry
  Obszar / Okres / Temat pozostają natywne; przy 320 px są w jednej kolumnie.
- Każdy wpis ma ikonę tematu, datę, typ i lokalizację. Dane źródłowe
  i status weryfikacji pozostają w szczegółach. Czerwone logo i kolory indeksu
  zachowują znaczenie; zaznaczenie mapy jest neutralne.
- Nowa prośba użytkownika: sygnały połączone z granicami regionów. Obsługujemy
  16 województw PL i 27 jednostek administracyjnych UA z Natural Earth v5.1.2.
  Flaga w stolicy = jawny zasięg krajowy, punkt = geometria lub zweryfikowane
  miasto, obrys = nazwany region. Kliknięcie obrysu pokazuje jego wpisy;
  wybór z listy zaznacza wszystkie powiązane regiony i odsłania je, jeśli
  były poza kadrem. Kilka regionów nie zwielokrotnia licznika sygnałów.
- Granica regionu nie jest zasięgiem zagrożenia. Jeśli raport dotyczy mniejszej
  lokalizacji w znanym regionie, obrys jest przerywany i podpisany
  „orientacyjnie”. Brak rozpoznanej lokalizacji pozostawia wpis na liście.
  Nie zgadujemy obszaru z tytułu ani nie zapisujemy współrzędnych do raportu.
- Filtry uwzględniają jawnie nazwane województwo w location.label także
  w starszych wpisach z pustym region_ids. To nawigacja po sygnałach;
  regionalny indeks, ocena i zamrożone raporty pozostają bez zmian.
- Ruch: hover 160 ms, wejście szczegółów 280 ms z opacity/translate,
  aby przewijanie mobilne znało docelową wysokość. Reduced motion wyłącza
  animację JS. Esc i zamknięcie wracają do wpisu lub obrysu/markera.

### Sprawdzenie lokalne

Rzeczywisty raport 04.10.2026, 11:28: dzisiaj 4 sygnały, w tym 2 obwody
na mapie i 2 bez zaznaczenia. Tydzień: 61 sygnałów. Filtr lubelskiego:
2 lokalne + 5 krajowych; pojedynczy sygnał wskazuje także podkarpackie.
Sprawdzono obwód wołyński, regiony PL, flagi Warszawy i Moskwy, punkt miasta,
wybór regionu klawiaturą, kilka wpisów w jednym regionie, powrót fokusu,
zoom/reset/powiększenie, pusty wynik i 5 pomiarów bez lokalizacji.
Mapa na desktopie zachowuje wymiar 708 × 620 px po otwarciu szczegółów.
Jasny i ciemny motyw, szerokości 320, 390, 1024 px oraz domyślny desktop;
bez przewijania poziomego. Zmiany nie uruchamiają kolektorów ani zapisów do bazy.

Testy: 40 dashboard + 14 hostingu; build aplikacji i build:site przechodzą.
Zachowano pełną geometrię podkładu; główny pakiet ma około 276 kB gzip
(Vite zgłasza ostrzeżenie rozmiaru, nie błąd). Nie było commit/push/deploy
tej iteracji. Użytkownik zaakceptował ekran 04.10.2026 i zlecił pracę nad Dziennikiem.

## Dziennik Sygnałów 0.5 — lokalny odbiór, 04.10.2026

- Wpisy pogrupowane według dni; godzina, ikona tematu, tytuł i krótki zestaw
  metadanych zastępują szeroką tabelę. Separator wyznacza dzień, bez osobnej
  karty dla każdego wpisu. Dziennik korzysta z tej samej neutralnej palety co
  zaakceptowane Przegląd i Mapa.
- Szczegóły otwierają się bezpośrednio pod wpisem. Na desktopie opis stoi
  obok metadanych i źródeł, na telefonie nad nimi. Wydawca pojawia się raz,
  z osobnymi linkami do materiałów. Niepewność oraz informacja o nowszej
  wersji materiału pozostają widoczne przed rozwinięciem.
- Obszar, okres, temat i źródło zachowują istniejące reguły filtrowania.
  Do 620 px filtry są początkowo zwinięte; aktywne ustawienia i ich liczba
  pozostają widoczne. Na desktopie filtry są zawsze rozwinięte.
- Grupowanie publikacji i godziny używają Europe/Warsaw. Pomiar dobowy
  zachowuje dzień UTC i podpis „Pomiar”, bez fikcyjnej godziny. Braki dat
  trafiają do „Bez ustalonej daty”. To chronologia publikacji i pomiarów,
  nie domniemanych dat zdarzeń.
- Rozwinięcie ma opacity/translate 280 ms i obsługę ograniczonego ruchu.
  Enter/Spacja otwiera i zamyka; Escape wraca fokusem do wpisu.
  Po korekcie użytkownika usunięto zbędny przycisk × — ponowne kliknięcie
  wiersza lub chevronu zwija szczegóły. Żaden link do źródła nie jest zagnieżdżony w przycisku.

### Sprawdzenie lokalne Dziennika

Raport 04.10.2026, 11:28 i rzeczywiste archiwum: 105 sygnałów w 24 grupach.
Sprawdzono osobne i łączone filtry, pusty wynik, 7 wpisów bez daty,
5 pomiarów dobowych, cztery materiały jednego wydawcy oraz 2 sygnały lokalne
+ 5 ogólnopolskich dla lubelskiego w ostatnim tygodniu. Dane i punktacja
pozostają niezmienione; nie uruchamiano kolektorów ani zapisów do bazy.

Sprawdzono ciemny i jasny motyw, szerokości 320, 390, 1024 i 1280 px,
zwijanie filtrów na telefonie, rozwijanie i zamykanie szczegółów klawiaturą,
powrót fokusu oraz przejścia do Przeglądu i Mapy. Brak poziomego
przepełnienia i błędów konsoli. Izolowany podgląd QA symulował preferencję
ograniczonego ruchu; ustawienia systemu nie były zmieniane.

Testy: 44 dashboard + 14 hostingu. Cztery nowe testy obejmują granicę doby,
DST, pomiary bez godziny, brak daty i widoczność zastrzeżeń. Build aplikacji
przechodzi. Dziennik pozostaje do odbioru lokalnego, bez commit/push/deploy.


## Raporty 0.5 — lokalny odbiór, 04.10.2026

Na prośbę użytkownika ukryto wybór rodzaju raportów: archiwum pokazuje
wyłącznie raporty dobowe. Raportów tygodniowych obecnie nie publikujemy.
Selektor formatu pobierania w czytniku pozostaje dostępny.

- Archiwum grupuje publikacje według miesiąca. Wiersz zawiera datę, godzinę
  stanu danych, wersję metodologii, oznaczenie korekty i neutralną wartość
  indeksu. Nie koloryzujemy skrótu bez pełnych danych o ostrzeżeniach.
  Wszystkie wersje pozostają dostępne, włącznie z historycznym null.
- Cały wiersz otwiera czytnik w miejsce archiwum; nagłówek dostaje fokus.
  „Wróć do archiwum” i Escape przywracają pozycję listy i fokus na publikacji.
  Nie ma ikony × ani podglądu schowanego pod długą listą.
- Czytnik używa zapisanego komentarza, indeksu, pewności, ograniczeń i luk
  konkretnego raportu. Nie dopisuje zaleceń. Wartość indeksu korzysta z tej
  samej reguły koloru co Przegląd, a data dotyczy wybranej publikacji.
- Sygnały są rozwijane, uporządkowane od najnowszych publikacji/pomiarów,
  z opisem, datą zdarzenia, statusem i bezpiecznymi linkami źródłowymi.
  Nie korzystają z późniejszych raportów ani uzupełnień archiwum Dziennika.
- Pobieranie TXT/JSON/GeoJSON jest w jednym miejscu w czytniku. Eksport
  zachowuje istniejący format i bazuje na dokładnie tym samym raporcie.
  Stan błędu pozwala ponowić odczyt; spóźniona odpowiedź nie otwiera zamkniętego
  czytnika ani nie zmienia innego widoku.
- Neutralna paleta wspólna z wcześniejszymi ekranami. Ruch: subtelna reakcja
  wiersza i wejście treści 240 ms; respektujemy ograniczony ruch.

Weryfikacja: rzeczywiste archiwum 17 publikacji, pusty stan raportów
 tygodniowych, historyczne zero i niewyliczony wynik, korekta, powrót fokusu,
 105 sygnałów najnowszego raportu oraz pobrane pliki TXT/JSON/GeoJSON.
 Eksporty tekstu i geometrii porównano z pobranym raportem JSON.
 Zmiany lokalne, bez modyfikacji danych, punktacji, commit/push/publikacji.

Sprawdzono oba motywy, telefon 390/320 px, Enter, Escape, powrót fokusu
oraz neutralne zero i historyczny null. W jasnym podglądzie QA symulowano
ograniczony ruch bez zmiany ustawień systemu. Konsola końcowej wersji bez
nowych błędów. 44 testy dashboardu i 14 hostingu przeszły; oba buildy poprawne.
Pełny audyt z odłożonymi skillami pozostaje osobnym, późniejszym zadaniem.


## Raport — zaakceptowana struktura v1, lokalna implementacja

Źródło wymagań: `docs/report-presentation.md`, zaakceptowane 04.10.2026.
Niniejsza iteracja zastępuje wcześniejszy skrócony czytnik Raportów 0.5.

- Jeden model `web/report-presentation.js` zasila treść strony, wariant druku
  i TXT. Wynik, pewność, poziom, czas, komentarz i wydarzenia pochodzą wyłącznie
  z otwartego wydania. JSON/GeoJSON zachowują oryginalny kontrakt.
- Tytuł „Red Threat Alert — raport dzienny”, data, godzina Europe/Warsaw,
  duży indeks z poziomem i osobną pewnością, istniejące ustalenia, oficjalne
  ostrzeżenia, wydarzenia według wspólnej taksonomii, źródła i informacje
  o wydaniu. Wpis wielotematyczny pojawia się raz, zachowując etykiety.
- Podział komentarza zachowuje Sytuację, Wpływ na Polskę i Zalecenia;
  starszy akapit jest pojedynczym tekstem. Brak komentarza nie tworzy sekcji.
  Zero i historyczny null nie są zamieniane; delta wymaga porównywalnego,
  wcześniejszego raportu wskazanego w trendzie i pokazuje jego datę.
- Trwały adres: `/#raport/<report_id>`, wariant druku: ten sam adres z `/druk`.
  Działa wejście bezpośrednie i odświeżenie. Korekta prowadzi do poprzednika;
  znana korekta może być wskazana w starszym wydaniu bez zmiany jego treści.
- Czytnik izoluje ostrzeżenia i pokrycie od bieżącego Przeglądu. Statusy
  ostrzeżeń odnoszą się jawnie do chwili wydania, także gdy brak komentarza.
- Wariant druku rozwija wszystkie grupy i źródła, pokazuje adresy materiałów,
  używa jasnej powierzchni oraz reguł A4, marginesów i podziału stron.
  CSS `@page` zawiera numerację stron; jej wykonanie zależy od przeglądarki.
  `beforeprint` rozwija również sekcje zamknięte w czytniku, `afterprint`
  przywraca stan. Gotowy PDF jest opcją „PDF (.pdf)” we wspólnym selektorze
  formatów, dostępną po potwierdzeniu metadanych artefaktu. Jeden przycisk
  „Pobierz” obsługuje wszystkie formaty (integracja lokalna 05.10.2026).
- Metadane szablonu: `rta-report-v1`, osobne od metodologii. Kontrolki,
  nawigacja i kontekst bieżącego dashboardu są usuwane z wydruku.

### Weryfikacja specyfikacji

18 rzeczywistych publicznych wydań z lokalnego, odczytowego API: 995 wpisów
w sumie, zachowane liczby i streszczenia w modelu/TXT. Najnowszy testowany
raport ma stan na 04.10.2026 20:09, indeks 1,7 oraz 106 wydarzeń. Sprawdzono
korektę z 02.10 i jej poprzednika bez komentarza, starszy pojedynczy komentarz,
zero, null oraz krótkie wydanie z 9 wpisami. W publicznym archiwum nie było
oficjalnych ostrzeżeń ani dostępnych delt; te przypadki mają osobne testy
na izolowanych obiektach, bez danych syntetycznych w publicznym podglądzie.

50 testów dashboardu + 14 hostingu i oba buildy przechodzą. Kontrola DOM:
106 wpisów w 7 niepustych grupach, komplet 8 rozwiniętych sekcji w wariancie
wydruku, brak poziomego przepełnienia przy 320 px, fokus na tytule raportu.
Powyższa kontrola dotyczyła etapu czytnika. Integracja generatora 05.10.2026
dodaje kontrolę gotowego PDF: A4, tekst i linki wszystkich 106 wydarzeń,
numery stron i przegląd renderów. Systemowy dialog drukowania pozostaje
odrębną funkcją przeglądarki.

Zmiany wyłącznie lokalne na `codex/ux-index-history`, bez commit/push/deploy.

### PDF — łamanie długich list źródeł

Wspólny komponent źródeł wydarzenia ma w druku dwie kolumny. Pojedynczy
odnośnik pozostaje razem z nazwą wydawcy. Długie wydarzenie może przejść
na następną stronę; cały wpis nie wymusza pustego miejsca przed jego początkiem.
Zmiana dotyczy wyłącznie wariantu druku, bez skracania treści i źródeł.

### Zakres wydania 05.10.2026 — PDF odłożony

Decyzja użytkownika: publikujemy stronę raportu, wersję do druku i istniejące
eksporty TXT/JSON/GeoJSON. Wspólny selektor formatu pozostaje; gotowy PDF
nie jest dostępny i czytnik nie odpytuje jego metadanych. Powyższe opisy
lokalnej integracji PDF zachowują kontekst prototypu, nie status produkcji.

## Ujednolicenie rozwijanych sygnałów — 05.10.2026

Zaakceptowano wzorzec Dziennika dla wszystkich trzech list. Wspólna fabryka
`ui/components/signal-item.js` i arkusz CSS zawierają nagłówek z chevronem,
stan rozwinięcia oraz układ szczegółów. Wariant zwarty obsługuje Oś czasu
i listę przy mapie. Usunięto lokalne style oraz × i powtórzony tytuł
z rozwinięć. Dane, filtrowanie i układ głównych sekcji pozostają bez zmian.

Sprawdzenie: 51 testów frontendu bez błędów; build produkcyjny poprawny.
W przeglądarce: trzy listy, Enter/Spacja/Escape, fokus na nagłówku, wybór
z obszaru mapy, szerokości 1350/390/320 px bez przewijania w bok.

## Wszystkie kategorie w Przeglądzie — 05.10.2026

Zaakceptowano stałą kolejność: Lotnictwo, Cyber, Nawigacja, Infrastruktura,
Granica, Wojsko, Pozostałe. Siatka 4 + 3 na desktopie i dwie kolumny
na tablecie/telefonie, bez ramek. Licznik prowadzi do Dziennika z tym samym
regionem, okresem 168 godzin i datą wybranego raportu; powrót zachowuje
pozycję Przeglądu. Usunięto podgląd trzech wpisów z × i chevron rozwijania.
Hover zachowany we wspólnym komponencie, → komunikuje nawigację.

## Newsletter — podgląd lokalny, 05.10.2026

Przedstawiono dwa warianty: formularz nad stopką albo przycisk otwierający
osobne okno. Do lokalnego podglądu przyjęto pierwszy; wybór pozostaje
do odbioru użytkownika. Bez zmiany głównych ekranów, nawigacji i kolorystyki.
Formularz zawiera adres, osobną niezaznaczoną zgodę, informację o potwierdzeniu
i link do prywatności. Na telefonie przechodzi do jednej kolumny.

Potwierdzenie i prywatność używają natywnego dialogu z przyciskiem zamknięcia,
obsługą Escape i powrotem fokusu. Aktywacja zapisu wymaga osobnego przycisku.
Mail opiera się na wspólnym modelu raportu, zachowuje pełne wydarzenia
i źródła; zawiera link do konkretnego wydania, BuyCoffee i wypis.
Operator: Miłosz Michałowski-Żuk Pixels4Users, dane przekazane przez użytkownika.

Zakres i uruchomienie: `docs/newsletter-runbook.md`. Obecny etap obejmuje kod,
symulację całego zapisu i testy lokalne; nie uruchamia publicznej listy.
Infrastrukturę przedstawia ikona pociągu `train-front` ze wspólnej taksonomii.
Granicę przedstawia szlaban `construction`; flaga pozostaje oznaczeniem
zasięgu ogólnokrajowego. Wszystkie widoki pobierają ikonę kategorii
z `config/signal-presentation.json`.

Weryfikacja: 52 testy frontendu przeszły. Każdy z siedmiu liczników
otworzył identyczną liczbę wpisów; sprawdzono również zero, województwo
łódzkie i raport historyczny. Szerokości 1350/390/320 px, Enter i powrót
z przywróceniem fokusu oraz pozycji przewinięcia — poprawne. Efekt
focus korzysta z tych samych reguł ruchu co hover. Konsola bez błędów.

## Sekcja newslettera — iteracja według referencji, 06.10.2026

Na prośbę użytkownika wyróżniono sekcję neutralnym tłem i większą typografią.
Wizualizacja układu wiadomości jest po lewej, a nagłówek, opis i formularz
po prawej. Makieta nie pokazuje fikcyjnych odczytów ani dat; ma podpis
„Przykładowy układ newslettera”. Pole e-mail i pełny primary CTA „Zapisuję się
na raport” są jeden pod drugim. Zgoda pozostaje osobna i niezaznaczona.
Czerwień występuje wyłącznie w znaku marki; akcja korzysta z neutralnych tokenów.

Na telefonie formularz poprzedza wizualizację. Sprawdzono 1350, 390 i 320 px,
jasny i ciemny wygląd, wymaganą zgodę, lokalny zapis oraz Escape i powrót fokusu
w informacji o prywatności. Brak poziomego przewijania.
Kod tej iteracji jest w istniejącym worktree `codex/ux-index-history`;
zmiany pozostają lokalne, bez commit/push/publikacji.


### Skróty do zapisu, 06.10.2026

Na prośbę użytkownika dodano primary „Newsletter” nad BuyCoffee w nawigacji
oraz bezpośrednio po jego lewej stronie w stopce. Oba są natywnymi linkami
do sekcji `#newsletter` i korzystają z istniejących neutralnych kolorów akcji.
Sekcja przyjmuje fokus po przejściu linkiem; kolejny Tab prowadzi do e-maila.
Przy wyłączonym newsletterze skróty są ukrywane razem z formularzem.
Stopka mieści skróty w jednym szeregu również na małym ekranie.


### Okna newslettera — dopracowanie, 06.10.2026

Zgodnie z korektą użytkownika okno potwierdzenia i sukcesu jest wyśrodkowane,
ma maksymalnie 520 px i hierarchię: mała etykieta Newsletter, nagłówek, treść,
główna akcja. Padding 32 px i odstęp 24 px oddzielają grupy; na małym ekranie
padding ma 24 px. Przycisk „Potwierdzam zapis” jest pełnym, neutralnym primary
o wysokości min. 48 px. „Zamknij” zastąpiono ikoną Lucide X z dostępną nazwą
„Zamknij okno” i celem 44 × 44 px. Po sukcesie tekst o wypisie jest pomocniczy.
Prywatność zachowuje szerszy limit 680 px i przewijanie długiej treści.
Escape, ograniczenie Tab do dialogu oraz powrót fokusu pozostają dostępne.

Weryfikacja tej korekty: 52 testy dashboardu i build frontend/Worker przeszły.
W lokalnym symulatorze sprawdzono pełne potwierdzenie, błąd wygasłego linku,
Escape, powrót fokusu, 320 px bez przepełnienia, ciemny wygląd i przewijanie
prywatności. Konsola bez błędów. Test nie wysyłał rzeczywistych wiadomości.

### Szablon wiadomości — podgląd lokalny, 06.10.2026

Na prośbę użytkownika rzeczywisty mail otrzymuje nagłówek nawiązujący do
wizualizacji na stronie: ciemne tło, czerwony znak radar, tekstowa nazwa
RedThreatAlert, etykieta „Raport dzienny”, data i godzina stanu raportu.
Nagłówek i stopka są wspólnym komponentem `ui/email/layout.mjs`, używanym
także przez potwierdzenie zapisu. Nie są częścią jednorazowego podglądu.

Biała kolumna 680 px na tle #f6f6f6, padding 32 px (20 px na telefonie),
jasne wyróżnienie ustaleń oraz dyskretne nagłówki kategorii porządkują pełny
raport. Czerwień pozostaje tylko w znaku marki. Wariant e-mail systemu używa
stałych wartości jasnej palety z `theme.css`, fontów systemowych, tabel
prezentacyjnych i stylów inline dla głównego układu. Nazwa i data pozostają
tekstem również przy wyłączonych obrazach. PNG ma trwały, wersjonowany adres.

Treść zatwierdzonego raportu z 06.10 oraz temat i wersja TXT pozostały
identyczne; HTML zawiera wszystkie 128 wydarzeń i dwa linki wypisu.
Sprawdzono lokalny wygląd 1350/320 px, ładowanie znaku i brak przepełnienia
poziomego oraz błędów konsoli. 11 testów newslettera oraz build Edge i strony
przeszły. To lokalna propozycja, bez wdrożenia ani wysyłki. Odbiór
w rzeczywistym kliencie pocztowym wymaga osobnego testu.

### Krótki mail z kategoriami — 06.10.2026

Użytkownik wybrał listę kategorii z linkami do raportu. „Wydarzenia i kontekst”
pokazuje np. „Lotnictwo · 74 →”, „Cyber · 6 →” w stałej kolejności kategorii,
bez rozwijania wewnątrz maila. Liczniki pochodzą z tego samego zamrożonego
modelu co raport, a wpis wielotematyczny należy do jednej grupy głównej.
Kliknięcie prowadzi do konkretnego wydania i kategorii, rozwija ją,
przewija i ustawia fokus na jej nagłówku. Inne kategorie pozostają zwinięte.

Indeks, zatwierdzony komentarz, oficjalne ostrzeżenia, zakres źródeł i braki
pozostają w mailu. Zmiana dotyczy również tekstowej wersji wiadomości;
pełny raport i jego pobierany TXT nie tracą żadnej treści.
Akordeon HTML nie jest stosowany w wiadomości ze względu na niejednolitą
obsługę klientów pocztowych. Podgląd kieruje linki do lokalnej strony.

Weryfikacja lokalna: wszystkie 7 linków otworzyło poprawną kategorię tego
samego wydania, z zgodną liczbą wpisów, fokusem i przewinięciem. Sprawdzono
1350/390 px i Enter bez przepełnienia oraz błędów konsoli. 53 testy
dashboardu, 12 testów newslettera i oba buildy przeszły. HTML maila z 06.10
ma 12 810 bajtów zamiast 127 138; komentarz pozostaje identyczny. Bez publikacji
zmian i bez wysyłki.

## Analityka i zgoda — 06.10.2026, lokalnie

Zaakceptowano komunikat „Pliki cookie”, przyciski „Tylko niezbędne” i „Akceptuj”
oraz linki „Ustawienia” i „Polityka prywatności”. Neutralne, równie dostępne
akcje. Korekta użytkownika: baner jest stałą warstwą przy dolnej krawędzi
okna, nad treścią. Na telefonie pozostawia dostęp do dolnej nawigacji.
„Akceptuj” ma pełny, neutralny styl primary; odmowa zachowuje obrys.
Dialog wykorzystuje istniejące tokeny, dwie kategorie i domyślnie wyłączone
statystyki. Stopka zawiera „Ustawienia prywatności”. Wycofanie zatrzymuje GA
i odświeża stronę. Bez zmiany wyglądu pozostałych ekranów i bez publikacji.
