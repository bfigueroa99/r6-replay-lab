# 50. Partidas cerradas y partidas holgadas

estado: revisado
candado: qa 2026-10-16T12:05Z
rama: claude/equipo-dev/50-partidas-cerradas-y-holgadas
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B10 ([aurelix](https://aurelix.app), tarjeta "Close games")
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_margen.py, backend/tests/test_api.py, frontend/src/margen.js, frontend/src/margen.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261015T1711Z, arquitecto 20261015T1811Z, dev 20261015T2004Z, revisor 20261016T0004Z, dev 20261016T0404Z, revisor 20261016T0805Z

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

(Dev 20261015T2004Z)

Quedo todo el diseno, sin desvios de alcance:

- `aggregates.by_margin()` + `TRAMOS_MARGEN` + `_tramo_margen()` justo antes de
  `round_endings`. `matches_excluded` = partidas elegidas por los filtros menos
  las que cayeron en un tramo (pre-Y9S4, sin resultado y, por si acaso, margen 0
  con resultado). `rounds` de cada fila sale de `totals()` (0 si no hay).
- `/api/trends/` trae `by_margin`.
- `frontend/src/margen.js`: `filasDeMargen`, `hayMargen`, `etiquetaMargen` y
  `MUESTRA_PARTIDAS = 10` (el umbral del aviso, exportado en vez de numero suelto
  en la pagina).
- Panel "Partidas cerradas y holgadas" en `Trends.jsx` despues de Remontadas.
- Fila **Margen final** en `docs/metricas.md`, seccion Remontadas y derrumbes,
  aclarando que su corte es mas laxo (no exige todas las rondas).

Tests: `tests/test_margen.py` (9: tramos y orden, prorroga gana al margen, Y9S3
fuera, empate fuera, sin resultado fuera, `side` ignorado, filtro de mapa, el
rating mira todas tus rondas aunque se filtre operador, base vacia),
`test_api.test_trends_trae_by_margin`, `src/margen.test.js` (4) y el e2e
`Tendencias muestra partidas cerradas y holgadas`.

Criterios -> tests: 1 `test_los_tramos_salen_en_orden_fijo_con_partidas_y_winrate`
+ `test_trends_trae_by_margin`; 2 `test_una_partida_anterior_a_y9s4_queda_fuera_y_se_cuenta`;
3 `test_una_partida_con_prorroga_cae_en_prorroga_aunque_gane_por_dos`;
4 `test_el_filtro_de_lado_no_parte_la_partida`, `test_el_filtro_de_mapa_recorta_partidas`,
`test_base_vacia_devuelve_los_cuatro_tramos_en_cero`; 5 e2e; 6 fila en metricas.md.

Revision ciega previa (subagente con `revision.md`): aprobar con 3 menores,
corregidos: la nota de excluidas culpaba solo al marcador (tambien cuenta
empates y sin resultado); test nuevo que pasa de verdad por el
`exclude(won__isnull=True)`; comentario del e2e que aclara que el 4-3 de
`seed_demo` es sintetico.

Para el Revisor: en ranked real un 3-3 va a prorroga; si un `.rec` no trae
`overtimeRoundNumber`, un 5-4 caeria en "1 ronda" y no en "Prorroga". Es la
misma fuente que usa Mitades y prorroga; no se infiere de `reglas_partida` para
no tener dos definiciones de prorroga.


## Revision 2026-10-16 sobre a98a1b1

(Revisor 20261016T0004Z. Subagente ciego con `revision.md` y lectura propia;
cada hallazgo reproducido por el lider. Rama con `origin/main` 2a6c86b ya
fusionado; `check.sh`: `Todo en verde.`, 643 tests backend, 90 vitest, build
ok, 38 e2e.)

- [test] backend/tests/test_margen.py:90 (`test_el_filtro_de_lado_no_parte_la_partida`)
  Que pasa: el test pasa aunque `by_margin` no descarte `side`.
  Como reproducirlo o por que es cierto: mutacion
  `filtros = {k: v ... if k != "side"}` -> `filtros = dict(filters)` en
  `aggregates.py:737` y `manage.py test tests.test_margen` sigue en `OK`:
  las dos partidas de `_partida` tienen una ronda tuya de ataque, asi que
  `side="Attack"` elige las mismas partidas con o sin el filtro, y `totals`
  ya lee todas las rondas por su cuenta.
  Arreglo sugerido: agregar una partida con solo rondas tuyas de defensa (p. ej.
  `make_match` + dos `make_round(..., side="Defense")`, marcador 4-1) y
  afirmar que con `side="Attack"` sigue en el tramo `3+` y en
  `matches_known`. Con la mutacion de arriba el test nuevo tiene que caer.

Aviso, no bloquea esta ficha (viene de antes): `ingest.py:146-169` saca
`my_score`/`opponent_score` y `won` del ultimo `.rec` importado. Si falta
el de la ronda final (ranked 4-2 importada hasta 3-2), la partida cuenta como
ganada "por 1 ronda". Es el mismo dato que ya muestran Partidas y el winrate
de toda la app, asi que no se corrige aca; queda como candidato a ficha
`tipo: bug` (marcar `won=None` cuando el marcador final no cierra la
partida segun `reglas_partida`), ver `## Para el humano` de ESTADO.md.

Ficha contra el diff: los 6 criterios tienen test o e2e con nombre (el 4 con
el hueco de arriba); el diff toca solo `archivos:`; fila en
`docs/metricas.md`; UI con tildes, identificadores sin; sin `print` ni
`console.log`; sin migracion ni dependencias.

Veredicto: corregir antes de entregar (el hallazgo [test]: el criterio 4 no
queda probado; el arreglo es un test).

## Correccion de hallazgos

(Dev 20261016T0404Z, sobre 2d8e5f5)

- [test] criterio 4: nuevo `test_una_partida_solo_de_defensa_sigue_contando_con_filtro_de_ataque`
  en `test_margen.py`, una partida 4-1 con solo rondas tuyas de defensa;
  con `side=Attack` sigue en `3+` y en `matches_known`. Mutacion del revisor
  (`filtros = dict(filters)` en `aggregates.py`) -> el test cae (`FAILED
  (failures=1)`); sin la mutacion, `OK`.
- El aviso de `ingest.py` (marcador del ultimo `.rec`) no se toca aca, como
  dice la revision.

`check.sh`: `Todo en verde.` (644 tests backend, 90 vitest, build ok, 38 e2e).

## Revision 2026-10-16 sobre 69eac5c

(Revisor 20261016T0805Z, segunda pasada. Subagente ciego con `revision.md` y
lectura propia. Rama al dia con `origin/main` 2a6c86b, sin merge nuevo;
`check.sh`: `Todo en verde.`, 644 tests backend, 90 vitest, build ok, 38 e2e.)

Sin hallazgos. El subagente ciego reviso `by_margin` (prorroga antes que
margen, empates y sin resultado en `matches_excluded`, `side` ignorado,
rating sobre todas tus rondas, base vacia), los tests (cada uno cae con el bug
que nombra, incluido el nuevo de la partida solo de defensa) y el e2e (29
partidas 4-3 de `seed_demo`, Y9S4, sin prorroga).

Hallazgo de la revision anterior: corregido en 269f464 y verificado (el test
nuevo cubre el criterio 4).

Ficha contra el diff: los 6 criterios con test o e2e con nombre; el diff toca
solo `archivos:`; fila en `docs/metricas.md`; UI con tildes,
identificadores sin; sin `print` ni `console.log`; sin migracion ni
dependencias.

Sigue en pie el aviso de la revision anterior sobre `ingest.py` (marcador
del ultimo `.rec`): no bloquea esta ficha.

Veredicto: aprobar.
