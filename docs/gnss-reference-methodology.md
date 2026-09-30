# GNSS — opisowe porównanie wspólnego obszaru

Stan 23.09.2026; implementacja `src/osint_dashboard/early_warning/comparison.py`, wersja `gnss-comparison-1`. Wynik jest częścią każdego nowego wydania sygnałów wczesnych. Automatycznie wylicza zmianę miary, ale nie nadaje priorytetu alarmowego, nie prognozuje ataku i nie zmienia RTB.

## Co mierzymy

Od 30.09.2026 [import do głównego przeglądu](gnss-review-integration.md) pozwala
pokazać zaakceptowany pomiar w raporcie RTB i uwzględnić go w pokryciu danych.
Sam wynik porównania nadal nie nalicza punktów, nie potwierdza atrybucji i nie
uruchamia korelacji taktycznej.

Miara to **udział komórek, w których wartość według wzoru GPSJAM osiąga co najmniej 10%**. Mianownik stanowi wspólny zestaw komórek H3, a nie liczba samolotów, powierzchnia państwa ani wszystkie komórki widoczne danego dnia. Wzór źródła i sposób interpretacji dokładności nawigacji opisuje [instrukcja pilotażu](early-warning-runbook.md), na podstawie [FAQ GPSJAM](https://gpsjam.org/faq).

Porównujemy ostatnią zakończoną dobę UTC z wcześniejszą dostępną historią w oknie konfiguracji (obecnie 30 dni). Oczekiwany dzień musi być dostępny, znany przed granicą czasu raportu i pozbawiony flagi `suspect`. Starszego pomiaru nie przedstawiamy jako bieżącego.

## Dobór odniesienia

1. Cofamy się od dnia badanego przez dostępne dni. Pierwsza zmiana konfiguracji, dostawcy lub grup pochodzenia zamyka odniesienie. Sekwencja A → B → A nie łączy obu epok A.
2. Wyłączamy dzień badany oraz wcześniejsze dni z flagą jakości. Raport zachowuje listę wyłączeń i braków kalendarzowych. W luce nie zakładamy zerowej aktywności ani nie potwierdzamy stałości dostawców.
3. Dla każdego minimum próby `good+bad` równego 1, 5, 10 i 20 wybieramy przecięcie komórek obecnych i spełniających minimum **we wszystkich** dniach odniesienia i w dniu badanym.
4. Liczymy miarę dla każdego dnia na tej samej siatce. Warunek wysokiej wartości sprawdzamy na liczbach całkowitych: `10 * (bad - 1) >= good + bad`, przed zaokrągleniem prezentacji.
5. Z wcześniejszych dni wyliczamy medianę, kwartyle Q1/Q3, minimum i maksimum. Kwartyle używają interpolacji liniowej `statistics.quantiles(method="inclusive")`; dla jednej doby wszystkie kwartyle są równe jej wartości. To opis próby, nie przedział ufności. [Dokumentacja Python](https://docs.python.org/3/library/statistics.html#statistics.quantiles).
6. Różnica to wynik bieżący minus mediana, w **punktach procentowych**. Nie dzielimy przez medianę, więc zerowa mediana nie powoduje nieskończonej zmiany. Zachowujemy też liczbę wcześniejszych dni z wynikiem niższym, równym i wyższym.

Każdy wariant zachowuje dokładne identyfikatory komórek i wersje obserwacji. `comparison_id` jest hashem specyfikacji, wyboru wejść i wyników. Wspólna siatka jest wybrana dla danego porównania: może zmienić się w kolejnym raporcie. Nie jest z góry zamrożonym, niezależnym zbiorem walidacyjnym. Brak wspólnych komórek daje `null`, nie 0%.

## Pierwszy wynik rzeczywisty

Pomiar 22.09.2026; odniesienie 27.08–21.09, **26 dób** z zestawu `merged` (ADS-B Exchange + airplanes.live). Pierwsze trzy doby archiwum nie weszły do odniesienia ze względu na wcześniejszy zestaw dostawców. W samym okresie porównania nie było brakujących dni ani flag jakości.

| Minimum próby | Wspólne komórki | Udział 22.09 | Mediana odniesienia | Różnica w pkt proc. |
|---:|---:|---:|---:|---:|
| 1 | 566 | 17,67% | 22,26% | −4,59 |
| 5 | 491 | 13,85% | 18,33% | −4,48 |
| 10 | 452 | 12,17% | 15,49% | −3,32 |
| 20 | 404 | 9,41% | 12,01% | −2,60 |

Wyniki wyliczono z lokalnie zachowanych pomiarów GPSJAM, nie z oceny barwy mapy. Przy minimum 5 wynik dotyczy 68 z 491 wspólnych komórek. Odmienna wartość 103/550 = 18,73% w opisie pojedynczego dnia używa wszystkich kwalifikujących się komórek **tego dnia**, zatem ma inny mianownik i nie jest bezpośrednio porównywalną zmianą czasową.

Wniosek ogranicza się do niższego udziału komórek o takiej wartości niż mediana zebranej serii. Różna wielkość różnicy między wariantami pokazuje zależność wyniku od minimalnej próby i obszaru. Nie oznacza spadku ryzyka wojny, identyfikacji sprawcy ani dowodu braku zakłóceń poza wspólną siatką.

## Co pozostaje do walidacji

Stałe komórki nie gwarantują stałej liczby i składu samolotów, wysokości, tras ani odbiorników. Archiwum pobrano retrospektywnie 23.09; nie dowodzi dostępności tej wiedzy w sierpniu. Nie ustalono, które dni są „normalne”, jak działają sezonowość i ćwiczenia ani czy odchylenia zapowiadają zdefiniowane zdarzenie.

Następny eksperyment wymaga osobnego, wersjonowanego rejestru wyników: definicji zdarzenia, daty jego wystąpienia, momentu uzyskania dowodu, źródeł, późniejszych sprostowań i stanu nierozstrzygniętego. Dla hipotezy należy przed wynikiem zapisać horyzont oraz warunek zamknięcia. Kalibrację odseparować czasowo od późniejszej walidacji, zachowując stan wiedzy dostępny w danym momencie. Brak oficjalnego komunikatu nie wystarczy jako etykieta negatywna.

Dopiero wtedy można ocenić przeoczenia, fałszywe alarmy, wyprzedzenie i skutki zmiany progów. Bieżący kod ma `detector_enabled=false` i `normality_verified=false`; nie zamienia opisanej mediany w próg alarmu.
