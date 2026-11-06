# 92. El stack rival en el detalle de la partida

estado: propuesto
candado: arquitecto 2026-11-06 00:15
rama: -
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: D9 de ALCANCE.md (idea del arquitecto 20261105T1920Z-cAaALb8 al disenar la 90); tramo siguiente de la ficha 90
archivos: -
turnos: po 20261105T1945Z-cvqUYh1

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Al abrir una partida, ves sobre el scoreboard si en el equipo rival venia un
grupo que ya te toco junto en otras partidas ("Kaid_, Mozzie99 y Thorn.exe ya
te tocaron juntos en 4 partidas, récord 1-3"), con enlace a Duelos. Saber que
el stack de enfrente ya te gano sin ir a buscarlo a otra pagina; es el
segundo tramo de la epica de rivales despues de la tabla de stacks (ficha 90).

**Implementar despues de que #90 se mergee**: usa `rival_stacks` de esa ficha (`replays/analytics/aggregates.py`) y suma una clave a `match_detail` (`replays/views.py`).

## Criterios de aceptacion

- [ ] `GET /api/matches/<id>/` trae una clave `rival_stacks`: lista de los
      grupos de `rival_stacks` (ficha 90, sin filtros globales: sobre todas
      tus partidas) cuyas partidas incluyen esta, cada uno con sus jugadores
      (id y nick), partidas juntos, ganadas y perdidas contra ellos. Lista
      vacia si no hay ninguno, nunca ausente.
- [ ] El record de cada grupo cuenta esta partida igual que la tabla de
      Duelos (mismos numeros que la fila de la ficha 90 para ese grupo): test
      con una base de `factories.py` donde el mismo trio rival aparece en 3
      partidas.
- [ ] Si un grupo esta contenido en otro mas grande que tambien aplica a esta
      partida, se muestra solo el mas grande (mismo criterio de maximalidad
      que la ficha 90; si la 90 no lo define, el Arquitecto lo fija aca).
- [ ] En `MatchDetail` se ve un aviso sobre el scoreboard por grupo, con los
      nicks enlazados a su perfil y un enlace a Duelos; sin grupos, no se
      renderiza nada (ni panel vacio).
- [ ] Una partida sin rondas o sin rivales identificados devuelve
      `rival_stacks: []` y el detalle no se rompe (e2e de la partida sin rondas
      sigue verde).
- [ ] e2e: una partida de `seed_demo` con stack repetido muestra el aviso con
      los numeros que fija el seed (si el seed no tiene ninguno, el Arquitecto
      decide si se agrega uno y actualiza los numeros que cambien).

## Fuera de alcance

- La columna "Última vez" (D10, otra idea).
- Stacks de tus compañeros (C1).
- Recalcular con los filtros globales: el aviso es sobre todo tu historial.
- Nombres de equipo o clan: el `.rec` no los trae.

## Diseno

## Implementacion

## Revision

## QA

## Pendiente

## Para el humano
