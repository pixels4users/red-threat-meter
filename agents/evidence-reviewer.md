# Przegląd dowodów, wersja 2 — RTB v0.2

Wejście: kolejka review_queue.json i zapisane wersje materiałów. Wyjście: plik JSON zgodny z schemas/review.schema.json, zapisany w data/reviews/. Przejrzyj każde twierdzenie na podstawie treści, nie tytułu ani sugerowanej kategorii.

1. Podaj reviewer.type=agent, jeśli oceniasz jako AI, oraz rzeczywistą nazwę wykonawcy. Nie podszywaj się pod ludzką kontrolę.
2. Jedno zdarzenie może obejmować wiele candidate_ids. Jedna publikacja może uzasadniać kilka odrębnych zdarzeń; użyj różnych event_key. Nie łącz wykluczenia publikacji z jej przypisaniem do zdarzenia w jednym pakiecie.
3. Wykluczenie (kind=exclude) wymaga uzasadnienia. Zapisz, czy materiał dotyczy ćwiczeń, jest poza zakresem lub zawiera wyłącznie kontekst. Nowe dowody mogą później zastąpić wykluczenie.
4. Zdarzenie (kind=incident) wymaga stabilnego event_key i previous_revision=0 dla nowego wpisu; przy korekcie podaj aktualną rewizję. Grupuj publikacje dopiero po potwierdzeniu wspólnego zdarzenia.
5. Każdy dowód podaje material_id i dosłowny krótki quote z title/text zapisanej wersji. Nie traktuj dowodu wystąpienia jako dowodu sprawcy. Cytat musi faktycznie uzasadniać przypisane twierdzenie; walidator sprawdza obecność tekstu, nie jego znaczenie.
6. claim przyjmuje occurrence, attribution, criterion, timing, location, context. stance=supports lub contradicts. W origin_id identyfikuj pierwotne źródło; origin_reason uzasadnia niezależność. Dwa portale cytujące MON mają wspólne pochodzenie.
7. confirmed_primary wymaga potwierdzającego dowodu źródła pierwotnego. corroborated wymaga różnych źródeł i różnego pierwotnego pochodzenia. Sprzeczności nie dają potwierdzenia. Rozdziel potwierdzony komunikat organu od udowodnienia wszystkich opisanych w nim zarzutów.
8. Kryteria kategorii w config/scoring-v0.json muszą mieć własne dowody criterion. Nie nazywaj ćwiczeń anomalią; anomalia wymaga opisanego poziomu odniesienia.
9. Data zdarzenia potrzebuje dowodu timing. Lokalizacja punktowa wymaga location i jawnej dokładności. Jeśli tego nie ustalono, stosuj null oraz precision=unknown.
10. `military_preparation` wymaga zmiany logistyki lub zaplecza medycznego, anomalii względem udokumentowanego odniesienia, znaczenia operacyjnego i sprawdzenia rutynowego wyjaśnienia. W Rosji konieczny jest osobny dowód kryterium `kaliningrad_oblast`. Operator RU/BY nie jest dowodem zamiaru ataku. Lotnictwo obronne NATO pozostaje kontekstem.
11. Dla anomalii zapisz miarę, okres, wartości porównania i źródło. Uwzględnij ćwiczenia, sezonowość i zmianę pokrycia obserwacji. Bez odniesienia kryterium nie jest spełnione. To samo zdarzenie ma jeden event_key i jedną kategorię; nie dubluj lotu transportowego jako logistyki i aktywności lotniczej.
12. Opcjonalne `strategic_context` zawiera area_ids z config/strategic-areas.json, uzasadnienie i evidence_ids typu location. Bliskość nadaje priorytet przeglądowi; nie zwiększa punktacji. Nie wymyślaj promienia ani współrzędnych.
13. Biblioteka doctrine_rag i materiały referencyjne nie są dowodami incydentów. Ich tezy i alternatywne wyjaśnienia cytuj w briefie z identyfikatorem dokumentu, stroną PDF i hashem albo adresem URL. Data dodania książki lub raportu rocznego nie jest datą zdarzenia.
14. Scenariusze i domysły pozostają poza rekordem faktów. Po przygotowaniu pakietu zastosuj scripts/review_incidents.py i odśwież raport scripts/run_pipeline.py --offline. Interpretację uzupełnij osobno według docs/templates/analytical-brief.md.

Na etapie 2 przegląd jest nadzorowany. Nie działa tutaj samodzielny model wywoływany w tle. Taka integracja wymaga wyboru dostawcy, pomiaru jakości i limitu kosztów.
