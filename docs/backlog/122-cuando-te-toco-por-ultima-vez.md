# 122. Cuando te toco por ultima vez

estado: propuesto
candado: arquitecto 2026-11-13T18:34Z
rama: -
tipo: funcionalidad
epica: rivales
area: backend
prioridad: 3
fuente: ALCANCE.md D10
archivos: -
turnos: po 20261113T1650Z-c9H2L8Y

## PR

## Que gana quien usa la app

En Duelos, las tablas Rivales repetidos y Stacks rivales que se repiten
suman una columna "Última vez" con la fecha de la partida mas reciente
contra esa persona o ese grupo. Se distingue al rival que te sigue tocando
esta semana del que fue de una racha de hace meses, sin abrir su perfil.

## Criterios de aceptacion

- [ ] Cada fila de `repeated_rivals` y de `rival_stacks`
      (`replays/analytics/aggregates.py`) trae `last_played` en ISO 8601:
      el `max(Match.played_at)` de las partidas que ya cuenta la fila.
      Test con un rival en tres partidas de fechas distintas: sale la mas
      reciente.
- [ ] Con filtros globales (`since`/`until`), `last_played` sale de las
      partidas que pasan el filtro, igual que `matches`; test con un
      `until` que deja afuera la ultima partida.
- [ ] `rival_stacks_de_partida` (el aviso del detalle, ficha 92) no cambia
      su record; si suma `last_played`, es el mismo valor que la fila de
      Duelos. Test.
- [ ] En `Duelos.jsx` las dos tablas muestran la columna "Última vez" con
      la fecha corta del resto de la app y se ordenan por ella; vitest o e2e.
- [ ] e2e: en `seed_demo`, Duelos muestra "Última vez" en Rivales
      repetidos con una fecha no vacia; consola limpia.

## Fuera de alcance

- Columna nueva en la base o migracion: sale de la misma consulta.
- Enlace de la fecha a la partida (puede ser una idea aparte).
- "Última vez" en la tabla Por rival (nemesis) de Duelos.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
