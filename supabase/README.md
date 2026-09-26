# Supabase — stan integracji

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
- Supabase może udostępniać opublikowane wyniki, historię i dostęp użytkowników dla dashboardu. Model tabel, uprawnienia RLS i zapis danych wymagają zaprojektowania oraz wdrożenia. Obecny proces nadal korzysta z lokalnego SQLite.
- Kolektory i analiza Python potrzebują własnego wykonawcy. Połączenie gałęzi GitHub z Supabase nie uruchamia istniejących skryptów.
- Frontend wymaga osobnego zbudowania i hostingu. Aktualizacja jego kodu oraz aktualizacja danych to osobne procesy.

## Połączenie GitHub i późniejsze wdrożenia

Według [dokumentacji integracji Supabase](https://supabase.com/docs/guides/deployment/branching/github-integration), sprawdzonej 26.09.2026:

1. Zapisane połączenie można sprawdzić w **Project Settings → Integrations → GitHub**. Repozytorium i katalog `.` są już ustawione; nie twórz drugiej integracji.
2. Przed włączeniem **Deploy to production** porównaj rzeczywisty schemat projektu z zatwierdzonymi migracjami w repozytorium. Jeśli projekt ma już tabele, najpierw zachowaj jego schemat jako punkt wyjścia.
3. Przy późniejszym uruchamianiu wdrożeń ustaw **Production branch name** na `main`. Widoczna w nagłówku panelu gałąź Supabase „main / Production” nie potwierdza ustawienia tej opcji GitHub.
4. Wdrażanie automatycznych gałęzi pozostaje opcjonalne; nie uruchamiaj go tylko po to, aby połączyć repozytorium. Ten etap nie zamawia dodatkowych środowisk ani zmiany planu.

Na tym etapie w `supabase/` nie ma migracji, zdefiniowanych funkcji ani bucketów. Katalog `migrations/` w głównym katalogu projektu zawiera migracje **SQLite** istniejącego pilotażu; nie należy kopiować ich do `supabase/migrations/` ani wykonywać w PostgreSQL.

Integracja może wdrażać nowe migracje PostgreSQL, zadeklarowane Edge Functions i buckety Storage po zmianach na gałęzi produkcyjnej. Nie przenosi automatycznie danych z lokalnego SQLite. Edge Functions używają środowiska Deno/TypeScript; nie wykonają obecnego projektu Python bez osobnej adaptacji. [Zakres funkcji Supabase](https://supabase.com/docs/guides/functions).

## Sekrety i odtwarzanie

Identyfikator projektu i adres repozytorium nie są hasłami. Hasła bazy, tokeny dostępu oraz klucze administracyjne muszą pozostać w lokalnym magazynie poświadczeń lub sekretach wykonawcy, poza Git i frontendem. `supabase/.temp/` i `.branches/` są wykluczone z repozytorium; logowanie i połączenie z chmurą są osobnymi operacjami.

Wcześniejsza historia rozwoju i dane pilotażu pozostają lokalnie. Historyczne identyfikatory commitów podane w raportach odnoszą się do zachowanego repozytorium lokalnego i kopii kodu; pierwsza publikacja przez integrację GitHub udostępnia bieżący stan plików. Integralność istniejących wydań nadal sprawdza lokalny replay.
