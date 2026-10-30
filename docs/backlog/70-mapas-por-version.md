# 70. Cada version de un mapa en su propia fila

estado: revisado
candado: -
rama: claude/equipo-dev/70-mapas-por-version
tipo: funcionalidad
epica: temporada-y-modo
area: fullstack
prioridad: 2
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (ficha 49, descartada como bug; idea A4 de `ALCANCE.md`). Camino que dejo el Arquitecto en la 49: agrupar por `Match.map_id` (`ingest.py:160`) con la etiqueta del identificador de `MAPS`
archivos: backend/pydissect/header.py, backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/export.py, frontend/src/mapas.js (nuevo), frontend/src/mapas.test.js (nuevo), frontend/src/components/Filters.jsx, backend/tests/test_pydissect.py, backend/tests/test_aggregates.py, backend/tests/test_api.py, backend/tests/test_export.py, backend/tests/test_coach.py, docs/metricas.md
turnos: po 20261029T0004Z, arquitecto 20261029T0404Z, dev 20261030T0404Z, revisor 20261030T0804Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Consulate, Club House o Fortress rehechos son otro mapa con el mismo nombre,
y hoy sus rondas se suman con las de la version vieja en Mapas, sitios y el
Coach. Con esto cada version tiene su fila ("Consulate" y "Consulate (Y10)")
con sus propios winrates por lado y sitios, y ves si el rework te cambio el
mapa.

## Criterios de aceptacion

- [ ] Con partidas en `ConsulateY7` (3 de 4 rondas de ataque ganadas) y en
      `ConsulateY10` (0 de 4), `by_map` devuelve dos filas con
      `attack_winrate` 75 y 0 y `map` "Consulate (Y7)" y "Consulate (Y10)"
      (o el nombre base para la version sin sufijo); un mapa con una sola
      version sigue con su nombre de siempre. Agrupa por `Match.map_id`.
- [ ] La etiqueta sale de la tabla `MAPS` de `pydissect/constants.py` (el
      sufijo `Y7`/`Y10`/`Y11` del identificador interno) con una funcion
      pura y testeada, no de una lista a mano en Django.
- [ ] `by_site` y `by_spawn` separan por version: el mismo nombre de sitio
      en dos versiones son dos filas. El filtro de mapa (`?map=`) sigue
      aceptando el slug de siempre (todas las versiones) y ademas elige una
      version sola; el selector de la UI ofrece las versiones.
- [ ] El CSV `/api/export/?table=maps`, la pagina Mapas y las señales de mapa,
      sitio y spawn del Coach muestran las versiones separadas (test sobre una
      base sembrada con las dos versiones; e2e de Mapas al dia si
      `seed_demo` cambia).
- [ ] Sin migracion ni reimportar: `map_id` ya esta guardado. `docs/metricas.md`
      dice en las filas de mapas y sitios que se agrupa por version del mapa.

## Fuera de alcance

- Selector "juntar versiones" en la tabla.
- Filtro de temporada (A3).
- Mapas que cambiaron sitios sin ID nuevo (Villa Y11S3): sin dato.
- Otros usos de `map_name` que muestran una partida y no agregan (listado,
  records, sesiones, detalle de partida).
- IDs que faltan en `MAPS` (idea P1): una version sin entrada sigue saliendo
  como `Unknown(<id>)`.
- (Arquitecto) "Mejor y peor mapa" del Resumen (`matches_summary`), "Clutch
  por mapa y sitio" (`clutch_by_site`), el progreso por mapa de Tendencias
  (`_corte_por_periodo` con `map_slug`) y los mapas de Duelos: siguen por
  slug. Si se quieren por version, otra ficha de la misma epica.
- (Arquitecto) No existe una pagina "Mapas": las tablas de mapas, sitios y
  spawns le llegan al usuario por el CSV de `/api/export/` y por las señales
  del Coach. El criterio 4 se cumple sobre esas dos.

## Diseno

Arquitecto 20261029T0404Z, sobre `origin/dev@c3597f4`. Ninguna rama de
trabajo abierta. Toca `docs/metricas.md` como #67 y #68, pero en filas
distintas: no hace falta orden.

**Hallazgo que cambia la forma: la clave no puede ser `map_id` solo.**
`seed_demo` y `tests/factories.py` crean partidas con `map_id = 0` (el
default del modelo): agrupar solo por `map_id` juntaria todos los mapas del
seed en una fila. La clave de agrupado es `(map_slug, map_id)`: el slug
separa mapas como hoy y el `map_id` separa versiones dentro de un slug. Con
`map_id = 0` cada slug tiene una sola version y nada cambia (seed, e2e y
tests actuales intactos).

**Etiqueta, estatica y sin mirar la base.** `MAPS` ya trae el sufijo en el
identificador interno (`ConsulateY7`, `ConsulateY10`, `CoastlineY11`). Regla:
si el identificador termina en `Y<n>`, la etiqueta es `"<nombre> (Y<n>)"`; si
no, el nombre a secas. Consulate queda en tres filas: "Consulate (Y7)",
"Consulate" y "Consulate (Y10)". Kanal, que tiene una sola version, sigue
"Kanal". Un `map_id` fuera de `MAPS` (0, desconocido, o etiquetado por el
usuario en Datos via overrides) usa el `map_name` guardado tal cual. No se
calcula "solo si hay dos versiones en tu base": la misma partida tendria otra
etiqueta segun lo que importaste despues.

**Filtro de mapa, un solo parametro.** `?map=<slug>` sigue igual (todas las
versiones). `?map=<digitos>` filtra por `map_id` (una version). Ningun slug es
solo digitos (`map_slug` sale del nombre; los desconocidos son
`unknown-<id>`), asi que no hay ambiguedad y no hace falta una clave nueva en
`FILTER_KEYS` ni en los filtros de la URL del frontend.

`archivos:` y por que:

- `backend/pydissect/header.py`: funcion pura
  `etiqueta_de_version(map_id: int, nombre: str) -> str` junto a `map_name` y
  `map_slug` (la tabla `MAPS` vive en `pydissect/`; sin Django). Lee solo
  `MAPS` (no `extra_map` ni `record_unknown`: no tiene que anotar
  desconocidos al consultar). `nombre` vacio -> `MAPS[id][1]`.
- `backend/replays/analytics/aggregates.py`:
  - helper `filtro_mapa(valor: str, prefijo: str = "round__match__") -> dict`
    -> `{f"{prefijo}map_id": int(valor)}` si `valor.isdigit()`, si no
    `{f"{prefijo}map_slug": valor}`. `base_queryset` (l.52) lo usa.
  - helper `_etiquetar(rows)`: a cada fila con `map_id` y `map_name` le pone
    `row["map"] = etiqueta_de_version(...)` y quita `map_name`.
  - `by_map`: `group_by(qs, "round__match__map_slug", "round__match__map_id",
    "round__match__map_name", labels=("slug", "map_id", "map_name"), ...)` y
    `_etiquetar`. El dict de lados se indexa por `(slug, map_id, side)` (hoy
    por `(map_name, side)`, que juntaria las versiones).
  - `by_site` y `by_spawn`: mismo cambio, agrupando ademas por
    `round__site` / `spawn`. Las filas siguen trayendo `map`, ahora con la
    etiqueta, asi que el Coach no cambia de codigo.
  - Docstring corto en `by_map` con el por que de `(slug, map_id)`.
- `backend/replays/views.py`: `filter_options` (l.153) arma `maps` como
  lista de `{map_slug, map_name, versions}`, donde `versions` es
  `[{"map_id", "label"}]` ordenada por etiqueta **solo si el slug tiene 2 o
  mas `map_id` distintos** (si no, lista vacia; el selector no se ensucia).
  `match_list` (l.372) usa `agg.filtro_mapa(valor, prefijo="")`. Buscar con
  `grep -n 'map_slug=' backend/replays` cualquier otro filtro por slug que
  venga de `filters["map"]` y pasarlo por el helper.
- `backend/replays/export.py`: `_PRIMERAS` suma `"map_id"` despues de
  `"slug"`.
- `frontend/src/mapas.js` (nuevo, logica pura): `opcionesDeMapa(maps)` ->
  lista plana `[{value, label}]`: por cada mapa su opcion de slug con
  `map_name`, y debajo una por version con `value = String(map_id)` y
  `label = "  · " + label` (con espacios de no separacion si hace falta
  para que se vea la sangria). `frontend/src/mapas.test.js` lo prueba.
- `frontend/src/components/Filters.jsx` (l.68): renderiza
  `opcionesDeMapa(data?.maps || [])`.
- `docs/metricas.md`: fila **Mapa** (l.245) reescrita: cada version de un mapa
  (`Match.map_id`, dentro del mismo `map_slug`) es su propia fila en las
  tablas de mapas, sitios y spawns (CSV) y en las señales del Coach de mapa,
  sitio y spawn; etiqueta del sufijo `Y<n>` del identificador en `MAPS`, la
  version sin sufijo con el nombre a secas; el filtro de mapa por slug junta
  las versiones y elegir una version filtra por `map_id`; **Mejor y peor
  mapa**, **Clutch por mapa y sitio** y el progreso por mapa siguen juntando
  por slug (ver Fuera de alcance). La fila **Mejor y peor mapa** (l.15) no
  cambia de texto.

Tests nuevos (nombres exactos):

- `backend/tests/test_pydissect.py` (o el archivo de tests de `header` que
  exista): `test_la_etiqueta_lleva_el_sufijo_de_la_version`
  (`ConsulateY10` -> "Consulate (Y10)", `ConsulateY7` -> "Consulate (Y7)"),
  `test_la_version_sin_sufijo_queda_con_el_nombre`
  (379218689149 -> "Consulate", Kanal -> "Kanal"),
  `test_un_id_fuera_de_la_tabla_usa_el_nombre_guardado` (0 y un id inventado).
- `backend/tests/test_aggregates.py` (con `factories`, `map_id` explicito):
  `test_by_map_separa_las_versiones_de_un_mapa` (ConsulateY7 3 de 4 ataques
  ganados, ConsulateY10 0 de 4 -> dos filas, `attack_winrate` 75 y 0,
  etiquetas "Consulate (Y7)" y "Consulate (Y10)"),
  `test_by_map_con_map_id_cero_no_junta_mapas_distintos` (Club House y Border
  con `map_id=0` -> dos filas, como hoy),
  `test_by_site_separa_el_mismo_sitio_en_dos_versiones`,
  `test_by_spawn_separa_por_version`,
  `test_el_filtro_por_slug_junta_las_versiones` y
  `test_el_filtro_por_map_id_elige_una_version`.
- `backend/tests/test_api.py`:
  `test_filters_ofrece_las_versiones_solo_si_hay_dos` y
  `test_match_list_filtra_por_map_id`.
- `backend/tests/test_export.py`:
  `test_el_csv_de_mapas_trae_una_fila_por_version` (y `map_id` como columna).
- `backend/tests/test_coach.py`:
  `test_la_senal_de_peor_mapa_nombra_la_version` (15+ rondas en ConsulateY10
  perdidas y en otro mapa ganadas -> el `scope` es "Consulate (Y10)").
- `frontend/src/mapas.test.js`: `sin versiones solo sale el mapa`,
  `con dos versiones salen debajo del mapa con su map_id como valor`.

Orden: (1) `etiqueta_de_version` + tests; (2) `filtro_mapa`, `by_map`,
`by_site`, `by_spawn` + tests; (3) `filter_options`, `match_list`, export;
(4) Coach (solo test); (5) frontend `mapas.js` + Filters; (6)
`metricas.md`; (7) `npm run build`, `check.sh`.

Que puede romperse:

- Tests que leen `by_map`/`by_site`/`by_spawn` comparando el dict entero: la
  fila gana `map_id`. Ajustar el esperado, no la funcion.
- `group_by` agrupa por `map_name` tambien: si un override renombro un mapa
  despues de importar partidas, salen dos filas del mismo `(slug, map_id)`.
  Ya pasaba hoy con `(map_name, slug)`; no empeora.
- `test_export.py` cuenta filas de `maps` (l.75-81) con `map_id=0`: no
  cambian.
- Los minimos por fila (Coach: 15 rondas por mapa, 8 por sitio y spawn)
  ahora se cuentan por version: un mapa con pocas rondas en cada version
  puede dejar de dar señal. Es lo esperado (cada version es otro mapa); no se
  bajan los umbrales.
- `?map=` con digitos que no existen da tablas vacias, igual que un slug
  inexistente hoy.
- e2e: `seed_demo` no cambia (todo `map_id=0`), los numeros tampoco. No hace
  falta tocar `frontend/e2e/`; si el selector cambia de forma visible,
  `humo.spec.js` sigue pasando porque no hay versiones en el seed.

Verificacion manual: base con dos partidas de Consulate (ids 2609221242 y
418126004176) via `factories`; `curl '/api/filters/'` trae las dos versiones;
`curl '/api/export/?table=maps'` dos filas; `curl '/api/coach/?map=418126004176'`
solo cuenta la Y10.

Sin migracion, sin umbral nuevo, sin fila nueva (se reescribe **Mapa**).

Skills: no aplica (no hay grafico ni tabla nueva: cambia la clave de
agrupado y un `<select>`). Sin arena: la forma del filtro tenia dos opciones
(clave nueva o digitos en `map`) y la de digitos gana sin discusion porque
no toca `FILTER_KEYS` ni la URL.

## Implementacion

Dev 20261030T0404Z, sobre `origin/dev@1c92273`. Diseno completo, sin migracion.

- `pydissect/header.py`: `etiqueta_de_version(map_id, nombre="")`, pura y sin
  Django; lee solo `MAPS`.
- `aggregates.py`: `filtro_mapa` (lo usa `base_queryset` y `match_list`);
  `by_map`, `by_site` y `by_spawn` agrupan por `(map_slug, map_id, map_name)`
  y las filas traen `slug`, `map_id` y `map` con la etiqueta. Los lados de
  `by_map` se indexan por `(slug, map_id, side)`.
- `views.py`: `/api/filters/` trae `maps[].versions` (`[{map_id, label}]`),
  vacia si el slug tiene una sola version. `export.py`: `map_id` entre las
  primeras columnas.
- Frontend: `mapas.js` (`opcionesDeMapa`) + `Filters.jsx`. Las versiones van
  con sangria de espacios de no separacion.
- `docs/metricas.md`: fila **Mapa** reescrita.

Desvios del diseno, por la revision ciega del Dev:

- `filtro_mapa` exige `isascii()` y `< 2**63`: `?map=²` daba 500 (`int()`
  lo rechaza) y un numero gigante desbordaba SQLite. Lo raro cae al slug y
  devuelve vacio. Test `test_un_map_raro_no_da_500`.
- `etiquetas_de_version` (en `aggregates.py`, usada por las tablas y por
  `/api/filters/`): un id que `MAPS` no conoce y que el usuario nombro en
  Datos igual que la version conocida compartia etiqueta con ella; ahora
  lleva "(id N)". Test `test_un_id_nombrado_igual_que_una_version_lleva_el_id`.
- Las versiones del selector van por `map_id` y no por etiqueta (por texto,
  "Y10" quedaba antes que "Y7"). En `MAPS` el id crece con la version.
- `test_match_list_filtra_por_map_id` comprueba la partida por `played_at`:
  `/api/matches/` no expone `map_id` y no hacia falta agregarlo.
- Tests extra: `sin datos no revienta` (vitest) y Coastline (Y11) en la
  etiqueta.

Criterios: 1 -> `VersionesDeMapaTests.test_by_map_*`; 2 ->
`EtiquetaDeVersionTests`; 3 -> `test_by_site_*`, `test_by_spawn_*`,
`test_el_filtro_por_*`, `test_filters_ofrece_las_versiones_solo_si_hay_dos`,
`mapas.test.js`; 4 -> `test_el_csv_de_mapas_trae_una_fila_por_version`,
`test_la_senal_de_peor_mapa_nombra_la_version` (`seed_demo` no cambia: e2e
igual); 5 -> sin migracion, fila **Mapa**.

Limite: `seed_demo` deja `map_id=0`, asi que el e2e no ve el selector con
versiones; lo cubren vitest y `test_api`.

Skills: no aplica (el diseno ya lo dijo; no hubo dominio nuevo).

## Revision 2026-10-30 sobre c7548d8

Revisor 20261030T0804Z. Rama ya al dia con `origin/dev@1c92273` (sin merge).
`check.sh` en `Todo en verde.`: 838 tests backend (4 omitidos, ninguno del
diff), 133 vitest, build ok, 53 e2e.

Revision ciega (subagente con `revision.md` sobre el diff sin
`docs/backlog`): sin hallazgos, veredicto aprobar. Confirmado por el lider:

- Todo filtro por `?map=` pasa por `filtro_mapa` (`base_queryset` y
  `match_list`); no queda ningun `map_slug=` con `filters["map"]` suelto.
  `matches_summary`, `clutch_by_site` y Tendencias parten de
  `base_queryset`, asi que elegir una version tambien los restringe (la
  agregacion por slug de esas tablas sigue como dice Fuera de alcance).
- `by_map` indexa los lados por `(slug, map_id, side)` pero agrupa las filas
  tambien por `map_name`: dos nombres para el mismo `(slug, map_id)` darian
  lados combinados. No pasa: `retag.py:81` reescribe nombre y slug de todas
  las partidas de un `map_id` juntas. No es hallazgo.
- Las etiquetas de `MAPS` no se repiten dentro de un slug (9 slugs con
  varias versiones); el id mas grande queda lejos de 2^53, `String(map_id)`
  en el frontend no pierde precision.
- `map_id = 0` (seed, factories): la clave `(slug, map_id)` separa por slug
  como antes; `versions` vacia.

Ficha:

- Criterio 1 -> `test_by_map_separa_las_versiones_de_un_mapa`,
  `test_by_map_con_map_id_cero_no_junta_mapas_distintos`.
- Criterio 2 -> `EtiquetaDeVersionTests` en `test_pydissect.py` (Y7, Y10,
  Y11, sin sufijo, id fuera de la tabla).
- Criterio 3 -> `test_by_site_*`, `test_by_spawn_*`, `test_el_filtro_por_*`,
  `test_filters_ofrece_las_versiones_solo_si_hay_dos`,
  `test_match_list_filtra_por_map_id`, `mapas.test.js`.
- Criterio 4 -> `test_el_csv_de_mapas_trae_una_fila_por_version`,
  `test_la_senal_de_peor_mapa_nombra_la_version`; `seed_demo` no cambia, el
  e2e sigue igual (limite anotado por el Dev: el e2e no ve versiones).
- Criterio 5 -> sin migracion; fila **Mapa** de `metricas.md` reescrita.
- El diff toca exactamente `archivos:`. Identificadores sin tildes, UI con
  tildes, sin `print` ni `console.log`.

Veredicto: aprobar -> `revisado`.

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Sin decision pendiente (la tomaste el 2026-10-28). La etiqueta "(Y10)" es la
variante conservadora; si preferis el año del rework, se cambia en una sola
funcion.
