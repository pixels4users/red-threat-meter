# Analiza World Monitor dla RedThreatAlert

World Monitor może pomóc w wyborze dodatkowych źródeł i dopracowaniu kontroli jakości danych. Najbardziej przydatne kierunki dla RedThreatAlert to infrastruktura Bałtyku, rosyjskie zaplecze wojskowe oraz analizy zdolności Rosji. Rozszerzenie musi zachować cel RTA: zagrożenia dla Polski i wschodniej flanki NATO ze strony Rosji, z uwzględnieniem roli Białorusi.

- Analiza strony, kodu i dostępności wybranych źródeł: **02.10.2026**.
- Zapis dokumentu i doprecyzowanie preferencji użytkownika: **03.10.2026**.
- Przegląd analityczny: **`reviewer.type=agent`**. Użytkownik określił kierunek; nie przypisujemy mu wykonania weryfikacji źródeł.
- Status: zapis ustaleń i propozycji. Dokument nie stanowi uruchomienia integracji, zatwierdzenia nowych źródeł do punktacji ani zmiany metodologii.

## Decyzja użytkownika o zakresie rozbudowy

**Nie duplikujemy źródeł. Szukamy przydatnych źródeł, których RTA jeszcze nie ma.** Dotyczy to także ponownego pobierania tych samych danych przez inny serwis oraz uznawania kopii jednego komunikatu za niezależne potwierdzenia.

Przed dalszą pracą należy rozróżnić trzy sytuacje: źródło już podłączone, źródło wcześniej zapisane jako kandydat oraz nowy wydawca lub dostawca. Uzupełnienie istniejącego kandydata nie powinno tworzyć drugiego wpisu. Nowy wydawca nie oznacza automatycznie nowego pochodzenia informacji — może cytować źródło już wykorzystywane przez RTA.

Początkowa odpowiedź w czacie proponowała rozpoczęcie od mediów bałtyckich. Po doprecyzowaniu użytkownika traktujemy je jako istniejący plan integracji, a nie główną nowość wynikającą z analizy konkurencji. Nowe propozycje przedstawiono poniżej.

## Nowe źródła warte rozważenia

Kolejność jest rekomendacją analityczną, nie wynikiem pomiaru skuteczności. Dostępność odnosi się do sprawdzeń z 02.10.2026; przed integracją trzeba ją potwierdzić ponownie.

| Propozycja | Zastosowanie w RTA | Stan weryfikacji i ograniczenia |
|---|---|---|
| **Sjöfartsverket — ostrzeżenia nawigacyjne dla Bałtyku** | Oficjalny kontekst zakłóceń GNSS, ograniczeń żeglugi i ćwiczeń; pomoc w sprawdzaniu doniesień oraz rutynowych wyjaśnień. | Odczytano [stronę ostrzeżeń](https://navvarn.sjofartsverket.se/en/Navigationsvarningar/Navtexx). To własne doprecyzowanie kierunku zauważonego w module morskim WM, który korzysta z NGA. W RTA istnieje ogólny kandydat `maritime_ais_and_notices`; należy go doprecyzować zamiast dublować. Nie sprawdzono kolektora ani kompletności historii. Ostrzeżenie nie ustala rosyjskiego sprawcy ani intencji. |
| **Meduza lub The Moscow Times** | Odkrywanie doniesień o mobilizacji, zapleczu wojskowym i działaniach Rosji/Białorusi mających znaczenie dla Polski i flanki. | Oba bezpośrednie RSS zwróciły poprawny XML i HTTP 200. Propozycja: zacząć od jednego wydawcy i mierzyć, czy wnosi nowe ustalenia. Stosować filtr tematu, geografii i związku z celem RTA. Artykuł może powielać inne źródło; samo doniesienie nie potwierdza przygotowania do ataku. |
| **RUSI, następnie ewentualnie ISW** | Kontekst rosyjskich zdolności, logistyki i scenariuszy na 14–42 dni. Uzupełnienie OSW, jeśli wnosi odrębne ustalenia lub argumenty. | Odczytano [dział RUSI dotyczący Rosji i Eurazji](https://www.rusi.org/explore-our-research/regions-and-country-groups/russia-and-eurasia). Wybrana strona ISW zwróciła 403 w narzędziu WWW; nie dowodzi to powszechnej niedostępności serwisu. Kolektorów nie testowano. Analiza nie zastępuje dowodu konkretnego zdarzenia, a biblioteka kontekstu nie daje automatycznych punktów. |
| **Cloudflare Radar** | Kontekst zakłóceń łączności w Polsce i regionie, pomocny przy analizie infrastruktury. | Sprawdzono [dokumentację awarii](https://developers.cloudflare.com/radar/investigate/outages/), bez testu API wymagającego tokena. Późniejszy pilotaż. Awaria nie potwierdza cyberataku; przyczynę i atrybucję trzeba sprawdzać osobno. |
| **Yle News** | Opcjonalne rozszerzenie kontekstu Finlandii i północnej części Bałtyku. | Bezpośredni RSS zwrócił HTTP 200 i poprawny XML. Nie jest priorytetem wobec powyższych propozycji. Przydatność wymaga sprawdzenia na materiałach o bezpieczeństwie, ponieważ feed jest ogólny. |

W odczytanej wersji strony Sjöfartsverket występował komunikat: „GNSS, AIS, RADAR AND DGPS INTERFERENCE OBSERVED IN AREA”. Sama strona zastrzegała: „Updating of this page could be delayed”. Te fragmenty uzasadniają jej rolę jako kontekstu nawigacyjnego, bez traktowania jej jako pełnego strumienia bieżących incydentów.

## Źródła obecne lub wcześniej zaplanowane

Stan rejestrów RTA sprawdzono ponownie 03.10.2026: `sources-pilot-8`, `source-candidates-11`, `early-warning-1` oraz `aviation-pilot-1`.

| Źródło | Stan w projekcie | Wniosek z analizy konkurencji |
|---|---|---|
| GPSJAM | Istniejący pilotaż i import zweryfikowanych pomiarów do głównego przeglądu. | Nie pobierać drugiej kopii przez World Monitor. Dobowe dane nie stanowią taktycznego pomiaru w oknie 30 minut i nie uruchamiają bonusu korelacji. |
| ADSB.lol | Istniejący pilotaż jakości bieżącego API i odrębny audyt historii. | Zachować istniejący strumień. Inny interfejs do tych samych danych nie daje niezależności ani dodatkowych punktów RTA. |
| ERR, LSM, LRT | Kandydaci zaakceptowani do integracji 25.09.2026, bez podłączonych kolektorów w sprawdzonym rejestrze. | Użyteczne istniejące pozycje, nie nowe odkrycie. Próba RSS z 02.10 uzupełnia wiedzę o dostępie; szczególnie dla LRT, którego wcześniejszy wpis opisywał blokadę czytnika WWW. Nie zmieniono rejestru w ramach tej analizy. |
| NASA FIRMS | Kandydat; MAP_KEY nieskonfigurowany. | Zachować jako późniejszą możliwość weryfikacji doniesień o pożarach. Detekcja termiczna nie identyfikuje przyczyny ani sprawcy. [Dokumentacja API](https://firms.modaps.eosdis.nasa.gov/api/). |
| World Monitor military | Kandydat `worldmonitor_military`; wcześniej sprawdzona dokumentacja, bez testu uwierzytelnionych danych. | Traktować jako odniesienie badawcze. Nie dodawać agregatu jako niezależnego źródła już posiadanych obserwacji. |
| Źródła morskie | Ogólny kandydat `maritime_ais_and_notices`, dostawcy do wyboru. | Propozycja Sjöfartsverket doprecyzowuje tę lukę. AIS i mapy kabli wymagają osobnego sprawdzenia pokrycia, pochodzenia i warunków użycia. |

## Metodologia i kontrola jakości

Warto adaptować następujące zasady, po porównaniu z rozwiązaniami już istniejącymi w RTA:

1. **Oddzielna aktualność pobrania i treści.** Poprawne pobranie dzisiaj może zawierać stary materiał. Kontrakt World Monitor rozdziela też obserwację, obowiązywanie, publikację i pobranie oraz jawne wartości nieustalone. Cytat: „Transport freshness reports whether collection is `fresh`, `stale`, `missing`, or in `error`”. To kontrakt rozwijany etapami; dokumentacja nie oznacza, że wszystkie starsze strumienie już go stosują. [Wersja sprawdzona](https://github.com/koala73/worldmonitor/blob/773a02fff6cf7c34f9bcb9b283b61554ebb3ef94/docs/decision-signal-provenance.mdx).
2. **Rozdzielenie ważności i wiarygodności.** Pilne doniesienie może pozostawać niepotwierdzone. Cytat: „Importance” oraz „Credibility”. Warto wykorzystać ten podział w kolejce przeglądu, bez zastępowania dowodów liczbową reputacją wydawcy. [Metoda WM](https://github.com/koala73/worldmonitor/blob/773a02fff6cf7c34f9bcb9b283b61554ebb3ef94/docs/methodology/news-credibility.mdx).
3. **Katalog zgodny z konfiguracją.** Jawnie pokazywać źródła podłączone, częściowe, niedostępne i planowane. WM opisuje swój katalog jako „Inventory reconciled with the URLs used by the codebase”. To wzorzec kontroli spójności, a nie dowód jakości każdego strumienia. [Katalog odczytany 02.10.2026](https://www.worldmonitor.app/sources/).

Nie należy przenosić do RTA indeksu CII. Jego cel to wybór kraju wymagającego uwagi; łączy niepokoje społeczne, konflikty, aktywność wojskową i wiadomości. Wynik obejmuje 40% wartości bazowej i 60% komponentu zdarzeń oraz dodatkowe podwyższenia, m.in. za katastrofy. Autorzy zaznaczają: „These weights are editorial, not empirical”. CII nie mierzy zagrożenia Polski ze strony Rosji. [Sprawdzona metodologia CII v8](https://github.com/koala73/worldmonitor/blob/773a02fff6cf7c34f9bcb9b283b61554ebb3ef94/docs/methodology/cii-risk-scores.mdx).

Nie należy też kopiować prostego detektora współwystępowania jako dowodu przygotowań wojskowych. Dokumentacja opisuje komórkę 1° × 1°, okno 24 godzin i próg „3 or more different event types”. Taki wynik może skierować uwagę analityka, ale sam nie dowodzi związku przyczynowego, nierutynowości ani rosyjskiej atrybucji. [Sprawdzony opis detektora](https://github.com/koala73/worldmonitor/blob/773a02fff6cf7c34f9bcb9b283b61554ebb3ef94/docs/geographic-convergence.mdx).

Indeks RTA ma skalę 0–100, osobną pewność danych i rozdzielenie działań od przygotowań. Techniczny identyfikator wersji silnika to `rtb-v0.4`. Parametry pozostają niewalidowane prognostycznie. Zero nie potwierdza bezpieczeństwa. Obowiązujące kryteria są w [metodologii projektu](methodology.md).

## Utrzymanie skupienia na Polsce i flance

Nowy materiał powinien mieć udokumentowany związek z bezpieczeństwem Polski lub flanki albo z rosyjskimi/białoruskimi zdolnościami do oddziaływania na ten obszar. Samo wystąpienie nazwy kraju lub słowa „wojsko” nie wystarcza.

- Zdarzenia globalne trafiają do osobnego kontekstu tylko przy wyjaśnionym związku z celem RTA.
- Pomiary, doniesienia, analizy oraz oficjalne ostrzeżenia zachowują odrębne role.
- Ćwiczenia, awarie, sezonowość i zmiany pokrycia są sprawdzanymi wyjaśnieniami alternatywnymi.
- Jeden incydent opisany przez wiele portali pozostaje jednym incydentem. Niezależność ustala się dla konkretnego twierdzenia i materiału pierwotnego.
- O skuteczności nowego źródła świadczą dodatkowe istotne ustalenia i rozsądny koszt przeglądu, a nie liczba pobranych rekordów.

Ocena interfejsu WM jest opinią z oględzin: duża liczba równoległych zastosowań utrudnia szybkie zrozumienie priorytetu. Dla RTA warto utrzymać czytelne odpowiedzi na pytania: co się zmieniło, dlaczego dotyczy Polski oraz na jakich dowodach opiera się ocena. Ta analiza nie proponuje przebudowy interfejsu.

## Sprawdzenia dostępu i ograniczenia materiału

Próby wykonano **02.10.2026 około 22:49 CEST**, po jednym odczycie na kanał. Każda poniższa odpowiedź miała HTTP 200 i dała się odczytać jako RSS. Liczba pozycji dotyczy odpowiedzi, nie liczby istotnych incydentów ani pełnego pokrycia okresu.

| Wydawca i bezpośredni kanał | Pozycji RSS |
|---|---:|
| [ERR](https://news.err.ee/rss) | 50 |
| [LSM](https://eng.lsm.lv/rss/) | 50 |
| [LRT](https://www.lrt.lt/en/news-in-english?rss) | 100 |
| [Meduza](https://meduza.io/rss/en/all) | 30 |
| [The Moscow Times](https://www.themoscowtimes.com/rss/news) | 50 |
| [Yle News](https://yle.fi/rss/news) | 20 |

Nie potwierdzono ciągłości dostępu, kompletności historii, skuteczności filtrów, jakości pełnych artykułów ani uprawnień do ich redystrybucji. Zapis z 03.10 nie jest nowym testem dostępności usług.

Przejrzano kod WM w commicie **`773a02fff6cf7c34f9bcb9b283b61554ebb3ef94`**, którego data to 02.10.2026, 19:38:14 UTC. W `src/config/feeds.ts` wiele pozycji korzysta z Google News. Wiersz 287 nazywa kanał „Ukrainska Pravda EN”, ale kieruje zapytanie do `euromaidanpress.com`. To konkretny przykład wymagający kontroli tożsamości źródła przed adaptacją. [Kod wpisu](https://github.com/koala73/worldmonitor/blob/773a02fff6cf7c34f9bcb9b283b61554ebb3ef94/src/config/feeds.ts#L275-L287).

Katalog WM deklarował 757 aktywnych dostawców, obejmując również usługi techniczne i strony statusowe. Liczba ta nie odpowiada liczbie niezależnych źródeł informacji o zagrożeniu. Sam katalog zastrzegał: „It does not claim that a provider's redistribution terms have completed review”. [Katalog](https://www.worldmonitor.app/sources/), [część infrastrukturalna](https://www.worldmonitor.app/sources/infrastructure/).

Kod platformy WM jest objęty **AGPL-3.0-only**; prawa do danych dostawców i usługi hostowanej są odrębne. Adaptacja pomysłów, skopiowanie kodu i ponowne wykorzystanie danych to różne działania. Przed kopiowaniem kodu lub publikacją cudzych danych trzeba sprawdzić właściwe warunki. [Sprawdzona dokumentacja licencji](https://github.com/koala73/worldmonitor/blob/773a02fff6cf7c34f9bcb9b283b61554ebb3ef94/docs/license.mdx).

## Kontynuacja w innym czacie

Ten dokument zapisuje analizę i preferencję użytkownika. Przed wdrożeniem należy ponownie sprawdzić [źródła aktywne](../config/sources.json), [rejestr kandydatów](../config/source-candidates.json), [warstwę wczesną](../config/early-warning.json) i [pilotaż lotniczy](../config/aviation.json), ponieważ ich stan może się zmienić.

Proponowany kolejny krok to wybór jednego nowego źródła i ograniczona próba poza bazą live. Dla Sjöfartsverket należy rozwinąć istniejący temat morski; dla wydawcy rosyjskiego sprawdzić przyrost informacji wobec OSW i obecnych źródeł. Możliwy dwutygodniowy pilotaż powinien mierzyć nowe istotne ustalenia, powtórzenia, udział materiałów poza zakresem i czas przeglądu. Jest to propozycja dalszej pracy, nie uruchomiony harmonogram.
