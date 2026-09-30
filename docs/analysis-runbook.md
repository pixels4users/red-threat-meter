# Silnik analityczny — cykl Codexa

Stan: 29.09.2026. Wykonawcą analizy jest **Codex w tym projekcie**. Nie potrzeba
osobnego klucza do API modelu. Python pobiera materiały, sprawdza kontrakty i
dowody, liczy RTB, zamraża raport oraz publikuje go do Supabase. Codex podejmuje
decyzje analityczne i pisze komentarz na podstawie zapisanych materiałów.

## Uruchomienie

Zlecenie dla Codexa: „Wykonaj pełny dzienny cykl zgodnie z
`agents/analysis-cycle.md`, opublikuj wynik do Supabase i sprawdź odczyt”.
Ta sama instrukcja może być treścią zaplanowanego zadania. Sam skrypt powłoki
nie uruchamia AI; musi być wykonywany wewnątrz zadania agenta.

Instrukcja wykonawcza: [agents/analysis-cycle.md](../agents/analysis-cycle.md).
Konfiguracja: `config/analysis.json`. Polecenie:

```sh
.venv/bin/python scripts/analysis_cycle.py prepare
```

Polecenie zwraca identyfikator cyklu i ścieżkę zamrożonego pakietu do przeczytania.
Kolejne polecenia to `check`, `apply`, `calculate`, `editorial`, `finish`,
`publish`. Wymagane pliki i parametry opisuje instrukcja agenta. Nie uruchamiaj
drugiego pobrania w trakcie oceny. Zmiana materiałów, konfiguracji lub kodu
wymaga nowego cyklu; stare pliki pozostają w archiwum.

OSW pobiera pełne artykuły HTML i podlinkowane raporty PDF oraz uzupełnia do
10 znanych nierozstrzygniętych publikacji spoza RSS. Potrzebne do PDF narzędzia
`pdfinfo` i `pdftotext` są dostępne na tym Macu. Nowa treść wymaga nowej oceny;
awaria nie cofa zapisanej pełnej wersji do skrótu. `content_provenance` w pakiecie
pozwala przejść do archiwalnego HTML/PDF. Dla `pdf_text` oceń też oryginał, jeżeli
ustalenie zależy od tabel lub map. Limity opisuje [rejestr źródeł](sources.md).

`Opublikuj raport.command` nadal uruchamia wcześniejszy kolektor i wydawcę.
Nie wykonuje analizy Codexa i może opublikować odczyt z nierozstrzygniętą kolejką.
Przycisk na stronie odświeża tylko opublikowane wyniki.

## Kontrole przed publikacją

1. Pakiet obejmuje wszystkie nierozstrzygnięte materiały. Obecny limit to
   100 kandydatów i 2 MB. Przekroczenie zatrzymuje cykl, bez cichego pomijania.
2. Każda decyzja wskazuje konkretne wersje źródeł. Cytaty muszą występować
   w zapisanym materiale; daty, miejsce, atrybucja i kryteria mają osobne dowody.
3. Po propozycji Codex wykonuje drugi, jawny przegląd jej znaczenia. To kontrola
   tego samego agenta, nie niezależna weryfikacja faktów ani przegląd człowieka.
4. Wstrzymana decyzja pozostawia materiał nierozstrzygnięty. Wspólne pochodzenie
   publikacji nie zwiększa liczby niezależnych potwierdzeń. Kilka zdarzeń
   w jednym artykule przechodzi razem kontrolę kompletności.
5. Domyślna punktacja to `rtb-v0.3` z kontrolą 216 godzin historii; patrz [kontrakt](v0.3-implementation.md). Braki dają
   `RTB=null`. Pilotaże GNSS, logistyki i ADS-B nie zasilają punktacji.
6. Komentarz wymaga ustaleń dotyczących sytuacji, działań i skutków oraz
   przeglądu dokładnie tych trzech zdań. Nie wystarczy sam indeks. Przy braku
   podstaw komentarz jest pomijany; nie powstaje zapewnienie o bezpieczeństwie.
7. Publikacja jest zakończona dopiero po odczytaniu z Supabase identycznego
   pakietu (`verified_readback=true`). Ponowienie nie tworzy duplikatu.

Kontrole JSON i sumy kontrolne nie dowodzą prawdziwości twierdzeń. Dokumentują
wejścia, decyzje i wersje; semantyczna ocena źródeł pozostaje pracą agenta.
Nie obchodź wstrzymania przez zaznaczenie wszystkich kontroli jako poprawne.

## Archiwum i odtwarzanie

`data/analysis/cycles/<id>/` zawiera pakiet, propozycję, audyt, projekt odczytu,
materiały do komentarza oraz potwierdzenie publikacji. `data/snapshots/<id>/`
zachowuje gotowy raport, wejścia do replay, `analysis-audit.json` i opcjonalny
`commentary-review.json`. Manifest obejmuje także pliki przeglądu.

Do przeglądarki trafia tekst komentarza i ograniczona informacja o jego
pochodzeniu. Surowe materiały, nazwiska wykonawców, propozycje i logi pozostają
lokalnie. Klucz Supabase jest używany wyłącznie przez proces serwerowy.

```sh
.venv/bin/python -m pytest
.venv/bin/python scripts/replay_run.py IDENTYFIKATOR_WYDANIA
```

Testy pełnego cyklu używają odseparowanej bazy i fikcyjnych danych; publikacja
takiego pakietu do live jest blokowana. Replay wymaga zachowanej wersji kodu.

Dla odbioru z 29.09 zapisano również 90 plików kodu, schematów, instrukcji
i zależności w `data/analysis/code/<code_hash>/`, z osobnym manifestem.
Odtworzenie z tej kopii dało identyczny wynik. Ścieżka i potwierdzenie są
w `data/analysis/current-verification.json`. To lokalne archiwum kodu;
nie zastępuje kopii danych na innym nośniku. Przed kolejną zmianą kodu zachowaj
wersję potrzebną do odtworzenia wcześniejszych wydań.

## Harmonogram i strona WWW

Harmonogram nie został jeszcze włączony. Lokalny wariant zadania potrzebuje
włączonego Maca i działającej aplikacji Codex. Zadanie chmurowe ChatGPT nie
otrzymuje automatycznie dostępu do tego folderu, bazy SQLite ani lokalnych
sekretów. Warunki opisuje [dokumentacja zadań](https://learn.chatgpt.com/docs/automations).

Dashboard lokalny pobiera publikacje z Supabase co 30 sekund. Produkcyjny
hosting aplikacji nadal wymaga adaptera serwerowego i kontroli dostępu;
wcześniej opublikowany Design System jest osobną wizualizacją.
