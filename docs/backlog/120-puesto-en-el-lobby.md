# 120. Puesto en el lobby

estado: propuesto
candado: arquitecto 2026-11-13T18:03Z
rama: -
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E7
archivos: -
turnos: po 20261113T1603Z-cHj1H4k

## PR

## Que gana quien usa la app

En Tendencias, cuantas veces fuiste el mejor de la partida por Rating, el
mejor de tu equipo y el ultimo de los diez: el Rating suelto no dice si
arrastraste al equipo o te arrastraron. Solo sale de tus replays, que traen
a los diez jugadores.

## Criterios de aceptacion

- [ ] Un agregado nuevo en `aggregates.py` calcula, por partida, tu puesto
      entre los jugadores de la partida y dentro de tu equipo por el rating
      de la partida (`rating_points_expr` sobre las filas `RoundPlayer` de
      todos, como `trend_by_match`), y devuelve `matches`, `best_in_lobby`,
      `best_in_team` y `last_in_lobby` (conteo y %). Test con una partida
      armada de 10 jugadores de rating conocido.
- [ ] Empate de rating con otro jugador: cuenta como mejor (o ultimo) solo
      si nadie te supera (o nadie esta por debajo); regla en
      `docs/metricas.md` y test.
- [ ] Partidas con menos de 10 jugadores (abandonos) entran con los que hay;
      una partida en la que solo estas vos no cuenta. Test.
- [ ] Los filtros globales de partida (mapa, tipo, modo, fechas) aplican;
      los de ronda (lado, operador, sitio) recortan las rondas de todos por
      igual. Test con filtro de mapa.
- [ ] En Tendencias, una fila de tres stats (Mejor de la partida, Mejor de
      tu equipo, Último de la partida) con el % y el conteo; sin partidas,
      un texto y no ceros. e2e de humo con los numeros de `seed_demo` y la
      consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Puesto en el lobby").

## Fuera de alcance

- El puesto en el detalle de cada partida (otro tramo, chico, despues de este).
- Comparar contra el promedio del lobby (E9, otra idea).
- Puesto por score de la partida: el `.rec` ya no lo atribuye.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
