# 70. Cada version de un mapa en su propia fila

estado: entregado
candado: -
rama: claude/equipo-dev/70-mapas-por-version
tipo: funcionalidad
epica: temporada-y-modo
area: fullstack
prioridad: 2
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (ficha 49, descartada como bug; idea A4 de `ALCANCE.md`). Camino que dejo el Arquitecto en la 49: agrupar por `Match.map_id` (`ingest.py:160`) con la etiqueta del identificador de `MAPS`
archivos: backend/pydissect/header.py, backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/export.py, frontend/src/mapas.js (nuevo), frontend/src/mapas.test.js (nuevo), frontend/src/components/Filters.jsx, backend/tests/test_pydissect.py, backend/tests/test_aggregates.py, backend/tests/test_api.py, backend/tests/test_export.py, backend/tests/test_coach.py, docs/metricas.md
turnos: po 20261029T0004Z, arquitecto 20261029T0404Z, dev 20261030T0404Z, revisor 20261030T0804Z, qa 20261030T1204Z, release 20261030T1204Z

## PR

Titulo: `[equipo-dev][backend] Cada version de un mapa en su propia fila`

### Que cambia

Consulate, Club House, Bank y los demas mapas rehechos dejan de sumarse con
su version vieja: las tablas de mapas, sitios y spawns (CSV de
`/api/export/`) y las señales del Coach muestran "Consulate (Y7)",
"Consulate" y "Consulate (Y10)" por separado. El selector de mapa ofrece
cada version debajo del mapa (`?map=<map_id>`); `?map=<slug>` sigue juntando
todas. Sin migracion ni reimportar: `map_id` ya estaba guardado.

### Por que esto y no otra cosa

Decision del humano del 2026-10-28 (ficha 49 descartada como bug, idea A4).
Clave `(map_slug, map_id)` y no `map_id` solo: `seed_demo` y los tests dejan
`map_id = 0` en todos los mapas. Filtro con digitos en `map` en vez de una
clave nueva: no toca `FILTER_KEYS` ni la URL.

### Como se probo

- `./scripts/check.sh`: 838 tests backend (4 omitidos), 133 vitest, build
  ok, 53 e2e, `Todo en verde.`
- Tests nuevos: `EtiquetaDeVersionTests` (Y7, Y10, Y11, sin sufijo, id fuera
  de `MAPS`), `VersionesDeMapaTests` (by_map, by_site, by_spawn, filtros por
  slug y por id, `?map=` raro, id nombrado igual que una version),
  `test_filters_ofrece_las_versiones_solo_si_hay_dos`,
  `test_match_list_filtra_por_map_id`,
  `test_el_csv_de_mapas_trae_una_fila_por_version`,
  `test_la_senal_de_peor_mapa_nombra_la_version`, `mapas.test.js`.
- QA: `runserver` sobre base sembrada con ConsulateY7 y ConsulateY10 y sobre
  base vacia; 16 rutas GET con `?map=` borde, todas 200; 5 mutaciones, las 5
  caen (ver `## QA`).

### Riesgos y lo que no entra

Los minimos del Coach (15 rondas por mapa, 8 por sitio/spawn) se cuentan
por version: un mapa repartido entre versiones puede perder su señal.
Fuera: "Mejor y peor mapa", "Clutch por mapa y sitio", progreso por mapa de
Tendencias y Duelos siguen por slug; listado y detalle de partida muestran
el nombre a secas.

### Como probarlo en 2 minutos

```
cd backend; python manage.py test tests.test_aggregates.VersionesDeMapaTests tests.test_api.VersionesDeMapaApiTests tests.test_pydissect.EtiquetaDeVersionTests
python manage.py runserver
curl "http://127.0.0.1:8000/api/filters/"              # maps[].versions si tenes dos versiones de un mapa
curl "http://127.0.0.1:8000/api/export/?table=maps"     # una fila por version, columna map_id
```

### Para el humano

Nada. La etiqueta "(Y10)" es la variante conservadora; el año del rework se
cambia en `etiqueta_de_version`.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Consulate, Club House o Fortress rehechos son otro mapa con el mismo nombre,
y hoy sus rondas se suman con las de la version vieja. Con esto cada version
tiene su fila ("Consulate" y "Consulate (Y10)") con sus propios winrates por
lado y sitios.

## Criterios de aceptacion

- [x] `by_map` separa ConsulateY7 (ataque 75) y ConsulateY10 (ataque 0); un mapa con una version sigue con su nombre. Agrupa por `(map_slug, map_id)`.
- [x] La etiqueta sale de `MAPS` (sufijo `Y<n>`) con `etiqueta_de_version`, pura y testeada.
- [x] `by_site` y `by_spawn` separan por version; `?map=<slug>` junta, `?map=<map_id>` elige una; el selector ofrece las versiones.
- [x] CSV `table=maps`, señales del Coach de mapa, sitio y spawn con versiones separadas.
- [x] Sin migracion; fila **Mapa** de `docs/metricas.md` reescrita.

## Fuera de alcance

Selector "juntar versiones"; filtro de temporada (A3); Villa Y11S3 (sin
ID nuevo); listado, records, sesiones y detalle de partida; IDs que faltan
en `MAPS`; "Mejor y peor mapa", "Clutch por mapa y sitio", progreso por mapa
y Duelos siguen por slug (otra ficha de la epica si se quieren por version).

## Diseno

Arquitecto 20261029T0404Z. Clave `(map_slug, map_id)`; etiqueta estatica
desde `MAPS`; `filtro_mapa` con digitos = `map_id`; `/api/filters/` con
`versions` solo si el slug tiene dos o mas. Detalle completo en `git log`.

## Implementacion

Dev 20261030T0404Z. Diseno completo. Desvios: `filtro_mapa` exige
`isascii()` y `< 2**63` (`?map=²` daba 500); un id fuera de `MAPS` nombrado
igual que una version lleva "(id N)"; versiones del selector ordenadas por
`map_id`.

## Revision 2026-10-30 sobre c7548d8

Revisor 20261030T0804Z: revision ciega sin hallazgos, `check.sh` en verde.
Veredicto: aprobar -> `revisado`.

## QA 2026-10-30 sobre f16a36a

QA 20261030T1204Z. Rama con `origin/dev@1c92273` ya incluido.

- `./scripts/check.sh` -> `Todo en verde.`: 838 tests (4 omitidos), 133 vitest, build ok, 53 e2e.
- Base sembrada (script en el scratchpad con `factories`: ConsulateY7 3/4 ataques ganados, ConsulateY10 0/4, Kanal, Club House con `map_id=0`, una ronda sin bajas) y `runserver`:
  - `/api/filters/` -> Consulate con `versions` [Y7 2609221242, Y10 418126004176]; Kanal y Club House con `versions: []`. Criterio 3.
  - `/api/export/?table=maps` -> "Consulate (Y7)" `attack_winrate` 75.0 y "Consulate (Y10)" 0.0, columna `map_id`; Club House con id 0 en su fila. Criterios 1 y 4.
  - `table=sites` y `table=spawns` -> "1F Tellers" y "Garage" en dos filas, una por version. Criterio 3.
  - `/api/matches/?map=418126004176` -> 2 partidas (solo Y10); `?map=consulate` -> 3. `/api/export/?table=maps&map=2609221242` -> solo la fila Y7.
- Barrido de las 16 rutas GET (`health`, `filters`, `overview`, `coach`, `operators`, `operators/catalog`, `trends`, `teammates`, `duels`, `sessions`, `compare`, `matches`, `export`, `unknown`, `import/status`, `import/progress`) con `map=418126004176`, `map=²`, `map=99999999999999999999999`, `map=-1`, `map=`, `map=0`, `map=1.5`, `map=consulate&side=Attack`, `until=foo&map=...`, `page=-1&map=...`, en base sembrada y en base vacia: todas 200, cero tracebacks en el log.
- Chunk inicial: `index-*.js` 188.72 kB en `origin/dev` -> 188.91 kB (+0.1 %).
- Mutaciones (todas caen): `filtro_mapa` ignora digitos -> 2 fallos; etiqueta sin sufijo -> 8 fallos; sin "(id N)" -> `test_un_id_nombrado_igual_que_una_version_lleva_el_id`; lados de `by_map` por `(slug, side)` -> `test_by_map_separa_las_versiones_de_un_mapa`; `opcionesDeMapa` con slug como valor -> vitest `con dos versiones...`.

Veredicto: `aprobado`. No toca migraciones, `recompute`, parser (solo una funcion pura nueva en `header.py`, no el decodificado), Electron ni `.ps1`: sin `## Verificar en el PC`.

## Para el humano

Nada pendiente (decision tomada el 2026-10-28).
