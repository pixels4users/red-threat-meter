# Jawne dane syntetyczne

`demo.json` jest niewielkim, stałym przykładem formatu wejścia, z fikcyjnymi publikacjami. Nie przedstawia obecnej sytuacji. Uruchomienie z katalogu projektu:

```sh
.venv/bin/python scripts/run_pipeline.py --fixture tests/fixtures/demo.json
```

Raport trafi do `data/demo/` i pozostanie oznaczony jako test. Publikacje nie mają ocen, więc wynik jest pusty. Aktualne, dynamiczne przypadki do kontroli naliczania punktów tworzy `tests/conftest.py`; nie wymagają sieci.
