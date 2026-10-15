# 49. Mapas rehechos mezclan el winrate por lado

estado: descartado (premisa falsa: las versiones de un mapa ya comparten slug y nombre; separarlas es decision de producto P10)
candado: -
rama: -
tipo: bug
epica: temporada-y-modo
area: backend
prioridad: 2
fuente: ALCANCE.md A4 (Investigador 2026-10-14); verificado por el PO contra main 2a6c86b en `aggregates.py:383-414`
archivos: -
turnos: po 20261015T1711Z, arquitecto 20261015T1811Z

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

(Arquitecto 20261015T1811Z, sobre main 2a6c86b) **Descartada: la premisa del bug no se
reproduce en main.**

- `pydissect/header.py:227-232`: `map_slug()` sale del nombre legible (`entry[1]`), no
  del identificador interno. Las variantes por temporada colapsan al mismo slug **a
  proposito** (docstring "las variantes por temporada colapsan al base", y
  `tests/test_pydissect.py:178`: `map_slug(837214085) == map_slug(407193663917)`).
  Comprobado: `Consulate`, `ConsulateY7` y `ConsulateY10` dan los tres
  `map_name="Consulate"`, `map_slug="consulate"`.
- Como `map_name` y `map_slug` salen de la misma entrada de `MAPS`, un nombre siempre
  tiene un solo slug: `by_map` no puede dar dos filas "Fortress", y unir el lado por
  `map_name` da el mismo resultado que unirlo por slug. No hay numero mal.
- `FortressY10` no esta en `MAPS` (`constants.py:72-115`): es la idea P1 de
  `ALCANCE.md` (IDs nuevos). Hoy un Fortress rehecho entra como `Unknown(<id>)` /
  `unknown-<id>` hasta que se agregue su ID, y entonces colapsara a "fortress".

Lo que la ficha pide en el fondo (separar versiones de un mapa) es una
**funcionalidad**, no un arreglo, y cambia como se agrupa una metrica que ya se muestra
(Mapas, Coach, CSV, filtro de mapa por slug): decision de producto que toca la
definicion de un numero visible (P10). Si el humano la quiere, el camino barato es
agrupar por `Match.map_id` (ya guardado, `ingest.py:160`) con la etiqueta del
identificador interno de `MAPS` (sufijo `Y7`/`Y10`/`Y11`), sin migracion ni reimportar.
Va a `## Para el humano` de `ESTADO.md`.

## Implementacion

## Para el humano

Sin decision pendiente. La etiqueta "(Y10)" es la variante conservadora; si
prefieres "(2025)" o el nombre de la temporada del rework, se cambia en un
solo lugar.
