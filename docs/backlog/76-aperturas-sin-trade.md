# 76. Aperturas que pesan: las que no te devolvieron y las que nadie vengo

estado: entregado
candado: -
rama: claude/equipo-dev/76-aperturas-sin-trade
tipo: funcionalidad
epica: impacto
area: backend
prioridad: 3
fuente: idea K10 de `ALCANCE.md` (Investigador 2026-11-03); [Siege.GG, rating rebalance](https://siege.gg/blog/946-player-rating-rebalance) (2026-08-11, "we are now only factoring in an extra weight on opening kills that were not traded"; "players are not penalized extra for going in first, only to die and have their deaths traded"). En `dev` bcdbdf5 `RoundPlayer` guarda `opening_kill`, `opening_death` y `was_traded`; `docs/metricas.md:160-171` define Duelos de apertura sin distinguir trades
archivos: backend/replays/models.py, backend/replays/migrations/0004_roundplayer_opening_kill_traded.py, backend/replays/analytics/metrics.py, backend/replays/ingest.py, backend/replays/recompute.py, backend/replays/management/commands/recompute.py, backend/replays/analytics/aggregates.py, frontend/src/aperturasTrade.js, frontend/src/aperturasTrade.test.js, frontend/src/pages/Dashboard.jsx, frontend/e2e/humo.spec.js, backend/tests/test_aperturas_trade.py, backend/tests/test_recompute.py, backend/tests/test_ingest.py, docs/metricas.md
turnos: po 20261104T1206Z-c8cAo8L, arquitecto 20261104T1604Z-cAKAGx1, dev 20261105T0220Z-cPG9p3E, revisor 20261105T0247Z-cw2xCMP, qa 20261105T0256Z-c25s1Gw, release 20261105T0256Z-c25s1Gw

## PR

Titulo: `[equipo-dev][backend] Aperturas que pesan: las que no te devolvieron y las que nadie vengo`

### Que cambia

El Inicio suma, debajo de la grilla de KPIs, el panel *Aperturas que pesan*: de tus aperturas ganadas, cuantas quedaron limpias y cuantas te devolvieron (el equipo de tu victima te mato dentro de la ventana de trade), y de las perdidas, cuantas vengo tu equipo y cuantas no, con el winrate de ronda de cada grupo. `GET /api/overview/` trae las 8 claves nuevas en `overall` y respeta los filtros de siempre. El Rating y los CSV no cambian.

### Por que esto y no otra cosa

Ficha 76, idea K10 de `ALCANCE.md` (epica `impacto`), de la rebalanceada del rating de Siege.GG (solo pesan las aperturas no tradeadas). Definicion: la marca `traded` del evento, la misma del timeline (respuesta del humano 2026-11-05: opcion a). Descartado: derivarla al consultar con `Exists` (rompe "se calcula al importar"), la letra con `death_clock` (contradice el timeline) y meterla en `AGGREGATES` (8 columnas mas en los CSV).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE c4c687fe6, 909 tests backend, 156 vitest, 55 e2e (QA, sobre `dev` 2da1b7d fusionado; despues solo commits de la ficha).
- Tests nuevos: `tests/test_aperturas_trade.py` (22: borde exacto de la ventana para devuelta y vengada, ventana corta, teamkill, victima fuera de los jugadores, ronda que abre con Death, reset de la marca; API con las cuatro filas que suman las crudas, filtro de lado, `null` sin muestra, CSV y Rating sin cambios; `recompute` llena, dry-run, idempotente; migracion y coincidencia con `recompute`), invariante en `test_ingest.test_datos_coherentes`, vitest `aperturasTrade.test.js` (3) y e2e `el Resumen muestra las aperturas que pesan`.
- Manual (QA): base con esquema de `dev` + `seed_demo` + siembra sintetica, `migrate` (0,39 s) y `recompute`: 0 de 1330 filas difieren entre migracion y recompute. `curl /api/overview/` con 16 combinaciones de filtros y bordes en base vacia y sembrada: 200, la suma cierra siempre. Chromium: panel visible, consola limpia. Chunk inicial +0,6 %. 4 de 5 mutaciones caen (la que sobrevive es casi equivalente).
- OMC: diseno plan=APPROVE · implementacion revisión=3 hallazgos (1 arreglado) · revision revisión=3 hallazgos LOW (1 arreglado con tests) · QA verificación=PASS.

### Riesgos y lo que no entra

Migracion `0004_roundplayer_opening_kill_traded` (AddField + RunPython que copia `Event.traded` del primer Kill, sin abrir `.rec`) y campo nuevo en `recompute`: en la base real, migrar antes de correr `recompute`. Queda limpia una apertura si moriste en la ventana por teamkill, por un Death sin autor o si la victima no figura entre los jugadores; un teamkill de apertura vengado por tu propio equipo queda devuelto. Fuera: peso de la apertura en el Rating (P10), el corte por operador o mapa, clutches silenciosos (K11).

### Como probarlo en 2 minutos

```bash
cd backend
python manage.py migrate
python manage.py test tests.test_aperturas_trade tests.test_recompute
python manage.py runserver
# http://127.0.0.1:8000/  -> panel "Aperturas que pesan" debajo de los KPIs
# http://127.0.0.1:8000/api/overview/?side=Attack  -> overall.opening_kills_clean + opening_kills_traded == opening_kills
```

### Verificar en el PC

Base real, en `backend/`: respaldo desde Ajustes; `python manage.py migrate` primero
(anotar cuanto tarda; con el codigo nuevo, `recompute` antes de migrar falla con `no such
column: replays_roundplayer.opening_kill_traded`, lo vio la QA); despues `python manage.py
recompute --dry-run` (anotar N; si N > 0, correr `python manage.py recompute` y otra vez
`--dry-run`: "Nada que recalcular"). En el Inicio, limpias + devueltas == aperturas ganadas
y vengadas + sin vengar == perdidas, con y sin filtro de lado.

### Para el humano

Nada (la pregunta de la apertura devuelta quedo respondida el 2026-11-05).

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Hoy entrar primero y morir tradeado cuenta igual que regalar la ronda, y
ganar la apertura para morir dos segundos despues cuenta igual que abrir
espacio de verdad. Con esto el Inicio dice, de tus aperturas ganadas,
cuantas quedaron limpias (no te mataron dentro de la ventana de trade) y,
de las perdidas, cuantas tu equipo vengo, con el winrate de ronda de cada
grupo: si tu forma de abrir le sirve al equipo aunque el 1-1 crudo no lo
muestre.

## Criterios de aceptacion

- [x] Apertura ganada *limpia*: tienes `opening_kill` y no moriste dentro de `TRADE_WINDOW_SECONDS` despues de esa baja (reloj del feed, el mismo que usa `traded`). Apertura perdida *vengada*: `opening_death` y `was_traded`. Se calcula al importar (regla de `CLAUDE.md`: las metricas se calculan al importar) y `manage.py recompute` llena lo ya importado. Test por cada caso, con borde exacto en la ventana.
- [x] `GET /api/overview/` devuelve en `total` `opening_kills_clean`, `opening_deaths_traded` y el winrate de ronda de las cuatro filas (ganada limpia, ganada devuelta, perdida vengada, perdida sin vengar); `null` sin muestra. Respeta los filtros de siempre.
- [x] Las cuatro filas suman las aperturas crudas (`opening_kills` y `opening_deaths`): test que lo afirma.
- [x] El Inicio (`Dashboard.jsx`) lo muestra junto a la tarjeta de Aperturas que ya existe, sin tarjeta nueva en la grilla de arriba (subtitulo o panel debajo, lo decide el Arquitecto); el e2e lo ve con `seed_demo`.
- [x] Fila nueva en `docs/metricas.md`, en *Duelos de apertura*. El Rating no cambia (cambiar su definicion es P10).

## Fuera de alcance

Cambiar el peso de la apertura en el Rating; el mismo corte por operador o
por mapa (otra ficha si rinde); clutches silenciosos (K11).

## Diseno

Columna `RoundPlayer.opening_kill_traded`, marcada en `annotate_trades` cuando `kill_events[0]` queda `traded` y su autor tiene `opening_kill`; migracion `0004` la llena desde `Event.traded`; `recompute` la rehace (`CAMPOS` y `opening_kill` en su dict). Desglose `APERTURAS_CON_TRADE` aparte de `AGGREGATES`, solo en `overview()["overall"]`. Panel debajo de la grilla `.kpis` del Inicio. `seed_demo` sin cambios. Detalle completo, decisiones y pre-mortem en `git log` de esta rama.

Skills: no aplica (panel y tabla que el repo ya resuelve; migracion con precedente `0003`).
OMC: plan=APPROVE · revisión=— · verificación=—

## Implementacion

(dev 20261105T0220Z-cPG9p3E) Diseno entero. Desvio menor: sin muestra la celda de winrate muestra un solo "—". Revision ciega: aprobar, 3 LOW (1 arreglado).

Skills: no aplica.
OMC: plan=— · revisión=3 hallazgos (1 arreglado) · verificación=—

## Revision 2026-11-05 sobre 6cb03c4

(revisor 20261105T0247Z-cw2xCMP) Tres ejes a ciegas (estandares, intencion, seguridad): aprobar, sin CRITICAL ni HIGH. Corregido: borde exacto de *perdida vengada* (2 tests agregados). Aceptados LOW: el e2e no ve devueltas ni vengadas (limite de `seed_demo`, lo cubre vitest); `metricas.md` no dice que un teamkill de apertura vengado por tu equipo cuenta como devuelta (esta en el PR).

Skills: no aplica.
OMC: plan=— · revisión=3 hallazgos LOW (1 arreglado con tests) · verificación=—

## QA 2026-11-05 sobre c4c687f

(qa 20261105T0256Z-c25s1Gw) Detalle completo en `git log` de esta rama (commit `Prueba: 76 aperturas sin trade`). `verificar.sh` VERDE c4c687fe6 (909 backend, 156 vitest, 55 e2e). Migracion sobre base con esquema de `dev`: OK en 0,39 s; 0 de 1330 filas difieren de `recompute`; invariante `opening_kill_traded => opening_kill` sin violaciones. `curl /api/overview/` con 16 combinaciones (incluidas `until=foo`, `page=-1`, `since=2026-13-40`, `map=NoExiste`) en base vacia y sembrada: 200, suma cerrada. Chromium: panel y consola limpia. Chunk inicial +0,6 %. Mutaciones: 4 de 5 caen; sobrevive quitar `autor == username` en la migracion (casi equivalente, LOW). omc-verifier PASS, 5 criterios VERIFIED. Veredicto: aprobado.

Skills: no aplica.
OMC: plan=— · revisión=— · verificación=PASS

## Verificar en el PC

Base real, en `backend/`: respaldo desde Ajustes; `python manage.py migrate` primero
(anotar cuanto tarda; con el codigo nuevo, `recompute` antes de migrar falla con `no such
column: replays_roundplayer.opening_kill_traded`, lo vio la QA); despues `python manage.py
recompute --dry-run` (anotar N; si N > 0, correr `python manage.py recompute` y otra vez
`--dry-run`: "Nada que recalcular"). En el Inicio, limpias + devueltas == aperturas ganadas
y vengadas + sin vengar == perdidas, con y sin filtro de lado.

## Pendiente

## Para el humano

- 2026-11-04 (arquitecto): la "apertura devuelta" se define con el trade del
  evento (el equipo de tu victima te mato dentro de la ventana), no con "no
  moriste dentro de la ventana". Quedan limpias aunque mueras enseguida: por
  teamkill, por `Death` sin autor, o si la victima no figura entre los
  jugadores. Si preferis la letra, es una linea de `annotate_trades` y un
  test; no hace falta frenar la ficha. Tambien: un teamkill de apertura que tu
  propio equipo venga queda "devuelto" (coherente con la regla, raro de leer).
- 2026-11-05 (humano, respondido en su sesion; lo anota po 20261105T0230Z-c8Ahepa):
  **respondida.** "Apertura devuelta" = (a), el trade del evento, lo ya
  disenado. No cambia nada del diseno ni de la implementacion.

(Si la migracion o `recompute` pesan: la ficha toca columnas de
`RoundPlayer` como la 55. Verificar `recompute` en el PC con la base real.)
