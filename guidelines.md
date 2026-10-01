# RTB — zasady UI

Powiązane: `design.md`, `theme.css`, `docs/dashboard-presentation.md`.
Wersja 0.2, 27.09.2026. Zasady kolorów wynikają z decyzji użytkownika;
zaakceptowany układ: **B — Chronologia**.

## Hierarchia i układ

1. RTB pozostaje największą liczbą, razem z trendem i mniejszą pewnością danych.
2. Trzy zdania komentarza są obok wyniku; na telefonie bezpośrednio pod nim.
3. Mapa oraz oś czasu tworzą asymetryczny układ; nie kolekcję identycznych kart.
4. Cztery pozycje menu zachowują nazwy i kolejność. Mobile używa hamburgera.
5. Każdy odstęp ma rolę z `theme.css`. Stosuj `gap` w szeregach i grupach.
6. Przy 320 px treść się zawija, bez poziomego przewijania i uciętych kontrolek.
7. RTB pozostaje przy przewijaniu. W B oś czasu poprzedza mapę, również na telefonie.
8. Rozwijany zakres obserwacji umieszczamy po treści widoku, przed stopką;
   w Przeglądzie po osi czasu i mapie. Skrót pewności pozostaje przy RTB.

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
  wybranego punktu czy „braku tłumaczenia”. Opisz taki stan neutralnie.

## Tekst i dane

- Polski, krótkie zdania, konkretne znaczenie dla mieszkańca Polski.
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
- Wykres i delta łączą tylko wyniki tej samej metodologii i konfiguracji.

## Interakcje i dostępność

- „Postaw kawę” jest osobnym linkiem wsparcia w menu i stopce, poza czterema
  widokami danych. Otwiera nową kartę, z etykietą dostępną i `noopener noreferrer`.
- Przycisk ma czasownik lub jednoznaczną nazwę; ikona ma dostępną etykietę.
- Zachowuj widoczny fokus. Dialogi zamykają się przez Esc i przycisk, po
  zamknięciu zwracają fokus; Tab nie wychodzi za otwarte okno.
- Cel dotykowy minimum 44 × 44 px. Nie pomniejszaj tekstu pól na telefonie.
- Docelowo kontrast tekstu minimum 4,5:1, dużego tekstu oraz istotnych
  wskaźników i kontrolek 3:1. Sprawdzaj oba motywy, także na stanach hover.
- Mapa: plus/minus/reset/duży widok, przesuwanie, pinch; zwykłe przewijanie
  przewija stronę. Punkt otwiera szczegóły, nie uruchamia innej akcji.
- Oś czasu i filtry zachowują wybór po powrocie ze szczegółów.
- W ruchu szanuj `prefers-reduced-motion`; brak migania i pulsujących alarmów.

## Procedura zmiany

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
