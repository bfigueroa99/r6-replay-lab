# 74. La version del mapa tambien en el Inicio, Clutch por mapa, Mapas que mejoran y el CSV de partidas

estado: en curso 2026-11-04
candado: dev 2026-11-04T20:05Z
rama: claude/equipo-dev/74-version-del-mapa-en-el-resto-de-pantallas
tipo: funcionalidad
epica: temporada-y-modo
area: backend
prioridad: 2
fuente: idea A8 de `ALCANCE.md`, tramo siguiente que dejo escrito el `## Fuera de alcance` de la ficha 70 ("Mejor y peor mapa", "Clutch por mapa y sitio", progreso por mapa y Duelos siguen por slug: otra ficha de la epica) y la QA de la 71 (tabla `matches` de Exportar sin version). En `dev` bcdbdf5: `matches_summary` agrupa por `map_slug` (`replays/analytics/aggregates.py:1031`), `clutch_by_site` por `round__match__map_slug` (`:1603`), el corte por mapa de `compare_periods` por `("round__match__map_slug", "round__match__map_name")` (`:2448`)
archivos: backend/replays/analytics/aggregates.py, backend/tests/test_aggregates.py, backend/tests/test_compare.py, backend/tests/test_export.py, frontend/src/pages/Teammates.jsx, frontend/src/pages/Trends.jsx, docs/metricas.md
turnos: po 20261104T1206Z-c8cAo8L, arquitecto 20261104T1604Z-cAKAGx1, dev 20261104T2004Z-cGQmDVc

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Desde la ficha 70 la pagina Mapas separa "Consulate (Y10)" de la Consulate
vieja, pero el Inicio todavia puede nombrar "Consulate" como tu peor mapa
sumando dos layouts distintos, y Clutch por mapa y sitio mezcla sitios de
dos mapas que solo comparten el nombre. Con este tramo cada pantalla por
mapa habla de la misma fila que Mapas, con la misma etiqueta, y el CSV de
partidas dice que version se jugo.

## Criterios de aceptacion

- [ ] `GET /api/overview/`, bloque `matches_summary` (`views.py:209`): con partidas de un mismo `map_slug` en dos `map_id` de `MAPS` distintos, cada version cuenta por separado para la muestra minima y el winrate, y `best_map`/`worst_map` traen la etiqueta de `etiquetas_de_version` ("Consulate (Y10)"). Test con dos versiones donde juntas darian otro mejor mapa que separadas.
- [ ] `clutch_by_site` (Tendencias, Clutch por mapa y sitio): una fila de mapa por `(map_slug, map_id)` con su etiqueta, y los sitios de cada version debajo de la suya. Test: dos versiones del mismo slug con un sitio de igual nombre no suman sus intentos.
- [ ] El corte por mapa de `compare_periods` (Mapas que mejoran y empeoran, ficha 56) separa versiones con la misma clave y etiqueta; un mapa con una sola version sigue saliendo con su nombre pelado, igual que en Mapas.
- [ ] `GET /api/export/?table=matches` agrega la columna con la etiqueta de version (o `map_id`, lo decide el Arquitecto) sin cambiar el orden ni el nombre de las columnas que ya existen.
- [ ] Con la base de `seed_demo` (todos los `map_id = 0`) los numeros que afirma el e2e no cambian, y `npm run e2e` sigue en verde.

## Fuera de alcance

La lista de mapas de cada rival en Duelos (`_agregar_mapas`, texto suelto sin
numeros); filtro de temporada (A3); selector "juntar versiones"; el Coach
(sus señales por mapa leen `by_map`, que ya separa). Sin migracion ni
`recompute`: es todo al consultar.

## Diseno

Una sola forma obvia: repetir en cuatro lugares lo que la ficha 70 ya hizo en
`by_map`/`by_site`. Sin arena ni consenso: es al consultar, sin migracion ni
`recompute`, y se deshace con un revert.

**Etiqueta.** En 2, 3 y 4 la etiqueta sale de `etiquetas_de_mapas(slugs)`
(`aggregates.py:500`), la que usa el detalle de partida (`views.py:538`): mira
todas las partidas del slug, asi el "(id N)" no depende de que filas trajo el
filtro. En 1, `etiquetas_de_version` sobre las versiones de la muestra (ver
abajo por que). Clave siempre `(map_slug, map_id)`.

**1. `matches_summary`** (`backend/replays/analytics/aggregates.py:1007`).
- `.values(...)` suma `"map_id"`. `por_mapa` se indexa por
  `(p["map_slug"], p["map_id"])` y cada entrada lleva `slug`, `map_id` y
  `map_name` = el nombre de la partida mas reciente de esa version (el bucle
  ya va en orden de fecha: se conserva el `m["map"] = p["map_name"]` actual,
  renombrado a `map_name`).
- Despues del bucle, `etiquetas = etiquetas_de_version(por_mapa.values())` y
  `m["map"] = etiquetas[(m["slug"], m["map_id"])]`; `map_name` se saca de la
  salida. **Aca no se usa `etiquetas_de_mapas`**: ordena por nombre y tomaria
  "Club House" en vez del mas reciente, y rompe
  `tests/test_resumen_partidas.py:101` (`test_variantes_del_mapa_cuentan_juntas`:
  mismo slug y mismo `map_id = 0`, nombre renombrado), que tiene que seguir
  pasando sin cambios. Se actualiza el comentario "Por slug: ..." a "Por
  version (`slug`, `map_id`): ...".
- `best_map`/`worst_map` traen `slug`, `map_id`, `map` (etiqueta), `matches`,
  `wins`, `winrate`. `Dashboard.jsx:251-252` lee `.map`: no cambia.

**2. `clutch_by_site`** (`aggregates.py:1593`).
- `.values("round__match__map_slug", "round__match__map_id", "round__match__map_name", "round__site")`.
- `mapas` indexado por `(slug, map_id)`; nombre = etiqueta de
  `etiquetas_de_mapas`. `_fila` agrega `"map_id"`. Orden: por etiqueta y
  despues por la clave (`key=lambda par: (par[1]["map"], par[0])` sigue
  valiendo con la tupla).
- `frontend/src/pages/Teammates.jsx:305`: `rowKey` pasa a
  `` `${row.slug}-${row.map_id}-${row.kind}-${row.site}` ``; sin eso dos
  versiones repiten la key de React y la consola del e2e se ensucia.

**3. Corte por mapa de `compare_periods`** (`aggregates.py:2445-2452`).
- `campos = ("round__match__map_slug", "round__match__map_id")`, `labels =
  ("slug", "map_id")`: sin `map_name` en la agrupacion, asi un renombre dentro
  de la misma version no parte la fila. Despues de `_corte_por_periodo`, una
  funcion chica `_etiquetar_corte(filas)`: `etiquetas = etiquetas_de_mapas({f["slug"] for f in filas})`
  y `f["map"] = etiquetas.get((f["slug"], f["map_id"]), f["slug"])`.
  `_corte_por_periodo` no cambia: la union entre periodos ya es por la tupla
  de labels, y su orden (`str` de cada label) queda slug y despues `map_id`.
  `tests/test_compare.py:180` (`club["map"] == "Club House"`) sigue pasando:
  con `map_id = 0` la etiqueta es el nombre guardado.
- `frontend/src/pages/Trends.jsx:59`: la key de `TablaDeCambio` pasa a
  `${row.slug}-${row.map_id}` cuando la fila trae `slug`, y la de operador
  (`${row.operator}-${row.side}`) igual que hoy.

**4. CSV de partidas** (`trend_by_match`, `aggregates.py:1279`, que exporta
`export.py:29`).
- `.values(...)` suma `"round__match__map_slug"` y `"round__match__map_id"`
  (la fila sigue siendo una por partida: los dos son de la partida). Se sacan
  de la fila con `pop` y se escribe una sola clave nueva **`map_version`**
  (etiqueta de `etiquetas_de_mapas`). Decision: etiqueta y no `map_id`, porque
  `map_id` esta en `_PRIMERAS` (`export.py:47`) y moveria las columnas que ya
  existen; `map_version` no esta, asi que cae al final del CSV y el orden de
  las demas no cambia. `map` sigue siendo el nombre guardado.
- `trend_by_match` tambien alimenta Tendencias (`views.py:257`) y el Coach
  (`coach.py:710`): una clave mas en cada fila no cambia nada que lean.

**Tests**, en `backend/tests/test_aggregates.py`, clase `VersionesDeMapaTests`
(`:200`, ya tiene Y7 y Y10 de Consulate) o una clase hermana con fixture
propio donde haga falta:
- `test_mejor_y_peor_mapa_separan_las_versiones`: Consulate Y7 3 de 3
  partidas ganadas, Consulate Y10 0 de 3, Border 2 de 3. Juntas, Consulate
  seria 3/6 = 50 %: mejor Border (67 %) y peor "Consulate". Separadas: mejor
  "Consulate (Y7)" (100 %) y peor "Consulate (Y10)" (0 %). Afirma `map`,
  `map_id` y `winrate` de los dos.
- `test_una_version_sin_muestra_minima_no_entra`: Y7 con 2 partidas y Y10 con
  2: juntas pasarian `MIN_PARTIDAS_MAPA = 3`, separadas ninguna es candidata.
- `test_clutch_por_sitio_separa_el_mismo_sitio_en_dos_versiones`: un clutch
  en "1F Lobby" en cada version: dos filas `map` y dos `site`, cada una con 1
  intento, etiquetas "Consulate (Y7)" y "Consulate (Y10)".
- `test_progreso_por_mapa_separa_versiones` (en `tests/test_compare.py`, que
  ya prueba `compare_periods`): dos versiones con muestra en los dos periodos
  salen en dos filas con su etiqueta; un mapa de una sola version sale con el
  nombre pelado.
- `test_csv_de_partidas_dice_la_version` (en `tests/test_export.py`): la
  columna `map_version` existe, vale "Consulate (Y10)" en esa partida, y las
  columnas anteriores del CSV conservan su orden (comparar la cabecera sin
  `map_version` contra la de antes, armada en el test).
- Los tests existentes de `matches_summary` (`tests/test_resumen_partidas.py`)
  y de `clutch_by_site` (`tests/test_clutch.py`) tienen que seguir pasando sin
  cambios: con `map_id = 0` en todo el fixture la clave nueva no parte nada.
  Si alguno compara un dict entero de `best_map`, se le suma `map_id` y
  nada mas.

**Orden:** 1, 2, 3, 4 (cada uno con su test), las dos keys del frontend,
`metricas.md`, `npm run build`, `check.sh`.

**`docs/metricas.md`**, fila **Mapa** (`:245`): la ultima oracion ("**Mejor y
peor mapa**, **Clutch por mapa y sitio** y el progreso por mapa de Tendencias
siguen juntando las versiones por slug.") pasa a decir que esas tres tambien
separan por version con la misma etiqueta, que el CSV de partidas trae la
columna `map_version`, y que lo unico que sigue por slug es la lista de mapas
de cada rival en Duelos. Sin fila nueva: no hay numero nuevo.

**Que puede romperse:** el e2e no (con `seed_demo` todo `map_id = 0` y una
version por slug: mismas etiquetas, mismos numeros). Si `seed_demo` alguna vez
tuviera dos `map_id` por slug, el e2e de Inicio podria cambiar de mejor mapa.
Keys de React duplicadas si se olvida una de las dos keys del frontend: la
consola del e2e lo veria solo con datos de dos versiones, asi que el test
backend es el que lo protege; el Revisor lo mira a mano.

**Verificacion manual (PC con base real que tenga Consulate vieja y Y10):**
Inicio muestra "Consulate (Y10)" si es tu mejor o peor; Compañeros > Clutch
por mapa y sitio muestra dos bloques de Consulate; `/api/export/?table=matches`
trae `map_version` al final.

Skills: no aplica (dominio que el repo ya resuelve: ficha 70).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Verificar en el PC

## Pendiente

## Para el humano
