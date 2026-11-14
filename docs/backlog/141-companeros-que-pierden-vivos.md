# 141. Compañeros que pierden vivos

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C20 (el reverso de la 131, `won_without_me`, que ya cuenta quien seguia vivo en las rondas que el equipo gano sin ti)
archivos: -
turnos: po 20261114T0040Z-chQsvnq

## PR

## Que gana quien usa la app

En Compañeros, por compañero habitual, cuantas de las rondas que tu equipo
perdio jugando con el terminaron con el vivo: quien se guarda cuando la ronda
se va. Hoy la app cuenta quien sigue vivo en las que ganaste sin ti (131),
pero no en las perdidas.

## Criterios de aceptacion

- [ ] Agregado nuevo: por compañero habitual (el mismo criterio de
      habitual que `won_without_me`), sobre tus rondas filtradas que tu
      equipo perdio (`Round.my_team_won=False`; sin ganador no cuenta) y en
      que el estaba en tu equipo: `lost_rounds`, `alive_at_end` (su
      `RoundPlayer.survived`) y `pct`. Test con un compañero vivo en 2 de 3
      perdidas y una ronda ganada que no entra.
- [ ] Al lado, la misma tasa tuya en esas rondas (tu `survived`), para
      comparar. Test.
- [ ] Un jugador que en otra ronda fue rival no suma en esa ronda (se lee
      `team_index` ronda por ronda). Test.
- [ ] Los filtros globales aplican sobre tu fila de la ronda; test con
      filtro de lado.
- [ ] Panel o columna en Compañeros, junto a "Ganadas sin ti", con el `n`
      (perdidas juntos) a la vista y aviso de muestra chica; sin filas, una
      nota. e2e con `seed_demo`, numeros de la API y consola limpia. Fila
      nueva en `docs/metricas.md`.

## Fuera de alcance

- Marcar esas rondas en el detalle de partida (otro tramo, como F27).
- Distinguir "vivo y escondido" de "vivo peleando": el `.rec` no trae
  posicion ni dano.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
