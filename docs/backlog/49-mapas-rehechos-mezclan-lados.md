# 49. Mapas rehechos mezclan el winrate por lado

estado: propuesto
candado: -
rama: -
tipo: bug
epica: temporada-y-modo
area: backend
prioridad: 2
fuente: ALCANCE.md A4 (Investigador 2026-10-14); verificado por el PO contra main 2a6c86b en `aggregates.py:383-414`
archivos: -
turnos: po 20261015T1711Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy Fortress (`Fortress`) y Fortress rehecho (`FortressY10`) salen como dos
filas "Fortress" en el Coach y en el CSV de mapas, y las dos muestran el mismo
winrate de ataque y defensa: `by_map` une el lado por `map_name` y no por
`map_slug`, asi que mezcla las rondas de los dos layouts. Con el arreglo cada
version del mapa tiene sus propios numeros por lado y una etiqueta que las
distingue ("Fortress" y "Fortress (Y10)"), y los sitios de layouts distintos
dejan de sumarse.

## Criterios de aceptacion

- [ ] Con rondas en `Fortress` (3 ganadas de 4 en ataque) y en `FortressY10`
      (0 de 4 en ataque), `by_map` devuelve dos filas con `attack_winrate`
      75 y 0, no 37.5 en las dos (test en `backend/tests/`).
- [ ] `by_site` y `by_spawn` agrupan por `map_slug`: el sitio "2F Comandos"
      de `Fortress` y el de `FortressY10` son dos filas.
- [ ] Las filas de un slug rehecho llevan un nombre distinguible (`map` con
      sufijo, p. ej. "Fortress (Y10)"), derivado de la tabla `MAPS` de
      `pydissect/constants.py` y no de una lista a mano en Django; un mapa
      sin version rehecha sigue con su nombre de siempre.
- [ ] El CSV `/api/export/?table=maps` y las señales de mapa, sitio y spawn
      del Coach (`coach.py:406,450,525`) muestran las dos filas separadas
      (test o `curl` sobre una base sembrada con los dos slugs).
- [ ] Sin migracion ni recompute: el arreglo es de agregacion. Fila de
      `docs/metricas.md` de mapas/sitios dice que se agrupa por version del
      mapa.

## Fuera de alcance

- Filtro de temporada (A3) o etiqueta de version en el detalle de partida.
- Unir las dos versiones a proposito (selector "juntar versiones").
- Villa y otros mapas que cambiaron sitios sin ID nuevo: sin dato, no se
  puede separar (verificar con `.rec` reales en el PC).
- Los otros usos de `map_name` (records, sesiones, listado de partidas):
  muestran la partida, no agregan.

## Diseno

(Arquitecto)

## Implementacion

## Para el humano

Sin decision pendiente. La etiqueta "(Y10)" es la variante conservadora; si
prefieres "(2025)" o el nombre de la temporada del rework, se cambia en un
solo lugar.
