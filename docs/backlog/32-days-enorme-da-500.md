# 32. Un ?days= enorme da 500 en nueve endpoints

estado: entregado
candado: -
rama: claude/equipo-dev/32-days-enorme-da-500
area: backend
prioridad: 2
fuente: bug reproducido en main dc0188b con `seed_demo`: `GET /api/overview/?days=1000000` responde 500 (`OverflowError: date value out of range` en `replays/views.py:_filters`, que solo atrapa `ValueError`). Lo mismo en coach, operators, trends, teammates, duels, sessions, compare y players/<id>.
archivos: backend/replays/views.py, backend/tests/test_api.py
turnos: dev 20261008T1502Z, revisor 20261008T2102Z, qa 20261009T1802Z, release 20261010T0002Z

## PR

Titulo: `[equipo-dev][backend] Un ?days= enorme ya no da 500`

## Que cambia

Un `?days=` absurdo en la URL (`days=1000000`, `days=99999999999`) ya no tumba con un 500 los endpoints que filtran por fecha: el filtro se ignora, igual que `days=abc`. Baja el riesgo de que un enlace compartido o mal tipeado deje una pagina en error de servidor.

## Por que esto y no otra cosa

Bug encontrado por el Dev sin trabajo tomable (ficha 32): `_filters` en `backend/replays/views.py` solo atrapaba `ValueError`, y `timedelta(days=99999999999)` (constructor) y `datetime.now() - timedelta(days=1000000)` (resta) lanzan `OverflowError`. Se descarto acotar `days` a un maximo: ignorar el valor invalido es lo que ya hace el resto de la query string (`ParametrosInvalidosTests`).

## Como se probo

- `./scripts/check.sh`: `Todo en verde.` (ruff, tests backend, 53 vitest, build, 17 e2e) sobre la rama con `origin/main` fusionado.
- Tests nuevos en `ParametrosInvalidosTests` (`backend/tests/test_api.py`):
  - `test_un_days_enorme_no_revienta_ningun_endpoint`: 10 endpoints x `days` 1000000 y 99999999999 -> 200.
  - `test_un_days_desbordado_se_ignora_como_cualquier_valor_invalido`: overview con `days=1000000` == overview sin filtro.
  - `test_un_days_normal_sigue_filtrando`: `days=7` cuenta solo la partida reciente.
- QA: repro del 500 en main con `seed_demo`; en la rama, 12 endpoints x 10 valores de `days` en base vacia y sembrada sin ningun 500; 3 mutaciones y las 3 caen.

## Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser, sin frontend. Fuera de alcance: lo que significa un `days` negativo (deja un `since` en el futuro y la respuesta sale vacia, sin 500).

## Como probarlo en 2 minutos

```bash
cd backend
python manage.py test tests.test_api.ParametrosInvalidosTests
python manage.py seed_demo && python manage.py runserver
curl -s -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:8000/api/overview/?days=1000000'      # 200 (en main: 500)
curl -s -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:8000/api/overview/?days=99999999999'  # 200
```

## Para el humano

Nada.

## Candidatos descubiertos

Ninguno.

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

Revisor 20261008T2102Z, revision ciega + confirmacion propia. Sin hallazgos: el `except (ValueError, OverflowError)` cubre constructor y resta, tambien negativos que pasan el anio 9999. Otros caminos de fecha (`_fecha`, `compare?by=days`, `session`) sin 500. Mutaciones caen. Veredicto: aprobar -> `revisado`.

## QA 2026-10-09 sobre 3fed9fb

QA 20261009T1802Z, main 6ec5961 fusionado. `check.sh` en verde (395 backend, 53 vitest, build, 17 e2e) y pasos de `ci.yml` sin `.env`. Repro del 500 en main; en la rama, 12 endpoints x 10 valores de `days` sin 500 en base vacia y sembrada; criterio 3 con md5 igual del cuerpo; `days=7` sigue filtrando. 3 mutaciones, las 3 caen. Veredicto: `aprobado`.
