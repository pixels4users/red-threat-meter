# Biblioteka doktryny i kontekstu

Stan katalogu: 23.09.2026. Rejestr maszynowy: `config/doctrine-sources.json`. Pliki PDF znajdują się lokalnie w `data/doctrine_rag/`, poza Git. Nie przesyłamy ich do usług zewnętrznych. Ta biblioteka pomaga stawiać pytania i sprawdzać interpretacje; nie jest strumieniem bieżących incydentów ani samodzielnym dowodem sprawstwa.

## Co sprawdzono

Przejrzano metadane, strony tytułowe i wybrane fragmenty, a następnie sprawdzono możliwość mechanicznego wydobycia tekstu. Nie oznacza to przeczytania ani weryfikacji wszystkich tez książek. Każdy dokument ma stabilny identyfikator i SHA-256 zapisany w rejestrze. Numer `page_pdf` oznacza pozycję strony w pliku, a nie numer drukowany.

W końcowym zestawie jest dziesięć dostępnych PDF-ów; indeks obejmuje 2295 stron zawierających co najmniej 80 znaków tekstu. Strony krótsze i puste zachowują swoje miejsca w numeracji PDF, lecz nie są wyszukiwane. Dwa dokumenty Romera były dostępne przy pierwszym przeglądzie, lecz zniknęły z katalogu przed końcową inwentaryzacją; ich wpisy pozostały jako `missing_file`. Doszedł artykuł Marcina Miszczuka. Indekser jawnie zgłasza pliki nieobecne, zmienione oraz nowe, jeszcze niezarejestrowane.

| Identyfikator | Materiał / autor | Rodzaj i zastosowanie | Stan treści |
|---|---|---|---|
| `dryblak_2024` | Łukasz Dryblak, „Rola i znaczenie rosyjskich dokumentów doktrynalnych”, 2024 | Opracowanie naukowe o doktrynach; nie sam dokument doktryny | 32 strony PDF; tekst dostępny |
| `chudoba_2023` | Mateusz Chudoba, „Zagrożenia hybrydowe — wnioski dla Sił Zbrojnych RP”, 2023 | Porządkowanie pojęć i rodzajów zagrożeń | 19 stron; tekst dostępny |
| `kraj_messner` | Kazimierz Kraj, „Wojny asymetryczne czy miatieżewojna…” | Opracowanie koncepcji Messnera | 7 stron; rok 2012 w nazwie pliku, bibliografia do potwierdzenia |
| `sykulski_2015` | Leszek Sykulski, „Rosyjska koncepcja wojen buntowniczych Jewgienija Messnera”, 2015 | Interpretacja koncepcji historycznej | 11 stron; tekst dostępny |
| `kokoshin_2011` | Andrei Kokoshin, „Ensuring Strategic Stability in the Past and Present”, 2011 | Stabilność strategiczna i odstraszanie; konieczna kontrola kontekstu nuklearnego | 78 stron; tekst dostępny |
| `ghamari_tabrizi_2005` | Sharon Ghamari-Tabrizi, „The Worlds of Herman Kahn”, 2005 | Historia myśli strategicznej; opracowanie o Kahnie | 397 stron; tekst dostępny |
| `kennan_russia_west` | George F. Kennan, „Russia and the West under Lenin and Stalin” | Historia dyplomacji | 432 strony; rok wydania do potwierdzenia; cytaty OCR sprawdzać na skanie |
| `kennan_lukacs_2010` | Kennan / Lukacs, „Through the History of the Cold War”, 2010 | Korespondencja historyczna | 289 stron; tekst dostępny |
| `bartosiak_2018` | Jacek Bartosiak, „Rzeczpospolita między lądem a morzem”, 2018 | Hipotezy geostrategiczne, komunikacja i geografia | 1059 stron; tekst dostępny |
| `miszczuk_nato_flank` | Marcin Miszczuk, „The Security of NATO’s Eastern Flank in the Context of the New U.S. National Security Strategy” | Analiza strategii USA i flanki; nie oficjalna strategia USA | 24 strony; zeszyt 38 oznaczony 2025, plik wytworzony w 2026; tekst gubi znaki i ligatury |
| `romer_1916` | Eugeniusz Romer, „Wojenno-Polityczna Mapa Polski”, 1916 | Geografia historyczna, bez zastępowania aktualnych danych GIS | Obecnie brak pliku; wcześniej 8 stron skanu bez warstwy tekstowej |
| `romer_link_stub` | Eugeniusz Romer, „Pisma geopolityczne” | W dostarczonym pliku tylko odsyłacz | Obecnie brak pliku; wcześniej jedna strona z okładką/linkiem, bez książki |

Dostępny tekst nie gwarantuje poprawnej ekstrakcji map, tabel, nazw i cytatów. Szczególnie w artykule Miszczuka wyszukiwanie może pomijać słowa z uszkodzonymi znakami. Nie przedstawiamy nieobecnych książek jako przeczytanych i nie pobieramy automatycznie treści z odsyłacza.

## Dodane źródła internetowe

- **Walerij Gierasimow, 2013** — przedruk tez wystąpienia, przydatny jako świadectwo poglądów autora. Nie wystarcza do uznania tekstu za formalną doktrynę ani do wnioskowania o bieżącym planie ataku. Serwis podaje 26.02.2013, a wskazany numer oryginalnego pisma jest z 27.02.2013. [Ценность науки в предвидении](https://vpk.name/news/85159_cennost_nauki_v_predvidenii.html).
- **Włodzimierz Bączkowski, 1938** — historyczny esej o metodach działania państwa. Użyteczny do formułowania hipotez, z uwzględnieniem epoki i publicystycznego charakteru. Uogólnienia etniczne i kulturowe w tekście nie są dowodem cech ludzi ani współczesnego sprawstwa. [Uwagi o istocie siły rosyjskiej](https://www.omp.org.pl/artykul.php?artykul=115).
- **NATO, 2022** — oficjalny punkt odniesienia dla języka i celów bezpieczeństwa Sojuszu. W rejestrze jako dokument strategiczny; nie jako incydent. Sprawdzono metadane i stronę, pełnego PDF-u nie dodano do indeksu lokalnego. [Strategic Concept](https://www.nato.int/content/dam/nato/webready/documents/publications-and-reports/strategic-concepts/2022/290622-strategic-concept.pdf).

Linki mają status sprawdzonego odniesienia, nie lokalnej kopii pełnego tekstu. Wyszukiwanie opisane poniżej obejmuje tylko zarejestrowane PDF-y dostępne na dysku.

## Jak korzystać

W katalogu projektu:

```sh
.venv/bin/python scripts/doctrine.py index
.venv/bin/python scripts/doctrine.py search 'kontrola refleksyjna' --limit 5
.venv/bin/python scripts/doctrine.py search 'strategic stability' --limit 3
```

Potrzebny jest Poppler (`pdftotext`, dostępny na tym Macu). Indeks zapisuje strony w `data/doctrine_index/<id>/` i atomowo zmienia `latest.json`; nie nadpisuje poprzednich indeksów. Wyszukiwanie jest lokalne, tekstowe, wymaga wszystkich słów zapytania i nie odróżnia polskich znaków. Nie jest jeszcze semantycznym RAG z embeddingami. Nie wymaga płatnego API ani uruchamiania starego `scripts/ingest.py`.

Wynik podaje identyfikator dokumentu, pełną ścieżkę, numer strony PDF, hash i krótki fragment. Otwórz tę stronę i sprawdź kontekst przed użyciem. Kontrola integralności blokuje użycie zmienionego indeksu, rejestru lub PDF-u w znalezionym wyniku. Po dodaniu albo zmianie pliku: przegląd metadanych i jakości, aktualizacja rejestru, ponowna indeksacja. Samo wrzucenie dokumentu do katalogu nie nadaje mu statusu dowodu ani nie uruchamia automatycznej analizy.

## Zasady interpretacji

1. Zapisuj autora, datę, gatunek i tezę. Oddziel oficjalną strategię, wypowiedź urzędnika, opracowanie akademickie i publicystykę.
2. Wyprowadź sprawdzalną hipotezę wraz z konkurencyjnym wyjaśnieniem. Wskaż, jakie współczesne dane mogłyby ją potwierdzić lub osłabić.
3. Cytuj w briefie `document_id`, SHA-256 i stronę PDF; dla tekstu WWW adres, datę odczytu i sekcję. Stosuj krótkie cytaty lub własną parafrazę, nie kopiuj książek do raportów.
4. Nie importuj doktryny jako dowodu `occurrence`, `attribution`, `timing`, `location` ani `criterion`. Punkty wymagają bieżącego, udokumentowanego zdarzenia.
5. Autorzy powtarzający tę samą historyczną tezę nie tworzą niezależnej weryfikacji incydentu. Dopasowanie wzorca nie potwierdza sprawcy ani nieuchronności eskalacji.

Dalsze uzupełnienia warto kierować ku dokumentom pierwotnym wskazanym w bibliografiach oraz aktualnym ocenom instytucjonalnym. Dla samego RTB większą luką pozostają źródła operacyjne i dane odniesienia; priorytety opisuje `docs/sources.md`.
