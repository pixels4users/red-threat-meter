# Metodologia RTB v0.1

Wersja z 22.09.2026. Status: eksperymentalna, bez kalibracji prognostycznej. Wykonywalna definicja znajduje się w `config/scoring-v0.json`; jej hash jest zapisywany w każdym wydaniu.

## Znaczenie i zakres

RTB mierzy nasilenie kwalifikujących się, potwierdzonych sygnałów przypisanych Rosji lub Białorusi. Nie mierzy prawdopodobieństwa ataku, strat ani spadku cen mieszkań. Nie wprowadzono progu alarmu ani reguł sprzedaży aktywów.

Zakres geograficzny v0: Polska, Litwa, Łotwa, Estonia, Czechy, Słowacja, Węgry, Rumunia, Bułgaria, Niemcy, Finlandia i Szwecja. To roboczy zakres obserwacji, szerszy od samego CEE. Zdarzenia na Ukrainie i informacje o nieustalonym sprawcy pozostają widoczne jako kontekst lub obserwacje poza punktacją. Źródła pilotażu skupiają się na Polsce i nie zapewniają pełnego pokrycia wymienionych państw.

Główne okno obejmuje bieżący dzień i sześć poprzednich dni kalendarzowych w Europe/Warsaw, do chwili odcięcia. Nie jest to dokładnie 168 godzin. Czas pobrań i ocen zapisujemy w UTC. Data publikacji nie zastępuje daty zdarzenia. Sygnał wypada z sumy po wyjściu poza okno; v0 nie stosuje dodatkowego wygaszania wykładniczego.

## Punkty

`RTB = min(100, 10 + suma wkładów po limitach kategorii)`, wyłącznie po przejściu kontroli kompletności. Zero kwalifikujących się punktów daje bazę 10, a nie dowód bezpieczeństwa.

| Kategoria | Punkty za zdarzenie | Limit w oknie | Wymagane ustalenia oprócz wystąpienia, czasu, kraju i atrybucji |
|---|---:|---:|---|
| Sabotaż | 10 | 30 | Celowe działanie i infrastruktura krytyczna |
| Eksplozja w zakładzie zbrojeniowym | 8 | 24 | Potwierdzona eksplozja i charakter obiektu |
| Naruszenie przestrzeni NATO | 5 | 25 | Udowodnione naruszenie, nie sam lot obronny |
| Anomalia lotnicza | 4 | 12 | Aktywność wojskowa i odchylenie od udokumentowanej normy |
| Cyberatak | 3 | 12 | Duża skala, cel rządowy lub bankowy |
| Presja graniczna | 3 | 9 | Granica PL–BY i wzrost względem udokumentowanego odniesienia |
| Zakłócenia GPS | 2 | 8 | Utrzymywanie się zakłóceń ponad 24 godziny |

Jedno zdarzenie ma stabilny `event_key` i najwyżej jedną aktualną rewizję. Wiele publikacji może wskazywać to samo zdarzenie; jedna publikacja może zawierać kilka zdarzeń. Łączenie wymaga przeglądu, nie samej zbieżności słów. Identyczny materiał pobrany ponownie nie tworzy nowego kandydata. Różne adresy opisujące ten sam fakt muszą być powiązane przez analityka.

Zdarzenia oznaczone wspólnym `campaign_id` liczą się raz w danej kategorii. Limity kategorii ograniczają koncentrację medialną, ale nie rozwiązują błędów kwalifikacji. Surową sumę i rzeczywiste wkłady zachowujemy dla audytu. Wagi, baza i limity są hipotezami roboczymi.

## Dowody

Rozdzielamy wystąpienie, przypisanie sprawcy, czas, lokalizację i kryteria kategorii. Pożar sam w sobie nie oznacza sabotażu; ćwiczenia ani start polskich samolotów nie dowodzą rosyjskiego naruszenia granicy.

| Status | Znaczenie |
|---|---|
| `unverified` | Brak wystarczającego potwierdzenia |
| `confirmed_primary` | Potwierdzenie odpowiedniego twierdzenia w źródle pierwotnym |
| `corroborated` | Potwierdzenia z co najmniej dwóch źródeł o niezależnym pochodzeniu |
| `disputed` | Występują dowody sprzeczne |
| `refuted` | Ocena uznaje twierdzenie za obalone, z zapisanym uzasadnieniem |

Punktacja przyjmuje pierwszoplanowe potwierdzenie lub niezależną weryfikację, zarówno wystąpienia, jak i atrybucji. Status komunikatu organu nie dowodzi automatycznie wszystkich zawartych w nim zarzutów. Ocena pochodzenia pozostaje zadaniem analityka. Dwa portale cytujące tę samą agencję otrzymują ten sam `origin_id`.

Walidator sprawdza obecność cytatu w zapisanej wersji materiału, identyfikatory, rodzaje dowodów, źródła oraz spójność deklarowanych statusów. Nie potrafi dowieść, że cytat semantycznie uzasadnia wniosek ani że deklarowana niezależność jest prawdziwa. To powód utrzymania nadzorowanego przeglądu. Brak potwierdzenia nie oznacza dezinformacji.

Geometria GeoJSON używa WGS84 i kolejności `[długość, szerokość]`. Punkt wymaga dowodu lokalizacji i oznaczenia dokładności. Bez ustaleń pozostaje `null`; v0 nie ma automatycznego geokodera. Nazwa regionu nie staje się punktem w jego środku.

## Kiedy wynik pozostaje pusty

- Wymagane źródło jest niedostępne, pobrane częściowo, nie obejmuje okna publikacji albo ostatnie pobranie ma ponad 8 godzin.
- Zmieniła się konfiguracja wymaganego źródła, a nie wykonano nowego pobrania.
- Dowolna aktualna wersja pobranego materiału nie ma oceny. Dotyczy to także starych publikacji, które mogą zawierać nowe aktualizacje.
- Potencjalny incydent nie ma ustalonej daty, używa błędnych dowodów albo kwalifikująca się ocena wskazuje starszą wersję źródła.

Wynik ma wtedy `score: null`, `status: incomplete` i listę przyczyn. Diagnostyczna suma ocenionych punktów nie zastępuje głównego RTB. Potwierdzone zdarzenia poza zakresem i niespełniające kryteriów są wykluczane z uzasadnieniem; nie traktujemy ich jako brakujących potwierdzonych punktów. Źródło opcjonalne może być niedostępne bez blokowania liczby, lecz błąd pozostaje widoczny.

„Pełne okno publikacji” oznacza, że kolektor odczytał listę aż do publikacji starszych niż początek okna. To kontrola techniczna podłączonej listy przy założeniu chronologicznego układu. Nie dowodzi kompletności wszystkich wiadomości wydawcy ani wszystkich incydentów. RSS może zawierać tylko skróty; ich zakres jest jawnie zapisany.

## Historia i porównania

Materiały, obserwacje wersji, oceny i odczyty są dopisywane. Zmiana treści źródła wymaga nowej oceny. Korekta zdarzenia tworzy kolejną rewizję; zapisane raporty pozostają niezmienione. SQLite ma blokady aktualizacji/usuwania tabel audytowych, a wydania mają manifesty hashy. Nie jest to ochrona przed administratorem dysku — potrzebne są kopie.

Każde wydanie zawiera zamrożone wejścia, wersję metodologii, hash konfiguracji źródeł i kodu. Replay nie pyta ponownie modelu. Trend i delta są obecnie `null`: nie ma jeszcze porównywania równoważnych okresów ani wiarygodnej historii. Kolejny etap musi uwzględnić zgodność metodologii, źródeł, kompletności i momentu odcięcia. Nie wolno sklejać różnych konfiguracji w jeden pozornie ciągły trend.

Przed użyciem alarmów potrzebny jest pilotaż na ręcznie opisanych przypadkach, obejmujący błędy i późniejsze sprostowania. Warstwa rynku nieruchomości i scenariusze majątkowe wymagają osobnych danych i oceny jakości.
