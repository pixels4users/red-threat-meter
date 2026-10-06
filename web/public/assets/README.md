# Znak marki w newsletterze

`rta-mark-v1.png` to niezmieniona kopia przezroczystego eksportu z
`artifacts/branding/red-threat-alert-transparent.png` (Lucide radar, kolor
#bd302b). Licencja: `artifacts/branding/LUCIDE-LICENSE`.

Vite kopiuje ten plik bez hashowania pod `/assets/rta-mark-v1.png`.
Wysłane wiadomości potrzebują trwałego adresu: przy przyszłej zmianie znaku
dodaj kolejną wersję, zachowując ten plik. Publikacja assetu na stronie musi
poprzedzić wdrożenie szablonu Edge. Podgląd lokalny korzysta z lokalnej kopii.
