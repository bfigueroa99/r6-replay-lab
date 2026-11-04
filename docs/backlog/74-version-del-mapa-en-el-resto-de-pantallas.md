# 74. La version del mapa tambien en el Inicio, Clutch por mapa, Mapas que mejoran y el CSV de partidas

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: temporada-y-modo
area: backend
prioridad: 2
fuente: idea A8 de `ALCANCE.md`, tramo siguiente que dejo escrito el `## Fuera de alcance` de la ficha 70 ("Mejor y peor mapa", "Clutch por mapa y sitio", progreso por mapa y Duelos siguen por slug: otra ficha de la epica) y la QA de la 71 (tabla `matches` de Exportar sin version). En `dev` bcdbdf5: `matches_summary` agrupa por `map_slug` (`replays/analytics/aggregates.py:1031`), `clutch_by_site` por `round__match__map_slug` (`:1603`), el corte por mapa de `compare_periods` por `("round__match__map_slug", "round__match__map_name")` (`:2448`)
archivos: backend/replays/analytics/aggregates.py, backend/replays/export.py, backend/tests/, docs/metricas.md
turnos: po 20261104T1206Z-c8cAo8L

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

## Implementacion

## Revision

## QA

## Verificar en el PC

## Pendiente

## Para el humano
