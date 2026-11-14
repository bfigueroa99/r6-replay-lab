# 140. Ventaja tirada marcada en el detalle de partida

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F26 (salio del Fuera de alcance y de la lista de la 133, ya en dev)
archivos: backend/replays/views.py (match_detail), backend/tests/test_ventaja_tirada_en_detalle.py (nuevo), frontend/src/ventajaTiradaDetalle.js (nuevo), frontend/src/ventajaTiradaDetalle.test.js (nuevo), frontend/src/pages/MatchDetail.jsx, frontend/src/styles.css, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T2318Z-cpCpgff, arquitecto 20261114T0104Z-choi73m

## PR

## Que gana quien usa la app

En el detalle de partida, las pestañas de las rondas que tu equipo perdio
despues de quedar con mas vivos llevan una marca, con la ventaja maxima en el
`title`: ves en la propia partida cuales se tiraron sin ir a Duelos. Duelos
(ficha 133) da el total entre partidas; esto lo pone donde se revisa la ronda.

## Criterios de aceptacion

- [ ] `/api/matches/<id>/` suma a cada ronda `max_advantage`: el valor de
      `metrics.ventaja_maxima` sobre el feed de esa ronda (`Kill`, `Death`,
      `PlayerLeave` en orden, con `clock`) para tu equipo, o `null` si no
      hubo ventaja medible. Misma regla que `/api/duels/thrown-advantage/`, sin
      reimplementarla: test que para una partida sembrada compara cada ronda
      con lo que cuenta `thrown_advantage` filtrado a esa partida.
- [ ] Test de la vista: ronda 5v4 perdida -> `max_advantage: 1`; ronda que
      llego a 5v3 y se perdio -> `2`; eliminacion ganada sin ventaja previa ->
      `null` o `< 1`; ronda sin bajas -> `null`. Sin consultas extra por
      ronda (`assertNumQueries` constante con 1 y con 3 rondas).
- [ ] Funcion pura en el frontend `esVentajaTirada(ronda)`:
      `my_team_won === false` y `max_advantage >= 1`; vitest con ganada con
      ventaja, perdida con ventaja, perdida sin ventaja y sin ganador.
- [ ] La pestaña de una ronda tirada lleva una marca visible (clase y texto
      corto, no solo color) y su `title` suma "Ventaja tirada: +N"; las
      demas pestañas se ven igual que hoy. e2e sobre `seed_demo`: la primera
      ronda tirada que da la API tiene la marca y una ronda ganada no;
      consola limpia.
- [ ] Fila en `docs/metricas.md` (o la de Ventaja numérica tirada ampliada)
      que diga que el detalle usa la misma regla.

## Fuera de alcance

- Marcar las rondas dadas vuelta en inferioridad (F12).
- La linea de vivos de la ronda (F13).
- Un filtro de "solo rondas tiradas" en la tira de rondas.

## Diseno

(arquitecto 20261114T0104Z-choi73m) Filtros duros: pasa. Usa `Kill`, `Death` y
`PlayerLeave` del feed, su `clock` y el `team_index` de cada fila, que el
`.rec` entrega; sin red, sin dependencias, sin POST, sin migracion. No es
premisa falsa: el detalle no marca hoy ninguna ronda por ventaja; Duelos (133)
solo da el total y una lista de 20. Una sola forma obvia (llamar a
`metrics.ventaja_maxima` con el feed que el detalle ya trae): sin arena ni
consenso.

Implementar despues de que #136 se mergee: la 136 toca el mismo bloque
`.round-tabs` de `frontend/src/pages/MatchDetail.jsx` (clase, `title` y un
`span` dentro del boton), el dict `datos` de cada ronda en `match_detail`
(`views.py`), el CSS de `.round-tab` y el test e2e del detalle. Sobre la 136
ya mergeada esto se suma al lado sin pisarse.

**Backend** (`backend/replays/views.py`, `match_detail`):
- Importar `ventaja_maxima` y `PLAYER_LEAVE` de `.analytics.metrics` (y
  `Event` si no esta).
- Dentro del bucle de rondas, con lo ya prefetcheado (`players__player`,
  `events`; `Event.Meta.ordering = ["round", "order"]`), sin consultas
  nuevas: `team_of = {rp.player_id: rp.team_index for rp in rnd.players.all() if rp.player_id}`;
  `mia = next((rp for rp in rnd.players.all() if rp.is_me), None)`;
  `feed = [{"kind": e.kind, "actor": e.actor_id, "target": e.target_id, "clock": e.clock} for e in rnd.events.all() if e.kind in (Event.KILL, Event.DEATH, PLAYER_LEAVE)]`
  (las mismas claves que arma `aggregates.thrown_advantage`);
  `"max_advantage": ventaja_maxima(feed, team_of, mia.team_index) if mia else None`
  en `datos`, al lado de `overtime`. Es exactamente la llamada de
  `thrown_advantage` (`aggregates.py`, bucle de `filas`): mismo `team_of`
  por `player_id`, misma fila tuya (`base_queryset` = tus filas, `is_me`).
  Sin fila tuya en la ronda: `null` (Duelos tampoco la cuenta). El valor va
  tal cual, tambien `0` o negativo: el umbral `>= 1` lo aplica el frontend,
  como el `ventaja < 1` de `thrown_advantage`.
- Nada mas cambia en el payload; `describe_round(datos)` no lee la clave.

**Tests Django** (`backend/tests/test_ventaja_tirada_en_detalle.py`, nuevo,
con las fabricas de `test_ventaja_tirada.py`, que ya arma rondas con feed y
`team_index`):
- `test_ronda_5v4_perdida_da_ventaja_uno` (cae un rival, despues tu equipo
  pierde la ronda -> `max_advantage == 1`).
- `test_ronda_que_llego_a_5v3_da_ventaja_dos`.
- `test_eliminacion_ganada_sin_ventaja_previa_no_suma` (trade 1x1 en
  segundos distintos y despues tu equipo elimina -> lo que devuelva
  `ventaja_maxima`, `None` o `< 1`).
- `test_ronda_sin_bajas_da_null`.
- `test_ronda_sin_tu_fila_da_null`.
- `test_el_detalle_coincide_con_duelos` (una partida con 3-4 rondas
  variadas: las rondas con `max_advantage >= 1` y `my_team_won is not None`
  son `agg.thrown_advantage()["rounds"]`, las perdidas de esas son
  `["thrown"]`, y los `(match_id, round)` de `recent` son las perdidas
  marcadas).
- `test_consultas_constantes`: mismo numero de consultas del detalle con 1
  y con 3 rondas (`CaptureQueriesContext`, como `test_tira_de_rondas.py`).
  Si el detalle ya hoy no es constante por otra clave, el test fija que la
  clave nueva no suma ninguna (el Dev lo anota).

**Frontend:**
- `frontend/src/ventajaTiradaDetalle.js` (nuevo): `esVentajaTirada(ronda)`
  -> `ronda?.my_team_won === false && ronda?.max_advantage >= 1` (`null` da
  `false`); `textoVentajaTirada(ronda)` -> `"Ventaja tirada: +N"` o `''`.
- `frontend/src/ventajaTiradaDetalle.test.js` (vitest): `ganada con ventaja
  no es tirada`; `perdida con ventaja es tirada`; `perdida sin ventaja no
  es tirada` (0, negativo y `null`); `sin ganador no es tirada`; `el texto
  lleva el signo y la ventaja` (+1, +2); `vacio si no es tirada`.
- `frontend/src/pages/MatchDetail.jsx`, el boton de `.round-tabs`: con
  `esVentajaTirada(r)`, clase `tirada`; el `title` suma
  ` · Ventaja tirada: +N` (despues de lo que deje la 136); dentro, una marca
  visible `<span className="marca-tirada" aria-hidden="true">+N</span>` y
  `<span className="solo-lector"> · ventaja tirada de +N</span>`. Sin
  `aria-label` (label-in-name, como la 136). Flechas, `p` y `#ronda-N` no
  cambian: no se agrega nada fuera de los botones.
- `frontend/src/styles.css`, junto a `.round-tab.overtime`:
  `.round-tab.tirada` con una marca que no sea solo color (p. ej.
  `box-shadow: inset 0 -2px 0 var(--bad)` ademas del texto) y `.marca-tirada`
  (10-11px, `font-weight: 700`); contraste lo mide QA.

**e2e** (`frontend/e2e/humo.spec.js`, test nuevo `el detalle marca las
rondas con ventaja tirada`): pide `/api/duels/thrown-advantage/`; si
`recent` esta vacio, abre el detalle de la primera partida y afirma 0
`.round-tab.tirada` dentro de `#rondas`; si no, abre
`/partidas/<recent[0].match_id>#ronda-<n>` (el ancla que ya usa la lista de
Duelos) y afirma que la pestaña activa tiene `tirada` y el texto
`+<max_advantage>` que da `/api/matches/<id>/` para esa ronda, y que una
pestaña `.win` de esa partida no tiene `tirada`. Consola limpia. Los
numeros salen de la API, no de literales del seed.

**`docs/metricas.md`**: ampliar la fila **Ventaja numérica tirada** con:
"El detalle de partida marca la pestaña de cada ronda tirada (perdida con
ventaja maxima de 1 o mas) con la misma regla, `max_advantage` de
`/api/matches/<id>/`; la marca es por ronda y no tiene muestra minima." Sin
fila ni corte nuevos.

**Orden:** tests Django en rojo -> clave en la vista -> vitest -> helper ->
JSX + CSS -> e2e -> `metricas.md` -> `npm run build`.

**Que puede romperse:** el e2e de la 136 cuenta `.round-tab` y
`.round-tab.overtime` (no cambia); el texto que leen otros e2e
(`.round-tab.active .n`, `toContainText('R1')`): la marca va en su propio
`span` y `.n` sigue igual. Si `seed_demo` no tuviera rondas tiradas, el e2e
cae en la rama de ausencia y la marca solo la cubren Django y vitest
(anotarlo en `## Implementacion`).

**Verificacion manual:** Duelos -> Ventaja numérica tirada -> una ronda de la
lista: en el detalle su pestaña lleva `+N` y el `title` dice "Ventaja
tirada: +N"; una ronda ganada con ventaja no lleva marca.

Skills: no aplica (una clave mas en el detalle con la regla existente y una marca en el selector).
Skills del repo: testing-strategy (regla y coincidencia con Duelos en Django, predicado en vitest, marca en e2e por la API); statistical-analysis (sin numero nuevo: misma regla y denominador que la 133; la marca es por ronda, sin muestra minima); dataviz no aplica (sin grafico).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

(nada)
