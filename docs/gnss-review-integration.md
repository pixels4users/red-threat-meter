# Pomiary GNSS w głównym cyklu — gnss-review-1

Stan: 30.09.2026. Import `gpsjam_reviewed` w `sources-pilot-8` wykorzystuje
istniejący kolektor GPSJAM. Nie dubluje pobierania ADS-B ani plików mapy.
Odczyt CSV, kontrola pomiaru i kwalifikacja zagrożenia są odrębnymi czynnościami.

## Pobranie i integralność

1. Przed cyklem uruchom `scripts/early_warning.py collect` przez `.venv/bin/python`.
   Domyślnie pobierane są trzy zakończone doby. Jednorazowy `--days 7` uzupełnia
   tygodniową przerwę. Zachowuj istniejące Retry-After i limity; nie ponawiaj
   odczytu tylko po to, aby uzyskać pozornie nowszy czas.
2. `analysis_cycle.py prepare` importuje najnowsze zamrożone wydanie pilotażu.
   Sprawdza tryb live/fixture, hashe wydania i surowych plików, odtwarza pomiary
   z CSV i przelicza porównanie wspólnych komórek. Kopiuje dowody do archiwum RTB.
3. Wymagana jest poprzednia doba UTC, bez flagi suspect, z kwalifikującymi się
   komórkami i kontrolą GPSJAM nie starszą niż 8 godzin. Pusty, zmieniony,
   nieaktualny albo brakujący materiał daje unavailable; nie blokuje RTB.
4. Import nie zmienia daty kontroli źródła. Kolejny raport offline nie odmładza
   pomiaru. Dane historyczne nie dowodzą wcześniejszej wiedzy systemu.

## Przegląd i dowód liczbowy

Materiał ma `text_kind=measurement`. W `source_record` są dokładna obserwacja,
identyfikator jej wersji, dzienna siatka i wynik `gnss-comparison-1`. Tekst
wygenerowany przez parser jest opisem pomocniczym, nie cytatem z publikacji.
Dowód używa `measurement` zamiast `quote`, np.:

```json
{"observation_id":"ewo_…","field":"high_cells","value":111}
```

To ilustracja kształtu dowodu, nie wpis do bazy. Dozwolone pola obejmują dobę,
liczniki komórek, udział dobowy, bbox oraz miary wspólnego obszaru. Walidacja
porównuje wartości z zamrożonym pomiarem. `origin_id` zachowuje wspólne
pochodzenie GPSJAM i dostawców ADS-B; nie są to niezależne potwierdzenia.

Po przeglądzie i drugim audycie zapisujemy jeden wpis `context` dla doby UTC,
`country=null`, `geometry=null`, sprawca `unknown`, bez kryteriów punktacji,
oceny taktycznej i ostrzeżenia. Powtórzenie odczytu nie tworzy nowego zdarzenia.
Zmiana danych dla tej samej doby wymaga nowej rewizji. Opis publiczny jest
po polsku; pełne siatki i pliki CSV pozostają w archiwum roboczym.

## Wpływ na wynik i pewność

Zaakceptowany, aktualny pomiar dostarcza obserwacji domeny GNSS w confidence.
Samo pobranie lub decyzja defer/exclude nie daje tego udziału. Limit źródła 1
jest mnożony przez 0,5 za częściowy zasięg. Daje to 50% obserwacji jednej z ośmiu
domen, przed wspólnym współczynnikiem przeglądu i historii. Nie jest to
prawdopodobieństwo poprawności ani skalibrowana czułość pomiarów.

Sam pomiar daje **0 punktów RTB**. GPSJAM wykorzystuje dokładność nawigacji
raportowaną przez samoloty, nie mierzy bezpośrednio nadajnika zakłócającego.
Agregat dobowy nie dowodzi ciągłości ponad 24 godziny, rosyjskiej/białoruskiej
atrybucji ani zbieżności w oknie 30 minut. Bonus korelacji pozostaje wyłączony.
[Porównanie wspólnych komórek](gnss-reference-methodology.md) pozostaje opisowe;
mediana historii nie jest „normalnym poziomem” ani progiem alarmowym.

Wcześniejszą konfigurację pewności zachowuje
`config/archive/scoring-v0.4-source-coverage.json`. Nowy hash konfiguracji
rozdziela serie; wzrost pokrycia nie jest przedstawiany jako zmiana zagrożenia.
