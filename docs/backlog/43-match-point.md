# 43. Match point y ronda decisiva

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B5, segundo tramo de B2 (rondas bajo presion); el primer tramo (adelante/empatado/atras) entro con la ficha 41
archivos: backend/replays/analytics/reglas_partida.py, backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_match_point.py, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T0911Z, arquitecto 20261014T1012Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver como rindes en las rondas que pueden cerrar la partida: cuando tu equipo
esta a una ronda de ganarla, cuando el rival esta a una de ganarla, y cuando
pasan las dos cosas a la vez. Completa el panel "Según el marcador" de la
ficha 41 con el momento de mas presion.

## Criterios de aceptacion

- [ ] Una tabla de reglas en `pydissect/constants.py` (o `replays/`, a
  eleccion del Arquitecto) dice, por tipo de partida y desde que
  `code_version` vale, a cuantas rondas se gana y como es la prorroga. Una
  partida cuyo tipo o temporada no tiene regla no cuenta como match point:
  cae en "sin regla". Test con un tipo inventado que afirma que va a "sin
  regla" y no a "normal".
- [ ] `GET /api/trends/` devuelve una lista nueva (p. ej. `match_point`) con
  las filas `mine` (tu equipo a una ronda de ganar), `theirs` (el rival a una
  de ganar), `both` (las dos a la vez), `normal` y `unknown` (sin marcador o
  sin regla), con las metricas de siempre. Las filas suman todas tus rondas.
  Test con factories y una partida de punta a punta.
- [ ] Reusa la lectura de `score_before` de `by_score_state` (mismo corte por
  `code_version >= Y9S4`; antes de eso el marcador es [0, 0] y va a
  `unknown`). Test con una partida Y9S3 que afirma `unknown`.
- [ ] Tendencias muestra el panel junto a "Según el marcador", con la banda de
  muestra chica; base vacia sin error en consola. El e2e lo ve con
  `seed_demo` (si hace falta, `seed_demo` usa un tipo con regla; los numeros
  que afirma el e2e se actualizan en la misma rama).
- [ ] Fila nueva en `docs/metricas.md` que explica las reglas por tipo y que
  una partida sin regla no cuenta.

## Fuera de alcance

- Inferir la regla desde las partidas importadas (el marcador final): sesga
  hacia las partidas que terminaron y no detecta un match point perdido.
- Probabilidad de ganar la partida segun el marcador.
- Modos sin rondas por equipos (si aparecen, "sin regla").

## Diseno

(arquitecto 20261014T1012Z, sobre main 3438ab2)

Filtros duros: pasa. Lee `Round.score_before`, `RoundPlayer.team_index`,
`Match.match_type` y `Match.code_version`, que ya estan en la base; la regla
de cada tipo es una tabla de datos en el codigo, no una consulta a nadie. Sin
migracion ni dependencia.

**Implementar despues de que #42 se mergee**: las dos tocan `aggregates.py`
(al lado de `by_score_state`), la vista `trends`, `Trends.jsx`, `humo.spec.js`
y la misma seccion de `metricas.md`. Prioriza, no bloquea: si 42 sigue sin
rama cuando un Dev llegue, puede tomar esta primero y la otra resuelve el
conflicto con P3.

**La tabla de reglas y su fuente.** Solo entra lo que se puede citar:

| `match_type` | desde | gana a | prorroga | fuente |
|---|---|---|---|---|
| `Ranked` | `Y9S4` | 4 | con 3-3, la gana el primero a 5 | [Dexerto, "Rainbow Six Siege ranks explained", actualizado 2024-06-04](https://www.dexerto.com/rainbow-six/rainbow-six-siege-ranked-all-ranks-climb-fast-tips-1627443/): "first-to-four rounds format... If scores are all tied at 3-3 by the end of regulation, there'll be a three-round overtime" |

No hay pagina oficial de Ubisoft que lo diga en texto (busqueda del
20261014: solo guias de terceros; los que dicen "primero a 5 con prorroga en
4-4" describen el formato de esports, no ranked). `Unranked`, `Standard`,
`QuickMatch` y los custom **quedan fuera** porque no se encontro fuente: sus
rondas van a `unknown`. Agregar una regla despues es agregar una entrada,
con su fuente en un comentario, sin tocar logica. `desde` es `Y9S4` y no
antes porque antes de Y9S4 no hay marcador por ronda: una regla mas vieja
no cambiaria nada.

**Archivos y por que:**

- `backend/replays/analytics/reglas_partida.py` (nuevo, sin Django; en
  `replays/` y no en `pydissect/` porque es una regla de juego que usa la
  analitica, no algo que el parser lea del `.rec`):
  - `REGLAS: dict[str, tuple[dict, ...]]`, por tipo una tupla de
    `{"desde": <code_version>, "para_ganar": 4, "prorroga_hasta": 5}`
    ordenada por `desde`, con la fuente en un comentario. Sin prorroga,
    `prorroga_hasta == para_ganar`.
  - `regla_para(match_type, code_version) -> dict | None`: la de mayor
    `desde` que sea `<= code_version`; `None` si no hay.
  - `objetivo(propio, ajeno, regla) -> int`: `prorroga_hasta` si
    `min(propio, ajeno) >= para_ganar - 1`, si no `para_ganar`.
  - `cierra(propio, ajeno, regla) -> bool`: `propio + 1 >= objetivo(...)`.
  - `estado(mio, suyo, regla) -> str`: `"both"` si cierran los dos, `"mine"`
    o `"theirs"` si cierra uno, si no `"normal"`. Con ranked: 3-2 `mine`,
    3-3 `normal` (la prorroga sube el objetivo a 5), 4-3 `mine`, 4-4 `both`.
  - `tramos(regla, desde, hasta) -> dict[str, list[tuple[int, int]]]`: los
    pares `(mio, suyo)` de `0..prorroga_hasta` agrupados por `estado`. Es lo
    que la consulta usa, asi que la semantica vive en una sola funcion pura.
- `backend/replays/analytics/aggregates.py`:
  - Extraer de `by_score_state` un helper `_marcador_conocido(qs)` que
    devuelve `(qs_anotado, conocido)` con las anotaciones `mio`/`suyo` y el
    filtro de dos equipos y `code_version >= Y9S4`. `by_score_state` lo usa
    sin cambiar su salida (`test_marcador.py` lo cuida).
  - `by_match_point(**filters)`, orden fijo `MATCH_POINT = ("mine",
    "theirs", "both", "normal", "unknown")`. Por cada `match_type` de
    `REGLAS` y cada tramo de version (`desde` hasta el `desde` siguiente), un
    `Q(round__match__match_type=t, round__match__code_version__gte=desde,
    [code_version__lt=siguiente])` combinado con el `OR` de
    `Q(mio=a, suyo=b)` de los pares de cada estado. `con_regla` = `conocido`
    filtrado por el `OR` de los `Q` de tipo y version. `mine`, `theirs`,
    `both` = `con_regla` filtrado por su `Q`; `normal` = `con_regla` menos
    esos tres (cubre marcadores fuera de rango); `unknown` =
    `qs.exclude(pk__in=con_regla.values("pk"))`. Filas con
    `_filas_por_tramo("match_point", ...)`: mismas metricas que los paneles
    vecinos. Las cinco suman todas tus rondas por construccion.
- `backend/replays/views.py`: `"by_match_point": agg.by_match_point(**filters)` en `trends`.
- `frontend/src/pages/Trends.jsx`: constante `MATCH_POINT = { mine: 'Tu
  match point', theirs: 'Match point rival', both: 'Los dos a una ronda',
  normal: 'Sin match point', unknown: 'Sin marcador o sin regla' }`; panel
  **"Match point"** justo despues de "Según el marcador", con `TablaDeCorte`
  (`rowKey="match_point"`, `csvName="match-point"`), la fila `unknown`
  filtrada igual que `porMarcador` (solo si tiene rondas) y el hint de
  `filasConPocaMuestra`; sin muestra chica: `'Rondas que podían cerrar la
  partida. Por ahora solo ranked: los otros modos no tienen regla
  confirmada.'`.
- `frontend/e2e/humo.spec.js`: test `Tendencias muestra el match point`.
  `seed_demo` es ranked, Y9S4, 7 rondas por partida y ganas las pares: la
  ronda 5 llega 3-2 (`mine`) y la 6 llega 3-3 (`normal`). El test afirma las
  celdas `Tu match point` y `Sin match point`, ninguna `Sin marcador o sin
  regla`, y consola limpia. `seed_demo` no se toca.
- `backend/tests/test_match_point.py` (nuevo).
- `docs/metricas.md`: fila **"Match point"** en `## Contexto de la ronda`,
  debajo de "Segun el marcador".

**Tests (`test_match_point.py`; las funciones puras sin base, el agregado
con `factories.py` y el helper `_partida` de `test_marcador.py` copiado o
importado):**

- `test_ranked_tres_a_dos_es_tu_match_point`
- `test_ranked_tres_a_tres_no_es_match_point_por_la_prorroga`
- `test_ranked_cuatro_a_cuatro_es_de_los_dos`
- `test_dos_a_tres_es_match_point_rival`
- `test_sin_prorroga_el_empate_a_uno_de_ganar_es_de_los_dos` (regla
  inventada `para_ganar == prorroga_hasta == 3`)
- `test_un_tipo_sin_regla_va_a_unknown_y_no_a_normal` (`match_type="Arcade"`)
- `test_quick_match_sin_fuente_va_a_unknown`
- `test_una_partida_y9s3_va_a_unknown`
- `test_siendo_el_equipo_uno_el_marcador_se_lee_al_reves`
- `test_las_cinco_filas_salen_en_orden_y_suman_todas_tus_rondas` (una
  partida ranked de punta a punta con los marcadores 0-0, 1-0, 1-1, 2-1,
  2-2, 3-2, 3-3, 4-3, 4-4)
- `test_regla_para_toma_la_de_mayor_desde_que_aplica`

**Orden:** `reglas_partida.py` + sus tests -> helper en `aggregates.py` con
`test_marcador.py` en verde -> `by_match_point` + tests -> vista -> panel ->
e2e -> `metricas.md`.

**Que puede romperse:** el refactor de `by_score_state` (lo cuida
`test_marcador.py`, que no se toca). Una regla mal escrita marca match point
donde no hay: por eso la tabla cita fuente y queda corta.

**Fila de `metricas.md`** (texto sugerido): "Rondas segun si alguien podia
cerrar la partida ganandola, leido del marcador antes de la ronda (el mismo
de 'Segun el marcador'). *Tu match point*: tu equipo gana la partida si gana
esa ronda; *match point rival*: al reves; *los dos*: las dos cosas. Depende
de a cuanto se gana cada tipo de partida, que sale de una tabla con fuente:
hoy solo ranked (gana a 4; con 3-3 hay prorroga y gana el primero a 5, asi
que 3-3 no es match point y 4-4 es de los dos). Unranked, rapida y custom no
tienen regla confirmada y van a 'Sin marcador o sin regla', junto con las
rondas sin marcador. Las cinco filas suman todas tus rondas."

**Verificacion manual (Verificar en el PC):** con la base real,
`/tendencias?match_type=Ranked`: el panel marca match point en partidas
ranked de 4-x; `?match_type=QuickMatch` las manda todas a "Sin marcador o
sin regla".

**Umbral:** ninguno nuevo; usa `MUESTRA_CORTE`.

## Implementacion

## Para el humano

Aviso, sin pregunta abierta: la tabla de reglas (a cuantas rondas se gana
cada tipo y como es la prorroga) se arma desde fuentes publicas y se probo
solo con datos sinteticos. Solo ranked tiene fuente (una guia de Dexerto de
2024, no una pagina oficial); unranked y rapida quedan en "sin regla" hasta
que alguien cite la suya. Si sabes la regla de esos modos, agregarla es una
linea en `reglas_partida.py`. Conviene mirar en el PC que el panel marque
match point en una partida ranked y una rapida reales.
