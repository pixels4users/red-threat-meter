# RTB — Design System

Wersja: **0.4 — historia indeksu i wspólna karta**, 03.10.2026. Żywy dokument: aktualizowany razem z interfejsem.
Zakres: wdrożony frontend; prototyp z `codex/ux-index-history` został włączony
do `codex/analysis-runtime` po akceptacji użytkownika.
Publiczny dashboard korzysta z tego interfejsu od 03.10.2026, wersja Sites 18.
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
RTB: 112 px w A, 104 px w B, 88 px na telefonie. Tytuł strony: 28/36 px;
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
  względem poprzednich 7. Kliknięcie prowadzi do tego samego zbioru w Dzienniku.
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

## Historia indeksu — kierunek zaakceptowany 03.10.2026

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
