# Git — układ pracy od 04.10.2026

Utrzymujemy dwie aktywne gałęzie, obie śledzące swoje odpowiedniki na GitHubie:

- `main` — sprawdzony kod procesu analizy i strony. Główny katalog
  `/Users/milosz/Documents/Codex/OSINT Dashboard` pozostaje na tej gałęzi;
  tutaj są rzeczywista baza, prywatne materiały i konfiguracja wykonawcy.
- `codex/ux-index-history` — jedyna gałąź dalszych prac nad UI, w istniejącym
  worktree `/Users/milosz/.codex/worktrees/rta-regional-ui/OSINT Dashboard`.
  Nie kopiujemy do niego sekretów ani bazy live.

Przed zmianą sprawdź `git status --short --branch` i pobierz `git fetch origin`.
Zmiany UI testuj i zapisuj w jego worktree. Po odbiorze włącz je do `main`,
wyślij na GitHub i osobno wykonaj wymagany proces publikacji strony.
Zapis kodu na GitHubie nie potwierdza wdrożenia ani publikacji raportu.
Poprawki procesu analizy zapisuj w małych commitach po odpowiednich testach;
następnie przenieś aktualny `main` do gałęzi UI, zachowując jej własne zmiany.
Nie przełączaj głównego katalogu w trakcie dobowego cyklu.

## Archiwum

Zakończone gałęzie z GitHuba mają lokalne znaczniki `archive/2026-10-04/remote/*`.
Ich lokalne końcówki mają znaczniki `archive/2026-10-04/local/*`.
Starsze, nigdy niepublikowane historie pozostają wyłącznie lokalnie pod
`private-archive/2026-10-04/*`; nie wysyłaj ich poleceniem `git push --tags`.
Znaczniki pozwalają odtworzyć gałąź przez `git switch -c <nazwa> <znacznik>`.

Pełna lokalna kopia historii sprzed porządków jest w ignorowanym pliku
`data/backups/git-before-cleanup-2026-10-04.bundle`. Zawiera także prywatne
odnośniki robocze; nie publikuj tego pliku. Lista znaczników: `git tag --list`.

Bazy, surowe materiały, sekrety, lokalne uprawnienia `.codex/config.toml`
i zamrożone pakiety raportów pozostają poza Git. Archiwum kodu konkretnego
raportu pozostaje podstawą jego replay, niezależnie od aktualnej gałęzi.

## Odbiór porządków

Kod zapisano przez integrację GitHub; lokalny Git nie miał uwierzytelnienia
HTTPS do push. Obie aktywne gałęzie mają identyczne commity i upstream.
Wszystkie znaczniki archiwalne pozostają lokalne, a kod zakończonych prac
jest w historii `main` (regionalna poprawka ma równoważny commit).

Podczas kontroli pojawiło się 118 nieśledzonych kopii plików z dopiskiem `2`
i nieprawidłowa kopia odnośnika Git. Przeniesiono je bez kasowania do
`data/backups/duplicate-files-2026-10-04/` (z manifestem) oraz
`data/backups/invalid-ui-ref-copy-2026-10-04`. Nie zastąpiono nimi oryginałów.
Źródło powstawania kopii wymaga osobnego ustalenia, jeśli problem wróci;
nie synchronizuj wnętrza `.git` narzędziem kopiującym konflikty plików.
