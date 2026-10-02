# UX: znaczenie wydarzeń dla użytkownika

Status: propozycja do iteracji, 02.10.2026. Żaden kierunek nie został jeszcze zaakceptowany ani wdrożony na stronie publicznej.

## Cel i hipoteza

Pierwszy ekran powinien odpowiadać na trzy pytania: co się dzieje, czy dotyczy mnie i czy powinienem coś zrobić. RTA pozostaje największą liczbą i występuje wyłącznie w Przeglądzie. Wydarzenia, ich zasięg i oficjalne instrukcje pozwalają zinterpretować tę liczbę.

Pierwszy eksperyment dotyczy kolejności informacji w Przeglądzie. Zachowujemy paletę, czteropunktową skalę odstępów, nawigację i dostęp do mapy, dziennika oraz raportów. Nie uruchamiamy powiadomień ani nowych analiz.

## Dwa kierunki

### Dla Ciebie — rekomendowany punkt wyjścia

1. Indeks dla Polski i krótki komentarz: najważniejsze sprawdzone wydarzenia.
2. Wybór województwa przy sekcji regionalnej. Polska jako domyślna opcja; zapamiętanie świadomego wyboru tylko w tej przeglądarce, bez konta i geolokalizacji.
3. Wydarzenia dotyczące wybranego obszaru oraz osobno komunikaty ogólnopolskie. Wyróżnione oficjalne zalecenia z miejscem, terminem, źródłem i datą sprawdzenia.
4. Zmiany w tematach, następnie dotychczasowe oś czasu i mapa. Szczegółowy zakres obserwacji pozostaje niżej.

Dobry dla osoby odwiedzającej stronę po raz pierwszy. Region wpływa na dobór treści; indeks pozostaje jawnie opisany jako wynik dla Polski. Nie wprowadzamy na tym etapie regionalnego „poziomu bezpieczeństwa”.

### Raport zmian

Po wyniku i komentarzu główny obszar zajmuje przegląd tematów: co nowego i jak zmieniła się aktywność względem poprzedniego porównywalnego okresu. Wybrany region i zalecenia są w bocznej kolumnie; na telefonie trafiają przed tematy. Kliknięcie tematu pokazuje wydarzenia i podstawę porównania.

Dobry dla regularnego czytelnika. Wymaga bardziej kompletnej historii oraz większej dyscypliny rozróżnienia nowej publikacji od nowego zdarzenia. Aktualne dane pozwalają przedstawić nowe komunikaty, ale nie zapewniają jeszcze porównywalnego trendu w każdej dziedzinie.

## Ustalenia z obecnych danych

Sprawdzono lokalny dashboard oraz zamrożony eksport `data/analysis/commentary-revisions/2026-10-02-verified-events-v2/publication-daily.json` (stan na 02.10.2026, 09:25 czasu Warszawy):

- RTA 2,7/100, pewność 25%, `trend.direction=unavailable`, `official_warnings=[]`.
- Eksport zawiera 83 rekordy: 27 z dokładnością krajową, 28 regionalną, 9 miejską i 19 bez ustalonej lokalizacji. Liczby te nie opisują liczby nowych incydentów w dobie.
- Zapowiedzi ćwiczeń w powiecie pyrzyckim i neutralizacji niewybuchów w Świnoujściu mają w eksporcie lokalizację „Polska”. Przed filtrowaniem regionalnym należy dopisać zweryfikowane obszary obowiązywania; nie wyciągać ich automatycznie z tekstu tytułu.
- Ostrzeżenie CERT o fałszywych wiadomościach podatkowych ma kategorię punktacji `context`. Potrzebuje niezależnego tagu tematycznego „Cyberbezpieczeństwo”, bez zmiany oceny lub punktów.
- `rtb.regions` zawiera 16 zerowych wyników. To nie jest dowód równomiernego pokrycia ani bezpieczeństwa każdego województwa.
- `confidence.domains[].percent` to pokrycie źródeł. Nie wolno używać tych procentów jako nasilenia zagrożenia lub jego wzrostu.
- Bieżący trend wymaga zgodnych identyfikatorów metodologii, konfiguracji, źródeł, kodu oraz porównania pewności. Nie usuwamy tych kontroli na potrzeby UI.

Makiety korzystają z treści powyższego raportu. Przypisanie lokalnych przykładów do zachodniopomorskiego jest ręczną demonstracją projektową, a nie zapisem nowej oceny w bazie. Zmiana regionu nie przelicza indeksu. Brak podstaw porównania pozostaje widoczny; makiety nie wymyślają trendu ani zapewnienia o bezpieczeństwie.

## Warunki dla treści

### Czy dotyczy mnie

Rozdzielamy miejsce zdarzenia od obszaru wpływu lub obowiązywania instrukcji. Proponowane przyszłe pola prezentacyjne: `topics`, `affected_areas` (stabilny identyfikator, zakres lokalny/krajowy/nieustalony), `relevance_summary`, odwołania do sprawdzonych ustaleń i przeglądu. Pola wymagają projektu kontraktu i nowej wersji eksportu, nie domysłów przeglądarki.

Komunikat ogólnopolski jest widoczny po wyborze województwa, lecz oznaczony jako ogólnopolski. Nieustalonego zasięgu nie przypisujemy do każdego regionu. Flaga w stolicy nie tworzy lokalnego zdarzenia w Warszawie. Bałtyk jest obszarem zainteresowania, cyberbezpieczeństwo tematem; nie mieszamy ich na jednej skali.

### Czy powinienem coś zrobić

Oddzielna sekcja instrukcji służb: wydawca, bezpośredni URL, zakres, treść, czas obowiązywania, status i data sprawdzenia. Instrukcję pokazujemy wiernie i tylko dla właściwego obszaru; jej ważność wymaga weryfikacji. Zapowiedź na przyszły tydzień nie jest aktywnym zakazem dzisiaj.

Istotne obowiązujące ostrzeżenie trafia ponad zwykły układ podsumowania, także przy niskim RTA. Brak opublikowanej instrukcji, niepełny odczyt i odwołanie ostrzeżenia to różne stany. LLM nie tworzy samodzielnie zaleceń ewakuacji, decyzji finansowych ani zapewnień o bezpieczeństwie. W pierwszym kroku link do sprawdzonego komunikatu jest lepszy niż wygenerowana porada.

### Co się zmieniło

Rozdzielamy trzy komunikaty:

- **Nowy materiał / aktualizacja:** zmiana w raporcie albo publikacja w podanym okresie, z datą; nie oznacza automatycznie wzrostu aktywności.
- **Więcej / mniej zdarzeń:** tylko odrębne ocenione zdarzenia, porównywalne okna, stabilne źródła i znany zasięg obserwacji. Przedruki i aktualizacje nie zwiększają licznika.
- **Zmiana zagrożenia:** odrębna ocena analityczna, nie automatyczna etykieta z liczby publikacji.

Bez danych wyświetlamy „Brak podstaw do porównania”, a przy częściowym odczycie wyjaśniamy brak zakresu. Nie zastępujemy tego etykietą „normalnie”. Brak różnicy w porównywalnych pomiarach nie jest skalibrowaną normą. GNSS nadal jest kontekstem, bez punktacji i automatycznej atrybucji.

## Etapy po wyborze kierunku

1. **Iteracja ekranu:** dopracować wybrany układ na odseparowanych danych. Potwierdzić zachowanie przy wyborze regionu, ostrzeżeniu, jego odwołaniu i braku danych. Zapisać zaakceptowane zasady w `design.md`, `guidelines.md` i ewentualnie `theme.css`.
2. **Kontrakt znaczenia i zasięgu:** osobne tagi tematyczne, zweryfikowane obszary, podstawa porównania, źródła i ważność instrukcji. Rozszerzyć schemat i eksport wraz z testami. Bez zmiany punktacji RTA.
3. **Integracja lokalna:** wdrożyć zaakceptowane sekcje w `web/app.js`, `web/data.js`, `web/styles.css` i szablonie ekranu, zgodnie z faktycznymi nazwami plików sprawdzonymi przed implementacją. Pozostałe widoki otrzymają spójny filtr regionu dopiero po decyzji o jego zakresie; archiwalny raport zachowuje swój wynik i datę.
4. **Odbiór i publikacja:** sprawdzenie desktop/mobile, dostępności, prawdziwego eksportu, pustych stanów i regresji istniejącej nawigacji; akceptacja użytkownika; dopiero potem wdrożenie.
5. **Raporty regionalne, później powiadomienia:** najpierw lokalny widok raportu dobowego dla wybranego regionu. Wysyłka wymaga osobnej decyzji o kanale, subskrypcji i zasadach deduplikacji. Pilne alerty wymagają częstszego monitorowania oraz potwierdzonej aktualności źródeł; analiza raz dziennie nie zapewnia ostrzegania w czasie rzeczywistym.

## Kryteria pierwszej iteracji

- Czytelnik potrafi wskazać najważniejsze wydarzenie, jego znaczenie dla wybranego regionu i ewentualne obowiązujące zalecenie bez otwierania metodologii.
- Potrafi odróżnić ogólnopolskie ostrzeżenie cyber od lokalnego ograniczenia, planowane działanie od trwającego zdarzenia i brak danych od braku zagrożenia.
- Zmiana regionu nie zmienia po cichu znaczenia indeksu; data raportu pozostaje widoczna.
- Każde „więcej / mniej” ma wskazany okres, porównywalną podstawę i zdarzenia, z których wynika.
- Na szerokości 320 px da się wybrać region, otworzyć szczegóły i odczytać zalecenie; nawigacja pozostaje na dole. Klawiatura i fokus działają.
- Komunikaty ogólnopolskie nie znikają po wybraniu województwa. Ostrzeżenie nie znika wskutek niskiego indeksu.

## Stan prac

Gałąź eksperymentalna: `codex/ux-regional-context`, utworzona z `dfe9129`. Dokument i makiety są propozycją. Nie zmieniono kodu produkcyjnego, bazy, harmonogramu, konfiguracji źródeł ani hostingu. Szablony Design Systemu pozostają na wersji zaakceptowanej; aktualizacja nastąpi po wyborze kierunku. Prototyp nie jest częścią buildu produkcyjnego.

Makiety: `ui/experiments/rta-ux-directions.html`. Fragment zawiera dwa warianty i przykładowy wybór Polski, Mazowsza oraz zachodniopomorskiego. To skrócony podgląd nowych sekcji Przeglądu; istniejące mapa i oś czasu pozostają w planie poniżej nich i nie zostały przebudowane w makiecie. Widoczna nawigacja jest ilustracją; działają wybór regionu, szczegóły wpisów, porównanie wariantów i linki źródłowe. RSO ma w obecnym eksporcie adres strumienia XML — docelowo należy uzupełnić zweryfikowany adres czytelnego komunikatu, bez zgadywania URL.

Sprawdzenie lokalne: oba warianty, trzy opcje regionu, zachowanie komunikatu ogólnopolskiego po filtrowaniu, stały wynik krajowy, rozwijanie szczegółów klawiaturą, brak poziomego przepełnienia przy szerokości okna 320 i 1024 px, kontrolka wyboru wysokości 44 px i brak błędów JavaScript. Nie uruchamiano pełnej regresji aplikacji, bo kod produkcyjny pozostał niezmieniony.
