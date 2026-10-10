# 32. Un ?days= enorme da 500 en nueve endpoints

estado: aprobado
candado: release 2026-10-10 00:10
rama: claude/equipo-dev/32-days-enorme-da-500
area: backend
prioridad: 2
fuente: bug reproducido en main dc0188b con `seed_demo`: `GET /api/overview/?days=1000000` responde 500 (`OverflowError: date value out of range` en `replays/views.py:_filters`, que solo atrapa `ValueError`). Lo mismo en coach, operators, trends, teammates, duels, sessions, compare y players/<id>.
archivos: backend/replays/views.py, backend/tests/test_api.py
turnos: dev 20261008T1502Z, revisor 20261008T2102Z, qa 20261009T1802Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Un enlace con un filtro de dias absurdo (escrito a mano en la URL, o compartido
con un numero mal tipeado) ya no tumba la pagina con un error de servidor: se
ignora el filtro como cualquier otro valor invalido. Baja el riesgo de que un
valor de la query string vuelva a dar 500, que `ParametrosInvalidosTests` ya
declara como regla.

## Criterios de aceptacion

- [x] `GET /api/overview/?days=1000000` responde 200 (test).
- [x] `GET /api/overview/?days=99999999999` responde 200 en los nueve endpoints que usan `_filters` (test con subTest).
- [x] Un `days` desbordado se ignora: la respuesta es igual a la que se obtiene sin `days` (test).
- [x] `days=7` sigue filtrando como antes (test existente o nuevo).

## Fuera de alcance

- Cambiar que significa un `days` negativo (hoy deja un `since` en el futuro y la respuesta sale vacia, sin 500).
- Validar el resto de filtros de texto (`map`, `operator`): ya no dan 500.

## Diseno

(Dev, bug encontrado en el turno.) En `_filters`, atrapar
`(ValueError, OverflowError)` alrededor de `int(days)` + `timedelta` +
la resta: `timedelta(days=10**11)` desborda en el constructor y
`datetime.now() - timedelta(days=10**6)` en la resta. Tests nuevos en
`ParametrosInvalidosTests` de `backend/tests/test_api.py`. Sin migracion,
sin recompute, sin frontend.

## Implementacion

- `backend/replays/views.py` (`_filters`): el `except` de `days` atrapa
  `(ValueError, OverflowError)`. Hay dos puntos de desborde: `timedelta(days=99999999999)`
  en el constructor y `datetime.now() - timedelta(days=1000000)` en la resta
  (anio < 1). En los dos casos el filtro se ignora, igual que `days=abc`.
- `backend/tests/test_api.py`, en `ParametrosInvalidosTests`:
  - `test_un_days_enorme_no_revienta_ningun_endpoint`: 10 endpoints que pasan por
    `_filters` (overview, coach, operators, trends, teammates, duels, sessions,
    compare, players/<id>, export) x `days` 1000000 y 99999999999 -> 200.
  - `test_un_days_desbordado_se_ignora_como_cualquier_valor_invalido`: overview
    con `days=1000000` == overview sin filtro.
  - `test_un_days_normal_sigue_filtrando`: con una partida de ayer y dos de
    2026-09, `days=7` cuenta 1 partida y sin filtro 3.
- Sin el arreglo, los tests nuevos dan 19 errores (verificado con `git stash`).
- Revision ciega del diff: aprobar, con dos hallazgos de test ya corregidos
  (contar partidas exactas en vez de `assertNotEqual`; sumar `export/` a la lista).
- Desvio: no hay arquitecto ni PO en `turnos:` porque es un bug encontrado por el
  Dev sin trabajo tomable, segun el playbook.
- `check.sh` en verde: 369 tests backend, 53 frontend, build, 17 e2e.

## Revision 2026-10-08 sobre 1441c1d

Revisor 20261008T2102Z. Revision ciega del diff (`views.py` + `test_api.py`, sin `docs/backlog`) y confirmacion propia.

- Sin hallazgos. El `except (ValueError, OverflowError)` cubre los dos desbordes
  (constructor de `timedelta` con `99999999999`; resta con `datetime.now()` con `1000000`)
  y tambien los negativos que pasan el anio 9999 (`-2932896`, `-99999999999`).
  `days=-1000000` deja un `since` en el anio 4764: respuesta vacia, sin 500 (fuera de alcance, como dice la ficha).
- Otros caminos de fecha desde la query string, revisados: `_fecha` (`since=0001-01-01`,
  `until=9999-12-31` dan 200), `compare?by=days` acota `n` a 365 con `_int_param`,
  `session` enorme devuelve `[]`. Ninguno da 500.
- Criterios: los cuatro cubiertos por `test_un_days_enorme_no_revienta_ningun_endpoint`
  (10 endpoints x 2 valores), `test_un_days_desbordado_se_ignora_como_cualquier_valor_invalido`
  y `test_un_days_normal_sigue_filtrando`.
- Mutaciones: volver a `except ValueError` -> 21 errores en `ParametrosInvalidosTests`;
  ignorar `days` siempre -> falla `test_un_days_normal_sigue_filtrando`.
- Diff dentro de `archivos:`; sin metrica nueva (no hace falta fila en `metricas.md`);
  sin tildes en identificadores; sin `print`.
- `check.sh` en verde sobre bb61b8f (main dc0188b ya incluido): 369 tests backend
  (4 skipped, los de siempre), 53 frontend, build, 17 e2e.

Veredicto: aprobar -> `revisado`.

## QA 2026-10-09 sobre 3fed9fb

QA 20261009T1802Z. Rama con `origin/main` 6ec5961 fusionado (23 commits nuevos de main, sin conflicto). Sin migracion, sin parser, sin frontend: no aplica chunk ni `recompute`.

- `check.sh` completo: `Todo en verde.` (ruff, 395 tests backend con 4 skipped, 53 frontend, build, 17 e2e).
- Pasos de `ci.yml` tal cual, sin `.env`: `cd backend && ruff check .` -> `All checks passed!`; `python3 manage.py test tests` -> `OK (skipped=4)`.
- Repro del bug en main 6ec5961 (worktree, base de `seed_demo`): `curl -s -o /dev/null -w '%{http_code}' 'http://127.0.0.1:8000/api/overview/?days=1000000'` -> 500 (`OverflowError: date value out of range`); con `99999999999` -> 500.
- Criterio 1 y 2: en la rama, `runserver` con base vacia y con base de `seed_demo` (29 partidas, 203 rondas). Sonda `for ep in overview coach operators trends teammates duels sessions compare players/1 export matches filters; do for d in 1000000 99999999999 -1000000 -99999999999 7 abc "" 0 1e5 2932896; do curl -s -o /dev/null -w '%{http_code} ' "http://127.0.0.1:8000/api/$ep/?days=$d"; done; echo; done` -> todo 200 en base sembrada (en base vacia `players/1` da 404, que es lo correcto: no existe). Cero lineas ` 500 ` en el log del servidor.
- Criterio 3: `overview` sin `days`, con `days=1000000` y con `days=abc` -> mismo md5 del cuerpo; `overall.rounds` = 203 en los tres y con `99999999999`.
- Criterio 4: `overview?days=7` -> `overall.rounds` = 0 (la semilla es de 2026-08), `days=90` -> 203. Sigue filtrando.
- Vecinos con `days=1000000` combinado: `since=2026-01-01`, `until=foo`, `page=-1`, `map=`, `operator=`, `session=99999999999` -> 200 en `overview` y `matches`.
- Mutaciones sobre `ParametrosInvalidosTests`: volver a `except ValueError` -> 21 errores; `days` que nunca filtra -> cae `test_un_days_normal_sigue_filtrando`; desborde que fija `since` en 2100 en vez de ignorarse -> cae `test_un_days_desbordado_se_ignora_como_cualquier_valor_invalido`. Codigo restaurado despues de cada una.

Veredicto: los cuatro criterios con evidencia -> `aprobado`.
