# 76. Aperturas que pesan: las que no te devolvieron y las que nadie vengo

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: impacto
area: backend
prioridad: 3
fuente: idea K10 de `ALCANCE.md` (Investigador 2026-11-03); [Siege.GG, rating rebalance](https://siege.gg/blog/946-player-rating-rebalance) (2026-08-11, "we are now only factoring in an extra weight on opening kills that were not traded"; "players are not penalized extra for going in first, only to die and have their deaths traded"). En `dev` bcdbdf5 `RoundPlayer` guarda `opening_kill`, `opening_death` y `was_traded`; `docs/metricas.md:160-171` define Duelos de apertura sin distinguir trades
archivos: backend/replays/models.py, backend/replays/migrations/0004_roundplayer_opening_kill_traded.py, backend/replays/analytics/metrics.py, backend/replays/ingest.py, backend/replays/recompute.py, backend/replays/management/commands/recompute.py, backend/replays/analytics/aggregates.py, frontend/src/aperturasTrade.js, frontend/src/aperturasTrade.test.js, frontend/src/pages/Dashboard.jsx, frontend/e2e/humo.spec.js, backend/tests/test_aperturas_trade.py, backend/tests/test_recompute.py, backend/tests/test_ingest.py, docs/metricas.md
turnos: po 20261104T1206Z-c8cAo8L, arquitecto 20261104T1604Z-cAKAGx1

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

Plan por consenso (receta 1 de OMC, modo deliberado: migracion + `recompute`),
APPROVE en la ronda 1 con las correcciones del architect y del critic ya
absorbidas. Referencias sobre `dev` bcdbdf5.

**Lectura del criterio 2:** `overview()` devuelve `overall`
(`aggregates.py:278`); "en `total`" de la ficha es `overall` (`total` es la
variable de `Dashboard.jsx:32`).

### Decisiones

1. **Definicion: el trade del evento, no la letra de la ficha.**
   - *Ganada devuelta*: tienes `opening_kill` y el primer `Kill` de la ronda
     (que es tu apertura) quedo `traded` (el equipo de tu victima te mato
     dentro de `TRADE_WINDOW_SECONDS`; gap == ventana cuenta, igual que
     `annotate_trades`, `metrics.py:76-79`). *Ganada limpia*: `opening_kill`
     sin esa marca.
   - *Perdida vengada*: `opening_death` y `was_traded`. *Perdida sin vengar*:
     `opening_death` y no `was_traded` (un `Death` sin autor de apertura cae
     siempre aca).
   - Por que: es la misma marca "tradeada" que ya muestra el timeline (la
     ronda no puede decir tradeada y el Inicio limpia), coincide con Siege.GG
     ("opening kills that were not traded") y la migracion la llena exacta.
   - Diferencias con la letra ("no moriste dentro de la ventana"), que van a
     `metricas.md` y a `## Para el humano`: la apertura queda **limpia** si
     moriste dentro de la ventana (a) por teamkill, (b) por un `Death` sin
     autor, o (c) si la victima no figura entre los jugadores
     (`metrics.py:71-73`, `victim_team is None`). En 5v5 fuera de esos casos
     las dos lecturas dan lo mismo.
2. **Columna nueva `RoundPlayer.opening_kill_traded`** (opcion A). Descartadas:
   derivar al consultar con `Exists` (rompe "se calcula al importar" y mete
   una subconsulta correlacionada en `overview`); la letra con `death_clock`
   (habria que guardar el reloj de la apertura y contradice el timeline). Se
   elige la columna, ademas, porque es robusta ante una baja repetida sobre la
   misma victima (rareza de r6-dissect), donde la autounion de `RoundPlayer`
   divergeria.
3. **Agregados: dict aparte, solo en `overview()["overall"]`.** No va en
   `AGGREGATES`: no cambian los CSV de `export.py` (columnas = union de
   claves) ni `_fold` (`aggregates.py:1764`). Tampoco en `totals()`.
4. **UI: panel debajo de la grilla `.kpis` del Inicio**, antes de
   `ResumenPartidas` (`Dashboard.jsx:84-86`): el `sub` de la tarjeta de la
   `:65` no tiene lugar para 4 conteos con 4 winrates.
5. **`seed_demo` no cambia.** Ahi toda fila con `opening_kill` sobrevive
   (`seed_demo.py:229-240`, `indice%6==0` implica `murio=False`) y ninguna
   `opening_death` esta tradeada: el e2e ve limpias == aperturas ganadas y
   "—" en el winrate de devueltas y vengadas. Los casos con datos los cubre
   el backend.

### Claves (las fijan API, vitest y e2e)

En `overall`: `opening_kills_clean`, `opening_kills_traded`,
`opening_deaths_traded`, `opening_deaths_untraded` (conteos) y
`winrate_opening_kill_clean`, `winrate_opening_kill_traded`,
`winrate_opening_death_traded`, `winrate_opening_death_untraded` (`_pct`,
`null` sin muestra). Alias internos `won_opening_kill_clean` etc. Cuidado con
la `s`: `opening_kill_traded` es el campo y `opening_kills_traded` el alias;
ningun alias puede repetir un nombre de campo (`aggregates.py:158`).

### Plan

1. **Modelo, regla, migracion.**
   - `backend/replays/models.py:145-150`: `opening_kill_traded =
     models.BooleanField(default=False)` con comentario del por que.
   - `backend/replays/analytics/metrics.py`: linea en el docstring de
     definiciones (`:9-19`). En `annotate_trades` (`:51`): en el reset,
     `m["opening_kill_traded"] = False`; al final, si `kill_events` y
     `kill_events[0]["traded"]` y `metrics.get(actor, {}).get("opening_kill")`,
     True. Vale porque `opening_kill` solo existe si `death_events[0]` es un
     Kill (`:320-324`), y entonces es `kill_events[0]`. El dict base de
     `analyse_round` (`:307`) suma `"opening_kill_traded": False`.
   - `backend/replays/ingest.py:261`: pasar el campo.
   - `backend/replays/migrations/0004_roundplayer_opening_kill_traded.py`:
     AddField + `RunPython(llenar, noop)`, estilo `0003`. `llenar`: UPDATE
     `pk__in` de las filas con `opening_kill=True` cuyo primer `Event`
     `kind="Kill"` por `order` tiene `traded=True` y `actor_name == username`
     (Subquery). Copia el estado que dejo `annotate_trades` en `Event.traded`
     (no hay ventana persistida: es la que estaba en `settings` al importar o
     al ultimo `recompute`); no recalcula trades ni abre `.rec`.
2. **Recompute** (`backend/replays/recompute.py`): `"opening_kill_traded"` en
   `CAMPOS` (`:40`); `"opening_kill": p.opening_kill` en el dict de
   `:65-74` (sin eso recompute pone todas en False sin error: pre-mortem 1);
   docstring del modulo y `help` del comando.
3. **Agregados y API** (`backend/replays/analytics/aggregates.py`): dict
   `APERTURAS_CON_TRADE` junto a `AGGREGATES` y `desglose_aperturas(qs) ->
   dict` con las 8 claves; `overview()` hace `overall.update(desglose_aperturas(qs))`
   sobre el mismo `qs` filtrado (una consulta mas). `attack`/`defense` no cambian.
4. **UI y docs.**
   - `frontend/src/aperturasTrade.js` (modulo nuevo; `aperturas.js` ya existe
     y es de las marcas del timeline, con `casosApertura.json`: no se toca):
     `filasDeAperturasConTrade(overall)` -> 4 filas `{key, label, rondas, winrate}`
     en orden Ganada limpia, Ganada devuelta, Perdida vengada, Perdida sin
     vengar; claves ausentes (backend viejo) dan `null`.
   - `frontend/src/pages/Dashboard.jsx`: `<Panel title="Aperturas que pesan"
     hint="Si tu apertura sobrevivió al trade y si tu equipo vengó la que perdiste.">`
     con `DataTable` (Apertura / Rondas / Ganadas %), `rowKey` = `key`.
   - `docs/metricas.md`, seccion *Duelos de apertura* (`:160-171`): fila
     **Aperturas limpias, devueltas y vengadas** con la definicion de la
     decision 1, el borde, los tres casos (a)(b)(c), que las cuatro filas
     suman las crudas y que el Rating no cambia.
5. **Tests.**
   - Unit, `backend/tests/test_aperturas_trade.py` (con `round_data(gap)` de
     `tests/test_recompute.py:18`): `test_apertura_devuelta_en_el_borde_exacto_de_la_ventana`
     (gap 3.0, ventana 3.0 -> True), `test_apertura_limpia_si_la_venganza_llega_pasada_la_ventana`
     (3.01 -> False), `test_achicar_la_ventana_saca_la_apertura_devuelta`,
     `test_ronda_que_abre_con_death_no_marca_apertura_devuelta`,
     `test_solo_el_autor_de_la_apertura_queda_marcado`,
     `test_morir_por_teamkill_en_la_ventana_no_devuelve_la_apertura`,
     `test_victima_fuera_de_los_jugadores_deja_la_apertura_limpia`,
     `test_teamkill_de_apertura_vengado_por_el_equipo_queda_devuelto`.
   - Integracion: `test_las_cuatro_filas_suman_las_aperturas_crudas` (en
     `/api/overview/`), `test_el_desglose_respeta_el_filtro_de_lado`,
     `test_sin_muestra_el_winrate_es_null`,
     `test_el_csv_de_mapas_no_trae_columnas_nuevas`,
     `test_el_rating_no_cambia_con_la_apertura_devuelta`; en
     `tests/test_ingest.py` `test_datos_coherentes` (`:96`) suma el invariante
     `opening_kill_traded => opening_kill` y que coincide con `Event.traded`
     del primer Kill.
   - Recompute (`tests/test_recompute.py`): `test_recompute_llena_la_apertura_devuelta_de_lo_ya_importado`,
     `test_recompute_dry_run_no_escribe_la_apertura_devuelta`,
     `test_recompute_de_apertura_devuelta_es_idempotente`.
   - Migracion (patron `tests/test_clutch.py:249`):
     `test_la_migracion_llena_la_apertura_devuelta_desde_los_eventos` (Kill
     tradeado marca, no tradeado no, ronda que abre con Death y ronda sin
     jugadores no la tumban) y `test_migracion_y_recompute_coinciden`:
     siguiendo `test_recompute.py:233-235`, primero `recompute()` (las
     fabricas `kills=1, died=True` no cuadran con los eventos), despues
     `update(opening_kill_traded=False)`, `llenar(apps, None)` y recien ahi
     `recompute(dry_run=True).players_changed == 0`.
   - Vitest, `frontend/src/aperturasTrade.test.js`: `da cuatro filas en orden`,
     `sin muestra el winrate queda en null`, `sin claves nuevas no rompe`.
   - e2e, `frontend/e2e/humo.spec.js`: `el Resumen muestra las aperturas que
     pesan`: panel visible; "Ganada limpia" con el mismo conteo que
     `opening_kills` (leido de `/api/overview/` o del KPI "Duelos de
     apertura"); "Perdida sin vengar" con su conteo igual a `opening_deaths`;
     "Ganada devuelta" con "—" de winrate; consola limpia.

**Orden:** 1, 2, tests unit/recompute/migracion, 3 + integracion, 4 +
vitest + e2e, `npm run build`, `check.sh` completo.

**Pre-mortem:** (1) recompute borra las devueltas si falta `opening_kill` en
su dict: lo frenan los tests de recompute y de coincidencia. (2) meterlo en
`AGGREGATES` por comodidad: CSV con 8 columnas mas; lo frena el test del CSV.
(3) base real con `Event.traded` de una ventana vieja (cambiada sin
recompute): la migracion copia ese estado, coherente con el `was_traded` que
ya se muestra; `recompute` alinea las dos cosas.

**Que puede romperse:** migracion sobre la base real (UPDATE con Subquery,
sin tiempo medido); `recompute` (campo nuevo en `CAMPOS`); build. No se
mueven Rating, CSV ni numeros de `seed_demo`.

**Verificacion manual / Verificar en el PC (base real):** respaldo desde
Ajustes; `python manage.py recompute --dry-run` (anotar N); `migrate`
(anotar cuanto tarda); `recompute --dry-run` otra vez: si el primero dio 0,
el segundo tiene que dar 0 (si sube, migracion y regla discrepan: es bug);
si el primero dio N>0, correr `recompute` y seguir. En el Inicio, limpias +
devueltas == aperturas ganadas de la tarjeta y vengadas + sin vengar ==
perdidas, con y sin filtro de lado.

Skills: no aplica (panel y tabla que el repo ya resuelve; migracion con precedente `0003`).
OMC: plan=APPROVE · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Verificar en el PC

## Pendiente

## Para el humano

- 2026-11-04 (arquitecto): la "apertura devuelta" se define con el trade del
  evento (el equipo de tu victima te mato dentro de la ventana), no con "no
  moriste dentro de la ventana". Quedan limpias aunque mueras enseguida: por
  teamkill, por `Death` sin autor, o si la victima no figura entre los
  jugadores. Si preferis la letra, es una linea de `annotate_trades` y un
  test; no hace falta frenar la ficha. Tambien: un teamkill de apertura que tu
  propio equipo venga queda "devuelto" (coherente con la regla, raro de leer).

(Si la migracion o `recompute` pesan: la ficha toca columnas de
`RoundPlayer` como la 55. Verificar `recompute` en el PC con la base real.)
