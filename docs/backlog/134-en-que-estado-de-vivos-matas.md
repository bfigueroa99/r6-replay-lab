# 134. En que estado de vivos matas

estado: con hallazgos
candado: -
rama: claude/equipo-dev/134-en-que-estado-de-vivos-matas
tipo: funcionalidad
epica: impacto
area: backend
prioridad: 3
fuente: ALCANCE.md K8; Fuera de alcance de la ficha 116 ("el reverso, tus bajas por estado (K8): otro tramo de la epica")
archivos: backend/replays/analytics/metrics.py (estado_al_matar), backend/replays/analytics/aggregates.py (kill_state), backend/replays/views.py, backend/replays/urls.py, backend/tests/test_estado_al_matar.py (nuevo), frontend/src/estadoAlMatar.js (nuevo), frontend/src/estadoAlMatar.test.js (nuevo), frontend/src/components/EstadoAlMatar.jsx (nuevo), frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1954Z-cfZTvvE, arquitecto 20261113T2317Z-cBbsozQ

## PR

## Que gana quien usa la app

Tus bajas repartidas por el estado de vivos de la ronda en el instante en
que las haces (5v5, 5v4, 4v5, 2v3...) y el winrate de esas rondas: si tus
bajas abren ventajas o llegan cuando la ronda ya estaba decidida. Es el
reverso de Estado al morir (ficha 116), que ya esta en Duelos.

## Criterios de aceptacion

- [ ] Un agregado devuelve, por estado `tuyos vivos v rivales vivos` justo
      antes de cada baja tuya a un rival, `kills` y `winrate` de esas rondas
      (sobre las que tienen ganador; una ronda con dos bajas tuyas cuenta
      en los dos estados). Test con una ronda armada: tu primera baja en
      `5v5`, la segunda en `5v4`.
- [ ] Los teamkills no cuentan como baja tuya (como `kills` desde la
      ficha 67) pero si restan un vivo de tu equipo; un `PlayerLeave` resta
      un vivo (como `pydissect/stats.py`). Test de los dos.
- [ ] Ventaja, paridad y desventaja agregadas (`ahead`, `even`, `behind`)
      ademas del estado exacto, con su winrate, con la misma recorrida de
      vivos que `death_state` (`metrics.estado_al_morir` o su vecina). Test.
- [ ] Los filtros globales aplican (lado, mapa, operador, tipo, fechas,
      sesion). Test de lado.
- [ ] Se ve en Duelos junto a Estado al morir, con la muestra minima de
      `metricas.md` como aviso; sin bajas, un texto y no un error; e2e por
      esa pagina con la consola limpia. Fila nueva en `docs/metricas.md`
      ("Estado al matar").

## Fuera de alcance

- Probabilidad de ganar por estado o impacto por baja (K1, K2).
- Bajas de tus compañeros por estado.
- Partidas con menos de 5 por lado: el estado se cuenta con los jugadores
  que hay, sin normalizar a 5v5 (como la 116).

## Diseno

(arquitecto 20261113T2317Z-cBbsozQ) Filtros duros: pasa. Usa solo `Kill`, `Death` y `PlayerLeave` del feed y el `team_index` de cada fila, que el `.rec` entrega; sin red, sin dependencias, endpoint GET. No es premisa falsa: Duelos tiene Estado al morir (116) y Ventaja numerica tirada (133), ninguno cuenta tus bajas por estado. Una sola forma obvia (el espejo de `death_state`): sin arena ni plan por consenso.

Implementar despues de que #133 se mergee: pisa `backend/replays/analytics/aggregates.py`, `metrics.py`, `views.py`, `urls.py`, `frontend/src/pages/Duelos.jsx`, `frontend/e2e/humo.spec.js` y `docs/metricas.md` de su rama, todos en la misma zona (paneles de Duelos, al lado de `death_state`).

**Regla** (`metrics.estado_al_matar(eventos, team_of) -> dict[jugador, list[tuple[int, int]]]`, en `backend/replays/analytics/metrics.py`, justo debajo de `estado_al_morir` y con su mismo recorrido):
- `vivos = set(team_of)`; por cada evento `Kill` (muerto = `target`), `Death` o `PlayerLeave` (muerto = `actor`), si el muerto no esta en `vivos` se salta.
- Si es `Kill`, el `actor` esta en `team_of`, sigue en `vivos` y `team_of[actor] != team_of[target]`: se anota para el `actor` el par `(aliados_vivos_del_actor, rivales_vivos)` **antes** de descontar al muerto (contandose a si mismo). Un teamkill (mismo equipo), un `Kill` sin `actor` o con un `actor` que ya no esta vivo (murio o se fue antes; datos raros) no se anota, pero el muerto igual sale de `vivos`.
- Despues, `vivos.discard(muerto)`. Un `PlayerLeave` resta un vivo y no es baja.
- Sin agrupar por segundo de reloj: igual que `estado_al_morir`, cada baja ve el estado que dejo la anterior (un trade da 5v5 y 5v4 a cada uno). Se escribe en `metricas.md`.
- Los pares de un mismo jugador van en el orden del feed; como los vivos solo bajan, un jugador nunca repite estado en la misma ronda.

**Agregado** `aggregates.kill_state(**filters) -> dict`, debajo de `death_state` en `aggregates.py`, calcado de ella (docstring: se calcula al consultar como `death_state`, el algoritmo en `metrics` para que pasarlo a columna sea mecanico):
- `mias = base_queryset(**filters).filter(kills__gt=0)`; `filas = mias.values("round_id", "player_id", "round__my_team_won")`. `kills` ya excluye teamkills (ficha 67), asi que una ronda solo con teamkills tuyos no entra.
- Equipos y feeds con el mismo `Exists(mias.filter(round_id=OuterRef("round_id")))` que `death_state` (tope de parametros de SQLite), `kind__in=(Event.KILL, Event.DEATH, PLAYER_LEAVE)`, `order_by("round_id", "order")`. Total de consultas constante (3): test con `assertNumQueries`.
- Por fila, `pares = estado_al_matar(feed, equipos).get(player_id, [])`; cada par suma una baja al estado exacto `f"{a}v{r}"` y al grupo `ahead` (a > r), `even` o `behind`.
- Unidad de cada fila: `kills` (bajas) y `rounds`, `decided`, `won`, `winrate` sobre **rondas distintas** de esa fila. En un estado exacto coinciden (no se repite estado en una ronda); en un grupo, dos bajas tuyas con ventaja en la misma ronda son 2 `kills` y 1 ronda. Asi el winrate no pondera dos veces la misma ronda (statistical-analysis: el denominador es la ronda, que es lo que gana o pierde). Implementacion: un `set` de `round_id` por fila mientras se recorre, y `_sumar_caso` una vez por ronda nueva.
- `sin_feed`: bajas de `RoundPlayer.kills` que el feed no ubica (`kills` de la fila menos `len(pares)`, si es positivo), como la nota de `death_state`.
- Salida: `{"kills": n, "sin_feed": n, "states": [...], "groups": [...]}`, con `states` ordenado como `death_state` (`-allies`, `enemies`) y `groups` en `ESTADO_AL_MORIR_GRUPOS` (se reutiliza la constante). Cada fila de estado: `state`, `allies`, `enemies`, `group`, `kills`, `rounds`, `decided`, `won`, `winrate`.

**API.** `GET /api/duels/kill-state/` en `urls.py` (nombre `kill-state`, al lado de `death-state`) y `views.kill_state` en `views.py` (`_ok(agg.kill_state(**_filters(request)))`).

**Frontend.**
- `frontend/src/estadoAlMatar.js` (nuevo): `filasDeGrupos(data)` reutilizando `ETIQUETAS_GRUPO` importado de `estadoAlMorir.js`, `filasDeEstados`, `hayBajas(data)` (`data?.kills > 0`), `notaSinFeed(n)` con texto de bajas ("1 baja no se puede ubicar en el feed y no entra." / "N bajas no se pueden ubicar en el feed y no entran."), `avisoPocaMuestra(filas)` sobre `rounds` con `filasConPocaMuestra`.
- `frontend/src/components/EstadoAlMatar.jsx` (nuevo), calcado de `EstadoAlMorir.jsx`: panel "Estado al matar", tabla de grupos (Situación, Bajas, Rondas, Winrate de la ronda) y "Por estado exacto" (Estado, Bajas, Winrate de la ronda), `csvName` `estado-al-matar-grupos` y `estado-al-matar`, aviso de muestra ("alguna fila tiene menos de 30 rondas") y, sin bajas, "No hay bajas tuyas con evento en el feed con estos filtros.". Ayuda de Bajas: "Bajas a rivales; un teamkill no cuenta, pero resta su vivo."; ayuda de Rondas en grupos: "Una ronda con dos bajas en la misma situación cuenta una vez."
- `frontend/src/pages/Duelos.jsx`: import y `<EstadoAlMatar filters={filters} />` justo debajo de `<EstadoAlMorir />`.

**Tests** (testing-strategy: regla en `SimpleTestCase`, agregado y API en `TestCase`, textos en vitest, pagina en e2e).
- `backend/tests/test_estado_al_matar.py` (nuevo), con las fabricas de `test_estado_al_morir.py`:
  - `EstadoAlMatarPuroTests`: `test_tu_primera_baja_en_5v5_y_la_segunda_en_5v4`; `test_un_teamkill_no_es_baja_pero_resta_un_vivo` (mate0 mata a mate1 y despues vos a rival0 -> `[(4, 5)]`); `test_un_player_leave_resta_un_vivo` (rival0 se va, vos matas -> `[(5, 4)]`); `test_un_trade_ve_el_estado_que_dejo_la_baja_anterior`; `test_un_kill_de_quien_ya_no_esta_vivo_no_se_anota`; `test_sin_actor_no_es_baja_de_nadie`.
  - `EstadoAlMatarAgregadoTests`: `test_cuenta_bajas_por_estado_y_winrate`; `test_dos_bajas_con_ventaja_en_la_misma_ronda_son_una_ronda_del_grupo` (2 kills, 1 ronda); `test_una_ronda_sin_ganador_cuenta_bajas_y_no_winrate`; `test_solo_teamkills_no_entra`; `test_baja_sin_evento_va_a_sin_feed`; `test_el_filtro_de_lado_aplica_sobre_tu_fila`; `test_el_orden_de_estados_va_de_ventaja_a_desventaja`; `test_consultas_constantes` (`assertNumQueries(3)` con 1 y con 5 rondas); `test_la_api_responde_con_los_filtros` (`/api/duels/kill-state/?side=Attack`, 200).
- `frontend/src/estadoAlMatar.test.js` (nuevo): etiquetas y orden de grupos, `hayBajas` con `null`/0/n, `notaSinFeed` singular y plural, `avisoPocaMuestra` con 0, 29 y 30 rondas.
- `frontend/e2e/humo.spec.js`: en el bloque de Duelos, panel "Estado al matar" con los numeros de `/api/duels/kill-state/` (total de bajas de la fila Con ventaja y su winrate, celda exacta de un estado) y consola limpia. Si `seed_demo` no da bajas con ventaja, afirmar la fila que si tenga.

**Orden.** 1) regla y sus tests en rojo; 2) agregado y tests; 3) vista y url; 4) `estadoAlMatar.js` y vitest; 5) componente y Duelos; 6) e2e; 7) `metricas.md`.

**`docs/metricas.md`**: fila **Estado al matar** en la tabla de Duelos, debajo de Estado al morir: "Panel de Duelos (`/api/duels/kill-state/`). Por cada baja tuya a un rival, los vivos de tu equipo (contandote) y los rivales justo antes de ese `Kill`. Un `PlayerLeave` y un teamkill anteriores ya restaron su vivo; un teamkill tuyo no es baja. Sin agrupar por segundo: en un trade cada baja ve el estado que dejo la anterior. *Con ventaja*, *en paridad*, *en desventaja* como en Estado al morir. Bajas por fila; rondas y winrate sobre rondas distintas de la fila (dos bajas tuyas con ventaja en la misma ronda son una ronda del grupo), sobre las que tienen ganador. Bajas que el feed no ubica se informan aparte. Sin normalizar a 5v5. Todos los filtros globales aplican. Muestra minima 30 rondas por fila: no se oculta, se avisa." Y en `## Muestra minima`: "Estado al matar | 30 rondas por fila: no se oculta, se avisa".

**Que puede romperse.** El e2e de Duelos ya mide Estado al morir y Ventaja tirada: localizar el panel por su titulo exacto ("Estado al matar"), porque `hasText: 'Estado al m'` agarraria los dos. `ETIQUETAS_GRUPO` se importa, no se duplica. Sin migracion ni `recompute`.

**Verificacion manual.** `seed_demo`, Duelos: el panel aparece debajo de Estado al morir; la suma de Bajas por estado exacto + "no se pueden ubicar" = bajas totales del jugador con los mismos filtros (Resumen); filtro de lado Ataque cambia los numeros.

Umbral: el 30 es el corte comun de `muestra.js`; no hace falta calibrarlo aparte.

Skills: no aplica (sin tabla nueva ni migracion; espejo de un panel existente).
Skills del repo: statistical-analysis (winrate sobre rondas distintas, no por baja; muestra minima 30), testing-strategy (reparto Django, vitest, e2e), dataviz no aplica (tablas, sin grafico).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

(nada)
