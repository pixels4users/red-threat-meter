# Newsletter RedThreatAlert

Stan 06.10.2026: formularz i silnik są wdrożone. Migracja
`20261005150000_newsletter.sql` i prywatna funkcja `rta-newsletter` działają
w projekcie `dubhsimiblpfcaudbvjb`; frontend to wersja Sites 27
(dopracowane okna potwierdzenia i prywatności).
Newsletter włączono o 06:43:32 UTC z segmentem
`f4f11832-0f6f-4d6b-9c8a-8a7794dacc2b` (RedThreatAlert — raport dzienny).
Klucz Resend pozostaje w prywatnym `.env.newsletter` i sekretach Edge.
Testy lokalne korzystają z symulatora i nie wysyłają wiadomości.

Na produkcji sprawdzono zapis, dostarczenie potwierdzenia, brak aktywacji
przez sam GET, dwukrotne potwierdzenie z jednym dowodem zgody oraz usunięcie
adresu z tabeli oczekujących po zapisie. Pełny raport z 05.10 wysłano jako
TEST wyłącznie na zatwierdzony adres użytkownika, przez osobny segment.
Resend potwierdził `delivered`, a użytkownik potwierdził czytelność maila.
Link wypisu rzeczywiście ustawił kontakt jako `unsubscribed=true`.
Po wyraźnej zgodzie użytkownika 06.10 wykonano ponowny zapis i świeże
potwierdzenie: kontakt ma `unsubscribed=false`, należy do segmentu produkcyjnego,
nowa zgoda jest zapisana dokładnie raz, a adres usunięto z tabeli oczekujących.
Zapisano wąską regułę dla `dispatch_newsletter.py` i sprawdzono jej dopasowanie
do `--status` oraz `--cycle ... --send`; reguła nie obejmuje dowolnego `python -c`.
Istniejąca automatyzacja zawiera teraz wysyłkę po publicznym odczycie i replay,
z zachowaniem godz. 09:00 Europe/Warsaw, wątku i wszystkich limitów.
Ręcznie dodana reguła wymaga restartu Codexa; pierwsze wykonanie newslettera
z harmonogramu pozostaje do odbioru. Odczyt prywatnej funkcji zwraca `enabled`.
Przy tym odbiorze najnowszy raport pochodził nadal z 05.10, więc
nie uruchamiano wysyłki produkcyjnej ani dodatkowej analizy.
Dowód wdrożenia poza Git:
`data/diagnostics/newsletter-deploy-2026-10-06.json`.

## Przebieg zapisu

1. Formularz e-mail + niezaznaczona zgoda wywołuje tę samą domenę strony.
2. Worker dopuszcza tylko trzy ścieżki: status, subscribe i confirm. Sprawdza
   Origin, metodę, typ i rozmiar żądania; nadpisuje identyfikator IP klienta.
3. Prywatna funkcja `rta-newsletter` zapisuje zgłoszenie na 24 godziny.
   W bazie są skrót tokenu, HMAC e-maila/IP, czas i wersja zgody.
4. Wiadomość potwierdzająca prowadzi do strony z przyciskiem „Potwierdzam zapis”.
   Sam GET, otwarcie maila i skaner linków nie aktywują adresu.
5. Po potwierdzeniu kontakt trafia do wybranego segmentu Resend. Zgoda ma
   osobny zapis w bazie, a adres znika z tabeli zgłoszeń. Ponowny zapis
   wypisanego kontaktu wymaga nowego potwierdzenia.
6. Resend obsługuje link wypisu i stan `unsubscribed`; żaden cykl raportowy
   nie resetuje tego stanu. Link wypisu jest na początku i końcu maila.

Limity potwierdzeń na start: globalnie 100/dobę, 5/IP/godzinę, 3/adres/dobę,
z 15 minutami przerwy dla tego samego adresu i polem pułapką dla botów.
To limity aplikacji, niezależne od limitów planu Resend. Liczniki są wspólne
dla wszystkich instancji serwera. Dane starsze niż 7 dni (zgłoszenia) i 2 dni
(limity) są porządkowane przy żądaniach do funkcji; bez ruchu nie ma osobnego
zegara czyszczenia. Dowody zgód wymagają okresowego przeglądu retencji.

## Treść i wysyłka raportu

`hosting/newsletter-email.mjs` korzysta z `buildReportPresentation`, tego samego
modelu co szczegóły raportu, wydruk i TXT. Zachowuje pełne wydarzenia, źródła,
ostrzeżenia, niepewność, historyczne null i zero. Nie uruchamia nowej analizy.
Wersja HTML i tekst zawierają link do dokładnego wydania i BuyCoffee.

Pełny raport może być bardzo długi. Przykład z 05.10.2026 zawiera 118 wpisów
i około 106 KB HTML po usunięciu powtarzanych stylów linków. Klient pocztowy
może skrócić jego widok; zawartość nie jest ucinana przez generator. Podgląd
w przeglądarce nie potwierdza sposobu renderowania w Gmail/Outlook.

Polecenie po udanej publikacji:

```sh
.venv/bin/python scripts/dispatch_newsletter.py --cycle ID_CYKLU
```

Bez `--send` to kontrola offline, bez połączeń i wysyłki. Skrypt wymaga zgodnych
`publication-daily.json`, `published-daily.json` i `verification.json`:
to samo `report_id`, hash pliku eksportu, potwierdzony publiczny odczyt i
`replay.identical=true` z tym samym `run_id`. Nie uzupełnia brakujących dowodów.
Po aktywacji dodanie `--send` zleca wysyłkę prywatnej funkcji.

Funkcja ponownie waliduje publikację i porównuje ją z publicznym API strony.
Wymaga najnowszego raportu z bieżącego dnia w Europe/Warsaw, opublikowanego po
`newsletter_settings.enabled_at`. Brak raportu, awaria DNS/odczytu i rozbieżne
dane wstrzymują wysyłkę. Nie rozsyła wczorajszego raportu jako dzisiejszego.

Baza rezerwuje najwyżej jedno wydanie na dzień, również przy równoległych
wywołaniach. Korekta tego samego dnia nie powoduje automatycznej drugiej wysyłki.
Zamrożony mail i ID szkicu Broadcast są zapisywane przed wysłaniem.
Stan `sent` oznacza przyjęcie operacji przez Resend, nie potwierdzenie
dostarczenia każdej wiadomości do skrzynki.

### Nieznany wynik operacji

Resend dokumentuje idempotencję dla `/emails` i `/emails/batch`; nie zakładamy
jej dla Broadcasts. Timeout przy tworzeniu lub wysyłaniu Broadcast ustawia
`needs_review`. Nie ponawiaj automatycznie, nie usuwaj blokady dnia i nie
twórz drugiego Broadcast. Odczytaj zapisany `broadcast_id` oraz logi Resend,
ustal rzeczywisty stan i dopiero wtedy wykonaj udokumentowaną korektę stanu.
Przerwany proces w stanie `sending` może jedynie sprawdzić status tego samego
Broadcast. Nieznany wynik jest sygnalizowany, bez ślepego powtórzenia wysyłki.

## Podgląd i testy

```sh
npm run test:newsletter
.venv/bin/python -m pytest tests/test_newsletter_dispatch.py -q
npm test
npm run test:site
npm run build:newsletter
npm run build:site
node scripts/preview_newsletter.mjs
```

Podgląd: `http://127.0.0.1:8771/`, wiadomości:
`http://127.0.0.1:8771/__newsletter_preview`. Formularz korzysta z prywatnej,
tymczasowej bazy PGlite i symulatora Resend. Nie ładuje kluczy ani nie łączy
się z usługami wysyłki. Po zamknięciu serwera testowe zapisy znikają.
Raporty do wyglądu są odczytywane z już opublikowanych lokalnych eksportów.
Parametr `?appearance=dark` służy tylko podglądowi wyglądu.

Sprawdzenie 05.10.2026: 10 testów newslettera w Node/PGlite, 5 testów bramek
wydawcy w Python, 52 istniejące testy dashboardu i 14 testów Workera — bez
błędów. Build strony, funkcji Edge i minimalnego pakietu Sites przeszedł;
skan gotowych plików klienta nie znalazł zapisanych kluczy. Przeglądarka:
wymagana zgoda, formularz → lokalny mail → potwierdzenie, Escape i fokus,
widoki 1350 i 320 px, ciemny wygląd, brak poziomego przepełnienia i błędów
konsoli. Podgląd pełnego maila zawiera 118 nagłówków wydarzeń i dwa linki wypisu.

## Uruchomienie po odbiorze lokalnym

1. Potwierdź formularz, wygląd maila, dane administratora i treść informacji
   o prywatności. Tekst w interfejsie jest przygotowany do przeglądu;
   implementacja nie stanowi poświadczenia zgodności całej działalności.
2. Zweryfikuj limity obecnego planu Resend i segment przeznaczony wyłącznie
   dla potwierdzonych zapisów RTA. Nie importuj adresów bez zgody.
3. Zastosuj tylko nową migrację `20261005150000_newsletter.sql` w przypiętym
   projekcie Supabase. Settings domyślnie wyłączają newsletter; istniejących
   migracji raportów nie powtarzaj. Tabele i RPC mają RLS i dostęp wyłącznie
   `service_role`. Sprawdź brak dostępu `anon` oraz `authenticated` w chmurze.
4. Zbuduj funkcję. Wygeneruj prywatny plik runtime z `RESEND_API_KEY`
   z `.env.newsletter` oraz `RTA_GATEWAY_KEY` równym istniejącemu kluczowi
   serwerowemu z `.env.dashboard`; nigdy nie wyświetlaj wartości. Ustaw mode
   600, prześlij przez `supabase secrets set --env-file ... --project-ref
   dubhsimiblpfcaudbvjb`, a tymczasowy plik usuń po przesłaniu. Supabase
   dostarcza `SUPABASE_URL` automatycznie. Klucz używany do HMAC musi pozostawać
   dostępny przy obsłudze starych dowodów zgody; jego rotacja wymaga planu.
5. `supabase functions deploy rta-newsletter --project-ref dubhsimiblpfcaudbvjb
   --use-api`. `verify_jwt=false` dotyczy wyłącznie tej funkcji: każda trasa
   wymaga własnego tajnego klucza gateway, zgodnego z istniejącym kluczem
   strony. Sprawdź 401 bez niego i 200/status=disabled z nim.
6. Publikuj frontend w istniejącym projekcie Sites zgodnie z
   `hosting-runbook.md`. Pakiet zawiera wyłącznie publiczną konfigurację
   i wąskie proxy. Resend API key oraz kod zaplecza nie trafiają do frontendu.
7. Zapisz właściwy `segment_id`, `enabled_at=now()` i `enabled=true`.
   Wykonaj rzeczywisty zapis/potwierdzenie, test pełnego maila tylko na
   `pixels4users@gmail.com`, wypis i ponowny zapis. Sprawdź brak duplikatu,
   nagłówki/list-unsubscribe i odczyt w rzeczywistej skrzynce.
8. Dopiero po tym dołącz polecenie `dispatch_newsletter.py --cycle ... --send`
   na końcu **istniejącej** automatyzacji `rtb-codzienna-analiza-i-raport`, po
   publicznym odczycie i replay. Zachowaj preflight, wszystkie limity pobrań,
   brak eskalacji w cyklu i godz. 09:00 Europe/Warsaw. Jeśli dzisiejszy raport
   już jest, można wznowić tylko newsletter z dowodami tego samego cyklu,
   bez ponownej analizy. Przy braku reguły sieciowej zgłoś blokadę;
   konfigurację dostępu ustal przed uruchomieniem harmonogramu.

Wyłączenie: `newsletter_settings.enabled=false` blokuje zapisy i nowe operacje
wysyłki, a formularz się ukrywa. Operacja już przekazana Resend może nadal
zostać dostarczona. Nie cofaj stanu bazy ani nie zmieniaj DNS do wyłączenia.

Dokumentacja dostawców:
[idempotencja Resend](https://resend.com/docs/dashboard/emails/idempotency-keys),
[Contacts i segmenty](https://resend.com/docs/api-reference/contacts/add-contact-to-segment),
[Broadcast](https://resend.com/docs/api-reference/broadcasts/create-broadcast),
[sekrety Supabase](https://supabase.com/docs/guides/functions/secrets),
[konfiguracja funkcji](https://supabase.com/docs/guides/functions/function-configuration).

## Źródła i podgląd po wdrożeniu

Zaakceptowane UI i silnik połączono na `main` i `codex/ux-index-history`.
Podgląd na 8771 pozostaje symulatorem; rzeczywisty zapis jest dostępny na
https://redthreatalert.pl/#newsletter. Testy lokalne nie powinny otrzymywać
produkcyjnych kluczy. Zmiany dokumentacji i polecenia wydawcy nie wymagają
ponownej publikacji frontendu; zmiany Edge wymagają osobnego build/deploy.

Kontrola gotowości prywatnej funkcji bez wysyłki:

```sh
.venv/bin/python scripts/dispatch_newsletter.py --status
```

Instalator zgłosił GHSA-68fv-2mgg-jv7q dla `source-map-js@1.2.1` w zależnościach
Vite/PostCSS. Dotyczy przetwarzania map źródeł w narzędziach budowania;
nie jest częścią wdrożonego Workera ani kodu przeglądarki. Aktualizacja
narzędzi budowania pozostaje osobnym zadaniem.
