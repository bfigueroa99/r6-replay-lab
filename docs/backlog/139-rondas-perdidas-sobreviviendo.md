# 139. Rondas perdidas sobreviviendo

estado: propuesto
candado: arquitecto 2026-11-14T01:07Z
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F11
archivos: -
turnos: po 20261113T2318Z-chc2kiA

## PR

## Que gana quien usa la app

Cuantas rondas terminaste vivo y tu equipo igual las perdio, por lado y por
mapa, con la lista de las mas recientes para abrirlas: dice si te guardas de
mas cuando la ronda se esta perdiendo (en ataque, tiempo agotado o defuse; en
defensa, la bomba que entra mientras sigues vivo).

## Criterios de aceptacion

- [ ] Agregado nuevo en `aggregates.py` (p. ej. `lost_alive(**filters)`)
      sobre `base_queryset`: por lado (`Attack`, `Defense`) y total, rondas
      perdidas (`Round.my_team_won is False`) con tu `RoundPlayer.survived`
      en `True`, sobre tus rondas perdidas de ese lado. Las rondas con
      `my_team_won` nulo no entran ni al numerador ni al denominador. Test
      Django con una ronda perdida vivo, una perdida muerto, una ganada vivo
      (no cuenta) y una sin resultado (fuera).
- [ ] El mismo agregado por mapa (con la version del mapa, como el resto de
      las tablas por mapa) y los filtros globales aplicados; test con filtro
      de lado o de mapa.
- [ ] Lista de las 10 rondas perdidas vivo mas recientes (partida, mapa,
      lado, numero de ronda) con enlace que abre esa ronda en el detalle
      (`?ronda=` como el resto de enlaces a ronda). Test del orden y del
      tope.
- [ ] Panel en la UI (pagina a elegir por el Arquitecto, cerca de
      "Duración de la ronda" o "Estado al morir") con la ayuda que diga que
      cuenta; e2e sobre `seed_demo` con los numeros de la API y consola
      limpia.
- [ ] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Juzgar si quedarse vivo estuvo bien o mal: no hay coordenadas ni plants
  exactos en temporadas nuevas (`docs/formato-rec.md`); no se usa
  `possible_plant`.
- Señales del Coach sobre esto.
- Lo mismo para tus compañeros (idea C20 de `ALCANCE.md`).
- Marcar esas rondas en el detalle de partida (idea F27).

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
