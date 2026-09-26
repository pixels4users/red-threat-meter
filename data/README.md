# Dane lokalne

Zawartość robocza tego katalogu jest wyłączona z Git. Kod, konfiguracja i dokumentacja są wersjonowane osobno.

- `raw/`: niezmienne kopie odpowiedzi źródeł z nazwami opartymi na hashach.
- `database/osint.sqlite3`: lokalna baza i tabele historii, SQLite WAL.
- `runs/<id>/review_queue.json`: zamrożona kolejka przeglądu utworzona przez dany przebieg.
- `reviews/`: wejściowe pakiety ocen.
- `snapshots/<id>/`: raport, JSON, GeoJSON, zamrożone wejścia do replay i manifest sum kontrolnych.
- `latest.json`: wskazanie ostatniego spójnego wydania; wcześniejsze pozostają w archiwum.
- `backups/`: kopie bazy z manifestem; nie zastępują kopii plików surowych i raportów.
- `demo/`: osobne dane syntetyczne, jeśli uruchomiono `--fixture`.
- `.mode.json`: zabezpieczenie przed mieszaniem danych live i fixture.
- `doctrine_rag/`: lokalne PDF-y kontekstu; nie trafiają do kolejki incydentów.
- `doctrine_index/`: niezmienne wydania indeksu tekstowego stron PDF i wskaźnik latest.json; to indeks referencyjny, nie baza zdarzeń.
- `briefs/`: osobne interpretacje analityka według docs/templates/analytical-brief.md, ze wskazaniem run_id raportu. Katalog powstaje przy zapisaniu pierwszego briefu.
- `early_warning/`: osobny działający pilotaż GNSS/logistyki: `raw/`, `database/observations.sqlite3`, `reviews/`, `translations/`, `snapshots/`, `backups/`, `latest.json` i `.mode.json`. Nie wchodzi do bazy ani punktacji RTB. Wersje pomiarów, publikacji, polskich opisów, kolejne pobrania i oceny są dopisywane. Oryginały pozostają w języku źródła. Obsługa i kopie: `docs/early-warning-runbook.md`.
- `research/aviation-access-2026-09-23/`: odpowiedź jednorazowego testu OpenSky, specyfikacja WorldMonitor i metadane jednego archiwum ADSB.lol. To materiały oceny dostępu, poza bieżącymi obserwacjami i RTB. Nie oznaczają działającego kolektora lotniczego.
- `aviation/`: odrębny pilotaż ADSB.lol: `raw/adsblol/`, `database/aviation.sqlite3`, `snapshots/`, `latest.json`, `request-state.json` i `.mode.json`. Próbki i raporty są dopisywane. GeoJSON zawiera agregaty pól; surowe odpowiedzi i diagnostyczny JSON pozostają lokalne. Obsługa i kopie: `docs/aviation-runbook.md`. Dane nie zmieniają RTB ani GNSS/logistyki.
- `research/aviation-pilot-2026-09-24/`: aktualna specyfikacja ADSB.lol i wstępny odczyt pojedynczego koła, wraz z czasem i hashami. Ten odczyt badawczy nie jest dodatkową próbką czterech obszarów w bazie pilotażu.
- `aviation_history/`: audyt wybranych okien historii ADSB.lol, osobny od próbek API. Niezmienne `raw/`, potwierdzenia `collections/`, raporty `snapshots/`, wskaźniki `latest-collection.json` i `latest.json`, blokada `request-state.json`, tryb `.mode.json` oraz kopie `backups/`. Nie wymaga nowej bazy SQLite. GeoJSON zawiera agregaty; surowe pliki i zbiory identyfikatorów do porównania pozostają lokalnie. Obsługa: `docs/aviation-history.md`.
- `research/aviation-history-2026-09-24/`: dowody formatu i dostępu do historii — strona i kod mapy, kod producenta, metadane archiwum, potwierdzenia pobrań i test odtworzenia kopii. Nie są niezależnym źródłem obserwacji wobec ADSB.lol.

Nie wystawiaj katalogu `data/` jako publicznego serwera plików. Przyszła strona otrzyma osobny eksport. Instrukcja odtwarzania: `docs/runbook.md`.
