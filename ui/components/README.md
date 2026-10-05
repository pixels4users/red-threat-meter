# RTA — wspólne komponenty

Tokeny komponentów są w `theme.css`. Działający frontend importuje arkusze
z tego katalogu w `web/styles.css`; nie kopiuje ich reguł do widoków.
Przykłady poniżej są składnią komponentów, nie danymi analitycznymi.

## Karta — `.r-card`

Neutralna powierzchnia grupująca powiązaną treść. Nie ma własnego układu
kolumn, interakcji, cienia ani koloru zależnego od zagrożenia. Nie jest
przyciskiem. Rodzaj elementu i nazwa sekcji wynikają z jego treści.

```css
@import "../../theme.css";
@import "./card.css";
```

```html
<div class="rtb-app" data-appearance="auto">
  <section class="r-card" aria-labelledby="summary-title">
    <h2 id="summary-title">Podsumowanie</h2>
    <!-- Powiązana treść; układ określa używający karty widok. -->
  </section>
</div>
```

Publiczne tokeny:

- `--color-card`: neutralne tło w jasnym i ciemnym wyglądzie.
- `--color-card-inset`: tło wydzielonego panelu wewnątrz karty; białe
  w jasnym wyglądzie, jaśniejsze grafitowe w ciemnym.
- `--card-padding`: 32 px, do 900 px szerokości 24 px, do 620 px 16 px.
- `--card-inset-padding`: 24 px, do 620 px szerokości 16 px.
- `--card-radius`: wspólne zaokrąglenie dużych powierzchni, 8 px.
- `--surface-background`: odziedziczone tło aktualnej powierzchni. Karta
  ustawia je dla zawartości; używają go nieprzezroczyste fragmenty wykresu.

Karty używamy wtedy, gdy jedna grupa potrzebuje wyraźnego oddzielenia.
Nie dodajemy kart automatycznie do każdej sekcji. Wewnątrz karty można
wydzielić jeden panel komentarza lub kontekstu wariantem `.r-card--inset`.
Nie tworzymy kolejnych poziomów zagnieżdżenia ani kart dla poszczególnych zdań.
Odstępy między sekcjami, Grid i Flexbox pozostają w warstwie układu.
Nie nadpisujemy tła, paddingu, promienia ani cienia karty w selektorach
konkretnej strony. Zmiana komponentu lub tokenów obejmuje każdą instancję.

## Panel wewnętrzny — `.r-card.r-card--inset`

```html
<section class="r-card" aria-label="Podsumowanie">
  <!-- Główna treść; układ kolumn ustala widok. -->
  <div class="r-card r-card--inset">
    <!-- Komentarz lub kontekst do głównej treści. -->
  </div>
</section>
```

Wariant zachowuje promień, kolor tekstu i brak cienia karty. Zmienia tylko
tło oraz odstępy. Ma tę samą neutralną rolę w obu wyglądach; nie komunikuje
zagrożenia ani jakości prognozy. Pusty panel pomijamy.

Pierwsze użycie: `web/index.html`, Przegląd — wspólna karta indeksu, historii
i komentarza. Liczniki, oś czasu i mapa pozostają poza nią. Pozostałe widoki
nie otrzymują kart przy okazji tej zmiany. Historyczny prototyp A/B ma własny
szablon i nie jest katalogiem obecnych komponentów produkcyjnego frontendu.

## Rozwijany sygnał — `createSignalItem`

`signal-item.js` i `signal-item.css` obsługują Oś czasu, listę przy Mapie
i Dziennik. Jedna implementacja przycisku, chevronu i dostępności; wariant
`compact` zmienia gęstość układu, nie zachowanie. Tytuł pozostaje w nagłówku.
Kliknięcie, Enter i Spacja przełączają `aria-expanded`; Escape zamyka
szczegóły i zwraca fokus do nagłówka. Linki do źródeł są poza przyciskiem.
`prepareSignalDetail` przygotowuje wspólny układ treści i metadanych bez ×
i powtórzonego tytułu. Wywołujący wiąże panel przez `aria-controls` oraz
`aria-labelledby`, przenosi go pod wybrany wpis i przechowuje stan wyboru.
Przycisk zamknięcia pozostaje tylko w oddzielnym panelu pełnoekranowej mapy.
Style instancji nie nadpisują chevronu, stanu rozwinięcia ani interakcji.

## Skrót kategorii — `.r-topic-button`

Arkusz `topic-shortcut.css` definiuje siatkę 4/2 kolumny, ikonę, nazwę,
liczbę i dostępną zmianę tygodniową. Strzałka → oznacza przejście do
Dziennika; nie stosujemy `aria-expanded` ani przycisku zamknięcia.
Hover i focus unoszą ikonę, przesuwają strzałkę i zmieniają neutralne tło.
`prefers-reduced-motion` usuwa animację. Zero pozostaje widoczne.
Kolejność i ikony pochodzą ze wspólnego rejestru kategorii.

## Etykieta kategorii — `createCategoryLabel`

Wspólna etykieta z `signal-item.js`: ikona 16 px, odstęp 4 px i nazwa
kategorii, opcjonalnie z liczbą (`2× Lotnictwo`). Ikona pochodzi ze wspólnego
rejestru kategorii, dziedziczy kolor tekstu i jest dekoracyjna (`aria-hidden`).
Nazwa pozostaje widoczna; cała etykieta zawija się jako jeden element.
Oś czasu używa jej przy pojedynczych sygnałach, zestawieniach godzinowych
i dobowych oraz dominujących kategoriach w widoku miesiąca.
