# 74. La version del mapa tambien en el Inicio, Clutch por mapa, Mapas que mejoran y el CSV de partidas

estado: entregado
candado: -
rama: claude/equipo-dev/74-version-del-mapa-en-el-resto-de-pantallas
tipo: funcionalidad
epica: temporada-y-modo
area: backend
prioridad: 2
fuente: idea A8 de `ALCANCE.md`, tramo siguiente que dejo escrito el `## Fuera de alcance` de la ficha 70 ("Mejor y peor mapa", "Clutch por mapa y sitio", progreso por mapa y Duelos siguen por slug: otra ficha de la epica) y la QA de la 71 (tabla `matches` de Exportar sin version). En `dev` bcdbdf5: `matches_summary` agrupa por `map_slug` (`replays/analytics/aggregates.py:1031`), `clutch_by_site` por `round__match__map_slug` (`:1603`), el corte por mapa de `compare_periods` por `("round__match__map_slug", "round__match__map_name")` (`:2448`)
archivos: backend/replays/analytics/aggregates.py, backend/tests/test_aggregates.py, backend/tests/test_compare.py, backend/tests/test_export.py, frontend/src/pages/Teammates.jsx, frontend/src/pages/Trends.jsx, docs/metricas.md
turnos: po 20261104T1206Z-c8cAo8L, arquitecto 20261104T1604Z-cAKAGx1, dev 20261104T2004Z-cGQmDVc, revisor 20261105T0004Z-cXefbfB, qa 20261105T0215Z-cfTdV9W, release 20261105T0215Z-cfTdV9W

## PR

Titulo: `[equipo-dev][backend] La version del mapa tambien en el Inicio, Clutch por mapa, Mapas que mejoran y el CSV de partidas`

### Que cambia

Mejor y peor mapa del Inicio, Clutch por mapa y sitio (Compañeros) y Mapas que mejoran y empeoran (Tendencias) separan las versiones de un mapa rehecho con la misma etiqueta que la pagina Mapas ("Consulate (Y10)"), asi el Inicio ya no nombra "Consulate" sumando dos layouts ni Clutch suma sitios de dos mapas distintos. El CSV `table=matches` de Exportar suma la columna `map_version` al final, sin mover las demas.

### Por que esto y no otra cosa

Ficha 74, idea A8 de `ALCANCE.md` (epica `temporada-y-modo`): el tramo que dejaron pendiente la 70 y la QA de la 71. Repite en cuatro lugares lo que la 70 hizo en `by_map`/`by_site`, clave `(map_slug, map_id)`. Descartado: `map_id` como columna del CSV (esta en `_PRIMERAS` y moveria las columnas existentes) y `etiquetas_de_mapas` en el Inicio (tomaria el nombre alfabetico y romperia `test_variantes_del_mapa_cuentan_juntas`).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 05414be, 887 tests backend, 153 vitest, 54 e2e (QA); VERDE sobre el commit de entrega (Release).
- Tests nuevos: `MejorYPeorMapaPorVersionTests` (`test_mejor_y_peor_mapa_separan_las_versiones`: juntas darian otro mejor mapa; `test_una_version_sin_muestra_minima_no_entra`: 2+2 partidas), `VersionesDeMapaTests.test_clutch_por_sitio_separa_el_mismo_sitio_en_dos_versiones`, `CortesPorMapaYOperadorTests.test_progreso_por_mapa_separa_versiones` (y nombre pelado con una sola version), `VersionesDeMapaCsvTests.test_csv_de_partidas_dice_la_version` (cabecera sin mover). `test_resumen_partidas` y `test_clutch` pasan sin cambios.
- Manual (QA): `runserver` con bases sembradas desde `factories.py` (Consulate Y7 y Y10): `overview`, `teammates`, `compare` y `export` con las etiquetas por version; bordes (`until=foo`, `page=-1`, `n=-1`, filtros vacios) sin 500; Chromium sin errores de consola en Inicio, Compañeros, Tendencias y Partidas; 4 mutaciones, cada una tumba su test.
- OMC: diseno plan=— · implementacion revisión=3 hallazgos (1 arreglado) · revision revisión=1 hallazgo (0 arreglados, LOW aceptado) · QA verificación=PASS.

### Riesgos y lo que no entra

Sin migracion ni `recompute`: todo es al consultar y se deshace con un revert. Si una misma version tiene dos nombres guardados (override parcial en Datos), el Inicio usa el mas reciente y Clutch, Tendencias y el CSV el primero alfabetico, como Mapas (decision del diseno). Fuera: lista de mapas de cada rival en Duelos (sigue por slug), filtro de temporada (A3), selector "juntar versiones".

### Como probarlo en 2 minutos

```bash
cd backend
python manage.py test tests.test_aggregates tests.test_compare tests.test_export tests.test_resumen_partidas tests.test_clutch
python manage.py runserver
# con una base que tenga Consulate vieja y Y10:
# http://127.0.0.1:8000/  -> mejor/peor mapa con "Consulate (Y10)" si corresponde
# http://127.0.0.1:8000/api/export/?table=matches  -> ultima columna map_version
```

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Desde la ficha 70 la pagina Mapas separa "Consulate (Y10)" de la Consulate
vieja, pero el Inicio todavia puede nombrar "Consulate" como tu peor mapa
sumando dos layouts distintos, y Clutch por mapa y sitio mezcla sitios de
dos mapas que solo comparten el nombre. Con este tramo cada pantalla por
mapa habla de la misma fila que Mapas, con la misma etiqueta, y el CSV de
partidas dice que version se jugo.

## Criterios de aceptacion

- [x] `GET /api/overview/`, bloque `matches_summary` (`views.py:209`): con partidas de un mismo `map_slug` en dos `map_id` de `MAPS` distintos, cada version cuenta por separado para la muestra minima y el winrate, y `best_map`/`worst_map` traen la etiqueta de `etiquetas_de_version` ("Consulate (Y10)"). Test con dos versiones donde juntas darian otro mejor mapa que separadas.
- [x] `clutch_by_site` (Tendencias, Clutch por mapa y sitio): una fila de mapa por `(map_slug, map_id)` con su etiqueta, y los sitios de cada version debajo de la suya. Test: dos versiones del mismo slug con un sitio de igual nombre no suman sus intentos.
- [x] El corte por mapa de `compare_periods` (Mapas que mejoran y empeoran, ficha 56) separa versiones con la misma clave y etiqueta; un mapa con una sola version sigue saliendo con su nombre pelado, igual que en Mapas.
- [x] `GET /api/export/?table=matches` agrega la columna con la etiqueta de version (o `map_id`, lo decide el Arquitecto) sin cambiar el orden ni el nombre de las columnas que ya existen.
- [x] Con la base de `seed_demo` (todos los `map_id = 0`) los numeros que afirma el e2e no cambian, y `npm run e2e` sigue en verde.

## Fuera de alcance

La lista de mapas de cada rival en Duelos (`_agregar_mapas`, texto suelto sin
numeros); filtro de temporada (A3); selector "juntar versiones"; el Coach
(sus señales por mapa leen `by_map`, que ya separa). Sin migracion ni
`recompute`: es todo al consultar.

## Diseno

Clave `(map_slug, map_id)` en los cuatro lugares. Etiqueta: `etiquetas_de_version` sobre la muestra en `matches_summary` (nombre de la partida mas reciente; `etiquetas_de_mapas` tomaria el alfabetico y romperia `test_variantes_del_mapa_cuentan_juntas`), `etiquetas_de_mapas` en `clutch_by_site`, `compare_periods.by_map` (`_etiquetar_corte`) y `trend_by_match` (`map_version`, ultima columna del CSV). Keys de React con `map_id` en `Teammates.jsx:305` y `Trends.jsx:59`. `metricas.md`, fila Mapa, al dia. Detalle completo en `git log` de esta rama.

Skills: no aplica (dominio que el repo ya resuelve: ficha 70).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261104T2004Z-cGQmDVc) Diseno entero, en orden. Desvio: `clutch_by_site` sin `map_name` en el `.values()`, asi un renombre dentro de la version no parte la fila. Los cinco tests nuevos fallan con el codigo de `dev`.

Skills: no aplica.
OMC: plan=— · revisión=3 hallazgos (1 arreglado) · verificación=—

## Revision 2026-11-05

(revisor 20261105T0004Z-cXefbfB, sobre 937a652) VERDE 5b4faee (887/153/54). Aprobar. Un LOW aceptado: con dos nombres en la misma version, Inicio usa el mas reciente y el resto el alfabetico (decision del diseno). Criterios cubiertos uno por uno por los tests nuevos.

Skills: no aplica.
OMC: plan=— · revisión=1 hallazgo (0 arreglados, LOW aceptado) · verificación=—

## QA 2026-11-05 sobre 05414be

(qa 20261105T0215Z-cfTdV9W) VERDE 05414be (887/153/54). Bases sembradas con `factories.py` (Consulate Y7 `map_id` 2609221242 3/3, Y10 418126004176 0/3, Border, Bank): `overview` da mejor "Consulate (Y7)" y peor "Consulate (Y10)"; `teammates` separa "1F Lobby" en las dos versiones (6 y 6, no 12); `compare?by=matches&n=6` da "Consulate (Y10)", "Consulate (Y7)" y "Bank" pelado; `export?table=matches` termina en `map_version`. Bordes (`until=foo`, `map=`, `map=nada`, `limit=-1`, `n=-1`, `n=foo`, `page=-1`) en base vacia y sembrada: 200, `table=nada` 400, cero 500. Chromium en `/`, `/companeros`, `/tendencias`, `/partidas`: consola limpia; keys de React unicas con dos versiones (el build de produccion no avisa de keys duplicadas: la proteccion es la key calculada). Mutaciones: las 4 tumban su test. Chunk inicial 188.91 kB, sin cambio.

Skills: no aplica.
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, fallback general-purpose: 5 de 5 VERIFIED)

## Verificar en el PC

Opcional (sin migracion ni `recompute`): con una base real que tenga Consulate vieja y Y10, el Inicio muestra "Consulate (Y10)" si es tu mejor o peor mapa, Compañeros > Clutch por mapa y sitio muestra dos bloques de Consulate, y `/api/export/?table=matches` trae `map_version` al final.

## Pendiente

## Para el humano
