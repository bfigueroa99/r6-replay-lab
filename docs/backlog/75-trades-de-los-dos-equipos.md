# 75. Trades de los dos equipos en el detalle de partida

estado: entregado
candado: -
rama: claude/equipo-dev/75-trades-de-los-dos-equipos
tipo: funcionalidad
epica: paridad-referencia
area: frontend
prioridad: 2
fuente: idea R2 de `ALCANCE.md`; fila `should` "Duelos limpios contra trades que se escapan, por equipo, en la partida" de `docs/backlog/replica/features.csv` (clone `partial`), de [r6-replay.com](https://r6-replay.com/) ("Know which duels your team wins clean and where trades slip through."). En `dev` bcdbdf5 `match_detail` (`replays/views.py:462`) ya devuelve `trade_kills`, `was_traded` y `untraded_death` por jugador y ronda, y el scoreboard (`views.py:576-593`, `MatchDetail.jsx:222-223`) los suma por jugador; nada los suma por equipo
archivos: backend/replays/views.py, backend/tests/test_trades_por_equipo.py, frontend/src/tradesEquipo.js, frontend/src/tradesEquipo.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261104T1206Z-c8cAo8L, arquitecto 20261104T1604Z-cAKAGx1, dev 20261105T0215Z-cVoFB5j, revisor 20261105T0247Z-cQMp2TZ, qa 20261105T0256Z-cFRtPBc, release 20261105T0256Z-cFRtPBc

## PR

Titulo: `[equipo-dev][frontend] Trades por equipo en el detalle de partida`

### Que cambia

El detalle de una partida suma el panel "Trades por equipo": tu equipo y el rival lado a lado con muertes, tradeadas, sin trade, % sin trade y trade kills, y resaltado el que sale mejor en cada columna comparable. Se ve si la partida se perdio regalando muertes sueltas aunque el K/D cuadre. `GET /api/matches/<id>/` trae `team_trades: {mine, rival}`.

### Por que esto y no otra cosa

Ficha 75 (idea R2 de `ALCANCE.md`, fila `should` de la referencia r6-replay.com). Suma las columnas que `metrics.py` ya escribe al importar: sin migracion, sin `recompute`, cero queries nuevas. Descartado recalcular trades al consultar (daria numeros distintos al scoreboard).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE 5e4c0ab, 895 tests backend, 159 vitest, 55 e2e.
- Tests nuevos (`tests/test_trades_por_equipo.py`): suma por equipo, cuadra con el scoreboard, equipo de cada ronda, sin tu fila vale el de la partida, % null sin muertes, teamkill, tradeada sin muerte no descuadra, suma `untraded_death` tal cual lo guardo el import. Vitest `tradesEquipo.test.js` (6). e2e `el detalle de una partida muestra los trades por equipo` compara las celdas con la API.
- Manual (QA): 29 partidas de `seed_demo` cuadran con el scoreboard; bordes con fabricas (un jugador, sin muertes, sin rondas); 4 mutaciones, todas atrapadas.
- OMC: Diseno `plan=— · revisión=— · verificación=—`; Implementacion `plan=— · revisión=3 hallazgos (2 arreglados) · verificación=—`; Revision `plan=— · revisión=2 hallazgos (1 arreglado con test) · verificación=—`; QA `plan=— · revisión=— · verificación=PASS`.

### Riesgos y lo que no entra

Nada persistente: el payload crece en un objeto. Si `team_index` cambiara entre rondas, el panel (por ronda) y el scoreboard (por indice) no cuadrarian; `metricas.md` lo dice. En `seed_demo` el rival sale con 0 sin trade porque el seed solo marca trades en tu fila. Fuera: el corte entre partidas (Tendencias, Compañeros), matriz de quien venga a quien, refrag.

### Como probarlo en 2 minutos

```
cd backend; python manage.py test tests.test_trades_por_equipo
cd frontend; npm run build; cd ../backend; python manage.py runserver
```
Abrir una partida en Partidas: el panel "Trades por equipo" queda entre "Matriz de duelos" y el scoreboard; la columna "Sin trade" de tu equipo es la suma de esa columna del scoreboard para tu equipo.

### Para el humano

Nada.

### Candidatos descubiertos

Ficha 81 (bug, `propuesto` en `backlog`): el detalle de una partida sin rondas rompe la pagina (`MatchDetail.jsx:33`), ya en dev.

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

Sumar las columnas que ya escribe `metrics.py` (`died`, `was_traded`, `untraded_death`, `trade_kills`) por equipo, con "tu equipo" resuelto por ronda (el `team_index` de tu fila; sin ella, el de la partida). `_trades_por_equipo` en `views.py` recorre las rondas ya armadas; `tradesEquipo.js` arma las filas y quien sale mejor; panel con `DataTable` y `chip win`, sin CSS nuevo. Sin migracion ni `recompute`. Detalle completo en `git log` de esta ficha.

Skills: no aplica.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

2026-11-05 (dev 20261105T0215Z-cVoFB5j). Diseno completo, sin desvios de fondo.

- Backend: `_trades_por_equipo(rounds, my_team_index)` en `replays/views.py`, junto a `_match_scoreboard`; recorre las rondas ya armadas (cero queries) y `match_detail` devuelve `team_trades: {mine, rival}` con `deaths`, `traded_deaths`, `untraded_deaths`, `trade_kills`, `untraded_pct`.
- Frontend: `src/tradesEquipo.js` (`filasTradesEquipo`, `textoTradesEquipo`) y el panel "Trades por equipo" en `MatchDetail.jsx`, entre la matriz y el scoreboard. `DataTable` sin orden por clic (siempre Tu equipo arriba), fila `me` en tu equipo, `chip win` en la celda del que sale mejor (menos sin trade, menor %, mas trade kills). Sin CSS nuevo, sin `csvName`.
- Tests backend (`tests/test_trades_por_equipo.py`): `test_trades_por_equipo_suma_cada_equipo`, `test_trades_por_equipo_cuadra_con_el_scoreboard`, `test_trades_por_equipo_usa_el_equipo_de_cada_ronda`, `test_sin_tu_fila_vale_el_equipo_de_la_partida`, `test_sin_muertes_el_porcentaje_es_null`, `test_un_teamkill_cuenta_como_ya_lo_guarda_el_import` (con evento Kill de un companero), `test_traded_sin_muerte_no_descuadra`.
- Vitest (`src/tradesEquipo.test.js`): los cuatro del diseno mas dos de la nota.
- e2e (`humo.spec.js`): `el detalle de una partida muestra los trades por equipo`: dos filas, muertes y sin trade de cada una iguales a `team_trades` de `/api/matches/<id>/` (no numeros fijos de `seed_demo`), la nota y consola limpia.
- `docs/metricas.md`, seccion Trades: fila **Trades por equipo**.

Criterios: 1 -> suma_cada_equipo + usa_el_equipo_de_cada_ronda; 2 -> cuadra_con_el_scoreboard; 3 -> teamkill + traded_sin_muerte; 4 -> e2e; 5 -> metricas.md.

Desvio menor: la revision ciega marco (MEDIUM) que con un `team_index` que cambie entre rondas el panel (por ronda, como pide el criterio 1) y el scoreboard (agrupa por indice y lo etiqueta con el de la partida) no cuadrarian. Se dejo la logica por ronda que pide la ficha y `metricas.md` lo dice explicito; en `seed_demo` y en partidas normales el indice es fijo y cuadran. Hallazgo LOW sin cambio: el test de cuadratura no puede comparar `traded_deaths` con el scoreboard porque el scoreboard no tiene esa columna.

Skills: no aplica (lo resuelven `DataTable` y `Panel`).
OMC: plan=— · revisión=3 hallazgos (2 arreglados) · verificación=—

## Revision 2026-11-05 sobre 5e780a5

Revisor 20261105T0247Z-cQMp2TZ. VERDE 5e780a5 (894/159/55). Veredicto: aprobar. Hallazgos: [LOW] el test del teamkill no distinguia sumar de recalcular -> agregado `test_suma_untraded_death_tal_cual_lo_guardo_el_import`; [LOW] un comentario de `TradesPorEquipo` dice el que, no el por que (borrar en el proximo toque).

Skills: no aplica.
OMC: plan=— · revisión=2 hallazgos (1 arreglado con test) · verificación=—

## QA 2026-11-05 sobre 5e4c0ab

QA 20261105T0256Z-cFRtPBc. Rama ya fusionada con dev 2da1b7d. Scripts temporales en el scratchpad; ningun `.rec` ni `.sqlite3` al repo.

- check.sh: `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s -- --de-nuevo` -> `VERDE 5e4c0ab3d en 116s: 895 tests backend, 159 vitest, 55 e2e`.
- Base vacia (`SQLITE_PATH=<tmp> manage.py migrate`, `runserver`): `/api/matches/` 200, `/api/matches/1/` y `/0/` 404. `/api/matches/-1/` y `/foo/` dan 200 `text/html` (catch-all del SPA, la ruta es `<int:pk>`): preexistente, no es de esta ficha.
- `seed_demo` (29 partidas): script que suma las filas de `scoreboard` por equipo (`deaths`, `untraded_deaths`, `trade_kills`) y las compara con `team_trades`: coinciden en las 29 y en los dos equipos (criterio 2). `tradeadas + sin trade != muertes` en `seed_demo` (ej. tu equipo 19/0/7, rival 11/0/0) porque el seed solo escribe `was_traded`/`untraded_death` en tu fila; el import real (`metrics.annotate_trades`) lo escribe para todos. La vista suma lo guardado (criterio 3); el panel de la demo muestra 0 % sin trade al rival.
- Bordes con `tests/factories.py`: partida de un solo jugador (ronda sin bajas y ronda muerto sin trade) -> tu equipo 1/0/1/0, 100.0 %; rival en ceros con `untraded_pct: null`. Partida sin muertes -> los dos `null`. Partida sin rondas -> ceros y `null`, 200.
- UI (Playwright sobre `runserver`): `/partidas/32` y `/33` muestran el panel con dos filas, `—` en el % nulo y la nota "Tu equipo dejó 1 muerte sin trade; el rival, 0.", consola limpia. `/partidas/34` (0 rondas) rompe con `TypeError ... reading 'label'` en `MatchDetail.jsx:33` (`rounds[Math.min(selected, rounds.length - 1)]`): codigo que ya esta en dev, fuera de esta ficha; queda como ficha bug aparte.
- Chunk inicial (`vite build`): dev `index` 188.91 kB, rama 188967 B (+57 B). `MatchDetail` (lazy) 12.12 -> 14.03 kB.
- Mutaciones (`manage.py test tests.test_trades_por_equipo`): sin el filtro `died` en tradeadas cae `test_traded_sin_muerte_no_descuadra`; equipo fijo de la partida cae `test_trades_por_equipo_usa_el_equipo_de_cada_ronda`; recalcular sin trade desde `died`/`was_traded` cae `test_suma_untraded_death_tal_cual_lo_guardo_el_import`; `untraded_deaths: 'mas'` en `tradesEquipo.js` hace caer 2 vitest. Codigo restaurado.

Criterios 1 a 5: cumplidos. Veredicto: aprobado.

Skills: no aplica.
OMC: plan=— · revisión=— · verificación=PASS

## Verificar en el PC

## Pendiente

## Para el humano
