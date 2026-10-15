# 50. Partidas cerradas y partidas holgadas

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B10 ([aurelix](https://aurelix.app), tarjeta "Close games")
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_margen.py, backend/tests/test_api.py, frontend/src/margen.js, frontend/src/margen.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261015T1711Z, arquitecto 20261015T1811Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Tendencias, tu winrate y rating en las partidas que se definieron por una
ronda o fueron a prorroga, contra las que se definieron por 3 o mas: si
cierras las parejas o solo ganas las que vas sobrado. Remontadas (ficha 45)
mira la trayectoria; esto mira el margen final.

## Criterios de aceptacion

- [ ] `/api/trends/` trae una clave nueva (p. ej. `by_margin`) con tramos
      fijos: `prorroga`, `1 ronda`, `2 rondas`, `3 o mas`; cada uno con
      partidas, partidas ganadas, winrate de partida y rating (test).
- [ ] El margen sale del marcador final (`Round.score_after` de la ultima
      ronda) con el mismo corte `code_version >= Y9S4` que `by_score_state`;
      las partidas anteriores o sin marcador no cuentan y la respuesta dice
      cuantas quedaron fuera (test con una partida Y9S3).
- [ ] Una partida con `overtime_number` en alguna ronda cae en `prorroga`
      aunque el margen final sea 2 (test).
- [ ] Los filtros de partida de siempre (mapa, `since`/`until`, ranked,
      sesion) recortan las partidas; `side` no parte una partida y se ignora.
      Base vacia devuelve 200 con los tramos en 0 (test).
- [ ] Panel en `Trends.jsx` con la tabla y la banda de ruido como las demas
      tablas de partida; e2e en `frontend/e2e/` que lo ve con `seed_demo`.
- [ ] Fila en `docs/metricas.md`.

## Fuera de alcance

- Margen por mapa o por lado.
- Exportarlo a CSV (H3 lo junta con las demas tablas nuevas).
- Umbrales configurables desde la UI.

## Diseno

(Arquitecto 20261015T1811Z, sobre main 2a6c86b)

**Fuente del margen.** `Match.my_score` / `Match.opponent_score` (`models.py:62-63`).
La ingesta los saca del `teams[i].score` del ultimo `.rec` (`ingest.py:146-149`), que es
el mismo dato que `Round.score_after` de la ultima ronda: se usa el de `Match` porque ya
esta resuelto a "tuyo/suyo" y no hay que repetir `_marcador_de_ronda`. Margen =
`abs(my_score - opponent_score)`. El corte `code_version >= Y9S4` se mantiene como pide
la ficha (variante conservadora: el mismo que `comebacks`).

**Archivos**

- `backend/replays/analytics/aggregates.py`: constante `TRAMOS_MARGEN = ("overtime",
  "1", "2", "3+")` y funcion `by_margin(**filters) -> dict`, ubicada justo despues de
  `comebacks()` (misma familia: lee partidas enteras). Pasos:
  1. `filtros = {k: v for k, v in filters.items() if k != "side"}`: el lado no parte una
     partida (criterio 4). El resto (mapa, operador, sitio, fechas, ranked, sesion) elige
     partidas como en `by_start_side`: `ids = base_queryset(**filtros).values_list(
     "round__match_id", flat=True).distinct()`.
  2. `partidas = Match.objects.filter(id__in=ids)`; `conocidas = partidas.filter(
     code_version__gte=Y9S4).exclude(won__isnull=True)`; `fuera = partidas.count() -
     conocidas.count()` (pre-Y9S4, empates y sin resultado).
  3. `con_prorroga = set(Round.objects.filter(match_id__in=conocidas.values("id"),
     overtime_number__gt=0).values_list("match_id", flat=True))`.
  4. En Python, por cada partida de `conocidas.values("id", "my_score",
     "opponent_score", "won")`: tramo `overtime` si su id esta en `con_prorroga`; si no,
     margen 1 -> `"1"`, 2 -> `"2"`, >=3 -> `"3+"`; margen 0 con `won` no nulo no puede
     pasar (won es nulo en empate) pero si pasa, va a `fuera`.
  5. Rating y KPR del tramo: `totals(RoundPlayer.objects.filter(is_me=True,
     round__match_id__in=ids_del_tramo), baseline)` con `baseline = rating_baseline()`
     calculado una sola vez (como `_filas_por_tramo`). Son todas tus rondas de esas
     partidas, sin recortar por operador/sitio: la partida se lee entera.
  6. Devuelve `{"rows": [{"margin": t, "matches": n, "wins": g, "winrate": _pct(g, n),
     "rounds": ..., "rating": ..., "kpr": ...} for t in TRAMOS_MARGEN], "matches_known":
     conocidas.count(), "matches_excluded": fuera}`. Tramo vacio = 0 partidas,
     `winrate`/`rating` `None` (lo que ya devuelve `totals` sin filas).
- `backend/replays/views.py` (`trends`, linea ~233): `"by_margin": agg.by_margin(**filters)`.
- `backend/tests/test_margen.py` (nuevo; mismo estilo que `test_remontadas.py`, con
  `factories.make_match/make_round/make_round_player`). Tests:
  - `test_los_tramos_salen_en_orden_fijo_con_partidas_y_winrate`
  - `test_una_partida_con_prorroga_cae_en_prorroga_aunque_gane_por_dos`
  - `test_una_partida_anterior_a_y9s4_queda_fuera_y_se_cuenta`
  - `test_el_filtro_de_lado_no_parte_la_partida` (misma respuesta con y sin `side=Attack`)
  - `test_el_filtro_de_mapa_recorta_partidas`
  - `test_base_vacia_devuelve_los_cuatro_tramos_en_cero`
  - en `test_api.py`: `test_trends_trae_by_margin` (200 y las 4 filas).
- `frontend/src/margen.js` + `frontend/src/margen.test.js` (nuevos, como
  `remontadas.js`): `filasDeMargen(byMargin)` -> filas con `orden` y `tramo` legible
  (`overtime` -> "Prórroga", `1` -> "1 ronda", `2` -> "2 rondas", `3+` -> "3 o más") y
  `hayMargen(byMargin)` (`matches_known > 0`). Tests: etiquetas y orden; respuesta
  ausente (`undefined`) devuelve `[]` sin romper.
- `frontend/src/pages/Trends.jsx`: panel "Partidas cerradas y holgadas" justo despues
  del panel "Remontadas y derrumbes". `DataTable` con columnas Margen, Partidas,
  Ganadas, Winrate (%), Rating, KPR, `initialSort` por `orden`, `csvName="por-margen"`.
  Hint: si `filasConPocaMuestra(filas.map((f) => ({ rounds: f.matches })), 10).length` (el helper mira `rounds`; aca la muestra son partidas, umbral 10) "Ojo: algún tramo tiene menos de 10 partidas; la diferencia puede ser varianza."; si no, "Margen final de
  la partida. Solo desde Y9S4." Si `matches_excluded > 0`, nota debajo: "N partidas sin
  marcador confiable quedaron fuera." Sin `matches_known`, nota igual que remontadas.
- `frontend/e2e/humo.spec.js`: `test('Tendencias muestra partidas cerradas y holgadas')`.
  `seed_demo` gana sus 29 partidas 4-3 sin prorroga, todas Y9S4: 4 filas, la de
  "1 ronda" con 29 partidas y 100 %, consola limpia.
- `docs/metricas.md`: fila **Margen final** en `## Remontadas y derrumbes` (mismo modo
  de leer partidas): definicion de tramo, prorroga primero, corte Y9S4, filtro de lado
  ignorado, rating sobre todas tus rondas de la partida.

**Orden:** aggregates + test_margen -> vista + test_api -> margen.js + test -> Trends.jsx
-> e2e -> metricas.md -> `check.sh`.

**Que puede romperse:** nada de datos (sin migracion ni recompute). `seed_demo` no se
toca. El e2e de remontadas cuenta `tbody tr` dentro de su propio panel; el panel nuevo es
otra `section.panel`, no lo afecta. Chunk de Trends crece poco (una tabla).

**Verificacion manual:** `curl -s localhost:8000/api/trends/ | python -m json.tool | grep
-A30 by_margin` sobre `seed_demo`; con `?side=Attack` tiene que dar lo mismo.

**Archivos ocupados:** ninguna rama de trabajo abierta; no pisa PR #14 (no toca
`Trends.jsx`).

## Implementacion
