# 132. Rivales que se repiten en la misma noche

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D13
archivos: -
turnos: po 20261113T1926Z-ce4Pmp6

## PR

## Que gana quien usa la app

En Duelos, la tabla de Rivales repetidos marca a los rivales que te tocaron
dos o mas veces dentro de una misma sesion (el lobby que vuelve a la cola
contigo esa noche) y tu record en esas revanchas. Separa al rival que
reencuentras por casualidad semanas despues del que te persigue esa noche.

## Criterios de aceptacion

- [ ] `repeated_rivals` (`aggregates.py`) suma por rival `same_session`:
      cuantas de sus partidas contra ti cayeron en una sesion donde ya lo
      habias enfrentado (la sesion es la de `_sessions_raw`, corte por
      `SESSION_GAP_MINUTES`), y el record (ganadas/perdidas) de esas
      revanchas con `Match.won` nulo fuera del record. Test con un rival
      que repite dentro de una sesion y otro que repite en sesiones
      distintas (este con `same_session = 0`).
- [ ] La primera partida contra el rival en una sesion no es revancha: con
      dos partidas en la misma noche, `same_session = 1`. Test.
- [ ] Los filtros globales aplican igual que al resto de `repeated_rivals`;
      test con filtro de mapa que deja una sola de las dos partidas de la
      sesion (`same_session = 0`).
- [ ] En Duelos, Rivales repetidos muestra la columna (p. ej. "Revanchas
      esa noche" con su record) y la ayuda dice que cuenta; e2e sobre
      `seed_demo` con los numeros de la API y consola limpia.
- [ ] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Una pagina o panel aparte de revanchas: es una columna de la tabla que ya
  existe.
- Stacks rivales (ficha 90) en la misma noche.
- Señales del Coach sobre esto.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
