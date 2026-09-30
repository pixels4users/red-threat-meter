# Supabase — stan integracji

## Cykl z przeglądem Codexa — 29.09.2026

Opublikowano i odczytano identycznie nowy raport:
`rpt_802bad8ad62333dcbb527032428b9fb62e1e1995e1f8d81b30423020ce9c47fd`.
Stan analizy: `2026-09-29T15:41:02+00:00`; publikacja:
`2026-09-29T15:41:20.112614+00:00`. RTB jest `null` z powodu czterech
nierozstrzygniętych materiałów OSW; 46 materiałów przeszło przegląd Codexa.

Historia zawiera trzy rzeczywiste wydania. Powtórny zapis nie dodaje raportu,
a lokalne API zwraca ten sam pakiet co Supabase. Potwierdzenie:
`data/analysis/current-verification.json`. Nie zmieniono migracji, RLS,
uprawnień ani dostępu odbiorców. Nie podłączono osobnego API modelu.

Pełny proces uruchamia Codex według `../agents/analysis-cycle.md`;
`scripts/analysis_cycle.py publish` kończy go dopiero po sprawdzeniu odczytu.
Prywatne dowody i audyty pozostają lokalnie. Harmonogram i hosting nowej
aplikacji nie są jeszcze uruchomione.

## Publikacje dashboardu — 27.09.2026

W projekcie `dubhsimiblpfcaudbvjb` wdrożono przez SQL Editor migrację
`migrations/20260927170000_dashboard_publications.sql`. Przed zmianą widok
schematu potwierdzał pusty `public`. Po zmianie zapytanie do `pg_class` i
`pg_policies` potwierdziło cztery tabele: `dashboard_reports`,
`dashboard_report_incidents`, `dashboard_report_sources`, `dashboard_readers`.
Każda ma włączone RLS i jedną politykę odczytu. Utworzono także RPC
`dashboard_publish` i blokady zmiany/usuwania historii. Kontrola przed pierwszą
publikacją potwierdziła: 0 raportów, 0 czytelników, brak uprawnień
`anon` do odczytu i publikacji, uprawnienie `service_role` do wykonania RPC.

Migrację przetestowano wcześniej w lokalnym PostgreSQL/PGlite: atomowa
publikacja, odrzucenie danych fixture, ponowienie, brak dostępu anonimowego,
odczyt tylko dla dopuszczonego użytkownika oraz niezmienność historii.
Następnie wykonano opisany poniżej test na rzeczywistych raportach w Supabase.

**Połączenie wykonawcy działa.** Użytkownik udostępnił token do logowania CLI.
Zalogowano CLI i potwierdzono dostęp do wskazanego projektu. Klucz serwerowy
zapisano w `.env.dashboard` z uprawnieniami `600`; plik i dane połączenia
w `supabase/.temp/` są wyłączone z Git. Wcześniejsza blokada odczytu panelu
połączenia w przeglądarce została rozwiązana oficjalnym logowaniem CLI,
bez pobierania poświadczeń przez przeglądarkę.

Po porównaniu schematu powiązano repozytorium z projektem i odnotowano ręcznie
wykonaną migrację jako zastosowaną. Wykonane polecenia:

```sh
supabase link --project-ref dubhsimiblpfcaudbvjb
supabase migration repair 20260927170000 --status applied --linked
supabase migration list --linked
```

`migration list` potwierdziło wersję `20260927170000` po obu stronach. Nie
uruchamiaj ponownie tej migracji ani naprawy jej historii. Nowe migracje
dodajemy w kolejnych plikach; zastosowanej wersji nie edytujemy.

## Odbiór rzeczywistych danych — 27.09.2026, 20:20 czasu Warszawy

Do prywatnej historii opublikowano dwa rzeczywiste raporty: zweryfikowane
wydanie historyczne z 23.09 oraz nowy wynik ręcznego cyklu. Bieżący cykl
pobrał 54 publikacje: RCB 20, MON 14, OSW 10 i Naval News 10. Wszystkie cztery
kolektory zwróciły `ok`; trzy wymagane źródła są gotowe.

Najnowszy raport w tamtym odbiorze: `rpt_5ca790fc3cfe68ef038d09f03346b0f5c3d8bbd42a972b173150621a87e81de6`.
Stan analizy: `2026-09-27T18:20:41+00:00`; publikacja:
`2026-09-27T18:20:42.116795+00:00`. Tryb `live`, metodologia `rtb-v0.2`.
RTB pozostaje `null` z powodu `unreviewed_candidates` — 32 materiały wymagają
przeglądu. Nie zastąpiono tego stanu wynikiem testowym ani zapewnieniem bezpieczeństwa.

Potwierdzono identyczność eksportu, pakietu odczytanego z Supabase i odpowiedzi
lokalnego API. Ponowny zapis tego samego raportu zwrócił `created=false`, a
historia zachowała dwa wydania. Otwarty dashboard sam zmienił datę odczytu
z 23.09 na 27.09 i dostępność wymaganych źródeł z 0/3 na 3/3, bez przeładowania.
Potwierdzenie techniczne: `data/dashboard/cloud-verification.json` (poza Git).
Dane syntetyczne nie trafiły do chmury. Lista `dashboard_readers` pozostaje pusta;
lokalny odczyt jest realizowany wyłącznie przez proces serwerowy.

Gotowe pliki: `config/dashboard.json`, `schemas/dashboard/report.schema.json`,
`scripts/publish_dashboard.py`, `scripts/serve_dashboard.py` i `web/`.
Kontrakt i obsługa: `../docs/dashboard-data-contract.md`,
`../docs/dashboard-runbook.md`. Lokalny frontend korzysta z serwerowego API;
nie zawiera klucza Supabase. Wcześniejsza publikacja Sites pozostaje statyczną
wizualizacją, bez podmiany na niedokończone wdrożenie chmurowe.

## Wcześniejsza konfiguracja GitHub — 26.09.2026

Stan zweryfikowany w zalogowanym panelu 26.09.2026: projekt `red-threat-meter` (`dubhsimiblpfcaudbvjb`) ma status **Healthy**, a integracja GitHub wskazuje `pixels4users/red-threat-meter` i katalog roboczy `.`. Połączenie było już zapisane przez użytkownika. **Deploy to production** i **Automatic branching** są wyłączone. Nie wykonano migracji, wdrożenia funkcji ani zapisu danych projektu przez tę integrację.

Konfigurację lokalną wygenerowano przez Supabase CLI 2.117.0. Sesja panelu WWW nie loguje automatycznie CLI; lokalny proces nadal korzysta z SQLite. Nie wykonano testu bezpośredniego połączenia PostgreSQL. Widok „No migrations” nie jest dowodem pustej bazy — przed pierwszym wdrożeniem trzeba odczytać rzeczywisty schemat.

| Ustawienie | Wartość |
|---|---|
| Repozytorium | [pixels4users/red-threat-meter](https://github.com/pixels4users/red-threat-meter) |
| Docelowa gałąź GitHub dla wdrożeń | `main`; pole **Production branch name** jest obecnie puste i nieaktywne przy wyłączonym wdrażaniu |
| Projekt chmurowy wskazany przez użytkownika | `dubhsimiblpfcaudbvjb` |
| Panel projektu | [Supabase Dashboard](https://supabase.com/dashboard/project/dubhsimiblpfcaudbvjb) |
| Katalog roboczy integracji GitHub | `.` — ten katalog zawiera `supabase/` |
| Automatyczne wdrożenia | Wyłączone |
| Automatyczne gałęzie podglądu | Wyłączone; bieżący panel planu Free wymaga zmiany planu do ich włączenia |
| `project_id` w `config.toml` | `red-threat-meter` — nazwa lokalnego środowiska, nie potwierdzenie połączenia z projektem chmurowym |

## Rola poszczególnych elementów

- GitHub przechowuje kod, testy, instrukcje i przyszłe migracje. Nie przechowuje roboczych baz SQLite, surowych materiałów ani sekretów.
- Supabase przechowuje oczyszczone publikacje i historię dashboardu w tabelach opisanych powyżej. Proces analityczny i archiwum dowodów nadal korzystają z lokalnego SQLite. Pełny cykl wykonawcy i lokalnego dashboardu z Supabase został sprawdzony 27.09.2026.
- Kolektory i analiza Python potrzebują własnego wykonawcy. Połączenie gałęzi GitHub z Supabase nie uruchamia istniejących skryptów.
- Frontend wymaga osobnego zbudowania i hostingu. Aktualizacja jego kodu oraz aktualizacja danych to osobne procesy.

## Połączenie GitHub i późniejsze wdrożenia

Według [dokumentacji integracji Supabase](https://supabase.com/docs/guides/deployment/branching/github-integration), sprawdzonej 26.09.2026:

1. Zapisane połączenie można sprawdzić w **Project Settings → Integrations → GitHub**. Repozytorium i katalog `.` są już ustawione; nie twórz drugiej integracji.
2. Przed włączeniem **Deploy to production** porównaj rzeczywisty schemat projektu z zatwierdzonymi migracjami w repozytorium. Jeśli projekt ma już tabele, najpierw zachowaj jego schemat jako punkt wyjścia.
3. Przy późniejszym uruchamianiu wdrożeń ustaw **Production branch name** na `main`. Widoczna w nagłówku panelu gałąź Supabase „main / Production” nie potwierdza ustawienia tej opcji GitHub.
4. Wdrażanie automatycznych gałęzi pozostaje opcjonalne; nie uruchamiaj go tylko po to, aby połączyć repozytorium. Ten etap nie zamawia dodatkowych środowisk ani zmiany planu.

W `supabase/migrations/` jest migracja publikacji PostgreSQL z 27.09.2026.
Nie utworzono bucketów ani Edge Functions. Katalog `migrations/` w głównym
katalogu projektu zawiera osobne migracje **SQLite** pilotażu; nie należy
kopiować ich do `supabase/migrations/` ani wykonywać w PostgreSQL.

Integracja może wdrażać nowe migracje PostgreSQL, zadeklarowane Edge Functions i buckety Storage po zmianach na gałęzi produkcyjnej. Nie przenosi automatycznie danych z lokalnego SQLite. Edge Functions używają środowiska Deno/TypeScript; nie wykonają obecnego projektu Python bez osobnej adaptacji. [Zakres funkcji Supabase](https://supabase.com/docs/guides/functions).

## Sekrety i odtwarzanie

Identyfikator projektu i adres repozytorium nie są hasłami. Hasła bazy, tokeny dostępu oraz klucze administracyjne muszą pozostać w lokalnym magazynie poświadczeń lub sekretach wykonawcy, poza Git i frontendem. `supabase/.temp/` i `.branches/` są wykluczone z repozytorium; logowanie i połączenie z chmurą są osobnymi operacjami.

Wcześniejsza historia rozwoju i dane pilotażu pozostają lokalnie. Historyczne identyfikatory commitów podane w raportach odnoszą się do zachowanego repozytorium lokalnego i kopii kodu; pierwsza publikacja przez integrację GitHub udostępnia bieżący stan plików. Integralność istniejących wydań nadal sprawdza lokalny replay.

## Migracja v0.3 — 29.09.2026

Zastosowano `20260929190000_rtb_v03_numeric_score.sql`: score ma typ numeric,
a funkcja publikacji zachowuje części ułamkowe. Historyczne payloady,
niezmienność wydań, RLS i role pozostają bez zmian. Próba lokalna PostgreSQL
sprawdziła zapis 12,5 wyłącznie w pamięci PGlite; dane syntetyczne nie trafiły do chmury.

Pierwsze rzeczywiste wydanie v0.3: cykl `2026-09-29T172300Z-57d7b9f6`, stan
29.09.2026 19:27 czasu Warszawy. Odczyt po publikacji jest identyczny z eksportem.
RTB pozostaje null: niewystarczająca historia 216 godzin i nierozstrzygnięty
materiał OSW. Samo wdrożenie obliczeń nie usuwa tych braków.
