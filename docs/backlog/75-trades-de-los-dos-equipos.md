# 75. Trades de los dos equipos en el detalle de partida

estado: propuesto
candado: arquitecto 2026-11-04T16:05Z
rama: -
tipo: funcionalidad
epica: paridad-referencia
area: frontend
prioridad: 2
fuente: idea R2 de `ALCANCE.md`; fila `should` "Duelos limpios contra trades que se escapan, por equipo, en la partida" de `docs/backlog/replica/features.csv` (clone `partial`), de [r6-replay.com](https://r6-replay.com/) ("Know which duels your team wins clean and where trades slip through."). En `dev` bcdbdf5 `match_detail` (`replays/views.py:462`) ya devuelve `trade_kills`, `was_traded` y `untraded_death` por jugador y ronda, y el scoreboard (`views.py:576-593`, `MatchDetail.jsx:222-223`) los suma por jugador; nada los suma por equipo
archivos: backend/replays/views.py, frontend/src/pages/MatchDetail.jsx, frontend/src/, backend/tests/, frontend/e2e/, docs/metricas.md
turnos: po 20261104T1206Z-c8cAo8L

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En el detalle de una partida, un panel "Trades por equipo" pone lado a lado a
tu equipo y al rival: muertes, cuantas fueron tradeadas, cuantas quedaron sin
trade y cuantos trade kills hizo cada uno. Se ve si la partida se perdio por
regalar muertes sueltas aunque el K/D del scoreboard cuadre, que es lo
primero que la referencia muestra de una partida.

## Criterios de aceptacion

- [ ] `GET /api/matches/<id>/` trae, por equipo (`mine` y `rival`, con el `team_index` de cada ronda: el lado cambia en la partida), `deaths`, `traded_deaths`, `untraded_deaths`, `trade_kills` y `% sin trade` (sobre muertes; `null` sin muertes). Test con una partida armada a mano.
- [ ] Los numeros de cada equipo cuadran con la suma de las filas de ese equipo en el scoreboard de la misma respuesta (mismas columnas *Trades* y *Sin trade*): test que lo afirma.
- [ ] Una muerte sin asesino o un teamkill cuentan como hoy en `was_traded`/`untraded_death` (no se recalcula nada: se suman las columnas que escribe `metrics.py` al importar).
- [ ] `MatchDetail.jsx` muestra el panel con los dos equipos y la diferencia resaltada; el e2e abre una partida de `seed_demo` y ve el panel con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Trades por equipo") con la definicion y la ventana (`TRADE_WINDOW_SECONDS`).

## Fuera de alcance

El mismo corte entre partidas (Tendencias, Compañeros); la matriz de quien
venga a quien (C2, C14); tiempo de refrag (C6); cambiar la ventana de trade.
Sin migracion: las columnas ya existen.

## Diseno

## Implementacion

## Revision

## QA

## Verificar en el PC

## Pendiente

## Para el humano
