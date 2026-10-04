# Ocena wartości pilotażu źródeł — 03.10.2026

**Rekomendacja: kontynuować oba pilotaże, zaczynając integrację od
Sjöfartsverket.** Ostrzeżenia morskie wypełniają konkretną lukę w kontekście
Bałtyku. Meduza pomaga odkrywać pominięte tematy, ale wymaga więcej selekcji
i dochodzenia do oryginalnego dowodu. Nie należy importować całego RSS jako
listy sygnałów.

To przegląd użyteczności, nie uruchomienie źródeł w dobowym cyklu.
Metodologia `rtb-v0.4`, konfiguracja źródeł, raport i strona pozostają bez zmian.
Przegląd i osobny przegląd krytyczny wykonał ten sam agent
(`reviewer.type=agent`); nie deklarujemy niezależnej kontroli drugiego analityka.

## Materiał i zakres porównania

Wykorzystano zapisane próbki z 03.10: 11 odrębnych ostrzeżeń Sjöfartsverket
oraz 30 pozycji Meduzy. Nie powtarzano pobrania żadnego kanału. Ręcznie
odczytano wybrane źródła pierwotne wskazane niżej.

Przejrzano pełne teksty 11 ostrzeżeń. Dla Meduzy oceniono wszystkie tytuły
i zapisane skróty, a dla 27 pozycji również treść dostępną w zapisanym RSS.
Trzy długie teksty poza zakresem — o emigrancie w Hiszpanii, Afganistanie
i karierze Wołodina — odrzucono po tytule i skrócie. Nie deklarujemy odczytu
wszystkich pełnych stron artykułów.

Porównanie wykonano na kopii rzeczywistej bazy: **603 wersje materiałów
i 99 ostatnich wersji zdarzeń**. Obejmowało wyszukiwanie nazw, miejsc,
wartości i identyfikatorów, przegląd tożsamości zdarzeń oraz odczyt trafień
tematycznych. Nie było ponownym audytem wszystkich historycznych ocen.
Brak dopasowania oznacza „nie znaleziono w przeszukanej bazie”, a nie
gwarancję kompletności historii.

| Wynik oceny | Sjöfartsverket | Meduza |
|---|---:|---:|
| Ocenione rekordy | 11 | 30 |
| Przydatny kontekst nawigacyjny | 3 | — |
| Trop doprowadzający do sprawdzonego, ograniczonego ustalenia | — | 4 |
| Pozostałe tropy do dalszego sprawdzenia | — | 5 |
| Tło o małej wartości dodatkowej dla dobowego RTA | — | 7 |
| Poza zakresem tej kolejki | 8 | 14 |

Dziewięć wybranych materiałów Meduzy nie oznacza dziewięciu nowych
incydentów. Cztery sprawdzone tropy nie oznaczają potwierdzenia wszystkich
twierdzeń w czterech artykułach. To wynik jednej próbki, bez ekstrapolacji
na skuteczność źródeł w kolejnych dniach.

## Sjöfartsverket: wysoka wartość jako kontekst morski

| Komunikat | Wartość dla RTA | Granica interpretacji |
|---|---|---|
| `BALTIC SEA NAV WARN 026/25` — zakłócenia nawigacji | Oficjalne ostrzeżenie dla żeglugi uzupełnia perspektywę GPSJAM. | Starszy komunikat nadal obecny na liście. Nie jest pomiarem bieżącego nasilenia ani potwierdzeniem sprawcy. |
| `BALTIC SEA NAV WARN 029/26` — ćwiczenia bez strzelań | Podaje obszar i zapowiedziane okno; pomaga sprawdzać rutynowe wyjaśnienia obserwowanego ruchu. | Zapowiedź nie potwierdza wykonania ćwiczeń, uczestników ani zamiaru. |
| `SWEDISH NAV WARN 162/26` — strzelania w rejonie Väddö | Konkretny kontekst czasowy i przestrzenny dla północnego Bałtyku. | Nie przypisujemy automatycznie rosyjskiego operatora ani punktów za ostrzeżenie. |

Źródło: zapis [listy ostrzeżeń Sjöfartsverket](https://navvarn.sjofartsverket.se/en/Navigationsvarningar/Navtexx)
z 03.10, 10:58:56 UTC. Pozostałe osiem wpisów dotyczy lokalnych utrudnień
żeglugowych, m.in. oznakowania i przeszkód na wodach śródlądowych.

**Deduplikacja działa w tej próbce:** 16 wystąpień w obszarach daje
11 ostrzeżeń. Komunikat o zakłóceniach występuje sześć razy; pięć dodatkowych
prezentacji nie zwiększa licznika. W bazie mamy już pomiary GPSJAM, lecz
nie znaleziono tych identyfikatorów ostrzeżeń. To dodatkowy rodzaj kontekstu,
nie drugi pomiar tego samego zjawiska.

Najważniejsze do sprawdzenia w kolejnych próbach: zachowanie numeru przy
zmianie treści, znikanie i odwoływanie ostrzeżeń, opóźnienie aktualizacji
oraz bezpieczne rozpoznawanie dat. Zapis czasu bez roku pozostaje surowy;
nie dopowiadamy go na podstawie dzisiejszego pobrania.

## Meduza: wartościowe odkrywanie tematów, umiarkowana wydajność

### Cztery tropy sprawdzone u oryginalnego wydawcy lub instytucji

1. **Lipsk — luka w wiedzy historycznej.** W migawce nie znaleziono tej
   próby sabotażu. Niemiecki rząd datuje zdarzenie na noc 4/5 sierpnia,
   a MSZ opublikowało stanowisko przypisujące je Rosji 1 września.
   Październikowy tekst aktualizuje wiedzę o podejrzanych; ich nazwisk
   i całego śledztwa prasowego nie zweryfikowano. Nie wolno tworzyć nowego
   ataku z datą publikacji. [Bundesregierung](https://www.bundesregierung.de/breg-de/suche/hybride-bedrohung-fragen-antworten-faq-2449150),
   [Auswärtiges Amt](https://www.auswaertiges-amt.de/de/newsroom/2800598-2800598).
2. **Finlandia — nowy temat do obserwacji.** Policja potwierdza otrzymanie
   zgłoszeń o podejrzeniach wtargnięć do mieszkań parlamentarzystów
   i rozpoczęcie wstępnego sprawdzania sprawy. To nie potwierdzenie rosyjskiej
   operacji ani serii ataków z jednego dnia. Relacja Yle dotyczy zdarzeń
   podejrzewanych w ciągu roku. [Policja Finlandii](https://poliisi.fi/-/poliisi-on-kaynnistanyt-esiselvityksen-liittyen-kansanedustajia-koskevaan-turvallisuusasiaan),
   [oryginalna relacja Yle](https://yle.fi/a/74-20249583).
3. **A7 — nowy kontekst finansowania.** Komunikat Treasury potwierdza
   sankcje OFAC wobec powiązanej z Rosją sieci płatniczej 1 października.
   Odrębne ograniczenie FinCEN opisano jako projekt regulacji. W bazie
   nie znaleziono tego tematu; nie ustalono jednak wpływu sankcji na zdolności
   Rosji. [Treasury](https://home.treasury.gov/news/press-releases/sb0644/).
4. **Kijów — uzupełnienie istniejącego bilansu nalotu.** Miasto opisuje
   trafienie Mostu Północnego 3 października oraz uszkodzenie jezdni i sieci
   trolejbusowej. To nowe szczegóły lokalne przy zapisanym już ogólnym
   bilansie Sił Powietrznych. Nie dodajemy drugi raz liczby dronów z tego
   nalotu. [Aktualizowany komunikat miasta](https://kyivcity.gov.ua/news/vorozha_ataka_na_stolitsyu_3_zhovtnya_informatsiya_onovlyuyetsya/).

W przypadku Kijowa narzędzie WWW udostępniło treść strony w wyniku
wyszukiwania; bezpośrednie otwarcie zwróciło błąd. Zachowano ten zakres
odczytu, bez deklarowania pobrania surowego dokumentu instytucji.

### Pięć pozostałych materiałów i ich ograniczenia

| Temat | Wartość dodatkowa i decyzja |
|---|---|
| Rzekomy plan ataków na energetykę, za NYT | Istotny trop, ale sama relacja Meduzy zaznacza brak uwierzytelnienia dokumentu. Oryginał NYT niedostępny dla narzędzia. Nie akceptowano planu jako ustalenia. |
| Projekt rosyjskiego budżetu wojskowego na 2027 | **Główna kwota 17,1 bln rubli jest już w OSW z 29.09, za Reutersem z 28.09.** Nowy element to przypisywana anonimowemu urzędnikowi przyczyna decyzji; nie została sprawdzona. Niski priorytet dalszej pracy. |
| Wypowiedź Zełenskiego dla FT o rozkazach Putina | Kontekst deklaracji i informacji wywiadowczych. Nie zweryfikowano oryginału rozmowy; nie jest dowodem wykonania rozkazu ani uwierzytelnieniem dokumentu NYT. |
| Uderzenia w Most Południowy w Kijowie | Możliwe dodatkowe lokalne skutki z 1–2.10; wymagają osobnego odczytu komunikatu zarządcy. Część tej relacji wraca w dwóch innych materiałach RSS. |
| Doniesienia o rafinerii i bazie paliw w Wołgogradzie/Samarze | Potencjalna aktualizacja wiedzy o rosyjskim zapleczu. Nie zweryfikowano nagrań i pierwotnych komunikatów. Starsze ataki są już w OSW; wspólna lokalizacja nie wystarcza do łączenia epizodów. |

Przy budżecie sprawdzono też cytowaną [analizę SWP z 04.09](https://www.swp-berlin.org/en/publication/russian-military-spending-soars-upending-the-kremlins-budget-plans).
Opisuje ona wcześniejsze wydatki i warunkową projekcję; nie potwierdza nowej
decyzji budżetowej z październikowego doniesienia. Zbieżność tematu
nie jest niezależnym potwierdzeniem tego samego twierdzenia.

### Co poprawić przed integracją Meduzy

- Filtr nadał priorytet 12 pozycjom. Siedem znalazło się wśród dziewięciu
  wybranych po przeglądzie; pięć okazało się tłem lub treścią poza zakresem.
  **Finlandia i A7 nie otrzymały priorytetu.** Filtr może porządkować kolejkę,
  ale nie powinien bezpowrotnie odrzucać pozostałych materiałów.
- Parser zachowuje skrót do 2000 znaków. Surowy RSS zawiera dłuższe treści
  oraz odnośniki do przywoływanych materiałów. Do pakietu analitycznego
  warto przekazywać wersjonowaną treść dostępną w RSS i odnośniki źródłowe,
  bez automatycznego otwierania wszystkich linków. Nie wymaga to dodatkowego
  pobrania kanału. Oryginalny dostarczony parser skillu pozostaje materiałem
  źródłowym; rozszerzenie powinno powstać w kodzie działającego procesu.
- Dwa teksty o tym samym pożarze rezydencji w Petersburgu są aktualizacją
  jednego epizodu, bez podstaw do rozpoznania sabotażu. Most Północny
  i Południowy to natomiast różne obiekty: deduplikujemy powtórzone fragmenty,
  nie całe artykuły tylko dlatego, że mówią o Kijowie.
- Materiały o wyborach na Łotwie w części powtarzają kontekst OSW i VDD.
  Sam nowy wydawca nie oznacza nowego ustalenia ani nowego sygnału na mapie.

## Zalecany kolejny etap

1. **Sjöfartsverket:** zebrać 2–3 kolejne dobowe próbki w istniejących
   limitach, sprawdzić aktualizacje i odwołania, następnie przygotować adapter
   do istniejącej kolejki ocen. Próba na kopii bazy ma potwierdzić, że
   powtarzany komunikat pozostaje tym samym materiałem/zdarzeniem.
2. **Meduza:** najpierw zachować pełniejszy materiał z RSS i pochodzenie
   twierdzeń, poprawić priorytety na ujawnionych przypadkach i sprawdzić
   kolejne próbki. Nie dodawać na tym etapie drugiego podobnego wydawcy.
3. **Przed codzienną pracą:** ustalić dozwolony zakres wykorzystania treści
   oraz przeprowadzić import na kopii bazy z kontrolą raportu i eksportu.
   Pełne teksty pozostają materiałem roboczym; ta ocena nie potwierdza
   uprawnień do ich redystrybucji.

Nie ma podstaw do nowej wersji metodologii z powodu samego dodania tych
źródeł. Materiały przechodzą dotychczasową ocenę i przegląd; dopiero
ustalenie spełniające obecne kryteria może wpłynąć na indeks. Kontekst
może poprawić komentarz i interpretację obserwacji bez dodawania punktów
lub osobnego wpisu na stronie. Zasady z Threshold służą tu kontroli jakości,
bez równoległego procesu analitycznego.

## Ślad przeglądu

- Kopia kodu odniesienia: commit `7e4029b616a87d1e6b1d24f3642240b730a989e9`.
- Prywatny pakiet: `data/source_pilots/reviews/2026-10-03T142723Z/`.
- `manifest.json`: tożsamość surowych próbek, kodu i kopii bazy.
- `review-v2.json`: aktualne decyzje dla wszystkich 41 rekordów i przegląd
  krytyczny. `review-v1.json` zachowano; wersja druga koryguje wcześniejszy
  wniosek o nowości kwoty budżetowej po znalezieniu jej w OSW.
- `primary-source-review-v1.json`, `primary-web-readbacks.json` i osobny
  `primary-web-readback-supplement.json`: zakres ręcznej weryfikacji i odczyty;
  nie są surowymi odpowiedziami HTTP wydawców.
- `baseline-matches.json`, `baseline-expanded-search.json`: dopasowania,
  w tym wynik wyszukiwania dokładnej wartości budżetu.
- `verification-v2.json`: sprawdzenie pokrycia decyzji, cytatów, hashy próbek
  i zgodności bazy live z kopią odniesienia; uzupełnia zachowany wcześniejszy
  `verification.json` o kontrolę cytatów w odczytach źródeł z sieci.

Przegląd nie obejmuje pomiaru ciągłości przez wiele dni ani wydajności
docelowego adaptera. Czas jednorazowego audytu zapisano w pakiecie;
nie jest to prognoza kosztu codziennej obsługi.
