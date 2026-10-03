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
- `--card-padding`: 32 px, do 900 px szerokości 24 px, do 620 px 16 px.
- `--card-radius`: wspólne zaokrąglenie dużych powierzchni, 8 px.
- `--surface-background`: odziedziczone tło aktualnej powierzchni. Karta
  ustawia je dla zawartości; używają go nieprzezroczyste fragmenty wykresu.

Karty używamy wtedy, gdy jedna grupa potrzebuje wyraźnego oddzielenia.
Nie zagnieżdżamy kart i nie dodajemy ich automatycznie do każdej sekcji.
Odstępy między sekcjami, Grid i Flexbox pozostają w warstwie układu.
Nie nadpisujemy tła, paddingu, promienia ani cienia karty w selektorach
konkretnej strony. Zmiana komponentu lub tokenów obejmuje każdą instancję.

Pierwsze użycie: `web/index.html`, Przegląd — wspólna karta indeksu, historii
i komentarza. Liczniki, oś czasu i mapa pozostają poza nią. Pozostałe widoki
nie otrzymują kart przy okazji tej zmiany. Historyczny prototyp A/B ma własny
szablon i nie jest katalogiem obecnych komponentów produkcyjnego frontendu.
