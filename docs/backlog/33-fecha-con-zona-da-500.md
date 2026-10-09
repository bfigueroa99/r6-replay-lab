# 33. Una fecha con zona horaria en ?since= o ?until= da 500

estado: en curso 2026-10-09
candado: -
rama: claude/equipo-dev/33-fecha-con-zona-da-500
area: backend
prioridad: 2
fuente: bug reproducido en main 6ec5961 con `seed_demo`: `GET /api/overview/?since=2026-01-01T00:00Z` responde 500 (`ValueError: SQLite backend does not support timezone-aware datetimes when USE_TZ is False`; `_fecha` en `replays/views.py` acepta el offset y el ORM lo rechaza). Lo mismo con `+00:00` o `-03:00`, en `since` y en `until`, en overview, coach, operators, trends, teammates, duels, sessions, export y players/<id>.
archivos: backend/replays/views.py, backend/tests/test_dates.py
turnos: dev 20261009T0902Z

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
