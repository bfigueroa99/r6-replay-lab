# 41. Rondas segun el marcador: adelante, empatado o atras

estado: propuesto
candado: arquitecto 2026-10-13T20:12Z
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B2 (rondas bajo presion), primer tramo; el match point queda para el segundo
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Trends.jsx, docs/metricas.md, backend/tests/, frontend/e2e/
turnos: po 20261013T1915Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver como rindes segun como va la partida antes de la ronda: yendo adelante,
empatado o atras en el marcador. Es la mitad de "rondas bajo presion" que no
depende de las reglas de cada modo, asi que sirve igual en ranked, unranked o
rapida.

## Criterios de aceptacion

- [ ] `GET /api/trends/` devuelve `by_score_state`: cuatro filas en orden fijo
      `ahead`, `tied`, `behind`, `unknown`, con las metricas de `totals()`.
      El estado sale de `Round.score_before` (`[equipo0, equipo1]`, de
      `startingScore` en `ingest.py:208`) comparando tu equipo
      (`RoundPlayer.team_index` de tu fila) contra el otro.
- [ ] Va a `unknown` la ronda con `score_before` vacio o con largo distinto
      de 2. La suma de `rounds` de las cuatro filas es igual a `rounds` de
      `/api/overview/` con los mismos filtros (test).
- [ ] Test con una partida 0-0, 1-0, 1-1, 1-2 desde tu lado, con tu equipo
      como equipo 1 en al menos una partida (el indice del equipo no puede
      darse vuelta sin que el test caiga).
- [ ] Tendencias muestra el panel "Según el marcador" con las filas
      conocidas, CSV y aviso de muestra chica bajo 30 rondas; `unknown` solo
      se muestra si tiene rondas.
- [ ] `docs/metricas.md` tiene la fila. `seed_demo` hoy no llena
      `score_before`: si el diseno lo llena, los numeros del e2e cambian y se
      ajustan en la misma ficha (CLAUDE.md); si no lo llena, el e2e afirma
      el panel con todo en `unknown` oculto y un aviso de "sin marcador".
- [ ] Base vacia y filtros raros devuelven 200.

## Fuera de alcance

- Match point y ronda decisiva: dependen de las reglas de cada modo (a cuanto
  se gana, prorroga). Segundo tramo de B2, como idea en `ALCANCE.md`.
- Inercia de la ronda anterior: ficha 39.

## Diseno

(Arquitecto) Implementar despues de #39 si las dos se disenan a la vez: tocan
la misma vista y la misma pagina.

## Para el humano

Nada por ahora.
