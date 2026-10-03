# Dashboard online — hosting i domena

Stan: 03.10.2026. Właściwy frontend **B — Chronologia z historią indeksu i wyborem regionu** działa pod adresem
[Red Threat Alert](https://red-threat-alert.michalomski.chatgpt.site).
Projekt Sites: `appgprj_6abe3ae4ab688191ade3a1f128a64451`.
Dostęp jest publiczny od 01.10.2026 na wyraźne polecenie użytkownika.
Adres docelowy: [redthreatalert.pl](https://redthreatalert.pl).
Design System pozostaje osobnym projektem.

## Osobne tło komentarza — 03.10.2026

Wersja Sites **19**, deployment `appgdep_6ac10d00d7b481918a564f61a4b65d2d`,
źródło Sites `39bb28b32c3e0f6d47b795cce69590422cd14eec`.
Publikacja zakończona `succeeded` o 14:11:30 UTC. Wspólny wariant
`.r-card.r-card--inset` wydziela komentarz neutralnym tłem i odstępami;
panel bez komentarza jest ukryty. Dostęp publiczny i konfiguracja bez zmian.

Sprawdzono build frontendu i Workera, lokalne szerokości 1440 i 320 px,
jasny i ciemny wygląd oraz zmianę komentarza wraz z datą raportu.
Brak poziomego przepełnienia strony i błędów konsoli.
Podgląd: `output/rta-commentary-panel-2026-10-03.jpg`.

## Historia indeksu i wspólna karta — 03.10.2026

Wersja Sites **18**, deployment `appgdep_6ac10820177081919dacc18eaa733d58`,
źródło minimalnego repozytorium Sites `e9c8dcb3fc3572140e04dafdd75e76d937c343cb`.
Publikacja zakończona `succeeded` o 13:50:41 UTC. Dostęp pozostaje publiczny,
domena `redthreatalert.pl` i konfiguracja odczytu Supabase bez zmian.

Zaakceptowane commity `25c6df2` i `ef2256d` włączono do `codex/analysis-runtime`.
Commit `5de73aa` dodaje wspólny komponent `ui/components/card.css` do listy
plików kopiowanych do minimalnego repozytorium Sites. Pakiet nadal pomija
dane analityczne, klucze i historyczne makiety. Obie gałęzie są na GitHubie.

Sprawdzono 31 testów frontendu/bazy, 14 testów adaptera oraz build z minimalnego
repozytorium. W publicznym interfejsie najnowszy raport z 03.10, 13:05 pokazuje
indeks 2,2, pewność 22% i liczniki 36 / 3 / 4. Wybór 02.10, 09:25 zmienia je
na 2,7, 25% i 16 / 2 / 3, razem z komentarzem, osią oraz punktami mapy.
Powrót przywraca najnowszy raport. Konsola bez ostrzeżeń i błędów.

Dowód: `data/sites/index-history-card-verification-2026-10-03.json`.
Nie uruchamiano nowego cyklu analitycznego, nie zapisywano nowych raportów,
nie zmieniano harmonogramu ani metodologii. Kolejne publikacje w Supabase
automatycznie zasilają ten sam interfejs.

## Zgodność regionalnego interfejsu — 03.10.2026

Wersja Sites **15**, deployment `appgdep_6ac0e019f0988191802d218993193def`,
źródło minimalnego repozytorium Sites `30f1b0ed93f29946f486d937396b76f273c94b22`.
Publikacja zakończona `succeeded`. Frontend i Worker przyjmują opcjonalne
metadane `signals-v1` z eksportera `dashboard-export-v5` oraz stare raporty.
W paczce builda znajduje się wspólna taksonomia `config/signal-presentation.json`.

Najpierw wdrożono zgodny odczyt i sprawdzono poprzedni raport, potem
zaktualizowano kod w katalogu harmonogramu i opublikowano nowe dane z 13:05.
Publiczne API zwróciło pakiet identyczny z zamrożonym eksportem, a Supabase
potwierdziło `verified_readback=true`. Nie była potrzebna migracja tabel,
zmiana domeny, sekretów ani uprawnień. Codzienna publikacja nadal zmienia
dane w Supabase; nie wymaga nowego wdrożenia frontendu.

Sprawdzono wybór regionu, liczniki, mapę, czytnik raportu v0.2 i mobilny
widok 390 × 844. Wyniki i granice testu:
`data/sites/regional-ui-verification-2026-10-03.json`.
Instrukcje dotyczące pierwotnej publikacji i domeny poniżej zachowują
daty historycznych wdrożeń.

## Przepływ danych

Codex wykonuje analizę lokalnie → wydawca zapisuje oczyszczony raport w
Supabase → serwer strony odczytuje publikację → przeglądarka pokazuje wynik,
oś czasu, mapę, dziennik i archiwum. Otwarta strona sprawdza nowy raport
co 30 sekund. Publikacja raportu nie wymaga nowego wdrożenia kodu strony.

Hosting działa niezależnie od Maca. **Tworzenie kolejnych analiz nadal wymaga
włączonego Maca i Codexa**: [harmonogram](automation-runbook.md) działa o 09:00
czasu Warszawy. Awaria analizy nie zmienia daty poprzedniej publikacji.
Próg nieaktualności to 30 godzin.

## Granica dostępu

`hosting/worker.mjs` obsługuje odczyt ustalonych ścieżek `/api/` z tabeli
`dashboard_reports` w przypiętym projekcie Supabase. Nie ma dowolnego proxy,
SQL, RPC ani zapisu z przeglądarki. Odbiorca otrzymuje tylko `dashboard-v1`,
bez surowego archiwum, prywatnych ocen i pełnych siatek GNSS.

Runtime Sites ma `SUPABASE_URL` i sekretny `SUPABASE_SECRET_KEY`. Klucz pozostaje
na serwerze; nie jest kluczem o uprawnieniach wyłącznie do odczytu. Ograniczenie
operacji egzekwuje adapter. RLS bazy nie zmieniono. Polityka Sites obejmuje
stronę i jej API. Publiczne udostępnienie jest osobną zmianą, nie skutkiem DNS.

Wydawca Python sprawdza hash zawartości, dowody i przegląd komentarza.
Adapter hostingu sprawdza zamknięty JSON Schema 2020-12, tryb live, tożsamość
rekordu, daty, adresy źródeł i spójność mapy oraz komentarza. Nie przelicza
sumy kontrolnej serializacji Python w JavaScript. Walidator AJV jest kompilowany podczas
budowania; serwer nie kompiluje kodu dynamicznie. Błąd odczytu zwraca HTTP 503,
bez zastępczego raportu i bez treści wyjątku.

## Budowanie i kolejne wdrożenia

Główne repozytorium pozostaje w GitHub. `.openai/hosting.json` zachowuje
tożsamość dashboardu. Minimalny checkout Sites w ignorowanym
`data/sites/dashboard-source/` zawiera frontend, adapter, schemat i konfigurację
odczytu. Nie zawiera bazy, materiałów źródłowych, skilli ani kluczy.

Kontrola lokalna z katalogu głównego:

```sh
npm ci
npm test
npm run test:site
npm run build:site
node scripts/serve_hosted_dashboard.mjs
```

Ostatnie polecenie uruchamia zbudowany Worker na `127.0.0.1:8770`, z prywatną
konfiguracją `.env.dashboard`. Zwykły build i serwer Python pozostają dostępne.

Przy następnej publikacji Codex używa skilli Sites:

1. Odczytaj manifest i ten sam projekt; nie twórz kolejnego Site.
2. Przed edycją otwórz istniejący checkout przez `site-workflow.mjs`,
   zachowując wynik jako `source`.
3. W katalogu głównym wykonaj `node scripts/stage_site_source.mjs`.
   Zainstaluj zmienione zależności checkoutu przez helper Sites.
4. W checkoutcie uruchom workflow z `source`, pozostałymi testami/budowaniem
   i ścieżką archiwum. Helper buduje `dist/client` i `dist/server/index.js`,
   zapisuje commit, wysyła źródło i pakuje dokładnie tę wersję.
5. Przekaż zwrócone `project_id`, `commit_sha` i `archive` do natywnej
   publikacji Sites. Zachowaj obecną grupę odbiorców. Wymagaj końcowego
   `status=succeeded`; przy błędzie kontynuuj ten sam projekt i wersję.
   Sekrety konfiguruj wyłącznie jako runtime secrets, poza kodem i logami.

Pierwsze wdrożenie: źródło Sites
`93b4f59881ab7d8f3ac7bff1a50b8436644ca9f0`,
deployment `appgdep_6abe3d6018a48191973b748622ea21ef`, runtime revision 1.
Natywna publikacja zakończyła się powodzeniem. Lokalnie sprawdzono rzeczywisty
odczyt, archiwum 12 raportów i pobieranie identycznego JSON. Przeszło 12 testów
adaptera oraz 7 testów frontendu/bazy. Paczka nie zawiera kluczy.
Dowód: `data/sites/deployment-verification-2026-10-01.json`.

Naprawa produkcyjna 01.10.2026: runtime odrzucał `redirect: 'error'` błędem
TypeError przed wysłaniem zapytania. Używamy `manual` i odrzucamy wszystkie
odpowiedzi 3xx: klucz nie jest przekazywany do adresu przekierowania.
Lokalny test Node nie wykrył pierwotnej niezgodności środowisk; dodano test
transportu i zakazu podążania za przekierowaniem. Przechodzi 14 testów adaptera.
Anonimowy odczyt produkcyjny potwierdził HTTP 200, raport z 01.10 o 12:12
(Warszawa), RTB 3, pewność 22%, 74 wpisy, archiwum 12 raportów i zgodność
pobranego JSON. Zweryfikowano widok raportu oraz menu mobilne w przeglądarce.
Źródło Sites: `89fe895e1702cf5d0252bd491ef81eb5fcec589f`,
deployment: `appgdep_6abe5fbdc2c48191a643aacb947b4ccb`, wersja 5,
runtime revision 1, public access revision 2.
Dowód: `data/sites/public-report-verification-2026-10-01.json`.

Przyciski „Postaw kawę” w nawigacji, menu mobilnym i stopce prowadzą do
`https://buycoffee.to/red-threat-meter`. Korzystają z neutralnych stylów
Design Systemu, bez zewnętrznego skryptu ani obrazka. Otwierają nową kartę
z `rel="noopener noreferrer"`.

## Domena redthreatalert.pl — aktywna od 01.10.2026

Delegacja DNS wskazuje `dns.home.pl`, `dns2.home.pl` i `dns3.home.pl`.
Przypisanie Sites `appgdom_6abe3d9d5ca88191a10d7a890f470322` ma status `active`,
podobnie certyfikat HTTPS. Adres: [redthreatalert.pl](https://redthreatalert.pl).
W zalogowanym panelu home.pl dodano dwa rekordy A i dwa TXT. Lista była pusta;
kontrola DNS nie wykazała wcześniejszych rekordów A, AAAA, MX ani TXT domeny
głównej. Delegacja DNS pozostała bez zmian. W chwili podłączania domeny dostęp
Sites był prywatny; później zmieniono go na publiczny zgodnie z opisem powyżej.
Potwierdzenie: `data/sites/domain-verification-2026-10-01.json`.
Zastosowane wartości otrzymane z Sites:

| Typ | Pełna nazwa | Wartość |
|---|---|---|
| A | `redthreatalert.pl` | `162.159.143.30` |
| A | `redthreatalert.pl` | `172.66.3.26` |
| TXT | `_openai-site-verification.redthreatalert.pl` | `openai-site-verification=HeQmYnqBe8es6HFS0vt3-t4laYx_LH3LU_bFX_kmLeM` |
| TXT | `_cf-custom-hostname.redthreatalert.pl` | `f510689d-a2a9-40e2-9824-2426c56f1c2c` |

Przed zastosowaniem odczytaj aktualny stan przypisania i istniejące rekordy
domeny. W home.pl przejdź do domeny i zarządzania rekordami DNS; oznaczenie
domeny głównej zależy od formularza. Nie twórz sprzecznych zestawów A/AAAA.
Zachowaj MX i TXT poczty; sprawdź, czy poczta nie korzysta z adresu domeny
głównej, zanim zmienisz A. [Instrukcja home.pl](https://pomoc.home.pl/baza-wiedzy/rekord-dla-domeny-jak-dodac-usunac-lub-zmienic-rekord-dla-subdomeny).

Przy przyszłej zmianie użytkownik może zalogować się do home.pl w przeglądarce,
a Codex wprowadzi uzgodnione rekordy, albo użytkownik przepisze je samodzielnie.
Nie potrzeba hasła w rozmowie, kodu AuthInfo ani transferu domeny.
Po zmianie sprawdź DNS oraz stan domeny i certyfikatu w Sites. Sam zapis
rekordów nie potwierdza aktywnego HTTPS. Wariant `www` wymaga własnego
przypisania i rekordów otrzymanych z Sites; nie został jeszcze dodany.
