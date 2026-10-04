# Ograniczony pilotaż nowych źródeł — 03.10.2026

Pierwsze próby po [analizie World Monitor](worldmonitor-analysis.md) obejmują
Sjöfartsverket i Meduzę jako dodatkowego wydawcę relacjonującego sprawy Rosji. Korzystamy bezpośrednio z ich
stron. Nie podłączamy World Monitor ani jego indeksu CII. Metodologia
`rtb-v0.4`, wagi, pewność i konfiguracja głównego cyklu pozostają bez zmian.

## Granice i obsługa

- Konfiguracja: `config/source-pilots.json`; kod: `src/osint_dashboard/source_pilots.py`.
- Uruchamianie ręczne, poza harmonogramem; najwyżej jedno żądanie na źródło
  i dobę Europe/Warsaw, bez ponowień, przekierowań i pobierania artykułów.
  Limit odpowiedzi: 1,5 MB; czas: 25 sekund. Respektujemy `Retry-After`.
- Próba jest rezerwowana przed połączeniem. Nieudana próba i wcześniejszy
  ręczny odczyt z zapisanym `fetch.json` również zużywają limit dobowy.
- Dane: prywatny `data/source_pilots/<źródło>/<dzień>/`; poza Git, SQLite,
  Supabase i eksportem dashboardu. Nie są automatycznie liczone jako sygnały.
- Surowa odpowiedź, jej hash, czas i wynik HTTP są zapisywane oddzielnie od
  rekordów parsera. Replay używa zapisanego pliku bez sieci. JSON Schema
  2020-12 sprawdza `parsed-v1.json`. Różniącej się wersji pliku nie nadpisujemy.
- Błąd strony/parsera oznacza błąd próby, nie zero ostrzeżeń. Wcześniejsze
  odczyty pozostają dostępne. Nie wnioskujemy o odwołaniu z nieobecności na liście.

```sh
.venv/bin/python scripts/source_pilot.py collect --source sjofartsverket
.venv/bin/python scripts/source_pilot.py collect --source meduza
.venv/bin/python scripts/source_pilot.py parse --source sjofartsverket --capture data/source_pilots/sjofartsverket/2026-10-03
.venv/bin/python -m pytest tests/test_source_pilots.py
```

## Sjöfartsverket: pierwszy odczyt

03.10, 10:58:56 UTC: HTTP 200, 39 726 bajtów. URL z benchmarku
`/en/Navigationsvarningar/Navtexx` zwraca stronę **Swedish navigational warnings
in force**; nie deklarujemy, że jest to kompletna depesza NAVTEX lub historia
ostrzeżeń. Aktualizacja strony `2026-10-03 12:15` nie zawiera strefy czasowej.
Jej tekst zachowano dosłownie, bez zamiany na UTC.

16 wystąpień w obszarach dało **11 odrębnych ostrzeżeń**. Komunikat
`BALTIC SEA NAV WARN 026/25` występuje w sześciu obszarach i pozostaje jednym
rekordem. Identyfikator nadawcy i numer ostrzeżenia określają tożsamość;
hash treści rozróżnia aktualizacje. Sprzeczne kopie przerywają parsowanie.

Trzy rekordy skierowano do wstępnego przeglądu kontekstu: ostrzeżenie o
zakłóceniach nawigacji, zapowiedź ćwiczeń bez strzelań oraz zapowiedź strzelań
w rejonie Wysp Alandzkich. Pozostałe obejmują m.in. światła nawigacyjne,
dryfującą boję i utrudnienia na wodach śródlądowych.

Czas w rodzaju `021100 UTC JUL` nie podaje pełnego roku. Parser zachowuje
go obok numeru `026/25`, bez dorabiania daty zdarzenia lub daty publikacji.
Dzisiejszy odczyt starszego ostrzeżenia nie staje się nowym incydentem.
Okresy ćwiczeń pozostają w treści do oceny; samo ostrzeżenie nie potwierdza
wykonania ćwiczenia, operatora, intencji ani rosyjskiej atrybucji.

## Meduza: pierwszy odczyt

03.10, 11:22:51 UTC: bezpośredni RSS `https://meduza.io/rss/en/all`, HTTP 200,
**30 pozycji**, z datami publikacji 01–03.10. Wykorzystujemy istniejący parser
RSS z dostarczonego skillu. Zachowujemy skróty do 2000 znaków i pełny surowy
RSS, bez deklarowania przeczytania pełnych artykułów. Oryginały nie trafiają
do polskiego interfejsu jako gotowe tłumaczenia.

Prosty filtr tematu i geografii wskazał **12 pozycji do wcześniejszego
przejrzenia**. To priorytet kolejki, nie akceptacja: wszystkie 30 pozycji
pozostaje w archiwum. Przejrzano tytuły wszystkich pozycji i skróty 12
wyróżnionych oraz czterech dodatkowych pozycji o flance i sankcjach.

Próba ujawniła fałszywe trafienia (m.in. Afganistan ze wzmianką o Rosji)
oraz pominięcie w priorytecie doniesienia z Finlandii. Dlatego słowa kluczowe
nie mogą samodzielnie rozstrzygać o wejściu materiału do analizy. Warto
dalej sprawdzić źródła pierwotne doniesień o sabotażu w Lipsku, rosyjskim
budżecie wojskowym oraz ukraińskiej infrastrukturze energetycznej.
Są to tropy; nie ustalono jeszcze ich nowości względem całej bazy.

Meduza w tej próbie cytuje m.in. The Telegraph, FT, NYT i inne redakcje.
Nie stanowi dodatkowego niezależnego potwierdzenia tych samych doniesień.
Rzekomy dokument opisany przez NYT ma nieustaloną autentyczność; sam tekst
nie dowodzi planu ani przeprowadzenia ataku. W próbie nie utworzono zdarzeń
ani punktów z tych publikacji.

## Włączenie do normalnego przepływu

Status obu źródeł to `isolated_pilot`, nie działający kolektor dobowego RTA.
Sjöfartsverket rozwija istniejący wpis `maritime_ais_and_notices`; nie tworzy
drugiego kandydata morskiego. Meduza jest odrębnym nowym wydawcą. Rejestr
wskazuje konfigurację pilotażu zamiast `config/sources.json`.

Przed uruchomieniem w głównym cyklu należy:

1. Zebrać kolejne ograniczone próby i porównać tożsamość, zmiany treści,
   opóźnienie, znikanie z listy oraz błędy. Jeden HTTP 200 nie potwierdza ciągłości.
2. Dla wybranych materiałów sprawdzić źródła pierwotne i dopasowanie do już
   zapisanych zdarzeń. Zmierzyć nowe istotne ustalenia, powtórzenia,
   materiały poza zakresem i czas potrzebny na przegląd. Nie zastępować
   tych miar liczbą rekordów ani reputacją wydawcy.
3. Ustalić zakres pełnego tekstu, tłumaczeń i dozwolonej redystrybucji;
   dotychczasowy pilotaż niczego nie publikuje. Dopiero potem dodać adapter
   materiałów i testy jego importu do istniejącej kolejki przeglądu.
4. Uruchomić próbny cykl na kopii bazy. Sprawdzić deduplikację, raport,
   eksport, mapę i liczniki, a następnie włączyć jeden adapter do codziennej pracy.

Docelowo pozostaje ten sam przepływ: **źródło → materiał → ocena i drugi
przegląd → zdarzenie lub kontekst → raport → Supabase → strona**. Nowe
źródło nie wymaga nowej metodologii, dopóki używa tych samych reguł oceny.
Zmiana wag, atrybucji albo znaczenia punktacji wymaga osobnej wersji i testów.
Nie zaplanowano dodatkowej automatyzacji pilotażu.

## Ocena przydatności po przeglądzie

03.10.2026 przejrzano wszystkie 41 rekordów i porównano je z kopią bazy.
Sjöfartsverket wnosi trzy przydatne komunikaty kontekstowe z 11 ostrzeżeń.
Z 30 pozycji Meduzy wybrano dziewięć do dalszej pracy: cztery doprowadziły
do sprawdzonych, ograniczonych ustaleń; pięć wymaga dalszej weryfikacji.
Nie oznacza to dziewięciu nowych incydentów. Dokładna kwota rosyjskiego
projektu budżetu była już w OSW, a część doniesień opisuje starsze zdarzenia.

Rekomendacja: najpierw adapter Sjöfartsverket, po kolejnych próbach i teście
na kopii bazy; Meduza po poprawie przekazywania treści RSS i priorytetów.
Oba źródła nadal mają status `isolated_pilot`. Wyniki, dowody, ograniczenia
i kolejność prac opisuje [ocena wartości pilotażu](source-pilots-review-2026-10-03.md).
