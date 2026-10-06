# RTB — zasady UI

Powiązane: `design.md`, `theme.css`, `docs/dashboard-presentation.md`.
Wersja 0.5 (Przegląd, Mapa i Dziennik po odbiorze, Raporty do odbioru lokalnego), 04.10.2026. Zasady kolorów wynikają z decyzji użytkownika;
zaakceptowany układ: **B — Chronologia**.

Newsletter (wdrożony 06.10.2026): wyróżniona sekcja nad stopką,
z wizualizacją wiadomości i neutralnym primary CTA pod polem e-mail,
bez domyślnie zaznaczonej zgody. Komunikaty rozróżniają wysłanie potwierdzenia
od aktywnego zapisu. GET nie aktywuje adresu. Mail korzysta z tego samego
zamrożonego modelu co czytnik raportu, z pełnymi ograniczeniami i źródłami.
Wydarzenia przedstawia jako listę kategorii z liczbą wpisów i linkiem do
konkretnej kategorii tego wydania. Pełne opisy pozostają w raporcie na stronie;
nie twórz nowej interpretacji na potrzeby maila. Link wypisu
umieszczaj na początku i na końcu. Primary „Newsletter” w nawigacji nad
BuyCoffee i w stopce po jego lewej stronie prowadzi do `#newsletter`; skróty
ukrywaj razem z wyłączonym formularzem. Uruchomienie: `docs/newsletter-runbook.md`.
Okno potwierdzenia ma maksymalnie 520 px, padding 32 px (24 px na telefonie),
24 px między nagłówkiem a treścią i pełny primary CTA o wysokości min. 48 px.
Zamknięcie to ikona × z etykietą dostępną i celem 44 × 44 px; zachowuj Escape
i powrót fokusu. Dłuższa informacja o prywatności ma osobną szerokość 680 px
i przewijanie treści wewnątrz okna.

Szablon maila: wspólny nagłówek i stopka z `ui/email/layout.mjs`, ciemny
masthead, czerwony znak marki PNG, tekstowa nazwa i data. Kolumna ma
maksymalnie 680 px. Wariant e-mail odwzorowuje jasną paletę i skalę odstępów
systemu w stylach obsługiwanych przez pocztę; nie używa Grid/Flex ani JS.
Nie zamieniaj tytułu i daty na obraz. Zachowuj trwałe adresy znaków marki
użytych we wcześniej wysłanych wiadomościach. Linki kategorii mają strzałkę
→, nie chevron rozwijania. Nie ukrywaj treści maila za nieobsługiwanym
akordeonem. Na stronie link otwiera tylko wskazaną kategorię i przenosi
do niej fokus; pozostałe pozostają zwinięte. Pełny eksport TXT się nie zmienia.

## Hierarchia i układ

1. Tylko w Przeglądzie indeks RTA pozostaje największą liczbą, razem z trendem i mniejszą pewnością danych.
2. Komentarz ma trzy nazwane miejsca: Sytuacja, Wpływ na Polskę / Twój region, Co zrobić. Nie dopisujemy zdań bez podstaw. Na telefonie jest pod wynikiem.
3. Mapa oraz oś czasu tworzą asymetryczny układ; nie kolekcję identycznych kart.
4. Cztery pozycje menu zachowują nazwy i kolejność. Mobile używa dolnego paska: Przegląd, Mapa, Dziennik, Raporty.
5. Każdy odstęp ma rolę z `theme.css`. Stosuj `gap` w szeregach i grupach.
6. Przy 320 px treść się zawija, bez poziomego przewijania i uciętych kontrolek.
7. Indeks występuje tylko w Przeglądzie i przewija się z treścią. W B oś czasu poprzedza mapę, również na telefonie.
8. Rozwijany zakres obserwacji umieszczamy po treści widoku, przed stopką;
   w Przeglądzie po osi czasu i mapie. Skrót pewności pozostaje przy RTB.
9. Indeks, historia i komentarz tworzą jedną wspólną `.r-card`. Używaj
   `ui/components/card.css` i tokenów `--card-*` / `--color-card` z `theme.css`.
   Nie kopiuj jej tła, paddingu, promienia ani cienia do reguł widoku.
   Karta nie narzuca Grid/Flexbox ani szerokości kolumn. Pozostałe sekcje
   zachowują dotychczasowy układ bez dodatkowych kart.
   Komentarz wewnątrz grupy korzysta z wariantu `.r-card.r-card--inset`
   i tokenów `--color-card-inset` / `--card-inset-padding`. Nie twórz
   lokalnego tła komentarza ani kolejnych kart dla jego poszczególnych zdań.
10. Opis poziomu, pewność i rozwinięcie „Skąd ten wynik?” grupujemy obok
    liczby; poniżej dopiero przy szerokości do 360 px. Wkłady i opis częściowych obserwacji są
    w rozwinięciu. Brak wyniku, objaśnienie zera i istotne ostrzeżenia
    pozostają widoczne. Rozwinięcie przesuwa treść, nie zasłania wykresu.

## Kolor

- Od 01.10.2026 użytkownik zatwierdził zielony niski wynik indeksu RTA.
  Zieleń opisuje niski poziom naliczonych sygnałów, nie gwarancję bezpieczeństwa.
  Robocza skala UI: (0,20] niski, >20 podwyższony; >60 wysoki dopiero z bramką
  czerwonego priorytetu. Zero/brak danych są neutralne; przy ostrzeżeniu
  oficjalnym nie używamy zieleni. Akcje nadal pozostają neutralne.
- Przyciski, aktywne menu, linki, hover, focus i przełączniki są neutralne.
  Wyjątek zaakceptowany 01.10.2026: zielony przycisk marki BuyCoffee,
  odróżniający wsparcie od aktywnej pozycji menu.
- Czerwień stosuj tylko do znaczenia zagrożenia oraz do ikony marki.
- Czerwona delta dodatnia oznacza wzrost indeksu, nie potwierdzenie ataku.
  Spadek jest neutralny; nie daje automatycznego komunikatu „bezpiecznie”.
- Dla punktu wysokiego zagrożenia dodaj również tekst i odpowiedni symbol;
  kolor nigdy nie jest jedynym nośnikiem znaczenia.
- Kategoria sygnału nie ustala jego poziomu zagrożenia. Ikona kategorii i
  oznaczenie ciężkości są oddzielne. Nie przywracaj palety tęczowej dla tematów.
- Nie używaj tokenu zagrożenia do błędu formularza, statusu połączenia,
  wybranego punktu mapy czy „braku tłumaczenia”. Opisz taki stan neutralnie.
  Punkt historii dziedziczy semantyczny kolor oceny z własnego raportu.

## Tekst i dane

- Polski, krótkie zdania, konkretne znaczenie dla mieszkańca Polski.
- Legenda mapy jest jedynym widocznym objaśnieniem symbolu flagi krajowej;
  nie dopisuj powtarzającej ją instrukcji do szczegółów sygnału.
- Metodyka, parsery, identyfikatory wersji i logi pozostają poza głównym UI.
- Nie ukrywaj istotnej niepewności w szczegółach źródła. Niepewnych sygnałów
  nie używaj do tworzenia pewnie brzmiącego komentarza.
- Brak wyniku lub komentarza nie oznacza niskiego zagrożenia. Nie podstawiaj
  przykładowego RTB do odczytu live i nie interpretuj pewności jako ryzyka wojny.
- Oś czasu grupuje czas publikacji. Nie zamieniaj go na datę incydentu.
- Fikcyjne odczyty muszą pozostać opisane jako podgląd, nawet bez banera.
- `null` wyniku oznacza „—” i krótki opis braku oceny; nigdy 0 ani ostatnią
  kompletną wartość udającą bieżący wynik. Awaria odczytu zachowuje ostatni
  raport z jego datą i informacją o braku odświeżenia.
- Nie wymyślaj procentu pewności. W v0.4 odczytuj go z confidence.percent; jest heurystyką jakości danych. Zero RTB to poprawna liczba; wyjaśnij, że brak naliczonych sygnałów nie potwierdza bezpieczeństwa. Historyczny null i brak odpowiedzi serwera nadal nie mogą być zastępowane zerem.
- Wykres i delta indeksu RTA łączą tylko wyniki tej samej metodologii i konfiguracji.
  Liczniki sygnałów stosują odrębne, prostsze reguły opisane poniżej.
- Historyczne wartości mogą pozostać widoczne jako osobne punkty także przy
  braku porównywalności. Nie łącz ich wtedy linią ani nie zastępuj braków zerami.
- Nieprzezroczyste fragmenty wizualizacji na karcie używają odziedziczonego
  `--surface-background`; nie zakładają białego tła strony.
- Wybór dnia stosuje się do indeksu, pewności, komentarza, mapy, osi i liczników.
  Korzystaj z treści zapisanej wtedy, bez późniejszych rewizji i dopisywania porad.
- Wykres ma stały zakres 14 dni kalendarzowych i skalę 0–100. Ponowne wydania
  jednego dnia nie wypierają wcześniejszych dni. Data końcowa nie przesuwa się
  po kliknięciu historycznego punktu. Brak raportu pozostaje przerwą.

## Interakcje i dostępność

- „Postaw kawę” jest osobnym linkiem wsparcia w menu desktop i stopce, poza czterema
  widokami danych. Otwiera nową kartę, z etykietą dostępną i `noopener noreferrer`.
- Przycisk ma czasownik lub jednoznaczną nazwę; ikona ma dostępną etykietę.
- Przegląd używa jednego dropdowna „Obszar”: „Cały obszar” jest domyślną
  opcją i sposobem powrotu z województwa. Bez dodatkowego przycisku obok pola.
  Kontrolka jest obok tytułu „Przegląd”; na innych ekranach działają ich własne filtry.
  Widoczną etykietę pomijamy tylko tutaj; dostępna nazwa pozostaje w
  `aria-label`, a `.r-field-unlabeled` usuwa pusty wiersz nad selektorem.
- Zachowuj widoczny fokus. Dialogi zamykają się przez Esc i przycisk, po
  zamknięciu zwracają fokus; Tab nie wychodzi za otwarte okno.
- Cel dotykowy minimum 44 × 44 px. Nie pomniejszaj tekstu pól na telefonie.
- Wybór dnia: kliknięcie/Enter/Spacja zatwierdza, strzałki i Home/End przenoszą
  fokus. Hover nie zmienia raportu. Wykres może przewijać się we własnym obszarze.
- Powrót do najnowszego raportu ma widoczną akcję. Odczyt w tle nie zmienia
  wybranego dnia; po niepowodzeniu pozostaw cały poprzedni raport wraz z datą.
- Wszystkie selektory korzystają ze wspólnego `.r-field > .r-select`
  w `web/styles.css` oraz tokenów `--select-*` w `theme.css`; nie twórz
  osobnych chevronów ani odstępów dla konkretnego ekranu. Zachowują natywną
  obsługę klawiatury i listy opcji.
  Chevron 16 px ma odstęp 16 px od prawej krawędzi oraz 12 px od tekstu;
  jest wycentrowany względem pola i nie przechwytuje kliknięć. W trybie
  wymuszonych kolorów przywracamy strzałkę systemową.
- Docelowo kontrast tekstu minimum 4,5:1, dużego tekstu oraz istotnych
  wskaźników i kontrolek 3:1. Sprawdzaj oba motywy, także na stanach hover.
- Mapa: plus/minus/reset/duży widok, przesuwanie, pinch; zwykłe przewijanie
  przewija stronę. Punkt otwiera szczegóły, nie uruchamia innej akcji.
- Oś czasu i filtry zachowują wybór po powrocie ze szczegółów.
- W ruchu szanuj `prefers-reduced-motion`; brak migania i pulsujących alarmów.
  Wyjątek użytkownika: wybrany dzień wykresu ma spokojny puls w kolorze
  historycznej oceny. Inne dni pozostają nieruchome; zredukowany ruch wyłącza
  puls, a karta w tle go wstrzymuje. Nie oznacza to nowego alarmu.
- Licznik tematu prowadzi bezpośrednio do Dziennika z tą kategorią, regionem
  i ostatnimi 7 dniami do wybranego raportu. Strzałka → oznacza przejście;
  licznik nie rozwija podglądu. Powrót przywraca pozycję i fokus w Przeglądzie.
- Na telefonie historia jest początkowo zwinięta, po komentarzu.
  Zawsze zachowaj przycisk rozwinięcia i datę wybranego raportu.

## Procedura zmiany

Pracujemy ekran po ekranie: prezentacja lokalna, poprawki i akceptacja,
weryfikacja danych, następnie commit/push i osobna publikacja. Nie rozszerzaj
redesignu na kolejny ekran przed odbiorem bieżącego.

Przeczytaj Design System, określ dotknięte widoki i edytuj wspólne tokeny
lub komponent. Frontend buduje `npm run build`; scenariusze uruchomienia
opisuje `docs/dashboard-runbook.md`. Historyczny podgląd A/B można nadal
wygenerować poniższym poleceniem; `--check` porównuje plik ze źródłem.

```sh
.venv/bin/python scripts/build_dashboard_preview.py \
  --output /private/tmp/rtb-design-system.html
```

Sprawdź desktop i telefon, oba motywy, klawiaturę, kliknięcie punktu, zmianę
okresu i pusty komentarz. Weryfikuj, że żadna akcja nie otrzymała czerwieni
i że zmiana układu nie zmieniła danych. Zapisz decyzję i ograniczenia w
`design.md`; wybór użytkownika odróżniaj od rekomendacji projektowej.

## Liczniki i kontekst regionalny

- Proza rekomendacji nie ma podkreślenia ani pozornej klikalności. Linkiem
  jest dopiero oddzielny odnośnik do źródła lub szczegółów.
- Liczniki pokazują zapisane sygnały, a nie liczbę ataków. Neutralne strzałki
  opisują zmianę liczby, bez automatycznych ocen „rutynowo” lub „anomalia”.
- Porównanie pokazujemy tylko wtedy, gdy jest dostępne. Bez niego zostaje
  sama liczba sygnałów, bez komunikatu zastępczego, strzałki i opisu porównania.
  Ukrywamy też podpis niedostępnego trendu indeksu. Informacje o niepełnym
  pokryciu źródeł pozostają dostępne osobno.
- Licznik porównuje zapisane sygnały po zakończeniu odczytu archiwum.
  Wcześniejsze sygnały mogą być zachowane także w nowszym raporcie.
  Gdy poprzedni okres nie ma wpisów, zero wolno przyjąć dopiero, gdy
  archiwum sięga początku obu okien. Błąd lub niezakończony odczyt ukrywa
  różnicę. Nie wymagamy identycznej konfiguracji źródeł, codziennych raportów,
  kompletności każdego kolektora ani pustej kolejki przeglądu.
- Okna tygodniowe to dwa rozłączne okresy po 168 h do daty raportu.
  Data publikacji i data zdarzenia pozostają rozdzielone.
- Region, temat, okres i źródło stosują te same reguły w licznikach i listach.
  Rozwinięcie mapy zachowuje jej filtry. Brak współrzędnych nie usuwa wpisu z listy.
- Zera przy województwach oznaczają zero lokalnych wpisów dla filtrów.
  Komunikaty ogólnopolskie są doliczane osobno i mają własną etykietę.
- Pewność całego obszaru nie jest pewnością wybranego województwa.
  Brak podstaw do obliczenia procentu regionalnego opisujemy słowem.
- Starsze raporty mają niepełne metadane. Nie przypisuj regionu z tytułu
  publikacji ani nie wymyślaj punktu w centrum województwa.

## Mapa Operacyjna — powiązanie z regionami

- Zachowuj stałą powierzchnię mapy przy otwieraniu szczegółów; wpis rozwija
  się w bocznej liście. Na telefonie lista nie ma własnego przewijania.
- Obrys jest powiązany z regionem zapisanym w raporcie, nigdy z dopowiedzeniem
  na podstawie tytułu. Granice pokazują kontekst administracyjny, nie zasięg
  ataku czy alarmu. Lokalność w znanym województwie = obrys orientacyjny.
- Dokładny punkt i zweryfikowana kotwica miasta mają pierwszeństwo przed
  szerokim obrysem. Flaga pozostaje oznaczeniem jawnego zasięgu krajowego.
- Każdy sygnał liczymy raz, nawet jeśli zaznacza kilka regionów. Rozróżniaj
  brak sygnałów i obecne sygnały bez lokalizacji, bez sugestii bezpieczeństwa.
- Regiony PL/UA pochodzą z wersjonowanego lokalnego podkładu; źródło, hash
  i transformacje są w web/assets/README.md. Bez zewnętrznego geokodowania
  treści raportów i bez dopisywania geometrii do danych live.

## Dziennik Sygnałów — chronologia i szczegóły

- Dziel listę na dni, zachowując ikonę tematu przy wpisie. Nie powtarzaj daty
  przy każdym wierszu i nie otaczaj każdego wpisu osobną kartą.
- Czas publikacji pokazuj w Europe/Warsaw; dobowy pomiar pozostaje przy
  jawnym dniu UTC z podpisem „Pomiar”. Nie zastępuj brakującej publikacji
  czasem zapisu, datą zdarzenia ani datą raportu.
- Szczegóły rozwijają się pod wybranym wpisem. Publikacja, status, źródło
  i lokalizacja pozostają dostępne; powtarzający się wydawca ma jedną nazwę
  oraz osobne linki do wszystkich materiałów.
- Nie ukrywaj niepewności ani nowszej wersji materiału wyłącznie w rozwinięciu.
- Na telefonie zwijaj filtry, zachowując podsumowanie aktywnych ustawień.
  Na desktopie pokazuj je stale. Lista przewija się razem ze stroną.
- Wpis jest natywnym przyciskiem z aria-expanded i aria-controls. Ponowne
  kliknięcie wiersza lub chevronu zwija szczegóły, bez osobnego przycisku ×.
  Escape zwraca fokus do wpisu; ograniczony ruch wyłącza wejście szczegółów.


## Raporty — archiwum i czytnik

- Dopóki nie publikujemy raportów tygodniowych, wybór rodzaju jest ukryty;
  archiwum domyślnie odczytuje raporty dobowe.

- Jeden wiersz = jedna publikacja. Zachowuj korekty i historyczne null;
  nie zastępuj starych ocen aktualną metodologią ani późniejszą treścią.
- Grupuj publikacje według miesięcy, bez czterech przycisków przy każdym
  wpisie. Pobieranie TXT/JSON/GeoJSON przenieś do czytnika.
- Czytnik zastępuje archiwum. Powrót przywraca fokus i pozycję listy;
  ładowanie, błąd i ponowienie pozostają w tym samym widoku.
- Pokazuj zapisany komentarz, ograniczenia i luki. Dane źródłowe są tekstem,
  nie HTML-em. Linki muszą przejść safeLink. Eksporty używają wybranego raportu.
- Nie pokazuj daty najnowszego raportu nad czytnikiem historycznym.
  Skrót archiwum ma neutralny indeks; kolor wymaga pełnego kontraktu RTA.


### Raport zgodny ze specyfikacją v1

- Stosuj `docs/report-presentation.md` i wspólny model treści strony/druk/TXT.
  Czytnik ma własną dużą wartość indeksu zgodnie z zaakceptowaną specyfikacją.
- Data i czas pochodzą z wydania. Późniejsze dane Przeglądu nie mogą zmieniać
  ostrzeżeń, pewności, wydarzeń ani treści czytanego raportu.
- Zachowuj dokładne `report_id` w adresie. Linki korekt są relacją `supersedes`,
  nigdy podobieństwem tytułu lub daty. Nie przenoś uwag o korektach do raportu live.
- Wszystkie szczegóły strony są dostępne w druku. Reguły druku zmieniają
  powierzchnię, typografię i paginację, a nie treść merytoryczną.
- Eksport ma jeden selektor formatu i jeden przycisk „Pobierz”. Opcję
  „PDF (.pdf)” dodawaj wyłącznie po odczycie poprawnych metadanych pliku dla
  konkretnego `report_id`; brak pliku ukrywa opcję. Nie dodawaj osobnego
  przycisku PDF. „Drukuj” pozostaje osobną funkcją przeglądarki.

### Zakres wydania 05.10.2026 — PDF odłożony

Decyzja użytkownika: publikujemy stronę raportu, wersję do druku i istniejące
eksporty TXT/JSON/GeoJSON. Wspólny selektor formatu pozostaje; gotowy PDF
nie jest dostępny i czytnik nie odpytuje jego metadanych. Powyższe opisy
lokalnej integracji PDF zachowują kontekst prototypu, nie status produkcji.

## Wspólny rozwijany sygnał (05.10.2026)

- Oś czasu, lista przy mapie i Dziennik używają `ui/components/signal-item`.
  Zwarty układ jest wariantem tego samego komponentu.
- Chevron jest widoczny przed rozwinięciem i obraca się po otwarciu.
  Nagłówek otwiera i zamyka; fokus pozostaje na nim. Nie dodawaj × ani
  drugiego tytułu do szczegółów we wpisie. Osobny panel pełnoekranowej mapy
  zachowuje możliwość zamknięcia.

## Kategorie Przeglądu — 05.10.2026

Wszystkie siedem kategorii, także z zerem, ma stałą kolejność z rejestru
`config/signal-presentation.json`. Siatka ma cztery kolumny na desktopie
i dwie do 1100 px. Wspólny komponent `ui/components/topic-shortcut.css`
zachowuje neutralne tło i unoszenie ikony na hover/focus oraz ruch →.
Ograniczony ruch wyłącza animację. Infrastruktura używa `train-front`.
Nie sortuj według liczby ani nie traktuj wolumenu jako rankingu zagrożeń.

## Analityka i prywatność — 06.10.2026

- Stosuj zaakceptowany tekst banera i nazwy przycisków; nie ukrywaj odmowy.
- GA4 ładuje się wyłącznie po zgodzie na skonfigurowanej domenie produkcyjnej.
- Zgoda newslettera jest niezależna. Nie przesyłaj tokenów, e-maili ani pól formularza.
- Zamknięcie ustawień/Escape nie zapisuje zmian; modal zwraca fokus.
- Baner jest stałą warstwą na dole nad treścią, ponad dolną nawigacją telefonu.
  „Akceptuj” jest primary; „Tylko niezbędne” pozostaje widoczne z obrysem.
  Niskie okno pozwala przewijać baner; ukrywamy go w druku.
- „newsletter_confirmed” wymaga nowego potwierdzenia API, nie ekranu sukcesu.
- Przed publikacją wykonaj listę odbioru z docs/analytics-plan.md.
