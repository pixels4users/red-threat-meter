# RTB — Design System

Wersja: **0.2**, 27.09.2026. Żywy dokument: aktualizowany razem z interfejsem.
Zakres: działający lokalnie frontend, wspólne tokeny i kontrakt publikacji.
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

## Komponenty v0.2

- Wsparcie (01.10.2026): neutralny przycisk „Postaw kawę” z ikoną filiżanki
  w nawigacji desktop/mobile i stopce; prowadzi do buycoffee.to/red-threat-meter
  w nowej karcie. Używa tokenów istniejących akcji, bez zewnętrznego obrazka.
- Powłoka: sidebar desktop, pasek z hamburgerem mobile, duży dialog menu.
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
- Kontrolki: przycisk neutralny, link, pole wyboru, przełącznik okresu,
  stany hover/pressed/disabled/focus. Cel dotykowy co najmniej 44 × 44 px.

## Pliki i utrzymanie

- `design.md` — kierunek, decyzje, komponenty i historia zmian.
- `guidelines.md` — reguły użycia i odbioru UI.
- `theme.css` — jedyne źródło wspólnych tokenów.
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

## Historia

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
