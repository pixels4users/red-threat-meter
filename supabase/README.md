# Supabase — przygotowanie integracji

Stan na 26.09.2026: konfiguracja lokalna wygenerowana przez Supabase CLI 2.117.0. Nie wykonano logowania, połączenia z bazą, migracji ani wdrożenia funkcji. Dostęp do projektu wymaga zalogowania przez właściciela; sam identyfikator nie potwierdza jego stanu.

| Ustawienie | Wartość |
|---|---|
| Repozytorium | [pixels4users/red-threat-meter](https://github.com/pixels4users/red-threat-meter) |
| Docelowa gałąź produkcyjna | `main` |
| Projekt chmurowy wskazany przez użytkownika | `dubhsimiblpfcaudbvjb` |
| Panel projektu | [Supabase Dashboard](https://supabase.com/dashboard/project/dubhsimiblpfcaudbvjb) |
| Katalog roboczy integracji GitHub | `.` — ten katalog zawiera `supabase/` |
| `project_id` w `config.toml` | `red-threat-meter` — nazwa lokalnego środowiska, nie potwierdzenie połączenia z projektem chmurowym |

## Rola poszczególnych elementów

- GitHub przechowuje kod, testy, instrukcje i przyszłe migracje. Nie przechowuje roboczych baz SQLite, surowych materiałów ani sekretów.
- Supabase może udostępniać opublikowane wyniki, historię i dostęp użytkowników dla dashboardu. Model tabel, uprawnienia RLS i zapis danych wymagają zaprojektowania oraz wdrożenia. Obecny proces nadal korzysta z lokalnego SQLite.
- Kolektory i analiza Python potrzebują własnego wykonawcy. Połączenie gałęzi GitHub z Supabase nie uruchamia istniejących skryptów.
- Frontend wymaga osobnego zbudowania i hostingu. Aktualizacja jego kodu oraz aktualizacja danych to osobne procesy.

## Połączenie GitHub

Według [dokumentacji integracji Supabase](https://supabase.com/docs/guides/deployment/branching/github-integration), sprawdzonej 26.09.2026:

1. Po publikacji kodu zaloguj się do wskazanego projektu i otwórz **Project Settings → Integrations → GitHub**.
2. Wybierz `pixels4users/red-threat-meter`, gałąź produkcyjną `main` i katalog roboczy `.`. Nazwy opcji mogą zależeć od wersji panelu.
3. Przed włączeniem **Deploy to production** porównaj rzeczywisty schemat projektu z zatwierdzonymi migracjami w repozytorium. Jeśli projekt ma już tabele, najpierw zachowaj jego schemat jako punkt wyjścia.
4. Wdrażanie automatycznych gałęzi pozostaje opcjonalne; nie uruchamiaj go tylko po to, aby połączyć repozytorium. Ten etap nie zamawia dodatkowych środowisk.

Na tym etapie w `supabase/` nie ma migracji, zdefiniowanych funkcji ani bucketów. Katalog `migrations/` w głównym katalogu projektu zawiera migracje **SQLite** istniejącego pilotażu; nie należy kopiować ich do `supabase/migrations/` ani wykonywać w PostgreSQL.

Integracja może wdrażać nowe migracje PostgreSQL, zadeklarowane Edge Functions i buckety Storage po zmianach na gałęzi produkcyjnej. Nie przenosi automatycznie danych z lokalnego SQLite. Edge Functions używają środowiska Deno/TypeScript; nie wykonają obecnego projektu Python bez osobnej adaptacji. [Zakres funkcji Supabase](https://supabase.com/docs/guides/functions).

## Sekrety i odtwarzanie

Identyfikator projektu i adres repozytorium nie są hasłami. Hasła bazy, tokeny dostępu oraz klucze administracyjne muszą pozostać w lokalnym magazynie poświadczeń lub sekretach wykonawcy, poza Git i frontendem. `supabase/.temp/` i `.branches/` są wykluczone z repozytorium; logowanie i połączenie z chmurą są osobnymi operacjami.

Wcześniejsza historia rozwoju i dane pilotażu pozostają lokalnie. Historyczne identyfikatory commitów podane w raportach odnoszą się do zachowanego repozytorium lokalnego i kopii kodu; pierwsza publikacja przez integrację GitHub udostępnia bieżący stan plików. Integralność istniejących wydań nadal sprawdza lokalny replay.
