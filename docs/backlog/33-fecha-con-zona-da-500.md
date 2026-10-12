# 33. Una fecha con zona horaria en ?since= o ?until= da 500

estado: entregado
candado: -
rama: claude/equipo-dev/33-fecha-con-zona-da-500
area: backend
prioridad: 2
fuente: bug reproducido en main 6ec5961 con `seed_demo`: `GET /api/overview/?since=2026-01-01T00:00Z` responde 500 (`ValueError: SQLite backend does not support timezone-aware datetimes when USE_TZ is False`; `_fecha` en `replays/views.py` acepta el offset y el ORM lo rechaza). Lo mismo con `+00:00` o `-03:00`, en `since` y en `until`, en overview, coach, operators, trends, teammates, duels, sessions, export y players/<id>.
archivos: backend/replays/views.py, backend/tests/test_dates.py
turnos: dev 20261009T0902Z, revisor 20261009T1202Z, dev 20261009T1502Z, revisor 20261009T2101Z, qa 20261010T1801Z, release 20261012T1640Z

## PR

Titulo: `[equipo-dev][backend] Una fecha con zona horaria en ?since= o ?until= ya no da 500`

## Que cambia

Un enlace con una fecha ISO completa en `?since=` o `?until=` (la que sale de `toISOString()` en JavaScript termina en `Z`; tambien `+00:00` o `-03:00`) ya no tumba con un 500 los endpoints que filtran por fecha: la fecha se pasa a la hora local de la app y filtra como cualquier otra. Las fechas sin zona se comportan igual que antes.

## Por que esto y no otra cosa

Bug encontrado por el Dev sin trabajo tomable (ficha 33): `_fecha` en `backend/replays/views.py` aceptaba el offset y el ORM lo rechazaba, porque con `USE_TZ=False` la base guarda hora local ingenua. Se convierte con `timezone.make_naive(fecha, timezone.get_default_timezone())`, que es la unica lectura que compara contra lo que hay en la base. Se descarto cambiar `USE_TZ` o como se guardan las partidas (fuera de alcance: migracion de datos para arreglar una query string). Una fecha con zona que se sale del rango de `datetime` al convertirla (`0001-01-01T00:00Z`) se ignora como cualquier fecha invalida en vez de dar `OverflowError`.

## Como se probo

- `./scripts/check.sh`: `Todo en verde.` (ruff, tests backend, 53 vitest, build, 17 e2e) sobre la rama con `origin/main` fusionado.
- Tests nuevos en `FechaConZonaTests` (`backend/tests/test_dates.py`, con `TIME_ZONE=America/Santiago` fijo):
  - `test_una_fecha_con_z_no_revienta_ningun_endpoint`: 10 endpoints x `since`/`until` con `Z`, `.000Z`, `+00:00` y `-03:00` -> 200.
  - `test_la_fecha_con_zona_se_pasa_a_la_hora_local`: `since=...00:30Z` incluye la partida de las 21:30 de Santiago y `00:31Z` la excluye; `until` al reves.
  - `test_un_offset_distinto_de_utc_tambien_se_convierte`: lo mismo con `-01:00`.
  - `test_una_fecha_con_zona_en_el_limite_del_calendario_se_ignora`: `since=0001-01-01T00:00Z` y `until=9999-12-31T23:59-05:00` -> 200, sin filtro.
- `RangoTests` (fechas sin zona) sin cambios y en verde.
- Revision ciega en dos pasadas: un hallazgo (`OverflowError` en el borde del calendario), corregido con su test.
- QA: 49/49 respuestas 200 en base vacia y 121/121 en base sembrada (11 endpoints x 11 parametros borde), cero `Traceback`; `since=...18:00Z` y `since=...14:00` (Santiago) devuelven el mismo JSON byte a byte. 3 mutaciones sobre `_fecha`, las 3 caen.

## Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser, sin frontend. Fuera de alcance: `USE_TZ` y el formato en que se guardan las fechas de las partidas. Una cadena de 10 caracteres con zona (`2026-09-08Z`) la sigue rechazando `fromisoformat` y se ignora, como antes.

## Como probarlo en 2 minutos

```bash
cd backend
python manage.py test tests.test_dates
python manage.py seed_demo && python manage.py runserver
curl -s -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:8000/api/overview/?since=2026-01-01T00:00Z'           # 200 (en main: 500)
curl -s -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:8000/api/sessions/?until=2026-12-31T23:59%2B00:00'    # 200
curl -s -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:8000/api/overview/?since=0001-01-01T00:00Z'           # 200
```

## Para el humano

Nada.

## Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Un enlace con una fecha en formato ISO completo ya no tumba la pagina con un
error de servidor: la fecha se pasa a la hora local de la app y filtra como
cualquier otra. Baja el riesgo de que un valor de la query string vuelva a dar
500, que `ParametrosInvalidosTests` declara como regla.

## Criterios de aceptacion

- [x] `GET /api/overview/?since=2026-01-01T00:00Z` responde 200 (test).
- [x] `since` y `until` con offset (`Z`, `+00:00`, `-03:00`) responden 200 en los endpoints que usan `_filters`, incluidos export y players/<id> (test con subTest).
- [x] Una fecha con offset se convierte a la hora local (`TIME_ZONE`) antes de filtrar: `since=<hora UTC equivalente a una partida local>` la incluye y un minuto despues la excluye (test).
- [x] Las fechas sin offset se comportan igual que antes: los tests de `RangoTests` siguen en verde sin cambios.

## Fuera de alcance

- Cambiar `USE_TZ` o como se guardan las fechas de las partidas.
- Tocar `days` (es la ficha 32).

## Implementacion

(Dev 20261009T0902Z; correccion del hallazgo en Dev 20261009T1502Z.) En
`_fecha`, si `fromisoformat` devuelve una fecha con `tzinfo`, se pasa a hora
local ingenua con `make_naive`, dentro de `try/except OverflowError` que
devuelve `None`. Tests en `test_dates.py` (no en `test_api.py`, que tocaba la
rama 32). Sin el arreglo, `tests.test_dates` da 40 errores. Sin desvios del
diseno.

## Revision

- 2026-10-09 sobre 69d569b (Revisor 20261009T1202Z): corregir. Hallazgo:
  `?until=9999-12-31T23:59-05:00` daba `OverflowError` en `make_naive`.
  Corregido en cab041d con subTest del limite del calendario.
- 2026-10-09 sobre cab041d (Revisor 20261009T2101Z): aprobar, sin hallazgos.
  24/24 casos borde (DST de Santiago, limites del calendario, `+14:00`,
  fracciones de 9 digitos) en 200.

## QA 2026-10-10 sobre 0378eba

(QA 20261010T1801Z.) main 0b547d7 fusionado sin conflicto (185ccbf).
`check.sh` en verde (399 backend, 53 vitest, build, 17 e2e) y pasos de
`ci.yml` sin `.env`. 49/49 (base vacia) y 121/121 (base sembrada) en 200; la
`Z` se convierte a hora local (18:00Z = 14:00 Santiago incluye la partida,
18:01Z la excluye). Mutaciones: sin el bloque de `tzinfo` 40 errores,
`replace(tzinfo=None)` 2 fallos, `except ZeroDivisionError` 2 errores.
Veredicto: aprobado.
