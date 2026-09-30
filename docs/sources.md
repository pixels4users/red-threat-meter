# Źródła bieżące i materiały referencyjne — v0.3

### Archiwum OSW i źródła do przeglądu — 30.09.2026

`sources-pilot-5` rozszerza OSW o maksymalnie trzy kolejne strony
[archiwum publikacji](https://www.osw.waw.pl/pl/publikacje), czytane aż do
przekroczenia granicy 216 godzin. RSS i archiwum są deduplikowane po URL.
Obowiązują wcześniejsze limity: 30 publikacji i 50 żądań łącznie. Brak daty,
zaburzona kolejność, przeskok paginacji lub wyczerpanie limitu nie dają
potwierdzenia pełnego okna. Daty pochodzą z jawnych znaczników wydawcy.
Kompletność listy publikacji nie jest poświadczeniem historii zdarzeń;
przegląd tej historii pozostaje osobnym krokiem v0.3.

Opcjonalne konta OSINT Defender i OSINT Technical mają [ograniczony kolektor
API i import odczytów przeglądarki](x-sources.md) oraz filtr Europy Wschodniej / Niemiec. Skill
`x-research` prowadzi pracę Codexa, a nie automatyczny skrypt dostępu do X.
Zapisujemy oryginały, ograniczenie zasięgu i decyzję filtra; nie naliczamy
punktów z samych postów ani popularności konta.

Dodano również dwa ograniczone zestawy dokumentów pierwotnych: łotewski MON
(`lv_mod`, trzy komunikaty o obronie powietrznej) i VDD (`lv_vdd`, trzy
komunikaty o wyborach, groźbach i śledztwie dotyczącym podpalenia). Adapter
odświeża wyłącznie wskazane URL, zachowuje pełny tekst i datę z dokładnością
do dnia (`source_record.published_on`). Bez godziny `published_at=null`;
nie dopisujemy północy ani nie przesuwamy daty przez konwersję stref.
Nie odkrywa nowych wiadomości i nie poświadcza
kompletności historii wydawcy. Listy URL są jawne w konfiguracji; wspólne
pochodzenie komunikatów wymaga deduplikacji w przeglądzie.

Źródła procesu RTB sprawdzono przez rzeczywiste pobrania 22.09.2026. Ich rejestr wykonywalny: `config/sources.json` (obecnie sources-pilot-6; od 30.09 także archiwum OSW, odczyty X i dokumenty łotewskie). Tabela zachowuje wynik pierwszego pilotażu. Osobny pilotaż GPSJAM i RSS belzhd uruchomiono 23.09.2026 według `config/early-warning.json`, a regionalny kolektor ADSB.lol — 24.09 według `config/aviation.json`. Ograniczony audyt historii z tego samego dnia ma osobną konfigurację `config/aviation-history.json`. Każdy przebieg zachowuje własny wynik dostępu, datę i błędy; opis poniżej nie gwarantuje przyszłej dostępności.

| Źródło | Dostęp i zakres | Rola | Wynik pilotażu |
|---|---|---|---|
| [RCB](https://www.gov.pl/web/rcb/komunikaty) | Lista HTML i treści komunikatów; uwzględnione wstępy i aktualizacje | Wymagane, pierwotne komunikaty publiczne | 20 materiałów |
| [MON](https://www.gov.pl/web/obrona-narodowa/aktualnosci5) | Lista HTML i treści artykułów; właściwa ścieżka to `aktualnosci5` | Wymagane, oficjalne informacje resortu | 14 materiałów |
| [OSW](https://www.osw.waw.pl/pl/rss.xml) | RSS, tytuły i skróty; bez obietnicy pełnej treści artykułów | Wymagane, kontekst analityczny | 10 materiałów |
| [Naval News](https://www.navalnews.com/feed/) | RSS o tematyce morskiej, także poza regionem | Opcjonalne | HTTP 503 w dwóch przebiegach; brak materiałów |
| [CERT Polska](https://cert.pl/posts/) | Integracja wyłączona; adres RSS nieweryfikowany | Kandydat na późniejszy etap | Próbny dostęp do strony: HTTP 403 |

Dwa pobrania dały łącznie 44 unikalne wersje materiałów; drugie nie dodało duplikatów. W przyszłości zmiana treści tej samej publikacji tworzy nową wersję i nową pozycję do oceny.

### Pełne treści OSW — rozszerzenie 29.09.2026

RSS służy do odkrywania publikacji. Kolektor pobiera właściwy tekst HTML
(`article.publikacje .field--name-body`); dla raportów pobiera jednoznacznie
podlinkowany PDF OSW. Interaktywny skrót raportu nie zastępuje dokumentu.
PDF wymaga lokalnego Popplera (`pdfinfo`, `pdftotext`); zapis `pdf_text` oznacza
ekstrakcję tekstu, bez OCR ani automatycznej interpretacji map i tabel.

Zakres obejmuje bieżący RSS oraz do 10 znanych, nierozstrzygniętych publikacji,
które wypadły z kanału. Limit łączny: 30 publikacji, 50 żądań (wraz z ponowieniami
i przekierowaniami), 3 MB odpowiedzi, PDF do 250 stron i 1 MB wydobytego tekstu.
Przekroczenie limitu, brak selektora, ostrzeżenia ekstraktora albo niedostępny
artykuł oznaczają niepełny wynik. Starsza pozycja z kolejki nie dowodzi pokrycia
całego okna RSS. W tej wersji z 29.09 nie przeszukiwano dodatkowo archiwum wydawcy; rozszerzenie z 30.09 opisano powyżej.

Host pozostaje `www.osw.waw.pl`; poza `/pl/` dopuszczono wyłącznie ścieżki
`/transformacja-bundeswehry/` i `/sites/default/files/`. Archiwum przechowuje
RSS, HTML/PDF, końcowe URL-e i sposób ekstrakcji. Tożsamość dokumentu zachowuje
pierwotny URL publikacji także po przekierowaniu. Nowy pełny tekst otrzymuje
nowy `material_id` i wymaga nowej oceny. Nieudane pobranie nie zastępuje
wcześniej zapisanego pełnego tekstu skrótem. Nowe, jeszcze niepobrane publikacje
zachowują skrót w kolejce do ponowienia; nie są oznaczane jako pełna treść.
Dotychczasowe materiały i oceny pozostają w historii. Ten etap OSW zakończono jeszcze na v0.2; późniejsze wdrożenie v0.3 opisano niżej.

## Osobna warstwa obserwacji — rzeczywiste pobrania 23.09.2026

| Źródło | Dostęp i wynik | Ograniczenie |
|---|---|---|
| [GPSJAM](https://gpsjam.org/) | Publiczny manifest i dzienne CSV mapy; 30/30 dób 24.08–22.09.2026 | Produkt dobowy, luki przestrzenne, brak atrybucji; 27.08 zmienił się zestaw dostawców |
| [belzhd — RSS](https://belzhd.info/feed/) | 10 publikacji z pełną treścią RSS od 2.07 do 16.09, cztery z rubryki wojskowej | Jeden wydawca, nie pełny spis transportów; kanał tematyczny 403; Telegram niepodłączony |

Powtórne pobranie trzech ostatnich dób i RSS nie utworzyło nowych wersji. Zachowano 13 kolejnych odczytów tych samych obserwacji. Źródła są obserwacyjne, nie uczestniczą w bramce kompletności RTB i nie naliczają punktów. Specyfikacja, dowody dostępu, miary i ich ograniczenia: [instrukcja pilotażu](early-warning-runbook.md).

## Dane lotnicze — pilotaż od 24.09.2026

ADSB.lol ma oddzielny kolektor czterech obszarów, archiwum i raport jakości po polsku. Próbki obejmują bbox `[14,49,29,60]`, z kontrolą duplikatów, czasu i braków. Wspólna grupa pochodzenia: `adsb:adsblol`; licencja danych według dostawcy: ODbL 1.0. Typ i flaga wojskowa są oznaczeniami dostawcy, operator i intencja pozostają nieustalone. Nie wyliczamy punktów RTB ani kompletności obserwacji wszystkich lotów. [Instrukcja i źródła kontraktu](aviation-runbook.md), [wyniki prób](STATUS.md).

Z tej samej grupy pochodzenia zebrano trzy półgodzinne pliki historii mapy, łącznie 78,1 MB treści i 540 przedziałów po 10 sekund. W jednym pliku odrzucono pojedynczy rekord, co oznaczono jako częściową jakość. Historia i API mają odmienny dobór pozycji oraz dostępne pola, dlatego tworzą osobne serie. Format historii nie zawiera typu samolotu ani flag wojskowych; nie uzupełniamy ich dzisiejszymi etykietami. [Audyt historii](aviation-history.md).

## Zasady dostępu

Kolektor publikacji WWW/RSS wykonuje publiczne żądania GET bez logowania i omijania zabezpieczeń. Ma limit 15 sekund na żądanie, jedno ponowienie przy błędach sieci lub 5xx, odstęp między żądaniami i limit odpowiedzi 3 MB. HTTP 429 lub odpowiedź z `Retry-After` wstrzymuje źródło bez ponowienia; termin blokady jest zachowany w `data/fetch-state/` między cyklami (minimum 5 minut, dłużej według nagłówka). Dopuszczalne hosty, ścieżki, liczba stron i pozycji są zapisane w konfiguracji. Przekierowania poza ten zakres są odrzucane.

Osobny kolektor X korzysta z zaakceptowanego płatnego API, tokena aplikacji i limitów opisanych w [instrukcji X](x-sources.md).

Bieżący kolektor ADSB.lol ma osobny transport **bez automatycznych ponowień**. Odstępy to co najmniej 2 sekundy między żądaniami oraz 60 sekund od końca cyklu. HTTP 3xx/4xx wstrzymuje pozostałe zapytania i utrwala blokadę kolejnego cyklu według `Retry-After`, nie krótszą niż 5 minut. Nie obchodzi przekierowań ani limitów API.

Audyt historii dopuszcza do trzech plików, 32 MB każdy i 96 MB łącznie, co najmniej 3 sekundy między żądaniami oraz godzinę od końca pobrania. Nie ponawia zapytań ani nie przechodzi za przekierowaniami. HTTP 3xx/4xx blokuje pozostałe żądania, z wyjątkiem 404 oznaczającego brak konkretnego okna; `Retry-After` jest zachowany. Pełne limity i stałe daty opisuje [instrukcja historii](aviation-history.md).

Surowa odpowiedź trafia na lokalny dysk przed ekstrakcją. Błąd pojedynczej daty lub artykułu daje stan częściowy; brak wpisów nie jest interpretowany jako brak incydentów. Źródła sprawdzane są podczas ręcznego uruchomienia, bez zainstalowanego harmonogramu.

## Luki i następne rozszerzenia

- Pełne teksty OSW są pobierane od 29.09. Niedostępne artykuły, nowe formaty stron, skany i przekroczone limity nadal wymagają uzupełnienia; sam tytuł nie rozstrzyga oceny.
- RCB i MON nie zapewniają kompletnej, niezależnej obserwacji wszystkich incydentów w CEE. Różne instytucje mogą powtarzać ten sam pierwotny komunikat.
- Są dobowe pomiary GNSS i krótkie próbki lotnicze, lecz brak skalibrowanego odniesienia i automatycznego detektora. Nie ma ciągłej obserwacji lotniczej, danych granicznych i systematycznych danych o cyberatakach. Kategorie wymagające poziomu odniesienia nie mogą być wypełniane domysłem.
- Konta X mają ograniczony kolektor API uruchamiany osobno przed cyklem, z kontrolą kosztów; nie ma poświadczenia pełnej historii ani harmonogramu. FIRMS, płatne mapy i modele predykcyjne pozostają niepodłączone. Każde rozszerzenie wymaga sprawdzenia dostępu, zakresu, kosztów i praw do ponownego wykorzystania.
- Lista z limitem stron pozwala na ograniczony powrót do starszych materiałów. Nie odtwarza automatycznie luk po wielotygodniowej przerwie ani wycofanych publikacji.

Opisowe porównanie GNSS jest już wdrożone; kalibracja normalnego poziomu i detektora pozostaje dalszą pracą. [Ocena dostępu lotniczego](aviation-access.md) poprzedziła [pilotaż API](aviation-runbook.md) i [ograniczony audyt historii](aviation-history.md). Kolejne badanie danych obejmie różne pory i dni, zmienność źródła oraz klasyfikację z datami obowiązywania. Równolegle pozostaje dodanie źródeł weryfikujących. Doprecyzowany projekt: `docs/early-warning-design.md`. Zmiana aktywnego rejestru musi być widoczna w historii i uwzględniona przy porównywaniu odczytów.

## Odrębne rejestry

- `config/sources.json`: kolektory uruchamiane przez pipeline; tylko wpisy enabled uczestniczą w pobraniu.
- `config/early-warning.json`: działający, osobny pilotaż GPSJAM/RSS belzhd uruchamiany przez `scripts/early_warning.py`.
- `config/aviation.json`: działający pilotaż jakości ADSB.lol uruchamiany przez `scripts/aviation.py`; własna baza, bez wpływu na RTB.
- `config/aviation-history.json`: ograniczony audyt stałych okien historii przez `scripts/aviation_history.py`; własne pliki i manifesty, bez dopisywania próbek do API ani RTB.
- `config/source-candidates.json`: kandydaci oraz źródła zaakceptowane do integracji, z osobnym statusem dostępu i wdrożenia. Wpis nie oznacza dostępu ani wdrożonego adaptera.
- `config/doctrine-sources.json`: kontekst doktrynalny, historyczny i strategiczny. Zasady użycia oraz PDF-y: `docs/doctrine.md`. Bez automatycznych punktów RTB.

War on the Rocks, The War Zone, Defense One, Breaking Defense, mapy Liveuamap/DeepState i wskazane profile X zachowano jako kandydatów do sprawdzenia. Od wersji `source-candidates-6` rejestr odnotowuje działający pilotaż API ADSB.lol i osobny audyt historii; wersja 7 dodała strumienie opisane poniżej, a `source-candidates-8` zapisuje ich akceptację do integracji. Wdrożone GPSJAM/belzhd oraz ADSB.lol wskazują osobne konfiguracje runtime; pozostałe wpisy nie oznaczają działających integracji. Jednorazowy test OpenSky pozostaje odrębny od kolektora i harmonogramu.

<a id="rozszerzenie-zrodel-25-09-2026"></a>

## Rozszerzenie źródeł — zaakceptowane 25.09.2026

Rejestr `source-candidates-9` oznacza poniższe 12 pozycji jako `accepted_for_integration`, z datą `accepted_on=2026-09-25`. To akceptacja doboru źródeł i rozszerzenia RCB, nie potwierdzenie dostępu ani gotowości produkcyjnej. 25.09 sprawdzono opisy i adresy WWW. Od 29.09 działają adaptery PAŻP/AUP i RSO/ogólne opisane niżej; pozostałe źródła, detektory i harmonogram zachowują odrębny status. RCB ma już kolektor `rcb` w `config/sources.json` — rozszerzenie dotyczy semantyki jego treści, nie kolejnego pobierania tych samych materiałów. `checked_on` zachowuje datę ostatniej oceny dostępu; `accepted_on` dotyczy decyzji projektowej. Sama akceptacja nie odświeża wyniku kontroli źródła.

[Strażnik](https://straznik.eu/) służy analizie architektury. Nie jest źródłem naszych zdarzeń ani zależnością procesu; nie planujemy scrapowania jego interfejsu ani pobierania jego agregatów. ADS-B nadal pochodzi bezpośrednio z ADSB.lol, według [oceny dostępu](aviation-access.md), [pilotażu API](aviation-runbook.md) i [audytu historii](aviation-history.md). Nowe strumienie rozszerzają obserwację zagrożeń hybrydowych, infrastrukturalnych, morskich i geostrategicznych.

### PAŻP — plan i rzeczywista aktywność przestrzeni

Kandydat `pansa_airspace`: [airspace.pansa.pl](https://airspace.pansa.pl/), AUP/UUP i informacje o wykorzystaniu przestrzeni. Cel: wykrywać nierutynowe zmiany, które mogą poprzedzać działania obrony przestrzeni RP. Hipoteza wymaga sprawdzenia; samo wyznaczenie lub włączenie strefy nie dowodzi przygotowań bojowych. PAŻP rozróżnia planowanie i aktywację/dezaktywację struktur. [Opis systemu CAT](https://www.pansa.pl/cat/), [AUP/UUP i zarządzanie ASM](https://www.amc.pansa.pl/amc-polska/informacje-ogolne/).

Rejestrować ADHOC, R (Restricted), D (Danger) i NPZ oraz ich zmiany, zachowując oryginalny typ dostawcy. **NPZ w dokumentacji EUROCONTROL oznacza Non-standard Planning Zone**, obszar ograniczeń planowania lotu, a nie automatycznie „No Penetration Zone”. Nie każda struktura jest wojskowa. TRA/TSA/MRT/ATZ i regularne aktywacje służą również rozpoznaniu rutynowych wyjaśnień. [Definicja NPZ — ERNIP, pkt 2.5.5.3](https://www.eurocontrol.int/sites/default/files/2025-11/eurocontrol-ernip-part1-airspace-design-methodology-v3-2.pdf).

Docelowy kontrakt rozszerzonego adaptera: identyfikator i rewizja strefy, geometria i dokładność, dolna/górna granica z jednostką i odniesieniem wysokości, planowany przedział UTC, rzeczywisty status i czas jego zmiany, publikacja/pobranie, podstawa AUP/UUP/NOTAM oraz opis celu, jeśli podany. Stany: `planned`, `active`, `inactive`, `cancelled`, `unknown`; wpis w planie nie wystarcza do `active`. Tożsamość wystąpienia: strefa + okres obowiązywania, z rewizjami zamiast nowych incydentów przy każdym UUP. Brak na niepełnej liście nie dowodzi dezaktywacji. Regularność porównywać co najmniej z zebranym tygodniem; luka w historii daje `routine_status=unknown`, nie „rzadką strefę”.

Dostęp: 29.09 sprawdzono i podłączono publiczny HTML current AUP. Nie potwierdzono kompletności rzeczywistych statusów taktycznych ani opóźnienia. Nie kopiujemy aktywacji z mapy Strażnika.

### Ukraińskie doniesienia powietrzne — bez pośredniego agregatora

Publiczny opis NEPTUN w Strażniku wskazuje agregację OSINT, nie dostęp do radaru. Tak samo poniższe kanały traktujemy jako **publikacje**, dopóki konkretna wiadomość nie udostępnia sprawdzalnego pomiaru. Bezpośredni wydawca może cytować inne źródło; jego wpis nie staje się przez to niezależnym dowodem.

| Kandydat | Adres wydawcy | Status i rola |
|---|---|---|
| `ua_air_force_public` — Siły Powietrzne ZSU | [@kpszsu](https://t.me/kpszsu) | Oficjalny kanał wskazany również w [wykazie ukraińskiego Centrum Przeciwdziałania Dezinformacji](https://cpd.gov.ua/announcement/spysok-bezpechnyh-kanaliv-otrymannya-informacziyi/); komunikaty i odwołania, bez gwarancji surowej telemetrii |
| `ua_monitor_public` — Monitor | [@war_monitor](https://t.me/war_monitor) | Publiczny kanał monitorujący, nieoficjalny; pochodzenie i niezależność każdego doniesienia do ustalenia |
| `ua_vanek_public` — Nikolaevski Vanek | [@vanek_nikolaev](https://t.me/vanek_nikolaev) | Publiczny autor; opis profilu nie potwierdza dostępu radarowego ani kompletności obserwacji |

Priorytet odkrywania: doniesienia o kierunkach na obwody **lwowski i wołyński**, bez utożsamiania ich z kursem na Polskę. Słownik startowy: rakiety manewrujące (`крилаті ракети`, `крылатые ракеты`), balistyka (`балістика`, `баллистика`), Shahed (`Шахед`, `Шахід`, `БпЛА`) oraz starty MiG-31K (`зліт МіГ-31К`, `взлёт МиГ-31К`). Zapisywać też negacje, odwołania, cytowanie i retrospektywę. Samo słowo kluczowe ani start nosiciela nie potwierdzają ataku na Polskę. Opis dla użytkownika jest po polsku; oryginał i cytaty pozostają w archiwum.

Zachowywać identyfikator wiadomości, rewizję, źródło cytowane/przekazane, czas publikacji i zdarzenia z niepewnością, obszar oraz deklarowany kierunek. Nie tworzyć torów, dokładnych współrzędnych ani liczby fizycznych obiektów ze środka miejscowości lub liczby postów. Kanały są kandydatami; dostęp automatyczny i dozwolony sposób przetwarzania wymagają ustalenia według istniejącej [procedury Telegrama](early-warning-design.md#logistyka-i-telegram). Nie uruchomiono sesji ani bota.

<a id="rso-rcb-klasy"></a>

### RSO i RCB — trzy klasy treści ostrzeżeń

**RSO to Regionalny System Ostrzegania**, prowadzony przez MSWiA we współpracy z TVP. Kandydat `rso_public` korzysta z [opisu MSWiA](https://www.gov.pl/web/mswia/regionalny-system-ostrzegania) i wskazanego tam [wykazu obowiązujących komunikatów](https://komunikaty.tvp.pl/komunikaty/wszystkie/wszystkie). TVP jest tu kanałem dystrybucji systemu, nie niezależnym potwierdzeniem. 29.09 podłączono publiczny eksport XML kategorii ogólnej i sprawdzono zgodność liczby rekordów; kompletność historii pozostaje nieustalona.

Pozycja `rcb_alert_semantics` rozszerza przegląd materiałów istniejącego źródła [RCB](https://www.gov.pl/web/rcb/komunikaty). Przyjęto wewnętrzną klasyfikację **treści dotyczących zagrożenia z powietrza**, a nie nowe urzędowe stopnie alarmowe ani domniemanie gotowości bojowej wojska:

| Klasa | Znaczenie | Przykład treści źródłowej |
|---|---|---|
| `L1_monitoring` | Monitorowanie sytuacji / podwyższona uwaga | „Sytuacja jest monitorowana” — [komunikaty RCB](https://www.gov.pl/web/rcb/komunikaty) |
| `L2_readiness` | Wezwanie do czujności i reagowania na alarmy | „Reaguj na syreny alarmowe” — [RCB, 08.09.2026](https://www.gov.pl/web/rcb/alert-rcb---zmasowany-rosyjski-atak-powietrzny-na-ukraine-0809) |
| `L3_shelter` | Bezpośrednie zalecenie znalezienia bezpiecznego miejsca | „Znajdź bezpieczne miejsce” — [RCB, 17.09.2026](https://www.gov.pl/web/rcb/alert-rcb---zagrozenie-z-powietrza-17010) |

Przykłady są historyczne, nie stanowią oceny aktualnego alarmu. Klasyfikacja wymaga pełnej treści, obszaru i czasu obowiązywania; przy niejednoznaczności pozostaje `unknown`. Ćwiczenia, komunikaty pogodowe, odwołania i ostrzeżenia innych domen mają osobne typy. Nie klasyfikujemy ćwiczeń jako L3 na podstawie samego słowa „syrena”; ostrzeżenie o wodzie może wymagać osobnej analizy infrastruktury, lecz nie jest alertem powietrznym.

Ten sam Alert RCB rozesłany przez RSO, gov.pl i media ma jeden `alert_key` i wspólne pochodzenie. Liczy się aktualny stan dla wskazanego obszaru, nie suma kolejnych L1/L2/L3. Odwołanie zachowuje powiązanie i zakres terytorialny; nie wygasza innych, niezwiązanych zdarzeń. Rozbieżność tekstu i metadanych obszaru kieruje do przeglądu, bez zgadywania zakresu. Oficjalne zalecenie pozostaje widoczne niezależnie od odczytu RTB.

### Litwa, Łotwa i Estonia — własne publikacje i komunikaty służb

| Państwo | Media u źródła publikacji | Komunikaty sił zbrojnych | Dostęp sprawdzony 25.09.2026 |
|---|---|---|---|
| Litwa | `lt_lrt`: [LRT](https://www.lrt.lt/en/news-in-english) | `lt_armed_forces`: [Lietuvos kariuomenė](https://kariuomene.lt/en) | LRT: odczyt narzędziowy zablokowany przez robots.txt; witryna sił zbrojnych dostępna |
| Łotwa | `lv_lsm`: [LSM](https://eng.lsm.lv/) | `lv_armed_forces`: [Nacionālie bruņotie spēki](https://www.mil.lv/en/zinas) | Treści obu stron dostępne; angielska sekcja wiadomości używa ścieżki `/en/zinas` |
| Estonia | `ee_err`: [ERR](https://news.err.ee/) | `ee_defence_forces`: [Kaitsevägi](https://mil.ee/en/news/) | Treści obu stron dostępne |

Zakres: incydenty morskie i lotnicze, infrastruktura podmorska i portowa, sabotaż, zakłócenia GNSS oraz określenie „Baltic Jammer”. To ostatnie jest hasłem odkrywania publikacji, nie gotową atrybucją. Oddzielać zdarzenie od ćwiczenia, awarii, komentarza i podsumowania. Istniejący raport VSD/AOTD pozostaje kontekstem okresowym, nie strumieniem taktycznym.

Publikacja redakcji jest pierwotna tylko dla jej własnych ustaleń. Jeśli ERR, LRT lub LSM powtarza komunikat wojska, agencji prasowej lub operatora infrastruktury, zachować to pochodzenie i dotrzeć do wskazanego komunikatu. Nie naliczać redakcji jako kolejnego niezależnego sensora. Każdy z sześciu kandydatów wymaga testu bezpośredniego RSS/API/HTML, praw do wykorzystania, opóźnienia i korekt; dostęp WWW nie jest wdrożonym kolektorem. Blokady LRT nie obchodzimy przez agregator.

## Priorytet uzupełnień

Korekta po komentarzu użytkownika z 23.09.2026: pierwszeństwo ma pilotaż GNSS i logistyki, następnie obserwacje lotnicze po ustaleniu dostępu. Szczegóły, sprawdzone adresy i ograniczenia: `docs/early-warning-design.md`. Oficjalne komunikaty pozostają źródłem weryfikacji, korekt i kontekstu; nie traktujemy ich jako automatycznie bezbłędnych etykiet wyniku. Klasyfikacja sygnału jako wyprzedzającego zależy od czasu i treści, a nie samego wydawcy.

Poniższe źródła uzupełniają warstwę potwierdzeń i kontekstu. Ocena dostępu WWW z 23.09.2026 nie jest testem kolektorów; kolejność w tej tabeli nie zastępuje priorytetu sygnałów wczesnych.

| Kolejność | Źródło | Jaką lukę uzupełnia | Stan |
|---|---|---|---|
| 1 | [Komunikaty polskich służb specjalnych](https://www.gov.pl/web/sluzby-specjalne) | Informacje pierwotne o ujawnionych działaniach, zatrzymaniach i atrybucji | Strona dostępna; adapter do zbudowania. Rozróżniać ustalenia, zarzuty i rozstrzygnięcia |
| 2 | [Dowództwo Operacyjne RSZ](https://www.wojsko-polskie.pl/dorsz/) | Weryfikacja naruszeń przestrzeni i reakcji obronnych | Oficjalny adres zidentyfikowany; bezpośredni dostęp napotkał weryfikację dostępu. Adapter niepodłączony |
| 3 | [CERT Polska — raporty](https://cert.pl/tag/raport-roczny/) | Tło i taksonomia cyberzagrożeń; docelowo także bieżące komunikaty | Strona raportów dostępna w przeglądzie WWW; nie dowodzi naprawienia wcześniejszego 403 kolektora |
| 4 | [Litewska National Threat Assessment 2026](https://www.vsd.lt/en/reports/national-threat-assessment-2026/) | Okresowy kontekst Rosji, Białorusi i regionu bałtyckiego | Publikacja VSD/AOTD; deklarowany stan informacji do 6.02.2026. Nie jest strumieniem incydentów z ostatnich 7 dni |

Oficjalne materiały [NATO o zagrożeniach hybrydowych](https://www.nato.int/cps/fr/natohq/topics_156338.htm?selectedLocale=en) mogą ujednolicić terminologię. Nie zastępują atrybucji konkretnego wydarzenia. Dokumenty pierwotne należy zestawiać z niezależnym pokryciem, a nie traktować wszystkie oficjalne twierdzenia jako bezbłędne.

Przed włączeniem nowego źródła potrzebne są: stabilny dostęp, zapis treści i dat, test parsera na zachowanej próbce, jawna rola required/optional oraz co najmniej jeden rzeczywisty przebieg z oceną pokrycia. Dane lotnicze, GNSS, ruch graniczny i logistyka wymagają również serii odniesienia; bez nich nie oceniamy skali anomalii.

### PAŻP i RSO — pierwsze adaptery v0.3, 29.09.2026

| Źródło bezpośrednie | Wdrożony zakres | Ograniczenie |
|---|---|---|
| [PAŻP — current AUP](https://airspace.pansa.pl/aup/current) | Publiczne tabele HTML planu: oznaczenie strefy, pola wysokości/czasu/użytkownika, ważność i aktualizacja w UTC; 422 wiersze w pierwszej próbie | To plan, nie rejestr rzeczywistej aktywacji. UUP, geometrie i historia zmian nie są jeszcze podłączone |
| [RSO — ogólne, XML](https://komunikaty.tvp.pl/komunikaty/wszystkie/ogolne/0?_format=xml) | Cała dostępna lista kategorii ogólnej, ID, pełna treść, województwa i surowe okresy ważności; 42 rekordy w pierwszej próbie | Bez osobnych strumieni pogodowych/hydrologicznych i bez gwarancji historii. Klasyfikacja treści L1/L2/L3 wymaga przeglądu; rso_alarm nie jest tą klasyfikacją |

Oba adaptery działają w głównym `collect_sources.py` / `analysis_cycle.py`.
Maksymalnie dwa żądania na źródło (wliczając przekierowania i ewentualne jedno ponowienie po błędzie sieci/5xx);
respektują utrwalone Retry-After i wspólny limit odpowiedzi. Parser sprawdza
metadane oraz strukturę PAŻP i liczbę rekordów RSO względem totalItems;
zmiana formatu nie daje pustego poprawnego wyniku. Limity: 1500 wierszy AUP,
500 komunikatów RSO. RSO publikuje daty bez strefy: przyjęto jawnie
Europe/Warsaw, a niejednoznaczność lub luka przy zmianie czasu odrzuca odczyt.
Surowy okres ważności jest nadal przedmiotem przeglądu.

W tabelach PAŻP Y/N nie dowodzi aktywacji. [Instrukcja PAŻP](https://www.pansa.pl/OPS/ops_rpa_pl.htm)
rozróżnia plan AUP i jego aktualizacje; strumień nie potwierdza sam zamiaru
ani rozpoczęcia operacji. Zniknięcie komunikatu z XML RSO nie jest odwołaniem.
Wspólny alert RCB/gov.pl/RSO zachowuje jednego nadawcę i alert_key.

Oryginały i wersje są archiwizowane lokalnie. Material URL wskazuje rzeczywisty
zestaw XML, bez zgadywania adresu szczegółów na podstawie ID. Są to źródła
opcjonalne o zakresie current_official_state_only; poprawna bieżąca lista
nie otwiera bramki 216 godzin historii. Ich awaria jest raportowana.
