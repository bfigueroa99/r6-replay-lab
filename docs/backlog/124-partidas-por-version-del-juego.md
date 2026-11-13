# 124. Partidas por version del juego en Datos

estado: en curso 2026-11-13T19:37Z
candado: -
rama: claude/equipo-dev/124-partidas-por-version-del-juego
tipo: funcionalidad
epica: datos
area: backend
prioridad: 3
fuente: ALCANCE.md G8
archivos: backend/replays/unknowns.py (partidas_por_version), backend/replays/views.py (import_status), backend/tests/test_versiones_del_juego.py (nuevo), frontend/src/pages/Datos.jsx (panel Importación), frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1650Z-c9H2L8Y, arquitecto 20261113T1830Z-cTivbSq

## PR

## Que gana quien usa la app

En Datos, una tabla con cuantas partidas importadas hay de cada version del
juego, con la fecha de la primera y de la ultima. Se ve de un vistazo que
temporadas cubre el historial y si una version nueva entro sin nombre
(con mapas u operadores desconocidos), sin abrir partida por partida.

## Criterios de aceptacion

- [ ] Una funcion de agregado agrupa `Match` por `game_version` (y
      `code_version` como orden) con `Count`, `Min(played_at)` y
      `Max(played_at)`; ordenada de la version mas nueva a la mas vieja.
      Test con tres partidas en dos versiones.
- [ ] Las partidas con `game_version` vacio o nulo salen en una fila
      "Sin versión", al final. Test.
- [ ] La tabla va en un endpoint que Datos ya consulta
      (`/api/import/status/` o `/api/unknown/`, lo elige el diseno), sin
      POST nuevo y sin columna ni migracion. Base vacia: lista vacia, 200.
- [ ] `Datos.jsx` muestra la tabla (versión, partidas, primera, última)
      con el estado vacio del resto de la pagina; e2e en `seed_demo` que
      ve al menos una fila y consola limpia.

## Fuera de alcance

- Nombre de temporada ("Y11S3") derivado de la version: es A3.
- Filtro global por version o temporada (A3).
- Recalcular o reimportar desde esta tabla (G1).

## Diseno

(arquitecto 20261113T1830Z-cTivbSq, sobre `origin/dev@ed7bb52`) Filtros
duros: pasa. `Match.game_version` (CharField, `blank=True`, nunca nulo) y
`Match.code_version` (entero) ya se guardan al importar; sin columna, sin
migracion, sin POST, sin red, sin dependencias. Una forma obvia, ~150
lineas: sin arena ni consenso.

**Donde va el agregado: `backend/replays/unknowns.py`**, no `aggregates.py`.
Es un resumen de `Match` sin filtros de la barra, para la pagina Datos, como
`unknown_maps` (que ya agrupa `Match` con `Count`/`Min`/`Max` y `_iso` en ese
modulo, con esos imports hechos). Y `aggregates.py` lo pisa la 79 con su
guardia de partidas excluidas: ahi esta funcion tendria que clasificarse.
Ninguna rama abierta toca `unknowns.py`.

- `def partidas_por_version() -> list[dict]`, en una seccion nueva al final
  de `# --- descubrimiento` (despues de `unknown_match_types`):
  `Match.objects.order_by().values("game_version").annotate(partidas=Count("id"),
  code=Max("code_version"), primera=Min("played_at"), ultima=Max("played_at"))`.
  El `order_by()` vacio es obligatorio: `Match.Meta.ordering = ["-played_at"]`
  meteria `played_at` en el GROUP BY y partiria las filas (el mismo problema
  que comenta `unknown_maps` con `Round`).
- Orden en Python: primero las de `game_version` no vacio, por `-code` y
  despues `-ultima` (la mas nueva arriba); al final la fila de `""` (o
  solo-espacios: `.strip()` al agrupar no hace falta, el parser guarda el
  string tal cual; se compara `not fila["game_version"]`).
- Cada fila: `{"game_version": str, "code_version": int, "matches": int,
  "first": _iso(primera), "last": _iso(ultima)}`.
- Cuenta todas las partidas importadas, incluidas las que la 79 excluya de
  los agregados: es el inventario de lo importado, no una metrica. Una linea
  de docstring lo dice.

**Endpoint: `/api/import/status/`** (`views.import_status`), que Datos ya
consulta (`status = useApi('/import/status/')`): suma
`"versions": unknowns.partidas_por_version()` al dict. La 79 toca `views.py`
en otras vistas (`_ok`, filtros, `match_list`, `match_detail`), no esta.
`unknowns` ya esta importado en `views.py` (lo usa `unknown`).

**Tests, `backend/tests/test_versiones_del_juego.py`** (nuevo, con
`make_match` de `factories.py` y `game_version`/`code_version` seteados
despues de crear si la factory no los acepta):
- `test_agrupa_por_version_con_primera_y_ultima`: tres partidas, dos en
  `Y10S3` (code 20) y una en `Y10S4` (code 30): dos filas, `Y10S4` primero;
  `Y10S3` con `matches` 2 y `first`/`last` de sus fechas.
- `test_sin_version_va_al_final`: una con `game_version=""` y code mayor que
  las demas: igual sale ultima.
- `test_el_orden_del_modelo_no_parte_las_filas`: dos partidas de la misma
  version en fechas distintas -> una sola fila (cubre el `order_by()`).
- `test_import_status_trae_versions_y_base_vacia_da_lista_vacia`:
  `/api/import/status/` con base vacia -> 200 y `versions == []`; con una
  partida, una fila.

**Frontend, `frontend/src/pages/Datos.jsx`**, dentro del Panel "Importación"
despues de la tabla del log, un `<h3>Partidas por versión del juego</h3>` y
una `DataTable`: columnas Versión (`row.game_version || 'Sin versión'`,
`left`), Partidas, Primera y Última (`slice(0, 10)` de la fecha ISO, como
las demas fechas cortas de la pagina; `—` si nula), `rowKey` =
`game_version || 'sin-version'`, sin `initialSort` (el orden lo da la API),
`csvName="partidas-por-version"`, `empty="Todavía no hay partidas
importadas."`. El `hint` del panel no cambia. Sin logica pura nueva: el unico
calculo es el rotulo de la fila vacia, y lo cubre el e2e.

**e2e, `frontend/e2e/humo.spec.js`**, test `Datos muestra las partidas por
version del juego` junto a los de `/datos`: `seed_demo` deja las 29 partidas
con `game_version` vacio, asi que la tabla tiene una fila `Sin versión` con
`29` (leer el total de `/api/import/status/` para no fijar el numero a mano
si conviene: `versions[0].matches`); consola limpia.

**`docs/metricas.md`**: es un conteo de inventario, no una metrica de
rendimiento; igual entra una fila (la regla es "todo numero que muestra la
UI"): `| **Partidas por versión del juego** | En Datos, panel Importación (clave `versions` de `/api/import/status/`). Partidas importadas agrupadas por `Match.game_version` tal como viene del replay, con la fecha de la primera y la ultima. Orden: la version con `code_version` mas alto primero; las partidas sin version, en la fila "Sin versión", al final. Sin filtros de la barra y con todas las partidas importadas, tambien las excluidas de los agregados. |`

**Orden.** Tests backend (rojo) -> `partidas_por_version` -> vista -> tabla
en `Datos.jsx` -> e2e -> `metricas.md` -> `npm run build` -> `verificar.sh`.

**Que puede romperse.** `/api/import/status/` lo consulta tambien el vigia de
importacion de la barra (si lo hace): una clave mas no le cambia nada; el
costo es un GROUP BY sobre `Match` (una fila por partida, indice en
`played_at`): despreciable al lado de `find_match_folders`, que ya recorre
el disco en esa vista.

**Archivos ocupados.** 79: `views.py` (otras vistas), `frontend/src/pages/MatchDetail.jsx`
y su propio e2e; no toca `Datos.jsx` ni `unknowns.py`. 120, 122, 126:
`humo.spec.js` y `metricas.md` en otras zonas. No se frena.

**Verificacion manual.** `seed_demo` + `runserver`, `/datos`: fila "Sin
versión" con 29. Con la base real: una fila por temporada importada, la mas
nueva arriba; `curl -s localhost:8000/api/import/status/ | python -m
json.tool` y mirar `versions`.

Skills: no aplica (un GROUP BY sobre columnas que ya existen).
Skills del repo: testing-strategy (Django para la agrupacion, el orden y el
GROUP BY que el `ordering` del modelo partiria; e2e para la tabla con
`seed_demo`; sin vitest: no hay logica pura).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

(nada)
