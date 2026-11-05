# 75. Trades de los dos equipos en el detalle de partida

estado: en curso 2026-11-05
candado: -
rama: claude/equipo-dev/75-trades-de-los-dos-equipos
tipo: funcionalidad
epica: paridad-referencia
area: frontend
prioridad: 2
fuente: idea R2 de `ALCANCE.md`; fila `should` "Duelos limpios contra trades que se escapan, por equipo, en la partida" de `docs/backlog/replica/features.csv` (clone `partial`), de [r6-replay.com](https://r6-replay.com/) ("Know which duels your team wins clean and where trades slip through."). En `dev` bcdbdf5 `match_detail` (`replays/views.py:462`) ya devuelve `trade_kills`, `was_traded` y `untraded_death` por jugador y ronda, y el scoreboard (`views.py:576-593`, `MatchDetail.jsx:222-223`) los suma por jugador; nada los suma por equipo
archivos: backend/replays/views.py, backend/tests/test_trades_por_equipo.py, frontend/src/tradesEquipo.js, frontend/src/tradesEquipo.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261104T1206Z-c8cAo8L, arquitecto 20261104T1604Z-cAKAGx1

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

Una sola forma obvia (sumar columnas que ya escribe `metrics.py`): sin arena
ni consenso. Sin migracion, sin `recompute`, sin tocar el parser.

**Backend, `backend/replays/views.py`.**

- Funcion nueva `_trades_por_equipo(rounds: list[dict], my_team_index: int) -> dict`
  junto a `_match_scoreboard` (`views.py:574`). Recorre la lista `rounds` que
  `match_detail` ya armo (`views.py:468-532`, cada ronda con `players`): cero
  queries nuevas.
- Equipo de cada fila: en cada ronda, "mine" es el `team_index` de la fila con
  `is_me`; si la ronda no tiene fila `is_me`, `my_team_index` de la partida.
  Asi un `team_index` que cambie entre rondas no rompe nada (el criterio 1 lo
  pide), aunque hoy sea fijo por equipo.
- Por equipo suma: `deaths` (filas con `died`), `traded_deaths` (`died` y
  `was_traded`), `untraded_deaths` (`untraded_death`), `trade_kills` (suma de
  `trade_kills`) y `untraded_pct = round(untraded / deaths * 100, 1)` o `None`
  sin muertes. `traded_deaths + untraded_deaths == deaths` por construccion
  (`metrics.annotate_trades`: `untraded_death = died and not was_traded`);
  `traded_deaths` filtra por `died` para que una fila rara con `was_traded`
  sin muerte no descuadre. Nada se recalcula.
- `match_detail` agrega al payload `"team_trades": {"mine": {...}, "rival": {...}}`
  (despues de `scoreboard`). Las claves: `deaths`, `traded_deaths`,
  `untraded_deaths`, `trade_kills`, `untraded_pct`.

**Frontend.**

- `frontend/src/tradesEquipo.js` (logica pura, como `matrizDuelos.js`):
  `filasTradesEquipo(teamTrades)` devuelve las dos filas (`Tu equipo`,
  `Rival`) y, por columna, cual equipo sale mejor (`mejor: 'mine' | 'rival' | null`):
  menos `untraded_deaths` y menor `untraded_pct` es mejor; mas `trade_kills` es
  mejor; empate o `null` = `null`. Devuelve `[]` si `teamTrades` falta (una
  respuesta vieja cacheada no rompe la pagina).
- `frontend/src/tradesEquipo.test.js` (vitest): `marca al rival cuando dejo
  mas muertes sin trade`, `empate no marca a nadie`, `sin muertes el porcentaje
  queda en null y no marca`, `sin team_trades devuelve lista vacia`.
- `frontend/src/pages/MatchDetail.jsx`: `<Panel title="Trades por equipo"
  hint="Muertes que tu equipo y el rival dejaron sin vengar en la ventana de trade.">`
  entre "Matriz de duelos" (`:190`) y "Scoreboard de la partida" (`:197`).
  Tabla simple (`DataTable` como el scoreboard, `rowKey` por equipo, sin
  `csvName` nuevo si complica) con columnas Muertes, Tradeadas, Sin trade,
  % sin trade, Trade kills. La celda del equipo mejor en cada columna va en
  `<span className="chip win">` (`styles.css:303`): sin CSS nuevo.
  Debajo, una nota en una linea: "Tu equipo dejó N muertes sin trade; el rival, M."

**Tests backend**, `backend/tests/test_trades_por_equipo.py` (nuevo; fabricas
de `tests/factories.py`):

- `test_trades_por_equipo_suma_cada_equipo`: partida a mano con 2 rondas, 2
  jugadores por lado, muertes tradeadas y sin trade en los dos equipos;
  afirma los cinco numeros de `mine` y `rival` via `GET /api/matches/<id>/`.
- `test_trades_por_equipo_cuadra_con_el_scoreboard`: suma las filas de
  `scoreboard` con `team_index == my_team_index` (columnas `trade_kills` y
  `untraded_deaths`, y `deaths`) y las compara con `mine`; idem rival.
- `test_trades_por_equipo_usa_el_equipo_de_cada_ronda`: una ronda donde la
  fila `is_me` tiene otro `team_index` que `match.my_team_index`; sus
  compañeros de esa ronda cuentan en `mine`.
- `test_sin_muertes_el_porcentaje_es_null`.
- `test_un_teamkill_cuenta_como_ya_lo_guarda_el_import`: la fila muerta por
  teamkill con `untraded_death=True` suma en `untraded_deaths` de su equipo,
  sin recalcular.

**e2e**, `frontend/e2e/humo.spec.js`: test `el detalle de una partida muestra
los trades por equipo`, igual que el de la matriz (`:345`): abre la primera
partida, busca `section.panel` con heading `Trades por equipo`, ve dos filas
(`Tu equipo`, `Rival`) con celdas numericas y la consola limpia. No afirmar
numeros exactos salvo que el Dev los lea de `seed_demo` y los deje con
comentario de donde salen.

**`docs/metricas.md`**, seccion `## Trades` (`:177`): fila **Trades por
equipo**: por equipo de la partida (el de cada ronda), muertes, tradeadas, sin
trade, % sin trade sobre muertes y trade kills; misma ventana
`TRADE_WINDOW_SECONDS` y mismas columnas que el scoreboard; nada se recalcula
al consultar.

**Orden:** backend + tests, `tradesEquipo.js` + vitest, panel, e2e, `metricas.md`,
`npm run build`.

**Que puede romperse:** nada persistente. El payload crece en un objeto. El
riesgo es el e2e si `seed_demo` no tiene muertes en algun equipo: el panel
sale igual (ceros y `—`).

**Verificacion manual:** `runserver`, abrir una partida real: la suma de la
columna "Sin trade" del scoreboard de tu equipo es la celda "Sin trade" de
"Tu equipo".

Skills: no aplica (tabla y panel que el repo ya resuelve con `DataTable` y `Panel`).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Verificar en el PC

## Pendiente

## Para el humano
