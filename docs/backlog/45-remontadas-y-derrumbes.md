# 45. Remontadas y derrumbes

estado: aprobado
candado: release 2026-10-15T05:12Z
rama: claude/equipo-dev/45-remontadas-y-derrumbes
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B7 (idea del PO); cierra la epica lado-y-marcador despues de las fichas 36, 41 y 43
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_remontadas.py, frontend/src/remontadas.js, frontend/src/remontadas.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T1911Z, arquitecto 20261014T2311Z, dev 20261015T0011Z, revisor 20261015T0110Z, dev 20261015T0211Z, revisor 20261015T0310Z, qa 20261015T0411Z

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

### Correccion de la revision (dev 20261015T0211Z)

- Hallazgo del revisor (faltan las primeras rondas): corregido. `comebacks()`
  exige ademas que la primera ronda presente arranque `0-0`; test nuevo
  `test_si_faltan_las_primeras_rondas_la_partida_no_entra` con las rondas 3, 4
  y 5 del repro (`matches_known == 0`, tabla en 0). Mutacion: sin la condicion
  el test cae. `docs/metricas.md` lo dice.
- La revision ciega de este turno marco el caso simetrico (faltan las ultimas
  rondas). No se agrega control: el resultado de la partida (`my_score`,
  `opponent_score`, `won`) sale del `teamscore` del ultimo `.rec` importado
  (`ingest.py:146`), asi que con rondas finales faltantes el resultado ya esta
  truncado para toda la app y un control "marcador antes de la ultima + 1 ==
  final" nunca saltaria con datos reales. Queda anotado en `docs/metricas.md`.
- `seed_demo` arranca cada partida en 0-0: los numeros del e2e no cambian.

Verificacion: `./scripts/check.sh` -> `Todo en verde.` (ruff ok, 585 tests
backend, 86 frontend, build ok, 33 e2e).

## Revision 2026-10-15 sobre 6739aac

Revisor 20261015T0110Z. Revision ciega (subagente con `revision.md`, sin leer la
ficha) y despues confirmacion local. `./scripts/check.sh` -> `Todo en verde.`
sobre la rama (main ya incluido). Reglas: sin dependencias, sin escrituras
nuevas, sin tocar `pydissect/` ni `electron/`, filas en `docs/metricas.md`,
UI con tildes, identificadores sin tildes, sin `print`/`console.log`. El e2e
coincide con `comebacks()` sobre `seed_demo` (29 en `+1`, 100 %, listas
vacias). Criterios de aceptacion: todos cubiertos por tests salvo el que cae
con el hallazgo.

Hallazgos:

- [bug] backend/replays/analytics/aggregates.py:667
  Que pasa: el control de "partida completa" solo ve huecos en el medio; si
  faltan las **primeras** rondas (entraste o reconectaste tarde, o no estan
  sus `.rec`), la partida cuenta como conocida, puede perder la remontada y
  cae en un tramo equivocado de la tabla del cambio de lado.
  Como reproducirlo (confirmado): partida Y9S4 ganada con solo las rondas 3
  (`[1, 2]`, Attack), 4 (`[2, 2]`, Defense) y 5 (`[3, 2]`, Defense) ->
  `matches_known == 1`, `remontadas_total == 0` (el 0-2 que hubo no se ve)
  y la partida suma al tramo `0` aunque el cambio de lado real no se vio.
  Contradice `docs/metricas.md` ("con todas sus rondas importadas").
  Arreglo sugerido: exigir ademas que el marcador de la primera ronda
  presente sea `(0, 0)` (sirve con numeracion desde 0 o desde 1) y agregar
  `test_si_faltan_las_primeras_rondas_la_partida_no_entra` con las rondas
  de arriba: `matches_known == 0` y las cinco filas de la tabla en 0.

Veredicto: corregir (por el unico hallazgo, que es un bug de numeros; el
arreglo es una condicion y un test).

## Revision 2026-10-15 sobre 822da4f (segunda pasada)

Revisor 20261015T0310Z. Revision ciega (subagente con `revision.md`, sin leer la ficha)
y confirmacion local. `./scripts/check.sh` -> `Todo en verde.` sobre la rama
(main ya incluido): ruff ok, 585 tests backend, 86 frontend, build ok, 33 e2e.

- Hallazgo anterior (faltan las primeras rondas): corregido en 822da4f.
  `test_si_faltan_las_primeras_rondas_la_partida_no_entra` cubre el repro;
  mutacion confirmada (sin `marcadores[0] != (0, 0)` el test cae, 1 de 24).
- Criterios de aceptacion: los seis cubiertos (24 tests en
  `test_remontadas.py`, 6 vitest, e2e `Tendencias muestra remontadas y
  derrumbes`, filas en `docs/metricas.md`). El subagente reprodujo los numeros
  del e2e sobre `seed_demo` (29 partidas, listas vacias, `+1` 29/29 100 %).
- Reglas: sin dependencias, endpoint de lectura, sin `pydissect/` ni
  `electron/`, UI con tildes, identificadores sin tildes, sin `print` ni
  `console.log`. El diff no sale de `archivos:`.

Hallazgos:

- [estilo, menor] frontend/src/pages/Trends.jsx:546
  Que pasa: con `matches_known === 0` el panel dice "hace falta Y9S4 o
  posterior", pero tambien quedan afuera partidas Y9S4 con rondas faltantes,
  sin 0-0 inicial, marcador ilegible o `won` nulo.
  Como reproducirlo: una sola partida Y9S4 sin el `.rec` de la ronda 2 ->
  `matches_known: 0` y la UI pide Y9S4, que el usuario ya tiene.
  Arreglo sugerido: "Sin partidas con marcador conocido (hace falta Y9S4 o
  posterior, con todas sus rondas importadas)." No bloquea: el texto no da un
  numero equivocado.

Veredicto: aprobar (el unico hallazgo es un texto de vacio en un caso borde).

## QA 2026-10-15 sobre d98db16

QA 20261015T0411Z. Rama con `origin/main@f74a16f` ya incluido (merge-tree limpio).

- **check.sh**: `./scripts/check.sh` -> `Todo en verde.` (ruff ok, 585 tests
  backend, 86 vitest, build ok, 33 e2e).
- **Base vacia** (`SQLITE_PATH=<scratch>/empty.sqlite3 python manage.py migrate`,
  `runserver 8046`): `curl localhost:8046/api/trends/` -> 200, listas vacias,
  `matches_known: 0`, cinco filas `+2 +1 0 -1 -2` en 0 con `winrate: null`.
  `?until=foo`, `?page=-1`, `?map=` -> 200.
- **Base sembrada** con `factories.py` (script abajo; 31 partidas): 1 remontada
  0-3 -> 4-3 (Oregon), 1 derrumbe 3-0 -> 3-4 numerado desde 1 con
  `team_index=1` (Bank), 1 pre-Y9S4, 1 sin la ronda 2, 1 con `won` nulo, 1 con
  marcador de tres equipos, 25 remontadas 0-2 -> 4-2 (Kafe); una ronda sin
  bajas por partida. `curl localhost:8045/api/trends/ | jq .comebacks` ->
  `matches_known 27` (las cuatro trampa afuera), `remontadas_total 26` con 20
  en la lista (Oregon primero, `max_deficit 3`; despues la mas reciente),
  `derrumbes_total 1` (`max_lead 3`, el `team_index=1` leido al reves bien),
  tabla `+2: 1/0 0 %`, `-1: 25/25 100 %`, `-2: 1/1 100 %` (el -3 de Oregon
  junto en -2). Todo lo esperado a mano.
- **Filtros** (200 en todos): `until=foo`, `since=bar`, `page=-1`, `map=`,
  `side=` se ignoran (27); `map=oregon` -> 1 remontada, `map=bank` -> 1
  derrumbe, `map=NoExiste` -> 0; `side=Defense` -> 27 (la partida se lee
  entera, como dice el diseno); `since=2026-09-03` -> 4; `until=2026-09-01`
  -> 2; `days=-1` y `session=-1` -> 0, igual que `by_half` con los mismos
  parametros.
- **UI** (Chromium sobre la base sembrada, `/tendencias`): panel con 20 filas
  de remontadas, "Se muestran 20 de 26.", derrumbe "Ibas +3", tabla con
  "+2 o más / +1 / Empatado / -1 / -2 o menos" y `—` en los tramos vacios; 21
  enlaces `/partidas/<id>`, el primero abre el detalle de Oregon 4-3; consola
  sin errores. El estado vacio lo afirma el e2e sobre `seed_demo`.
- **Bundle**: `vite build` en la rama y en `origin/main`: chunk inicial
  `index-*.js` 186.80 kB en los dos (0 %); `Trends-*.js` (lazy) 17.16 ->
  19.41 kB.
- **Mutaciones** (`python manage.py test tests.test_remontadas` con el codigo
  roto a proposito, restaurado despues): `UMBRAL_REMONTADA = 3` -> 7 fallos y
  4 errores; `team_index 1` sin invertir -> cae; `_tramo_cambio` sin juntar
  `>= 2` -> cae; sin el filtro de `won` nulo -> cae. Vitest: signo fijo `-`
  en `filasDePartidas` -> 1 de 6 cae. Las cinco detectadas.
- Sin migracion, sin `recompute`, sin parser, sin Electron ni `.ps1`: no hace
  falta `## Verificar en el PC`.

Criterios de aceptacion: los seis se cumplen. El hallazgo menor del revisor
(texto de vacio que solo nombra Y9S4) sigue abierto y no bloquea.

Veredicto: aprobado.

Script de siembra (`SQLITE_PATH=/ruta/seed.sqlite3 python manage.py migrate`
y despues `SQLITE_PATH=/ruta/seed.sqlite3 python manage.py shell < sembrar.py`
desde `backend/`):

```python
# Uso: SQLITE_PATH=... python manage.py shell < sembrar.py
from tests.factories import make_match, make_round, make_round_player
from replays.models import Match
from pydissect.constants import Y9S4

def partida(idx, marcadores, lados, mio, suyo, *, mapa="Club House", ti=0, cv=Y9S4, start=0):
    m = make_match(index=idx, my_score=mio, opponent_score=suyo, map_name=mapa, code_version=cv)
    prev = None
    for i, (sc, lado) in enumerate(zip(marcadores, lados)):
        sb = list(sc) if ti == 0 else [sc[1], sc[0]]
        nxt = marcadores[i + 1] if i + 1 < len(marcadores) else (mio, suyo)
        gane = nxt[0] > sc[0]
        r = make_round(m, start + i, side=lado, won=gane, score_before=sb)
        make_round_player(r, team_index=ti, kills=0 if i == 1 else 1)  # ronda sin bajas incluida
    return m

A, D = "Attack", "Defense"
L6 = [A, A, A, D, D, D, D, D]
# 1: remontada 0-3 -> 4-3 (desventaja 3), cambio de lado en ronda 3 con 0-3 -> tramo -2
partida(1, [(0,0),(0,1),(0,2),(0,3),(1,3),(2,3),(3,3)], L6, 4, 3, mapa="Oregon")
# 2: derrumbe 3-0 -> 3-4, numerada desde 1, team_index 1
partida(2, [(0,0),(1,0),(2,0),(3,0),(3,1),(3,2),(3,3)], L6, 3, 4, ti=1, start=1, mapa="Bank")
# 3: pre-Y9S4 con remontada: no debe aparecer
partida(3, [(0,0),(0,1),(0,2),(1,2),(2,2),(3,2)], L6, 4, 2, cv=Y9S4 - 1)
# 4: falta la ronda 2: fuera
m = partida(4, [(0,0),(0,1),(0,2),(1,2),(2,2),(3,2)], L6, 4, 2)
m.rounds.filter(number=2).delete() if hasattr(m, "rounds") else m.round_set.filter(number=2).delete()
# 5: sin resultado
m = partida(5, [(0,0),(0,1),(0,2),(1,2),(2,2),(3,2)], L6, 4, 2); Match.objects.filter(pk=m.pk).update(won=None)
# 6: tres equipos en el marcador
partida(6, [(0,0,0),(0,1,0),(0,2,0),(1,2,0),(2,2,0),(3,2,0)], L6, 4, 2)
# 7..31: 25 remontadas 0-2 -> 4-2 para el tope de 20
for k in range(7, 32):
    partida(k, [(0,0),(0,1),(0,2),(1,2),(2,2),(3,2)], L6, 4, 2, mapa="Kafe Dostoyevsky")
print("ok", Match.objects.count())
```

## Para el humano

- Revisor 20261015T0310Z: texto de vacio del panel (Trends.jsx:546) menciona solo Y9S4; tambien saca partidas con rondas faltantes. Cambio de una linea, no bloquea; se puede corregir en la entrega o despues.
