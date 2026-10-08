# 32. Un ?days= enorme da 500 en nueve endpoints

estado: implementado
candado: revisor 2026-10-08 21:05 UTC
rama: claude/equipo-dev/32-days-enorme-da-500
area: backend
prioridad: 2
fuente: bug reproducido en main dc0188b con `seed_demo`: `GET /api/overview/?days=1000000` responde 500 (`OverflowError: date value out of range` en `replays/views.py:_filters`, que solo atrapa `ValueError`). Lo mismo en coach, operators, trends, teammates, duels, sessions, compare y players/<id>.
archivos: backend/replays/views.py, backend/tests/test_api.py
turnos: dev 20261008T1502Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Un enlace con un filtro de dias absurdo (escrito a mano en la URL, o compartido
con un numero mal tipeado) ya no tumba la pagina con un error de servidor: se
ignora el filtro como cualquier otro valor invalido. Baja el riesgo de que un
valor de la query string vuelva a dar 500, que `ParametrosInvalidosTests` ya
declara como regla.

## Criterios de aceptacion

- [ ] `GET /api/overview/?days=1000000` responde 200 (test).
- [ ] `GET /api/overview/?days=99999999999` responde 200 en los nueve endpoints que usan `_filters` (test con subTest).
- [ ] Un `days` desbordado se ignora: la respuesta es igual a la que se obtiene sin `days` (test).
- [ ] `days=7` sigue filtrando como antes (test existente o nuevo).

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
