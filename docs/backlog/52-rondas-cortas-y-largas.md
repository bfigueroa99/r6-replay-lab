# 52. Rondas cortas y rondas largas

estado: en curso 2026-10-17
candado: dev 2026-10-17T20:04Z
rama: claude/equipo-dev/52-rondas-cortas-y-largas
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B9 (y B12, que entra como columna de este tramo)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/factories.py, backend/tests/test_duracion.py, backend/tests/test_api.py, backend/tests/test_seed_demo.py, frontend/src/duracion.js, frontend/src/duracion.test.js, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md, docs/formato-rec.md
turnos: po 20261017T1204Z, arquitecto 20261017T1603Z, dev 20261017T2004Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Tendencias, tu winrate de ronda segun cuanto duro la fase de accion,
separado por lado: si en ataque solo ganas las ejecuciones rapidas o si en
defensa te quiebras cuando la ronda se alarga. Hoy la duracion solo aparece
como texto suelto en cada ronda del detalle (`MatchDetail.jsx:98`) y ningun
agregado la usa.

## Criterios de aceptacion

- [ ] `/api/trends/` trae la clave nueva `by_round_length`: una fila por
      tramo fijo de duracion (`0-45 s`, `45-90 s`, `90-135 s`, `135 s o mas`)
      y una fila aparte `Posible plant`, cada una con `rounds`, `rounds_won`,
      `winrate`, `rating` y `kpr`, por lado (`Attack`, `Defense`) y total.
      Tramo con 0 rondas: fila con `rounds: 0` y `winrate: null`, no se omite.
- [ ] La duracion es `Round.duration` (`clock_start - clock_end`). Una ronda
      con `possible_plant=True` cuenta solo en la fila `Posible plant` y en
      ningun tramo (despues del plant el reloj no mide la misma fase,
      `docs/formato-rec.md`); una ronda con `clock_start == 0` (reloj
      desconocido) no cuenta en ninguna fila. Test con una ronda de cada caso.
- [ ] Los filtros de siempre (`map`, `side`, `since`/`until`, `ranked`,
      sesion) recortan la tabla igual que al resto de Tendencias; con base
      vacia la clave existe y todas las filas tienen `rounds: 0`.
- [ ] Cada fila trae `avg_duration_won` y `avg_duration_lost` (segundos con
      un decimal, `null` sin rondas): cuanto tardas en ganar y en perder en
      ese lado (B12, sin separar por condicion de victoria).
- [ ] Tendencias muestra el panel "Rondas cortas y largas" con los tramos
      en filas y ataque, defensa y total en columnas; el e2e
      (`frontend/e2e/`) lo encuentra con datos de `seed_demo` y la consola
      queda limpia. La logica de armado de la tabla vive en un modulo puro con
      su test de vitest.
- [ ] `docs/metricas.md` tiene la fila **Duracion de la ronda** con los
      tramos, la exclusion de posible plant y de reloj desconocido.

## Fuera de alcance

- Tramos configurables desde la UI o el `.env`.
- Separar las rondas por condicion de victoria (eliminacion, objetivo,
  tiempo): `round_endings` ya lo hace por otro eje.
- Cualquier lectura del momento del plant: solo se infiere y no entra en
  metricas.
- CSV dedicado (va con H3 si alguien lo pide).

## Diseno

(Arquitecto 20261017T1603Z, sobre main 9e3d660)

**Filtros duros.** Pasa casi todos: sin red, sin dependencias, sin overlay, sin migracion,
sin metrica nueva al importar (la duracion es la resta de dos columnas que ya estan en
`Round`, lo mismo que hace la property `Round.duration`). **Falla uno, en parte:** la fila
`Posible plant` con `winrate`, `rating` y `kpr` es una metrica sobre plant inferido, que
`CLAUDE.md` ("Plants y defuses en temporadas nuevas: solo se infieren del reloj") y
`docs/backlog/ALCANCE.md:149` ("`possible_plant` ... no entra en ninguna metrica") dejan
fuera. Se corrige abajo (criterio 1): la fila existe, pero solo cuenta rondas.

**Fuente del dato (verificado).**
- `Round.clock_start` / `Round.clock_end` (`models.py:101-102`) y la property
  `Round.duration = max(clock_start - clock_end, 0)` (`models.py:114-117`). La property no
  se puede usar en el ORM: el agregado repite la resta como `ExpressionWrapper`.
- El parser los llena con `reader.clock_max` / `reader.clock_last` (`pydissect/match.py:81-82`,
  `pydissect/events.py:207-219`): el reloj mas alto (inicio de la fase de accion, 180 en
  ranked) y el **ultimo valor distinto de cero**. Una ronda que llega al final del reloj
  termina con `clock_end = 1`, no 0 (dura ~179 s y cae en el ultimo tramo).
- `metrics._clock_start` (`metrics.py:34-39`): si el `.rec` no trae reloj, cae al reloj mas
  alto de los eventos, que en la practica tambien es 0. Reloj desconocido = `clock_start <= 0`.
  Se agrega `clock_end <= 0` al mismo corte: como `clock_last` ignora ceros, un `clock_end` en
  0 con `clock_start > 0` solo sale de ese fallback, y la resta daria el reloj de un evento,
  no una duracion. Es defensivo y no cambia nada con datos reales.
- `possible_plant` (`metrics.py:236`): modo Bomb, perdedor **no barrido**, `clock_end > 5`
  y con ganador. **Premisa a matizar:** sacar `possible_plant` no saca todas las rondas con
  plant. Un plant seguido de una barrida (atacantes que matan a todos, o defensores que los
  eliminan antes del defuse) no queda marcado, y su `clock_end` es el del momento del plant
  (el reloj principal deja de emitirse). Esa ronda entra en un tramo con su "duracion hasta
  el plant". No hay forma de separarla con lo que trae el `.rec`; va escrito en
  `docs/metricas.md`.
- El lado es `RoundPlayer.side` (`models.py:127`), el mismo que filtra `base_queryset`
  (`aggregates.py:49-50`) y que usan `round_endings` y `first_teammate_death`. La duracion
  es de la ronda, igual para todos; el lado sale de tu fila.
- Ganada: `RoundPlayer.won` para `rounds_won`/`winrate` (es lo que usa `AGGREGATES`, asi el
  winrate del tramo es comparable con el resto de Tendencias). Para los promedios de
  duracion se usa `round__my_team_won` True/False: una ronda sin ganador no es "lo que
  tardas en perder" (misma razon que el comentario de `round_endings`, `aggregates.py:795`).

**Filtros (verificado).** `views._filters` (`views.py:57-84`) arma `side`, `map`,
`operator`, `site`, `match_type`, `ranked_only` (no `ranked`), `since`/`until`/`days` y
`session`; `base_queryset(**filters)` (`aggregates.py:44-66`) los aplica sobre tus
`RoundPlayer`. Partiendo de `base_queryset` todos recortan la tabla sin codigo propio.
Rating: `rating_baseline()` sin filtros, una vez por request (como `_filas_por_tramo`,
`aggregates.py:474-482`); `derive(row, baseline)` da `winrate`, `kpr`, `rating`.

**Tramos de 45 s.** Se quedan como estan. Razon: la fase de accion de ranked es 180 s, y
los cuatro tramos la parten en cuartos legibles (rush/roam temprano, contacto, ejecucion,
cierre). Sin base real a mano (el sandbox no tiene `data/`) no hay evidencia para
moverlos. Lo que se sabe de antemano: `0-45 s` va a tener pocas rondas (barrer a 5 en 45 s
es raro), y `135 s o mas` junta las ejecuciones tardias con **todas** las rondas que llegan
al final del reloj, que son derrota en ataque y victoria en defensa. Es estructural, no un
bug: el hint lo dice y el aviso de muestra (`MUESTRA_CORTE = 30`) cubre el tramo flaco. Los
tramos son segundos absolutos: un modo con fase de accion mas corta llena menos el ultimo.
Si la base real del humano deja casi todo en un tramo, se cambia una constante.

**Forma de la respuesta.** `by_round_length` es un dict (como `by_margin`), no una lista:

```
{
  "rows": [
    {"length": "0-45",    "Attack": celda, "Defense": celda, "total": celda},
    {"length": "45-90",   ...}, {"length": "90-135", ...}, {"length": "135+", ...},
    {"length": "plant",   ...}
  ],
  "summary": {"Attack": celda, "Defense": celda, "total": celda},
  "rounds_unknown_clock": int
}
celda = {"rounds", "rounds_won", "winrate", "rating", "kpr",
         "avg_duration_won", "avg_duration_lost"}
```

`summary` junta los cuatro tramos (sin plant ni reloj desconocido): es la respuesta a B12
("cuanto tardas en ganar y en perder en ese lado"). El promedio dentro de un tramo de 45 s
casi no informa (queda acotado por el tramo); el del lado entero si.

**Archivos**

- `backend/replays/analytics/aggregates.py`: bloque nuevo justo despues de `round_endings()`
  (termina en la linea 837, antes de `by_hour`): misma familia, "como terminan tus rondas,
  por lado". No toca `AGGREGATES` ni `derive` (los toca la ficha 53).
  - Constantes: `TRAMOS_DURACION = (("0-45", 0, 45), ("45-90", 45, 90), ("90-135", 90, 135),
    ("135+", 135, None))`, `FILA_PLANT = "plant"`, `LADOS_DURACION = ("Attack", "Defense")`,
    `CAMPOS_DURACION = ("rounds", "rounds_won", "winrate", "rating", "kpr",
    "avg_duration_won", "avg_duration_lost")`.
  - `_duracion() -> ExpressionWrapper`: `F("round__clock_start") - F("round__clock_end")`,
    `FloatField`. Funcion y no constante por lo mismo que `rating_points_expr`.
  - `_promedios_de_duracion() -> dict`: `{"avg_duration_won": Avg("duracion",
    filter=Q(round__my_team_won=True)), "avg_duration_lost": Avg("duracion",
    filter=Q(round__my_team_won=False))}`, instancias nuevas en cada llamada.
  - `_celda(raw: dict | None, baseline, *, con_metricas=True) -> dict`: `derive(dict(raw),
    baseline)` si hay `raw`, redondea los dos promedios a 1 decimal, y se queda solo con
    `CAMPOS_DURACION`. Sin `raw`: `rounds: 0, rounds_won: 0` y el resto `None`. Con
    `con_metricas=False` deja `rounds` y pone todo lo demas en `None` (fila plant).
  - `_celdas_por_lado(qs, baseline, *, con_metricas=True) -> dict`: una consulta
    `qs.filter(side__in=LADOS_DURACION).values("side").annotate(**AGGREGATES,
    **_promedios_de_duracion())` para los dos lados y una `qs.aggregate(...)` igual para
    `total`. **`total` son todas las rondas del tramo, tambien las sin lado** (como
    `first_teammate_death`): puede ser mayor que ataque + defensa.
  - `by_round_length(**filters) -> dict`. Pasos:
    1. `qs = base_queryset(**filters)`; `baseline = rating_baseline()` una vez.
    2. `sin_reloj = Q(round__clock_start__lte=0) | Q(round__clock_end__lte=0)`;
       `con_reloj = qs.exclude(sin_reloj).annotate(duracion=_duracion())`;
       `rounds_unknown_clock = qs.filter(sin_reloj).count()`.
    3. `medibles = con_reloj.filter(round__possible_plant=False)`. Por tramo `(nombre,
       desde, hasta)`: `medibles.filter(duracion__gte=desde)` salvo el primero (sin piso,
       asi una resta negativa cae en `0-45` como hace `max(..., 0)` de la property) y
       `.filter(duracion__lt=hasta)` salvo el ultimo. Bordes cerrados abajo: 45.0 es
       `45-90`, 135.0 es `135+`.
    4. Fila plant: `_celdas_por_lado(con_reloj.filter(round__possible_plant=True),
       baseline, con_metricas=False)`. Reloj desconocido gana sobre plant: no cuenta en
       ninguna fila.
    5. `summary = _celdas_por_lado(medibles, baseline)`.
    6. Devuelve `{"rows": [{"length": n, **celdas} ...], "summary": ..., 
       "rounds_unknown_clock": ...}`. Cinco filas siempre, en ese orden; base vacia = cinco
       filas en 0 y `summary` en 0. Son ~14 consultas por request; las de `trends` ya
       son del mismo orden por panel.
- `backend/replays/views.py` (`trends`, linea 235, despues de `"round_endings"`):
  `"by_round_length": agg.by_round_length(**filters)`.
- `backend/tests/factories.py` (`make_round`, linea 55): kwargs nuevos `clock_start: float =
  180`, `clock_end: float = 30`, `possible_plant: bool = False`, pasados al `create`. Los
  defaults son los de hoy: ningun test existente cambia.
- `backend/tests/test_duracion.py` (nuevo; estilo de `test_margen.py`, con un helper
  `_ronda(match, numero, lado, *, gano, fin, inicio=180, plant=False)` que arma la ronda y
  tu fila). Tests:
  - `test_los_tramos_salen_en_orden_fijo_con_ataque_defensa_y_total`
  - `test_una_ronda_de_45_segundos_cae_en_45_a_90` (y 135.0 en `135+`)
  - `test_una_ronda_que_llega_al_final_del_reloj_cae_en_135_o_mas` (`clock_end=1`)
  - `test_un_posible_plant_cuenta_solo_en_su_fila_y_sin_metricas` (aparece en `plant` con
    `rounds: 1`, `winrate`/`rating`/`kpr`/promedios `None`, y en ningun tramo ni en `summary`)
  - `test_una_ronda_con_reloj_desconocido_no_cuenta_en_ninguna_fila` (`clock_start=0`;
    `rounds_unknown_clock == 1`, tambien si ademas es `possible_plant`)
  - `test_un_tramo_vacio_trae_cero_rondas_y_winrate_nulo`
  - `test_los_promedios_de_ganadas_y_perdidas_van_con_un_decimal` (p. ej. 50 y 61 s -> 55.5)
  - `test_una_ronda_sin_ganador_no_entra_en_los_promedios`
  - `test_el_resumen_junta_los_cuatro_tramos_sin_plant`
  - `test_el_total_incluye_rondas_sin_lado`
  - `test_el_filtro_de_lado_deja_el_otro_lado_en_cero`
  - `test_el_filtro_de_mapa_recorta_las_rondas`
  - `test_rating_y_kpr_del_tramo_son_los_de_totals` (kpr exacto, rating = `totals` del mismo
    queryset)
  - `test_base_vacia_trae_las_cinco_filas_en_cero`
  - en `test_api.py`, junto a `test_trends_trae_by_margin` (linea 116):
    `test_trends_trae_by_round_length` (200, las 5 `length` en orden, `summary` y
    `rounds_unknown_clock`).
  - en `test_seed_demo.py` (`FormaTests`): `test_todas_las_rondas_duran_lo_que_afirma_el_e2e`
    (todas `clock_start=180`, `clock_end=20`, `possible_plant=False`): fija el contrato del e2e.
- `frontend/src/duracion.js` + `frontend/src/duracion.test.js` (nuevos, como `margen.js` /
  `cierres.js`):
  - `TRAMOS = {'0-45': '0–45 s', '45-90': '45–90 s', '90-135': '90–135 s', '135+': '135 s o
    más', plant: 'Posible plant'}`; `etiquetaDuracion(length)` (desconocido pasa tal cual).
  - `textoCelda(celda)`: `"57% (203)"`; sin rondas `"—"`; fila plant (winrate nulo con
    rondas) `"— (n)"`. El entero sale de `Math.round(winrate)`.
  - `filasDeDuracion(byRoundLength)`: `rows` -> `{...fila, orden, tramo, vista: {Attack,
    Defense, total}}` con `textoCelda`, y `rating`/`kpr` de `total` subidos a la fila.
  - `resumenDeDuracion(byRoundLength)`: tres filas (`Ataque`, `Defensa`, `Total`) desde
    `summary` con `rounds`, `avg_duration_won`, `avg_duration_lost`.
  - `celdasConPocaMuestra(byRoundLength, minimo = MUESTRA_CORTE)`: aplana las celdas de los
    cuatro tramos (no la de plant) y reusa `filasConPocaMuestra`.
  - `hayDuracion(byRoundLength)`: `summary.total.rounds > 0` o alguna fila con rondas.
  - Tests: `etiqueta los tramos en castellano y conserva el orden del backend`,
    `una celda sin rondas muestra guion y no 0 %`, `la fila de posible plant muestra solo el
    conteo`, `el resumen arma ataque, defensa y total con los promedios`, `avisa poca muestra
    solo con celdas de 1 a 29 rondas y no mira la fila de plant`, `respuesta ausente devuelve
    listas vacias sin romper`.
- `frontend/src/pages/Trends.jsx`: import en la linea 22; `const duracion =
  data.by_round_length` junto a `margen` (~linea 172). Panel **"Rondas cortas y largas"**
  justo despues de "Cómo se cierran tus rondas" (cierra en la linea 653) y antes de "Por
  hora del día": mismo eje (como terminan tus rondas, por lado). Se renderiza si `duracion`
  existe; si `!hayDuracion(duracion)`, nota "Sin rondas con reloj legible." en lugar de las
  tablas.
  - Tabla 1, `csvName="por-duracion"`: Duración (left) | Ataque | Defensa | Total (las tres
    con `render: (row) => row.vista[lado]`, `csv` con winrate exacto y rondas) | Rating
    (total, `digits: 2`, help "Sobre el total del tramo.") | KPR (total). `initialSort` por
    `orden`, `rowKey` = `length`. Help de la columna Duración: "Segundos de la fase de
    acción, del reloj de la ronda. Posible plant: el reloj se cortó arriba de 5 s sin
    barrida; esas rondas no entran en ningún tramo."
  - `<h3>Cuánto tardas en ganar y en perder</h3>` + Tabla 2, `csvName="duracion-promedio"`:
    Lado | Rondas | Ganadas en | Perdidas en (render `${Math.round(v)} s` o `—`).
  - Hint: con `celdasConPocaMuestra(duracion).length`, "Ojo: alguna celda tiene menos de 30
    rondas; la diferencia puede ser varianza."; si no, "Winrate según cuánto duró la fase
    de acción. Llegar al final del reloj cae en 135 s o más: en ataque es derrota y en
    defensa victoria."
  - Si `rounds_unknown_clock > 0`, nota: "N rondas sin reloj quedaron fuera."
- `frontend/e2e/humo.spec.js`: `test('Tendencias muestra rondas cortas y largas')`, **justo
  despues** de `'Tendencias muestra como se cierran tus rondas'` (linea 160), no al final del
  archivo (las fichas 53 y 54 agregan tests al final). Panel por heading exacto, como el de
  margen. Afirma (numeros de `seed_demo`, verificados corriendo el comando contra una base
  temporal: 203 rondas, `clock_start=180`, `clock_end=20` en todas, ninguna plant, ataque
  116 rondas todas ganadas, defensa 87 todas perdidas):
  - primera tabla `tbody tr` = 5;
  - fila "135 s o más": celdas `100% (116)`, `0% (87)`, `57% (203)`, rating `1.00`, KPR `0.49`;
  - fila "0–45 s": tres celdas `—`;
  - tabla de promedios: Ataque `160 s` / `—`, Defensa `—` / `160 s`, Total `160 s` / `160 s`;
  - consola limpia.
  Que todo caiga en un tramo es una limitacion del seed y no se cambia: tocar `clock_end`
  de `seed_demo` mueve la narrativa del detalle (`narrative.py` lee `clock_end`/`duration`)
  y los numeros de otros e2e. El reparto entre tramos lo prueban los tests de backend.
- `docs/metricas.md`: fila **Duracion de la ronda** (panel "Rondas cortas y largas") en
  `## Contexto de la ronda`, despues de **Como se cierran tus rondas** (linea 91). Contenido:
  `clock_start - clock_end` de la ronda (segundos de fase de accion, absolutos); tramos
  `0-45`, `45-90`, `90-135`, `135 o mas`, borde cerrado abajo; llegar al final del reloj
  cae en el ultimo; `Posible plant` fuera de los tramos y solo con conteo (no es una
  metrica de plant); un plant que termina en barrida no se marca y cuenta en un tramo con
  la duracion hasta el plant; reloj desconocido (`clock_start` o `clock_end` en 0) fuera de
  todo y contado aparte; winrate, rating y KPR los de siempre sobre el tramo; lado = el de
  tu fila; total incluye rondas sin lado; **Cuanto tardas en ganar / perder**: promedio de
  duracion de tus rondas ganadas / perdidas de los cuatro tramos, sin plant, sin rondas sin
  ganador; aviso de varianza con menos de 30 rondas en una celda.
- `docs/formato-rec.md` (linea 141, "no entra en ninguna metrica"): agregar "salvo para
  sacar la ronda de los tramos de duracion, donde se cuenta aparte sin metricas". Mismo
  matiz en `docs/backlog/ALCANCE.md:149` si el PO lo quiere; no es del Dev.

**Correccion de criterios**

1. *Criterio 1, fila `Posible plant`:* trae solo `rounds` por lado y total; `rounds_won`
   en 0 y `winrate`, `rating`, `kpr`, `avg_duration_won`, `avg_duration_lost` en `null`. Un
   winrate sobre rondas con plant inferido es una metrica de plant (descartada en
   `ALCANCE.md:149`); el promedio de duracion de esas rondas seria leer el momento del
   plant (fuera de alcance de la propia ficha).
2. *Criterio 1, forma:* `by_round_length` es `{rows, summary, rounds_unknown_clock}`, cada
   fila con celdas `Attack`/`Defense`/`total`. `summary` y `rounds_unknown_clock` son nuevos.
3. *Criterio 2, reloj desconocido:* `clock_start <= 0` **o** `clock_end <= 0`.
   Y la premisa de que sacar `possible_plant` saca todo lo post-plant es falsa: un plant con
   barrida no se marca. Se documenta, no se arregla.
4. *Criterio 3, filtros:* la clave es `ranked_only`, no `ranked`; tambien recortan
   `operator`, `site`, `match_type` y `days`.
5. *Criterio 4, B12:* el promedio que contesta "cuanto tardas" es el de `summary` por lado;
   el de cada tramo se entrega (el criterio lo pide) pero la UI muestra el de `summary`.
6. *Criterio 5, e2e:* con `seed_demo` todo cae en `135 s o mas`; el e2e afirma esa fila y las
   vacias, no un reparto.

**Orden:** factories + aggregates + test_duracion -> vista + test_api + test_seed_demo ->
duracion.js + test -> Trends.jsx -> e2e -> metricas.md + formato-rec.md -> `check.ps1`.

**Que puede romperse:** nada de datos (sin migracion ni recompute: lee columnas que ya
estan). `seed_demo` no se toca. Los defaults nuevos de `make_round` son los actuales. El e2e
de cierres busca su panel por `hasText: 'Cómo se cierran tus rondas'`: el panel nuevo no
puede contener ese texto (no lo contiene). El de margen cuenta `tbody tr` dentro de su
panel; el nuevo es otra `section.panel`. `/api/trends/` suma ~14 consultas.

**Verificacion manual:** `curl -s localhost:8000/api/trends/ | python -m json.tool | grep -A80
by_round_length` sobre `seed_demo`: `135+` con 116/87/203; con `?side=Attack`, Defense en 0
y total 116; con `?map=bank` total 70 (36+30+4). Abrir Tendencias y bajar el CSV de las dos
tablas.

**Archivos ocupados:** ninguna rama de trabajo abierta. Contacto con las fichas en paralelo:
`aggregates.py` (53 toca `AGGREGATES`/`derive`, 54 las funciones de compañeros; esta solo
agrega un bloque nuevo despues de `round_endings` y no edita ninguno de los dos),
`views.py` (53 `_match_scoreboard`, 54 `teammates`; esta una linea en `trends`) y
`humo.spec.js` (las tres agregan tests; esta inserta despues del test de cierres, no al
final). `factories.py` y `Trends.jsx` no los toca ninguna de las otras dos segun lo
declarado. Si 53 o 54 agregan kwargs a `make_round`, el merge es trivial.

## Para el humano

Los tramos de 45 s son una eleccion del PO sobre una fase de accion de
~180 s. Si con la base real casi todo cae en un tramo, el Arquitecto puede
ajustarlos antes de implementar; es reversible.

- Arquitecto 2026-10-17: la fila `Posible plant` queda solo con `rounds` (winrate, rating, KPR y promedios en `null`): una metrica sobre un plant inferido choca con CLAUDE.md. Un plant seguido de barrida no se marca `possible_plant` y entra a un tramo con la duracion hasta el plant; no se puede separar con lo que trae el `.rec` y queda documentado. Tramos de 45 s sin cambio; calibrar con la base real.
