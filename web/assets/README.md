Podkład: Natural Earth (naturalearthdata.com), public domain, zachowany
z zaakceptowanego prototypu. Katalog stolic rozszerzono 27.09.2026 do 19 państw
regionu. Współrzędne są wyłącznie kotwicą znaczników krajowych, nigdy
współrzędnymi incydentu; nie trafiają do eksportu raportu.

Źródło katalogu: [Natural Earth Populated Places 1:110m, 5.1.2](https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-populated-places/).
Plik źródłowy producenta:
`https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_110m_populated_places_simple.geojson`.
SHA-256: `0dbd25c9ad8bd797ddf164b067f563be5c16be2c002254eb594862377963f9dc`.
Wybór: `adm0cap=1`, państwa wskazane przez `country_code` w `capitals.json`.
Zachowano geometrię źródłową oraz `source_name`; polskie nazwy są etykietami UI.

## Regiony administracyjne — 04.10.2026

`admin1.json`: 16 województw Polski i 27 jednostek pierwszego poziomu Ukrainy.
Źródło: Natural Earth Admin 1, wydanie repozytorium **v5.1.2**, public domain.
https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/

Plik producenta:
https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_10m_admin_1_states_provinces.geojson
SHA-256: `22d0e3ad85eb3e27f17cabf8ba2d50e554fbc27a87796ff891d958185da62fb5`.

Wybór według `iso_3166_2` z prefiksami PL-/UA-, również UA-43 i UA-40.
Geometria źródłowa pozostaje bez zmian. Stare literowe identyfikatory PL
przypisano do obecnych identyfikatorów używanych w `signal-presentation.json`.
Zachowano źródłową nazwę i kod; polskie etykiety Kijowa rozdzielają miasto
od obwodu. `label_coordinates` producenta służą wyłącznie etykiecie obrysu.

To generalizowany podkład administracyjny, nie aktualna mapa kontroli terytorium,
zasięgu alarmów ani granic wojskowych. UI dopasowuje wyłącznie kraj i zapisane
metadane lokalizacji: region_ids lub nazwaną jednostkę w location.label.
Nie geokoduje tytułów, nie uzupełnia raportów i nie wymyśla punktu zdarzenia.
Dokładna geometria lub zweryfikowana kotwica miasta ma pierwszeństwo.
Opis części regionu dostaje przerywany obrys orientacyjny i objaśnienie.
