# 124. Partidas por version del juego en Datos

estado: propuesto
candado: arquitecto 2026-11-13T18:59Z
rama: -
tipo: funcionalidad
epica: datos
area: backend
prioridad: 3
fuente: ALCANCE.md G8
archivos: -
turnos: po 20261113T1650Z-c9H2L8Y

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

## Implementacion

## Revision

## QA

## Para el humano

(nada)
