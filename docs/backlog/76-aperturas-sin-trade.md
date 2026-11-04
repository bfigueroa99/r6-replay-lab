# 76. Aperturas que pesan: las que no te devolvieron y las que nadie vengo

estado: propuesto
candado: arquitecto 2026-11-04T16:05Z
rama: -
tipo: funcionalidad
epica: impacto
area: backend
prioridad: 3
fuente: idea K10 de `ALCANCE.md` (Investigador 2026-11-03); [Siege.GG, rating rebalance](https://siege.gg/blog/946-player-rating-rebalance) (2026-08-11, "we are now only factoring in an extra weight on opening kills that were not traded"; "players are not penalized extra for going in first, only to die and have their deaths traded"). En `dev` bcdbdf5 `RoundPlayer` guarda `opening_kill`, `opening_death` y `was_traded`; `docs/metricas.md:160-171` define Duelos de apertura sin distinguir trades
archivos: backend/replays/analytics/metrics.py, backend/replays/models.py, backend/replays/migrations/, backend/replays/analytics/aggregates.py, frontend/src/pages/Dashboard.jsx, backend/tests/, docs/metricas.md
turnos: po 20261104T1206Z-c8cAo8L

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy entrar primero y morir tradeado cuenta igual que regalar la ronda, y
ganar la apertura para morir dos segundos despues cuenta igual que abrir
espacio de verdad. Con esto el Inicio dice, de tus aperturas ganadas,
cuantas quedaron limpias (no te mataron dentro de la ventana de trade) y,
de las perdidas, cuantas tu equipo vengo, con el winrate de ronda de cada
grupo: si tu forma de abrir le sirve al equipo aunque el 1-1 crudo no lo
muestre.

## Criterios de aceptacion

- [ ] Apertura ganada *limpia*: tienes `opening_kill` y no moriste dentro de `TRADE_WINDOW_SECONDS` despues de esa baja (reloj del feed, el mismo que usa `traded`). Apertura perdida *vengada*: `opening_death` y `was_traded`. Se calcula al importar (regla de `CLAUDE.md`: las metricas se calculan al importar) y `manage.py recompute` llena lo ya importado. Test por cada caso, con borde exacto en la ventana.
- [ ] `GET /api/overview/` devuelve en `total` `opening_kills_clean`, `opening_deaths_traded` y el winrate de ronda de las cuatro filas (ganada limpia, ganada devuelta, perdida vengada, perdida sin vengar); `null` sin muestra. Respeta los filtros de siempre.
- [ ] Las cuatro filas suman las aperturas crudas (`opening_kills` y `opening_deaths`): test que lo afirma.
- [ ] El Inicio (`Dashboard.jsx`) lo muestra junto a la tarjeta de Aperturas que ya existe, sin tarjeta nueva en la grilla de arriba (subtitulo o panel debajo, lo decide el Arquitecto); el e2e lo ve con `seed_demo`.
- [ ] Fila nueva en `docs/metricas.md`, en *Duelos de apertura*. El Rating no cambia (cambiar su definicion es P10).

## Fuera de alcance

Cambiar el peso de la apertura en el Rating; el mismo corte por operador o
por mapa (otra ficha si rinde); clutches silenciosos (K11).

## Diseno

## Implementacion

## Revision

## QA

## Verificar en el PC

## Pendiente

## Para el humano

(Si la migracion o `recompute` pesan: la ficha toca columnas de
`RoundPlayer` como la 55. Verificar `recompute` en el PC con la base real.)
