# 33. Una fecha con zona horaria en ?since= o ?until= da 500

estado: implementado
candado: -
rama: claude/equipo-dev/33-fecha-con-zona-da-500
area: backend
prioridad: 2
fuente: bug reproducido en main 6ec5961 con `seed_demo`: `GET /api/overview/?since=2026-01-01T00:00Z` responde 500 (`ValueError: SQLite backend does not support timezone-aware datetimes when USE_TZ is False`; `_fecha` en `replays/views.py` acepta el offset y el ORM lo rechaza). Lo mismo con `+00:00` o `-03:00`, en `since` y en `until`, en overview, coach, operators, trends, teammates, duels, sessions, export y players/<id>.
archivos: backend/replays/views.py, backend/tests/test_dates.py
turnos: dev 20261009T0902Z, revisor 20261009T1202Z, dev 20261009T1502Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Un enlace con una fecha en formato ISO completo (la que sale de
`toISOString()` en JavaScript, o copiada de otra herramienta, termina en `Z`)
ya no tumba la pagina con un error de servidor: la fecha se pasa a la hora
local de la app y filtra como cualquier otra. Baja el riesgo de que un valor
de la query string vuelva a dar 500, que `ParametrosInvalidosTests` declara
como regla.

## Criterios de aceptacion

- [ ] `GET /api/overview/?since=2026-01-01T00:00Z` responde 200 (test).
- [ ] `since` y `until` con offset (`Z`, `+00:00`, `-03:00`) responden 200 en los endpoints que usan `_filters`, incluidos export y players/<id> (test con subTest).
- [ ] Una fecha con offset se convierte a la hora local (`TIME_ZONE`) antes de filtrar: `since=<hora UTC equivalente a una partida local>` la incluye y un minuto despues la excluye (test).
- [ ] Las fechas sin offset se comportan igual que antes: los tests de `RangoTests` siguen en verde sin cambios.

## Fuera de alcance

- Cambiar `USE_TZ` o como se guardan las fechas de las partidas.
- Tocar `days` (es la ficha 32).

## Diseno

(Dev, bug encontrado en el turno.) En `_fecha`, si `fromisoformat` devuelve
un datetime con `tzinfo`, pasarlo a la zona de `settings.TIME_ZONE` con
`django.utils.timezone.make_naive(fecha, timezone.get_default_timezone())`:
las fechas de la base son ingenuas en hora local, asi que esa es la unica
lectura que compara peras con peras. Tests nuevos en
`backend/tests/test_dates.py` (no en `test_api.py`, que esta tocando la rama
32). Sin migracion, sin recompute, sin frontend.

## Implementacion

- `backend/replays/views.py` (`_fecha`): si `fromisoformat` devuelve una
  fecha con `tzinfo` (`Z`, `+00:00`, `-03:00`), se pasa a hora local ingenua
  con `timezone.make_naive(fecha, timezone.get_default_timezone())`. Todas las
  fechas de la query string (`since`, `until`) pasan por `_fecha`, asi que el
  arreglo cubre los nueve endpoints de `_filters`. Las fechas sin offset no
  cambian.
- `backend/tests/test_dates.py`, clase nueva `FechaConZonaTests` con
  `@override_settings(TIME_ZONE="America/Santiago")` (no depende de la zona
  de la maquina):
  - `test_una_fecha_con_z_no_revienta_ningun_endpoint`: overview, coach,
    operators, trends, teammates, duels, sessions, compare, players/<id> y
    export x `since`/`until` con `Z`, `.000Z`, `+00:00` y `-03:00` -> 200.
  - `test_la_fecha_con_zona_se_pasa_a_la_hora_local`: la partida del 8 a las
    21:30 de Santiago (UTC-3) es 00:30 UTC del 9; `since=...00:30Z` la
    incluye, `00:31Z` no; `until` igual en sentido contrario.
  - `test_un_offset_distinto_de_utc_tambien_se_convierte`: lo mismo con `-01:00`.
  - `RangoTests` sin cambios y en verde (criterio 4).
- Sin el arreglo, `tests.test_dates` da 38 errores (verificado con `git stash`).
- Revision ciega del diff (subagente con `revision.md`): aprobar, sin
  hallazgos; confirmo por su cuenta que los tests nuevos fallan sin el arreglo.
- `check.sh` en `Todo en verde.`: 395 tests backend (4 skipped), vitest,
  build y 17 e2e.
- Desvio del diseno: ninguno. Los tests van en `test_dates.py` y no en
  `test_api.py` para no chocar con la rama 32, que tambien toca `views.py`
  pero en otra funcion (`_filters`, linea de `days`): merge de prueba limpio.

## Revision 2026-10-09 sobre 69d569b

Revision ciega (subagente con `revision.md`, sin leer la ficha) y
confirmacion del lider. `check.sh` en `Todo en verde.` sobre la rama (ya
contiene `origin/main` 6ec5961): 395 tests backend, 53 vitest, build, 17 e2e.

Criterios: los cuatro tienen test con nombre (`FechaConZonaTests` x3 y
`RangoTests` sin cambios). Los tests discriminan: sin el arreglo dan
`ValueError`; quitando el `tzinfo` sin convertir, `since=2026-09-09T00:30Z`
da 1 ronda y no 2. El diff solo toca los archivos de `archivos:`. Sin
numeros nuevos en la UI, sin tildes en identificadores, sin `print`.

Hallazgos:

- [bug] backend/replays/views.py:45 (`_fecha`)
  Que pasa: una fecha con zona cerca de los limites de `datetime` sigue
  dando 500: `make_naive` lanza `OverflowError` y `_fecha` solo atrapa
  `ValueError`.
  Como reproducirlo: `GET /api/overview/?until=9999-12-31T23:59-05:00` (o
  `?since=0001-01-01T00:00Z`) -> `OverflowError: date value out of range`
  (reproducido con el test client). La misma fecha sin zona
  (`since=0001-01-01`) responde 200, asi que el camino nuevo introduce un 500
  que la ficha dice eliminar (y que `ParametrosInvalidosTests` declara regla;
  es la misma familia que la ficha 32).
  Arreglo sugerido: envolver el `make_naive` en `try/except OverflowError:
  return None` (la fecha se ignora como una invalida) y agregar a
  `FechaConZonaTests` un subTest con `since=0001-01-01T00:00Z` y
  `until=9999-12-31T23:59-05:00` que espere 200.

Veredicto: corregir (un hallazgo, chico y local).

## Implementacion 2026-10-09 (correccion del hallazgo)

- `backend/replays/views.py` (`_fecha`): el `make_naive` va dentro de
  `try/except OverflowError` y devuelve `None`, asi que una fecha con zona
  que se sale del rango de `datetime` al pasarla a hora local se ignora
  como cualquier fecha invalida (200, sin filtro), igual que la misma fecha
  sin zona.
- `backend/tests/test_dates.py`:
  `FechaConZonaTests.test_una_fecha_con_zona_en_el_limite_del_calendario_se_ignora`
  con subTest `since=0001-01-01T00:00Z` y `until=9999-12-31T23:59-05:00`:
  200 y las 4 rondas. Sin el arreglo da 2 errores (`OverflowError`,
  verificado con `git stash`).
- `check.sh` en `Todo en verde.`: 396 tests backend, 53 vitest, build, 17 e2e.
- Revision ciega del diff (subagente con `revision.md`): aprobar, sin
  hallazgos; confirmo que los subtests del limite caen sin el `try/except`.
- Desvio del arreglo sugerido: ninguno.
