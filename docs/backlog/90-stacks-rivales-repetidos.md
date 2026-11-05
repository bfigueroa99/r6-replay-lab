# 90. Stacks rivales repetidos

estado: propuesto
candado: arquitecto 2026-11-05T19:20Z
rama: -
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: D4 de ALCANCE.md; `replica/features.csv` "Historial contra un equipo rival concreto" (should, partial: la referencia lo tiene por equipo y la app solo por persona, D1 en dev)
archivos: -
turnos: po 20261105T1759Z-cCJ5erc

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Duelos, debajo de "Rivales repetidos", los grupos de 2 o mas rivales que
te tocaron juntos en el mismo equipo en 2 o mas partidas, con tu record
contra cada grupo: reconocer al stack que ya te gano, no solo a la persona.
Solo gente de tus replays; no es scouting ni consulta a nadie.

## Criterios de aceptacion

- [ ] `GET /api/duels/` trae `rival_stacks`: una fila por conjunto de
      jugadores rivales (agrupados por `Player`, no por nick, como
      `repeated_rivals`) que estuvieron juntos en el equipo contrario en al
      menos `min_matches` (2 por defecto) de tus partidas filtradas, con
      `players` (id y nick), `matches`, `wins`, `losses` y `winrate` (las
      partidas sin resultado fuera del winrate). Test con tres partidas
      armadas a mano.
- [ ] El grupo es el mas grande que se repite: si A, B y C te tocaron juntos
      en dos partidas, sale la fila A+B+C y no tambien A+B, A+C y B+C con las
      mismas partidas; A+B sale aparte solo si suma partidas que A+B+C no
      tiene. Test.
- [ ] El equipo se lee por ronda como en `repeated_rivals`: un jugador que
      fue companero en una partida y rival en otra solo cuenta en la segunda.
      Respeta los filtros globales (test con filtro de mapa).
- [ ] En Duelos, un panel "Stacks rivales repetidos" con los nicks enlazados
      al perfil de cada jugador y el record; sin filas, dice que ningun grupo
      se repitio con esos filtros.
- [ ] Fila en `docs/metricas.md` y caso en el e2e (`frontend/e2e/`) con un
      numero de `seed_demo` afirmado (si el seed no tiene ningun stack
      repetido, el Arquitecto decide si el seed suma uno y que numeros del e2e
      cambian).

## Fuera de alcance

- Nombres de equipo o clan: el `.rec` no los trae.
- Stats de esos rivales fuera de tus partidas (API de Ubisoft): no.
- Stacks de tus companeros (eso es C1, otra idea).

## Diseno

(Arquitecto)

## Implementacion

(Dev)
