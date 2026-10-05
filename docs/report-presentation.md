# Raport RTA — strona i PDF

Status 05.10.2026: zaakceptowany redesign obejmuje stronę raportu, wersję
do druku oraz TXT/JSON/GeoJSON. Gotowe PDF-y odłożono decyzją użytkownika.
Poniższe wymagania PDF opisują przyszły etap, nie funkcję bieżącego wydania.
Wersja specyfikacji: 1.

Wspólna specyfikacja dla gałęzi redesignu i późniejszej integracji PDF.
Dotyczy prezentacji zatwierdzonego wydania. Nie zmienia metodologii rtb-v0.4,
ocen zdarzeń ani harmonogramu analizy. Kontrakt wejściowy:
[dashboard-v1](dashboard-data-contract.md).

## 1. Kolejność treści

### Tytuł i data

„Red Threat Alert — raport dzienny” oraz data wydania. Dla `weekly` używamy
„raport tygodniowy”. Niżej: „Stan na godz. … czasu polskiego”, z rzeczywistego
`as_of`, w strefie Europe/Warsaw. Nie podstawiamy godziny harmonogramu ani
bieżącego czasu urządzenia. Tytuł jest stałym szablonem, bez dodatkowego LLM.

Raport przedstawia stan wiedzy w chwili analizy, a nie wyłącznie zdarzenia
z tego dnia. Obejmuje okno zapisane w wydaniu; indeks nie jest średnią dobową.
Okno można podać w informacjach o wydaniu.

Korekta ma oznaczenie „Korekta” i odnośnik do poprzedniej wersji.
Strona ma własny, trwały adres przypisany do `report_id`. Gotowy plik
konkretnego wydania udostępnia opcję „PDF (.pdf)” w selektorze formatów.
Wszystkie formaty używają wspólnego przycisku „Pobierz”.

### Indeks RTA

Duża wartość X/100, opis poziomu według wspólnej skali dashboardu i mniejsza
„Pewność danych: Y%”. Formatowanie liczb oraz kolory pochodzą ze wspólnych
komponentów Design Systemu. Nie tworzymy osobnych progów dla raportu i PDF.

Zmianę pokazujemy tylko dla porównywalnego odczytu, z datą odniesienia.
Brak porównania oznacza pominięcie delty, bez komunikatu zastępczego.
Spadek liczby nie jest automatycznie opisem deeskalacji.

Stałe objaśnienie: „Indeks opisuje nasilenie sygnałów zagrożenia, nie
prawdopodobieństwo wojny”. Zero zachowuje znaczenie braku naliczonych sygnałów,
nie zapewnienia bezpieczeństwa. Historyczne `score=null` pozostaje brakiem
wyliczenia; brak pewności procentowej nie zamienia się w 0%.

### Najważniejsze ustalenia

Zatwierdzone podsumowanie: 1–3 krótkie zdania. Jeżeli wydanie zawiera podział
komentarza, używamy podpisów „Sytuacja”, „Wpływ na Polskę”, „Zalecenia”.
Wyświetlamy tylko istniejące części, bez powtarzania całego tekstu obok nich.
Starszy komentarz bez podziału pozostaje pojedynczym akapitem. Brak komentarza
oznacza pominięcie tej sekcji, bez dopisywania oceny bezpieczeństwa.

Istotne oficjalne ostrzeżenia pokazujemy przy podsumowaniu także wtedy, gdy
komentarza nie ma. Zachowujemy instytucję, obszar, instrukcję, status i znane
terminy. Ostrzeżenie o nieustalonym statusie nie staje się aktywnym ani
odwołanym. Informacje odnoszą się do chwili wydania raportu; archiwalnego
ostrzeżenia nie podpisujemy jako obowiązującego dzisiaj. Niski indeks nie
odwołuje zaleceń służb. Brak ostrzeżeń nie tworzy zapewnienia „brak zagrożeń”.

### Wydarzenia i kontekst

Lista zdarzeń z danego publicznego wydania: konkretny tytuł, miejsce i data
zdarzenia, jeżeli znane, krótkie streszczenie, temat, zrozumiały status oraz
odnośniki do źródeł. Data publikacji pozostaje odrębna od daty zdarzenia.
Braków miejsca i czasu nie uzupełniamy domysłami.

Grupowanie wykorzystuje wspólną taksonomię dashboardu. Pokazujemy wyłącznie
grupy zawierające wpisy. Wpis należący do kilku tematów występuje raz, z
odpowiednimi etykietami. Statusy zachowują różnicę między potwierdzeniem
pierwotnym, niezależnym potwierdzeniem i pojedynczym doniesieniem.
Jeżeli lista jest pusta: „Brak wydarzeń ujętych w tym wydaniu”.

Nie dokładamy wpisów z późniejszych raportów do czytanego wydania.
Korekta pozostaje osobnym raportem; stare wydanie zachowuje oryginalną treść
i może wskazywać dostępność nowszej wersji.

### Źródła i zakres obserwacji

Po wydarzeniach: źródła wykorzystane w raporcie, zakres obserwacji i istotne
braki opisane prostym językiem. Odróżniamy odnośniki do materiałów przy
wydarzeniach od listy monitorowanych wydawców i ich dostępności.
Szczegóły na stronie mogą być rozwijane, w PDF pozostają na końcu.

Nie eksportujemy błędów parserów, surowych materiałów, prywatnych ocen ani
logów. Nie ukrywamy niepewności przez zamianę niepełnego źródła na pełne.

### Informacje o wydaniu

Wersja metodologii i link do jej opisu, okno raportu, informacja o korekcie,
odnośnik do konkretnego wydania oraz „RedThreatAlert by Pixels4Users”.
PDF dodatkowo ma numery stron. Wersja szablonu jest metadanymi artefaktu,
odrębnymi od wersji metodologii i treści raportu.

## 2. Powiązanie z istniejącymi danymi

| Element | Publiczne dane | Zasada |
|---|---|---|
| Tytuł, data i okno | `report_type`, `as_of`, `window` | Stały polski szablon; data z Europe/Warsaw. |
| Tożsamość i korekta | `report_id`, `supersedes` | Stały adres wydania; bez nadpisania historii. |
| Indeks i pewność | `rtb.score`, `rtb.status`, `rtb.confidence.percent` | Wartości z raportu, bez ponownego obliczenia w widoku. |
| Poziom indeksu | `rtb` i wspólna funkcja `threatLevel` | Te same reguły prezentacji co dashboard; żadnych nowych progów. |
| Zmiana | `rtb.trend` | Tylko dostępne porównanie; data z raportu wskazanego przez `reference_report_id`. |
| Podsumowanie | `commentary.text`, opcjonalne `commentary.sections` | Zachowanie zatwierdzonego tekstu i istniejącego podziału. |
| Oficjalne ostrzeżenia | `rtb.official_warnings` | Status i znaczenie w chwili wydania, niezależnie od liczby RTA. |
| Wydarzenia | `incidents[]`, opcjonalne `presentation` | Istniejące streszczenia, statusy, daty i miejsca; starsze rekordy używają wspólnych reguł zastępczych. |
| Źródła wydarzeń | `incidents[].sources` | Zweryfikowane publiczne adresy, bez prywatnych dowodów. |
| Pokrycie i ograniczenia | `sources`, `gaps`, `limitations` | Czytelna prezentacja bez diagnostyki technicznej. |
| Metodologia | `provenance.methodology_version` | Zgodna z konkretnym historycznym wydaniem. |

Istniejący eksport zasila wspólny model `web/report-presentation.js`.
Czytnik i TXT zachowują komentarz, a generator PDF używa tego samego modelu
oraz `web/report-content.js`.

Rozpoznane uzupełnienia na etap implementacji:

- Publiczny obiekt ostrzeżenia zawiera instytucję, lecz nie adres materiału.
  Link do konkretnego ostrzeżenia wymaga jawnego powiązania ze źródłem;
  nie wyprowadzamy go z podobieństwa tekstu. Brak linku nie ukrywa instrukcji.
- Adres, gotowość i wersja PDF nie są częścią obecnego kontraktu. Projektujemy
  je jako metadane artefaktu przypisanego do `report_id`, bez zmiany treści
  i identyfikatora zatwierdzonego raportu.
- Prywatna selekcja tematów do komentarza nie jest eksportowana. Pierwszy
  widok pokazuje gotowe podsumowanie i listę wydarzeń; nie tworzy nowego
  rankingu redakcyjnego ani dodatkowych wniosków.

## 3. Wspólne wykonanie strony i PDF

Jeden model prezentacyjny z publicznego wydania i wspólne komponenty treści.
Wariant do druku zmienia układ, łamanie stron i nawigację, nie ustalenia.
Bez wymogu stałej liczby stron i bez nowych wywołań AI przy formatowaniu.
Wszystkie szczegóły dostępne w rozwijanych sekcjach strony są czytelne w PDF.

Generator dostaje dokładne `report_id`, nie zmieniający się adres „latest”.
Plik przechodzi kontrolę zgodności i dopiero potem staje się dostępny do
pobrania. Jego niepowodzenie nie blokuje raportu online. Ponowienie obejmuje
wyłącznie przygotowanie tego samego artefaktu, bez pobrań OSINT i nowej analizy.
Implementacja wykorzystuje lokalny Chromium i prywatny magazyn Supabase,
z pobieraniem przez istniejące serwerowe API. Metadane są osobne od raportu.
Przygotowaną lokalną implementację zachowano w prywatnym archiwum
`data/backups/redesign-before-pdf-deferral-2026-10-05/`. Nie jest dołączona
do wydania strony; nie wdrażamy jej migracji ani kroku w harmonogramie.

## 4. Kolejność prac i odbiór

1. Gałąź redesignu: strona raportu oraz projekt układu do druku według tej
   specyfikacji, przy użyciu istniejącego Design Systemu.
2. Ocena użytkownika na rzeczywistych publicznych wydaniach, poprawki i akceptacja.
3. Test i publikacja strony raportu, wersji do druku oraz eksportów TXT/JSON/GeoJSON.
4. Odłożony etap: generator PDF, zapis plików i osobny odbiór pobierania oraz harmonogramu.

Przed wdrożeniem sprawdzamy (punkty dotyczące PDF obowiązują dopiero w jego osobnym etapie):

- Zgodność indeksu, czasu, komentarza i listy wydarzeń pomiędzy eksportem,
  stroną, pobieranym tekstem i PDF.
- Aktualny raport, historyczny raport bez sekcji komentarza, brak komentarza,
  zero, historyczny niewyliczony indeks oraz brak porównania.
- Ostrzeżenie aktywne, zakończone i o nieustalonym statusie; treść archiwalna
  nie udaje bieżącej instrukcji.
- Korektę i linki między wersjami bez zmiany starego wydania.
- Krótkie i długie listy, puste grupy, polskie znaki, klawiaturę, mobile,
  linki do źródeł i podział stron PDF.
- Brak PDF, błąd generowania i bezpieczne ponowienie bez ponownej analizy.

Generowanie i publiczna prezentacja używają wyłącznie dozwolonego eksportu,
nigdy prywatnego snapshotu lub materiałów źródłowych całego cyklu.
