# 70. Cada version de un mapa en su propia fila

estado: propuesto
candado: arquitecto 2026-10-29 04:04 UTC
rama: -
tipo: funcionalidad
epica: temporada-y-modo
area: fullstack
prioridad: 2
fuente: decision del humano 2026-10-28 en `## Para el equipo` de `ESTADO.md` (ficha 49, descartada como bug; idea A4 de `ALCANCE.md`). Camino que dejo el Arquitecto en la 49: agrupar por `Match.map_id` (`ingest.py:160`) con la etiqueta del identificador de `MAPS`
archivos: -
turnos: po 20261029T0004Z

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

## Diseno

## Implementacion

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Sin decision pendiente (la tomaste el 2026-10-28). La etiqueta "(Y10)" es la
variante conservadora; si preferis el año del rework, se cambia en una sola
funcion.
