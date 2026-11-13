# 124. Partidas por version del juego en Datos

estado: aprobado
candado: release 2026-11-13T20:30Z
rama: claude/equipo-dev/124-partidas-por-version-del-juego
tipo: funcionalidad
epica: datos
area: backend
prioridad: 3
fuente: ALCANCE.md G8
archivos: backend/replays/unknowns.py (partidas_por_version), backend/replays/views.py (import_status), backend/tests/test_versiones_del_juego.py (nuevo), frontend/src/pages/Datos.jsx (panel Importación), frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1650Z-c9H2L8Y, arquitecto 20261113T1830Z-cTivbSq, dev 20261113T1926Z-cNCxUZs, revisor 20261113T1926Z-cq9nfTP, qa 20261113T2003Z-c3vr7mZ

## PR

## Que gana quien usa la app

En Datos, una tabla con cuantas partidas importadas hay de cada version del
juego, con la fecha de la primera y de la ultima. Se ve de un vistazo que
temporadas cubre el historial y si una version nueva entro sin nombre
(con mapas u operadores desconocidos), sin abrir partida por partida.

## Criterios de aceptacion

- [x] Una funcion de agregado agrupa `Match` por `game_version` (y
      `code_version` como orden) con `Count`, `Min(played_at)` y
      `Max(played_at)`; ordenada de la version mas nueva a la mas vieja.
      Test con tres partidas en dos versiones.
- [x] Las partidas con `game_version` vacio o nulo salen en una fila
      "Sin versión", al final. Test.
- [x] La tabla va en un endpoint que Datos ya consulta
      (`/api/import/status/` o `/api/unknown/`, lo elige el diseno), sin
      POST nuevo y sin columna ni migracion. Base vacia: lista vacia, 200.
- [x] `Datos.jsx` muestra la tabla (versión, partidas, primera, última)
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

Dev 20261113T1926Z-cNCxUZs, sobre `origin/dev@9ed994a`. Diseño completo.

- `unknowns.py`: `partidas_por_version()` al final de `# --- descubrimiento`; `order_by()` vacío antes del GROUP BY; orden por `-code_version` y, a igual código, por la última partida; las de `game_version` vacío al final. `views.import_status` suma `versions`.
- Tests (`test_versiones_del_juego.py`, vistos en rojo por `ImportError` antes del código): `test_agrupa_por_version_con_primera_y_ultima`, `test_sin_version_va_al_final`, `test_a_igual_codigo_va_primero_la_usada_mas_tarde` (extra), `test_el_orden_del_modelo_no_parte_las_filas`, `test_import_status_trae_versions_y_base_vacia_da_lista_vacia`.
- `Datos.jsx`: `<h3>Partidas por versión del juego</h3>` y `DataTable` (Versión, Partidas, Primera, Última; CSV `partidas-por-version`) al final del panel Importación.
- e2e: `Datos muestra las partidas por version del juego` (filas == `versions` de la API, primera fila = `versions[0]`) y `Datos ordena las versiones del juego como la API, no como texto` (respuesta con Y10S4, Y9S4 y sin versión inyectada sobre la real).
- `metricas.md`: sección `## Datos` con la fila.

Desvío del diseño: el diseño decía "sin `initialSort`, el orden lo da la API", pero `DataTable` siempre ordena (sin `initialSort`, por la primera columna como texto: "Y9S4" antes que "Y10S4"). Cada fila lleva `posicion` (índice de la API) y la tabla arranca con `initialSort` por ella. El segundo e2e lo fija: con el `initialSort` quitado cae (`toContainText` en la primera fila) y con él pasa.

Revisión ciega (`omc-code-reviewer`, `revision.md`, eje de estándares): 1 HIGH (el orden de arriba) y 1 MEDIUM (el e2e con `seed_demo` no podía verlo: una sola fila "Sin versión"), los dos corregidos como dice el desvío. `seed_demo` no se tocó: cambiaría los números de otros e2e.

P4 en el camino: `verificar.sh` dio ROJO en 69339eb por el e2e de la 126 (`Operadores muestra a qué operador cambias tras perder`, ya en dev): `request fallida: /api/filters/ (net::ERR_ABORTED)`. Causa: el segundo `page.goto('/operadores?side=Attack')` aborta la request de `/api/filters/` que la primera carga todavía tenía en vuelo, y `vigilarConsola` la cuenta; intermitente (pasó en las tres corridas anteriores). Arreglo: `await page.waitForLoadState('networkidle')` antes de ese `goto`, como los tests de las líneas ~1524 y ~1550.

Verificacion: `verificar.sh` VERDE e4d26b5cb (1266 tests backend, 399 vitest, 109 e2e).

Skills del repo: testing-strategy (Django para la agrupación, el orden y el GROUP BY; e2e para el render y el orden en el cliente; sin vitest: no hay lógica pura nueva fuera del componente). modern-web-guidance: sin guía aplicada, la tabla reusa `DataTable` y `Panel` de `ui.jsx`. ux-copy: "Sin versión" y "Todavía no hay partidas importadas." en el tono de la página.
Skills: ninguna de afuera.
OMC: plan=— · revisión=2 hallazgos (2 arreglados) · verificación=—

## Revision 2026-11-13 sobre 0bd7e6f

(revisor 20261113T1926Z-cq9nfTP) Punto de partida: la rama no contenia `origin/dev` (entraron 122 y 126); `git merge origin/dev` limpio (0bd7e6f) y `verificar.sh`: VERDE 0bd7e6f46 (1271 backend, 402 vitest, 109 e2e).

**Eje de estandares** (`omc-code-reviewer` ciego, prompt de `revision.md`, 192 lineas en 6 archivos; un solo tema, sin POST ni red: sin eje de seguridad): aprobar, 0 hallazgos. Confirmado leyendo el codigo: `game_version` y `code_version` no admiten nulos (`models.py:81-82`), asi que no hay grupo `NULL` junto al `""` ni `None` contra `int` en el `sorted`; el `order_by()` vacio evita que `ordering = ["-played_at"]` parta el GROUP BY (lo fija `test_el_orden_del_modelo_no_parte_las_filas`); el sort estable deja "Sin versión" al final aun con codigo alto; `USE_TZ = False`, el `slice(0, 10)` no corre el dia.

**Ficha.** Criterio 1: `test_agrupa_por_version_con_primera_y_ultima` (+ `test_a_igual_codigo_va_primero_la_usada_mas_tarde`); 2: `test_sin_version_va_al_final`; 3: `test_import_status_trae_versions_y_base_vacia_da_lista_vacia` (`/api/import/status/`, sin POST ni migracion); 4: e2e `Datos muestra las partidas por version del juego` y `Datos ordena las versiones del juego como la API, no como texto`. Diff dentro de `archivos:`; el `waitForLoadState('networkidle')` en el e2e de Operadores (126) esta explicado como P4 en Implementacion. `metricas.md` con la fila en `## Datos`; identificadores sin tildes, UI con tildes; sin `print` ni `console.log`.

Nota menor, no es hallazgo: la tabla nueva muestra las fechas `AAAA-MM-DD` y el resto de Datos `DD-MM` (`Datos.jsx:7`); si se quiere uniformar, reusar `fecha`.

Veredicto: aprobar.

Skills del repo: ninguna (revision con `revision.md`).
OMC: plan=— · revisión=0 hallazgos · verificación=—

## QA 2026-11-13 sobre 2cdd4b8

(qa 20261113T2003Z-c3vr7mZ) Rama con `origin/dev@f6cd92d` fusionado (entro la 123), merge limpio.

- `verificar.sh`: VERDE 2cdd4b862 en 196 s (1284 tests backend, 405 vitest, 111 e2e).
- Base vacia (`SQLITE_PATH` y `R6_ENV_FILE` temporales, `migrate`, `runserver 8124`): `curl -s localhost:8124/api/import/status/` -> 200, `versions == []`.
- Base sembrada con `make_match` (script en el scratchpad): Y10S3 code 20 x2 (2026-09-01 y 09-05), Y10S4 code 30 x1, `""` code 99 x1, Y9S4 code 10 x1. La API: Y10S4 1, Y10S3 2 (first 2026-09-01T20:00, last 2026-09-05T21:00), Y9S4 1, `""` 1 al final pese al code 99. Recalculado a mano: coincide.
- Borde: `?until=foo`, `?page=-1`, `?side=`, `?x=%00` -> 200; vecino `/api/unknown/` 200; `POST /api/import/status/` -> 403; `/datos` -> 200.
- Playwright en `/datos` (accessibility-review): heading presente; filas en el orden de la API (Y10S4, Y10S3, Y9S4, Sin versión), no por texto; encabezados botones alcanzables con Tab y Enter ordena; contraste de celda 14.17:1; consola sin errores ni warnings. 0 Critical, 0 Major en lo nuevo. Ya estaba: `DataTable` no pone `aria-sort` en los encabezados (WCAG 4.1.2), va como idea.
- Chunk inicial `index-*.js` 200116 bytes; Datos es chunk lazy propio: sin crecimiento del inicial atribuible.
- validate-data sobre la fila de `metricas.md`: conteo y fechas min/max, sin division ni promedio; sin redondeo.
- Mutacion (`tests.test_versiones_del_juego`): quitar el `sort` de "sin version al final" -> FAILED (1); `reverse=False` -> FAILED (2); quitar `versions` de la vista -> FAILED (errors=1); quitar el `order_by()` vacio -> OK. Sobrevive porque en Django 5.2.19 `values().annotate()` ya no mete `Meta.ordering` en el GROUP BY (`str(q.query)`: `GROUP BY 1`): el `order_by()` es defensivo y su comentario sobreestima. LOW, no es criterio.

Veredicto: aprobado.

Skills del repo: accessibility-review (0 Critical, 0 Major; aria-sort preexistente), validate-data (Y10S3 2 partidas 09-01 a 09-05, recalculado).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

(nada)
