# Metodologia RTB v0.2

Wersja z 23.09.2026. Status: eksperymentalna, bez kalibracji prognostycznej. Wykonywalna definicja znajduje się w `config/scoring-v0.json`; nazwa pliku jest stała, wersja i hash treści są zapisywane w każdym wydaniu. Instrukcje agentów, konfiguracja i ten dokument opisują ten sam model.

## Cel i znaczenie

RTB opisuje nasilenie potwierdzonych działań RU/BY oraz sygnałów przygotowań wojskowych istotnych dla Polski i wschodniej flanki NATO. Wspiera przegląd Indicators & Warnings. Nie mierzy prawdopodobieństwa wojny ani zamiaru ataku. Zdolność, intencja i wystąpienie zdarzenia są osobnymi ustaleniami. Baza i punkty nie mają empirycznej interpretacji procentowej.

Wynik rozdziela dwa wkłady: `hostile_activity` (pozostałe kategorie) i `preparation` (logistyka/medycyna oraz aktywność lotnicza RU/BY). Wkłady pokazuje się po limitach kategorii, bez bazy. Przy limicie całego indeksu 100 suma wkładów plus baza może przewyższać wynik. Przy niekompletnych danych wkłady służą wyłącznie diagnostyce.

Podstawowy zakres punktacji obejmuje PL, LT, LV, EE, CZ, SK, HU, RO, BG, DE, FI, SE. Szczególne zakresy kategorii podano niżej. Obserwacje mogą obejmować szerszy region, w tym Ukrainę i zachodnią Rosję, bez automatycznego naliczania punktów. To roboczy zakres; obecne kolektory skupiają się na Polsce i nie zapewniają pełnego pokrycia tych państw.

## Czas i scenariusze

Okno punktacji obejmuje bieżący dzień i sześć poprzednich dni kalendarzowych w Europe/Warsaw, do chwili odcięcia. Nie jest to dokładnie 168 godzin. Czasy pobrań i ocen są zapisywane w UTC. Data publikacji nie zastępuje daty zdarzenia. Sygnał wypada z sumy po opuszczeniu okna; nie stosujemy dodatkowego wygaszania ani wielokrotnego doliczania trwającego zdarzenia każdego dnia.

Dla trwałej aktywności nowy rekord wymaga odrębnej udokumentowanej zmiany, własnej daty oraz związku z wcześniejszą kampanią. Kontynuację bez nowego faktu opisujemy jako kontekst. Raport tygodniowy jest docelowym rytmem analizy; harmonogram nie jest jeszcze uruchomiony.

Interpretacja strategiczna używa roboczego horyzontu 14–42 dni. Scenariusz zawiera warunki, dowody, kontrargumenty i sygnały rozstrzygające. Nie generujemy z RTB liczbowej prognozy ani automatycznej oceny szczebla eskalacji. Skrypt tworzy raport danych; interpretację uzupełnia analityk według `docs/templates/analytical-brief.md`.

## Punktacja i kryteria

`RTB = min(100, 10 + suma wkładów po limitach kategorii)`, wyłącznie po przejściu kontroli kompletności. Zero zakwalifikowanych punktów daje bazę 10, co nie dowodzi bezpieczeństwa.

W każdej kategorii wymagamy potwierdzenia wystąpienia, daty, kraju i atrybucji RU/BY. Dla przygotowań atrybucja identyfikuje operatora sił lub infrastruktury, a nie zamiar ataku. Nieustalony sprawca oznacza obserwację poza punktacją, nawet gdy samo zdarzenie zostało potwierdzone.

| Kategoria / klucz | Punkty / limit w oknie | Zakres i dodatkowe kryteria |
|---|---:|---|
| Logistyka lub medycyna wojskowa / `military_preparation` | 15 / 30 | Białoruś albo obwód królewiecki; `logistics_or_medical_change`, `baseline_anomaly`, `operational_relevance`, `routine_explanation_checked`; dla RU także `kaliningrad_oblast` |
| Sabotaż / `sabotage` | 10 / 30 | Zakres podstawowy; `intentional_action`, `critical_infrastructure` |
| Eksplozja w zakładzie zbrojeniowym / `arms_explosion` | 8 / 24 | Zakres podstawowy; `explosion_confirmed`, `arms_facility` |
| Naruszenie przestrzeni NATO / `airspace_breach` | 5 / 25 | Zakres podstawowy; `nato_airspace_breach` |
| Anomalia lotnicza RU/BY / `air_activity` | 4 / 12 | Zakres podstawowy, Białoruś, obwód królewiecki; `baseline_anomaly`, `military_activity`; dla RU także `kaliningrad_oblast` |
| Cyberatak / `cyberattack` | 3 / 12 | Wyłącznie Polska/Litwa; `large_scale`, `target_banking_or_government` |
| Presja graniczna / `border_pressure` | 3 / 9 | Polska/Białoruś i granica PL–BY; `baseline_increase`, `pl_by_border` |
| Zakłócenia GPS / `gps_jamming` | 2 / 8 | Zakres podstawowy; `duration_over_24h` |

Każde spełnione kryterium wskazuje własne dowody typu `criterion`; jeden fragment może uzasadniać kilka kryteriów, jeśli rzeczywiście zawiera odpowiednie ustalenia. Sam szpital, transport lub pożar nie wystarcza. Uderzenie w obwodzie lwowskim nie jest naruszeniem przestrzeni NATO. Ćwiczenia lub loty obronne NATO pozostają kontekstem.

Dla anomalii analityk podaje miarę, okres odniesienia, wartości porównania, źródło i ograniczenia obserwacji. Powinien sprawdzić ćwiczenia, rotację, sezonowość i zmianę dostępności danych. Gdzie jest to możliwe, warto zacząć od co najmniej 30 dni danych i porównania ze zbliżonymi ćwiczeniami; to zalecenie badawcze, nie automatyczny próg. Brak podstawy porównania oznacza niespełnione kryterium. System nie oblicza jeszcze anomalii z danych telemetrycznych.

`routine_explanation_checked` oznacza zapisanie konkurencyjnego wyjaśnienia i powodów, dla których pozostaje istotna zmiana ponad zwykłą aktywność. Nie oznacza dowiedzionego zamiaru ataku. Sama etykieta „sprawdzono” bez treści dowodu jest niewystarczająca analitycznie.

Jedno zdarzenie ma stabilny `event_key`, jedną kategorię i najwyżej jedną aktualną rewizję. Wiele publikacji może wskazywać to samo zdarzenie; jedna publikacja może opisywać kilka odrębnych zdarzeń. Tożsamość ustala analityk. Tego samego lotu nie punktujemy raz jako logistyki, a drugi raz jako anomalii lotniczej. Powtórzenie pobrania identycznej treści nie tworzy nowego materiału.

Wspólny `campaign_id` ogranicza punktowanie do jednego zdarzenia w danej kategorii. Kod nie rozpoznaje automatycznie wspólnego zdarzenia pod różnymi event_key lub kategoriami. Limity kategorii ograniczają nadmierny wkład jednej kategorii, lecz nie naprawiają błędnego przeglądu. Surowa suma, wkłady i wykluczenia pozostają dostępne do audytu.

## Próg i priorytet geograficzny

Wynik **ściśle ponad 60** daje `alert.status=analyst_review_required`. To robocza reguła pilnego przeglądu, z `calibrated=false`, bez przypisywania wysokiego prawdopodobieństwa wojny. Wynik 60 nie przekracza progu. Przy `score: null` status wynosi `not_assessed`; brak oceny nie jest sygnałem uspokojenia. Nie działa wysyłanie powiadomień.

Obszary w `config/strategic-areas.json` nadają priorytet przeglądowi. Nie wprowadzamy mnożnika punktów ani arbitralnego promienia bliskości. `strategic_context`, jeśli występuje, wymaga identyfikatorów obszarów, uzasadnienia i dowodów lokalizacji. Samo skojarzenie nazwy miejsca z ważną bazą nie wystarcza.

GeoJSON używa WGS84 i kolejności `[długość, szerokość]`. Punkt wymaga dowodu lokalizacji i jawnej dokładności. W przeciwnym razie geometria ma wartość `null`; nazwa regionu nie staje się jego środkiem. Aktualna implementacja nie ma automatycznego geokodera. Lokalną bazą jest SQLite, bez wymogu PostGIS.

## Standard dowodowy

Oddzielnie dokumentujemy wystąpienie, przypisanie operatora/sprawcy, czas, lokalizację i kryteria. Wnioski o intencji, kontroli refleksyjnej i maskirowce są hipotezami do sprawdzenia, a nie domyślną kwalifikacją.

| Status | Znaczenie |
|---|---|
| `unverified` | Brak wystarczającego potwierdzenia |
| `confirmed_primary` | Potwierdzenie danego twierdzenia w źródle pierwotnym |
| `corroborated` | Co najmniej dwa źródła o niezależnym pochodzeniu |
| `disputed` | Zapisane dowody sprzeczne |
| `refuted` | Twierdzenie uznane za obalone, z uzasadnieniem |

Punktacja przyjmuje `confirmed_primary` lub `corroborated` dla wystąpienia i atrybucji. Komunikat o zatrzymaniu lub zarzutach nie jest automatycznie dowodem wszystkich zarzucanych czynów. Dwa portale cytujące MON lub tę samą agencję mają wspólny `origin_id`. Ocena niezależności pozostaje zadaniem analityka. Brak potwierdzenia nie oznacza dezinformacji.

Walidator sprawdza obecność cytatu w zapisanym materiale, identyfikatory i typy referencji, źródła oraz deklarowane statusy. Nie rozstrzyga semantycznego znaczenia cytatu, prawdziwości niezależności, skali anomalii ani intencji. Przegląd pozostaje nadzorowany; wykonanie przez model jest oznaczane `reviewer.type=agent`.

Biblioteka `data/doctrine_rag` ma osobny rejestr i indeks lokalny. Pomaga formułować hipotezy oraz kontrhipotezy. Nie jest podłączona do kolektora incydentów; walidator odrzuca materiał oznaczony `doctrine` lub `reference` jako dowód incydentu. Nie wolno obchodzić tej granicy przez zmianę etykiety dokumentu. Artykuły analityczne mogą dostarczać aktualnych ustaleń tylko po sprawdzeniu konkretnych faktów i ich pierwotnego pochodzenia. Zasady cytowania i katalog: `docs/doctrine.md`.

## Kompletność i brak odczytu

Wynik pozostaje pusty, gdy wymagane źródło jest niedostępne, częściowe, nie obejmuje okna publikacji lub jego pobranie ma ponad osiem godzin; gdy definicja źródła zmieniła się od pobrania; albo gdy pozostały nieprzejrzane aktualne wersje materiałów. Stara publikacja również może zawierać nową aktualizację.

Nierozstrzygnięta data potencjalnego incydentu, błędne dowody i użycie nieaktualnej wersji materiału również mogą blokować odczyt. Zdarzenia kontekstowe, poza zakresem lub niespełniające kryteriów mają uzasadnienie wykluczenia. Nie przedstawiamy ich jako potwierdzonych punktów. Błąd źródła opcjonalnego jest widoczny, lecz nie blokuje liczby.

Stan braku to `score: null`, `status: incomplete` i lista `blockers`. Suma przejrzanych punktów nie zastępuje RTB. „Pełne okno publikacji” jest kontrolą chronologicznej listy kolektora, nie dowodem pełnego pokrycia wydawcy ani regionu. Skrót RSS nie oznacza przeczytania artykułu. Nowe wydanie offline zachowuje prawdziwe daty pobrania.

## Historia, wersje i porównania

Materiały, oceny i wydania dopisujemy. Aktualizacja publikacji wymaga oceny nowej wersji; korekta incydentu tworzy rewizję. Raportów historycznych nie przepisujemy. SQLite blokuje aktualizacje/usunięcia tabel audytu; pliki mają manifesty hashy. Kopie pozostają potrzebne, ponieważ administrator dysku może zmienić pliki.

Wydanie zachowuje wejścia, wersję i hash metodologii, konfigurację źródeł oraz hash kodu, schematów i instrukcji agentów. Replay nie pyta ponownie modelu i wymaga tego samego kodu. Wydania v0.1 odtwarza się z kodu `cc98b68` w osobnym katalogu; nowy kod celowo nie udaje zgodności z ich hashem. Dawne reguły są w `config/archive/scoring-v0.1.json` i `docs/archive/methodology-v0.1.md`.

Zmiana na v0.2 dodaje kategorię przygotowań, uściśla zakres lotnictwa i cyberataków, dodaje próg przeglądu, dwa wkłady oraz kontekst obszarów strategicznych. Odczyty v0.1 i v0.2 nie są bezpośrednio porównywalne. `delta_points` i `comparison_run_id` pozostają `null` do wdrożenia porównywania zgodnych okresów, źródeł i kompletności. Nie oznaczamy braku porównania jako „stabilnie”.

## Ustalenia robocze i dalsza walidacja

Po komentarzu użytkownika doprecyzowano projekt osobnej warstwy sygnałów wczesnych w `docs/early-warning-design.md`. Może ona kierować do przeglądu anomalie bez potwierdzonego sprawcy; nie została jeszcze wdrożona. Obecne wagi, kryteria i odczyty RTB v0.2 pozostają bez zmian. Reguły tej warstwy wymagają osobnego kontraktu pomiarów, kontroli pokrycia oraz oceny wyprzedzenia na danych dostępnych w chwili prognozy.

Przyjęte teraz: Polska i flanka NATO jako cel; 7 dni dla punktacji; 14–42 dni dla scenariuszy; geografia jako priorytet; ponad 60 jako wezwanie do przeglądu; biblioteka doktryny oddzielona od zdarzeń.

Dalsze dane są potrzebne do kalibracji wag, limitów i progu, pomiaru fałszywych alarmów, zbudowania baz odniesienia dla anomalii oraz oceny pokrycia państw. „Wiarygodność” oznacza obecnie status dowodowy, bez pozornie precyzyjnego procentu. Pierwszy krok to opisane historyczne przypadki wraz z kontrprzykładami i późniejszymi sprostowaniami; dopiero potem porównanie wariantów wag i alarmów. Te luki nie wymagają zgadywania liczb przez użytkownika.
