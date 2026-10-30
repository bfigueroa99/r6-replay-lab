# 72. La apertura marcada en la timeline de la ronda

estado: propuesto
candado: arquitecto 2026-10-30 17:16 UTC
rama: -
tipo: funcionalidad
epica: paridad-referencia
area: frontend
prioridad: 2
fuente: idea R4 de `ALCANCE.md`; fila "Kill feed por ronda con la apertura destacada" de `replica/features.csv` (`must`, `clone: partial`), [r6-replay.com](https://r6-replay.com/) ("See exactly who got the opening pick, who traded it"). Hoy la timeline de `frontend/src/pages/MatchDetail.jsx:271-274` solo marca HS y tradeada; la apertura la dicen la tabla de jugadores ("1a baja", "1a muerte") y el resumen en texto
archivos: -
turnos: po 20261030T1653Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En la timeline de cada ronda, la baja que abrio la ronda lleva un chip
"apertura" y la primera baja de tu equipo un chip "entry" (si no es la
misma), junto a HS y tradeada: se ve de un vistazo quien abrio y cuanto
tardo tu equipo en responder, sin cruzar la timeline con la tabla de
jugadores. Es un `must` de la referencia que la app tiene a medias.

## Criterios de aceptacion

- [ ] Logica pura en un modulo de `frontend/src/` con vitest: dados los
      eventos de una ronda y el equipo de cada nick, marca como apertura el
      primer evento `Kill` o `Death` por `order`, la misma regla que
      `opening_kill`/`opening_death` en `replays/analytics/metrics.py`
      (bloque "aperturas"), aunque el array venga desordenado.
- [ ] Entry: el primer `Kill` de un jugador de tu equipo, con la misma regla
      que `entry_kill` en `metrics.py` (sobre `kill_events`); si es el mismo
      evento que la apertura, lleva solo "apertura". Vitest con los dos
      casos.
- [ ] Ronda sin bajas: ningun chip. Ronda que abre con un `Death` sin autor
      rival: ese evento lleva "apertura" y el entry sigue siendo el primer
      `Kill` de tu equipo. Ronda sin jugador `is_me` (partida de otro): se
      usa el equipo que ya calcula `myTeam` en `MatchDetail.jsx`; sin equipo,
      solo "apertura". Vitest por caso.
- [ ] Coherencia con lo guardado: con `seed_demo`, en cada ronda con bajas
      el autor del evento "apertura" es el jugador con "1a baja" (o la
      victima, el que tiene "1a muerte") en la tabla de jugadores de esa
      ronda. Lo afirma el e2e (`frontend/e2e/`) sobre una partida sembrada,
      junto con que hay exactamente un chip "apertura" por ronda con bajas.
- [ ] Sin cambios de backend: `/api/matches/<id>/` ya trae `order`, `kind`,
      `actor` y `target` de cada evento. Sin numero nuevo en la UI, asi que
      sin fila nueva en `docs/metricas.md`.

## Fuera de alcance

- El chip "TK" para teamkills en la timeline (idea F14).
- Marcar quien tradeo la apertura (el chip "tradeada" ya existe).
- La apertura en otras pantallas o como filtro de rondas (F1).
- Cambiar como se calculan `opening_kill`, `opening_death` o `entry_kill`.

## Diseno

## Implementacion

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Nada pendiente.
