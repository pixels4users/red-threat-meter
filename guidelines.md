# RTB — zasady UI

Powiązane: `design.md`, `theme.css`, `docs/dashboard-presentation.md`.
Wersja 0.3, 03.10.2026. Zasady kolorów wynikają z decyzji użytkownika;
zaakceptowany układ: **B — Chronologia**.

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

- „Postaw kawę” jest osobnym linkiem wsparcia w menu desktop i stopce, poza czterema
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

## Liczniki i kontekst regionalny

- Proza rekomendacji nie ma podkreślenia ani pozornej klikalności. Linkiem
  jest dopiero oddzielny odnośnik do źródła lub szczegółów.
- Liczniki pokazują zapisane sygnały, a nie liczbę ataków. Neutralne strzałki
  opisują zmianę liczby, bez automatycznych ocen „rutynowo” lub „anomalia”.
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
