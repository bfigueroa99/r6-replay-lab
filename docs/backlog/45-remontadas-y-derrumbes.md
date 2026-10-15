# 45. Remontadas y derrumbes

estado: implementado
candado: -
rama: claude/equipo-dev/45-remontadas-y-derrumbes
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B7 (idea del PO); cierra la epica lado-y-marcador despues de las fichas 36, 41 y 43
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_remontadas.py, frontend/src/remontadas.js, frontend/src/remontadas.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T1911Z, arquitecto 20261014T2311Z, dev 20261015T0011Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Tendencias aparece un panel que lista las partidas que ganaste yendo
abajo por 2 o mas rondas (remontadas) y las que perdiste yendo arriba por 2
o mas (derrumbes), cada una con enlace a su detalle. Debajo, tu winrate de
partida segun la diferencia de rondas que llevabas al cambio de lado: si
sueltas las partidas que tienes ganadas o si das vuelta las perdidas.

## Criterios de aceptacion

- [ ] `/api/trends/` devuelve una clave nueva (p. ej. `comebacks`) con dos
      listas, `remontadas` y `derrumbes`, cada item con `match_id`, mapa,
      fecha, marcador final y la maxima desventaja (o ventaja) en rondas
      que hubo antes de la ultima ronda. Una partida ganada que estuvo 1-3
      entra en `remontadas` con desventaja 2; una ganada que nunca estuvo
      abajo por 2 no entra.
- [ ] Una partida perdida que estuvo 3-1 a favor entra en `derrumbes`; una
      perdida que nunca estuvo arriba por 2 no entra.
- [ ] Solo cuentan partidas con marcador conocido: mismo corte que
      `by_score_state` (`code_version >= Y9S4`, marcador de dos equipos,
      `_marcador_conocido` en `aggregates.py`). Una partida anterior a Y9S4
      no aparece en ninguna lista ni en la tabla de diferencia. Test con
      una partida de cada lado del corte.
- [ ] Tabla de winrate de partida por diferencia de rondas al cambio de
      lado (primera ronda de la segunda mitad, la misma frontera que usa
      `by_half`): tramos `+2 o mas`, `+1`, `0`, `-1`, `-2 o menos`, con
      partidas y winrate por tramo. Respeta los filtros de la barra (mapa,
      fechas, sesion) como el resto de `/api/trends/`.
- [ ] Tendencias muestra el panel "Remontadas y derrumbes" con las dos
      listas (enlace al detalle de cada partida) y la tabla; con base vacia
      o sin partidas con marcador conocido muestra un texto de vacio, no un
      error. El e2e (`frontend/e2e/`) lo afirma sobre `seed_demo`.
- [ ] Fila en `docs/metricas.md` para la desventaja maxima y el winrate por
      diferencia al cambio de lado.

## Fuera de alcance

- Grafico del marcador ronda a ronda de cada partida (eso es F4, tira de
  rondas en el listado de Partidas).
- Umbral configurable desde la UI: el 2 queda fijo en el diseno.
- Probabilidad de ganar segun el marcador (modelo estadistico): solo
  conteos.

## Diseno

Arquitecto 20261014T2311Z, sobre `origin/main@f74a16f`. Pasa los filtros
duros: usa solo `Round.score_before`, `Round.my_side`, `Round.number`,
`Round.overtime_number`, `RoundPlayer.team_index` y `Match.won`, todo ya
importado; sin red, sin dependencias, sin migracion, sin recompute.

**Backend: `backend/replays/analytics/aggregates.py`**, funcion nueva
`comebacks(**filters) -> dict`, debajo de `by_match_point` (vive con los
otros cortes por marcador y reusa su corte de version).

1. Partidas: `ids = base_queryset(**filters).values_list("round__match_id",
   flat=True).distinct()`, igual que `by_start_side` (los filtros eligen
   partidas; la partida se lee entera, no solo las rondas filtradas).
2. Una sola query de tus filas de esas partidas, sin filtros de ronda:
   `RoundPlayer.objects.filter(is_me=True, round__match_id__in=ids)
   .values("round__match_id", "round__number", "round__overtime_number",
   "round__my_side", "round__score_before", "team_index")
   .order_by("round__match_id", "round__number")`. El `IN` es sobre una
   subquery (no se evalua `ids` a lista), asi no pega el tope de
   parametros de SQLite.
3. Marcador legible por ronda, con la misma regla que `_marcador_conocido`
   pero en Python (helper `_marcador_de_ronda(score_before, team_index) ->
   tuple[int, int] | None`): lista de exactamente 2 enteros, `team_index`
   en {0, 1}; si no, `None`. La partida entra solo si
   `Match.code_version >= Y9S4` y **todas** sus rondas tienen marcador
   legible (una ronda ilegible en el medio puede esconder el pozo). Las
   partidas con `won` nulo (empate o incompleta) no entran a nada.
4. Por partida: `desventaja = max(suyo - mio)` y `ventaja = max(mio - suyo)`
   sobre el `score_before` de todas sus rondas (incluida la ultima: su
   `score_before` es el marcador "antes de la ultima ronda"; el final no
   cuenta). Umbral fijo `UMBRAL_REMONTADA = 2` (constante de modulo, con
   comentario del por que: 1 ronda es una ronda cualquiera).
   - `remontadas`: `won is True` y `desventaja >= 2`; item `{"match_id",
     "map", "played_at" (iso), "score": "mi-su" final (`my_score`,
     `opponent_score`), "max_deficit": desventaja}`.
   - `derrumbes`: `won is False` y `ventaja >= 2`; mismo item con
     `"max_lead"`.
   - Orden: mayor desventaja/ventaja primero, despues la mas reciente.
     Tope 20 por lista (constante `TOPE_LISTA`, sin parametro nuevo);
     ademas `"total"` con el conteo sin tope.
5. Diferencia al cambio de lado: la primera ronda (menor `number`) con
   `overtime_number == 0` y `my_side` no vacio y distinto del lado de la
   menor ronda sin prorroga (misma frontera que `_lado_inicial` /
   `by_half`, pero en Python sobre las filas del paso 2). Su `mio - suyo`
   se pone en un tramo de `TRAMOS_CAMBIO = ("+2", "+1", "0", "-1", "-2")`
   (`>= 2` y `<= -2` se juntan). Partida sin ronda de segunda mitad (le
   falta el `.rec` o se corto) no entra a la tabla. Fila por tramo:
   `{"diff": tramo, "matches": n, "wins": g, "winrate": _pct(g, n)}`;
   las cinco filas siempre, aunque esten en 0.
6. Salida: `{"remontadas": [...], "derrumbes": [...],
   "remontadas_total": n, "derrumbes_total": n, "by_side_change_diff":
   [...], "matches_known": n}` (`matches_known` = partidas que pasaron el
   corte del paso 3, para el texto de vacio).

**`backend/replays/views.py`**: `"comebacks": agg.comebacks(**filters)` en
`trends`. Nada mas.

**Frontend.** `frontend/src/remontadas.js` (logica pura, como
`cierres.js`): `etiquetaTramo(diff)` ("+2 o más", "+1", "Empatado", "-1",
"-2 o menos") y `filasDeCambio(filas)` que oculta nada y formatea
winrate nulo como `—`; `frontend/src/remontadas.test.js` con vitest.
`frontend/src/pages/Trends.jsx`: un `Panel` "Remontadas y derrumbes"
despues del de match point, con dos `DataTable` chicas (mapa con
`<Link to={/partidas/${match_id}}>`, fecha, marcador final, "Ibas -N" /
"Ibas +N") y la tabla por diferencia al cambio de lado. Si
`matches_known === 0`: texto "Sin partidas con marcador conocido (hace
falta Y9S4 o posterior)." Si las listas estan vacias pero hay partidas:
"Ninguna remontada de 2 o más rondas todavía." / igual para derrumbes. Hint
del panel: que el corte es 2 rondas y que solo cuentan partidas desde Y9S4.

**Tests nuevos** en `backend/tests/test_remontadas.py` (con
`factories.make_match/make_round/make_round_player`, `code_version=Y9S4`):
- `test_ganada_que_estuvo_1_3_es_remontada_con_desventaja_2`
- `test_ganada_que_nunca_estuvo_abajo_por_2_no_entra`
- `test_perdida_que_estuvo_3_1_es_derrumbe`
- `test_perdida_que_nunca_estuvo_arriba_por_2_no_entra`
- `test_el_marcador_final_no_cuenta_como_desventaja` (la ultima ronda la
  perdiste 4-2 desde 3-2: ventaja maxima 1, no derrumbe)
- `test_partida_anterior_a_y9s4_no_aparece_en_nada`
- `test_partida_con_marcador_de_tres_equipos_no_aparece`
- `test_team_index_1_lee_el_marcador_al_reves`
- `test_partida_sin_resultado_no_entra`
- `test_diferencia_al_cambio_de_lado_por_tramo` (una partida por tramo,
  incluido `+3` en `+2` y `-4` en `-2`)
- `test_partida_sin_segunda_mitad_no_entra_a_la_tabla`
- `test_respeta_el_filtro_de_mapa`
- `test_trends_trae_comebacks_con_base_vacia` (200, listas vacias, cinco
  filas en 0) y `test_trends_con_filtros_raros_da_200` (`until=foo`,
  `session=-1`).

**e2e** (`frontend/e2e/humo.spec.js`): `test('Tendencias muestra
remontadas y derrumbes', ...)` que afirma el titulo del panel y las cinco
filas de la tabla. Ojo: en `seed_demo` el marcador alterna
(`score_before=[(n+1)//2, n//2]`), asi que nunca hay 2 de diferencia: las
listas quedan vacias y el e2e afirma el texto de vacio "Ninguna remontada"
y los numeros de la tabla que salgan de correr `curl
/api/trends/ | jq .comebacks` sobre `seed_demo`. **No tocar
`seed_demo`** (mueve los numeros de todos los e2e).

**`docs/metricas.md`**: seccion nueva `## Remontadas y derrumbes` despues
de `## Contexto de la ronda`, con filas **Remontada** (ganada yendo 2 o mas
abajo en el marcador antes de alguna ronda), **Derrumbe** (al reves),
**Desventaja / ventaja maxima** (el peor / mejor `mio - suyo` antes de
cada ronda, sin contar el final) y **Winrate segun la diferencia al cambio
de lado** (marcador antes de la primera ronda de la segunda mitad; misma
frontera que "Mitades y prorroga"; solo desde Y9S4).

**Orden:** helper + tests de backend -> `comebacks` -> vista -> logica
pura + vitest -> panel -> e2e -> metricas.md -> `check.sh`.

**Que puede romperse:** nada persistente (sin migracion). Riesgo: que
`seed_demo` numere rondas desde 0 (lo hace): no suponer `number == 1`.
Performance: una query por request; con 1000 partidas son ~10.000 filas
en Python, comparable con `sessions`.

**Verificacion manual:** `seed_demo`, `runserver`, abrir Tendencias y ver
el panel con el texto de vacio; con la base real, abrir una remontada y
confirmar en el detalle que el marcador estuvo 2 abajo.

Nota para tests: `make_match` no recibe `won`; la partida sin resultado se
arma con `Match.objects.filter(pk=m.pk).update(won=None)`.

## Implementacion

Dev 20261015T0011Z. Todo el diseno, sin desvios de alcance:

- `aggregates.comebacks()` debajo de `by_match_point`, con `_marcador_de_ronda`,
  `_tramo_cambio`, `UMBRAL_REMONTADA = 2`, `TOPE_LISTA = 20` y
  `TRAMOS_CAMBIO`. Las partidas Y9S4 se filtran ya en la query (`code_version`);
  las rondas tuyas se leen enteras para las partidas que eligen los filtros.
- `/api/trends/` trae `comebacks`.
- `frontend/src/remontadas.js` (+ vitest, 6 tests) y panel "Remontadas y
  derrumbes" en Tendencias despues de Match point: dos tablas chicas con
  enlace a `/partidas/<id>`, nota "Se muestran N de M" si pasa el tope, y la
  tabla "Por diferencia al cambio de lado" con las cinco filas.
- e2e `Tendencias muestra remontadas y derrumbes`: sobre `seed_demo` (29
  partidas Y9S4, todas ganadas, marcador alternado) las listas quedan vacias
  y el tramo `+1` tiene 29 partidas, 29 ganadas, 100 %.
- `docs/metricas.md`: seccion `## Remontadas y derrumbes` despues de
  `## Contexto de la ronda`.
- `backend/tests/test_remontadas.py`: 24 tests (los del diseno mas orden,
  tope, filtro de lado, ronda ilegible y ronda faltante).

Desvios del diseno:

- **Ronda faltante saca la partida** (hallazgo de la revision ciega): si los
  `number` de tus rondas no son consecutivos (falta un `.rec`), la partida no
  entra a nada. Sin eso, faltar la ronda del pozo bajaba la desventaja, y
  faltar la primera de la segunda mitad mandaba la partida al tramo de la
  ronda siguiente. Test `test_una_ronda_que_falta_saca_la_partida`.
- `test_el_marcador_final_no_cuenta_como_desventaja` del diseno no podia
  fallar (el final siempre juega en contra del resultado); quedo
  `test_el_marcador_antes_de_la_ultima_ronda_cuenta`, que si cae si se
  excluye la ultima ronda.
- Subtitulo de la tabla: "Por diferencia al cambio de lado" y no "Segun el
  marcador...": el e2e existente busca el panel por el texto "Según el
  marcador" y con dos paneles violaba el modo estricto.
- `test_trends_con_filtros_raros_da_200` prueba tambien `days=-1` y `map=`.

Revision ciega (subagente con `revision.md`): 1 bug (ronda faltante), 1 test
que no podia fallar, 1 ejemplo imposible en metricas.md; los tres corregidos.

Verificacion: `./scripts/check.sh` -> `Todo en verde.` (ruff ok, 584 tests
backend, 86 frontend, build ok, 33 e2e).

Verificacion manual sugerida en el PC: con la base real, abrir una remontada
del panel y confirmar en el detalle que el marcador estuvo 2 abajo.

## Revision

## QA

## Para el humano
