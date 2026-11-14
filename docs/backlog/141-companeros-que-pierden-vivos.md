# 141. Compañeros que pierden vivos

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C20 (el reverso de la 131, `won_without_me`, que ya cuenta quien seguia vivo en las rondas que el equipo gano sin ti)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_vivo_en_perdidas.py, frontend/src/vivoEnPerdidas.js, frontend/src/vivoEnPerdidas.test.js, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261114T0040Z-chQsvnq, arquitecto 20261114T0316Z-cwWsU9i

## PR

## Que gana quien usa la app

En Compañeros, por compañero habitual, cuantas de las rondas que tu equipo
perdio jugando con el terminaron con el vivo: quien se guarda cuando la ronda
se va. Hoy la app cuenta quien sigue vivo en las que ganaste sin ti (131),
pero no en las perdidas.

## Criterios de aceptacion

- [ ] Agregado nuevo: por compañero habitual (el mismo criterio de
      habitual que `won_without_me`), sobre tus rondas filtradas que tu
      equipo perdio (`Round.my_team_won=False`; sin ganador no cuenta) y en
      que el estaba en tu equipo: `lost_rounds`, `alive_at_end` (su
      `RoundPlayer.survived`) y `pct`. Test con un compañero vivo en 2 de 3
      perdidas y una ronda ganada que no entra.
- [ ] Al lado, la misma tasa tuya en esas rondas (tu `survived`), para
      comparar. Test.
- [ ] Un jugador que en otra ronda fue rival no suma en esa ronda (se lee
      `team_index` ronda por ronda). Test.
- [ ] Los filtros globales aplican sobre tu fila de la ronda; test con
      filtro de lado.
- [ ] Panel o columna en Compañeros, junto a "Ganadas sin ti", con el `n`
      (perdidas juntos) a la vista y aviso de muestra chica; sin filas, una
      nota. e2e con `seed_demo`, numeros de la API y consola limpia. Fila
      nueva en `docs/metricas.md`.

## Fuera de alcance

- Marcar esas rondas en el detalle de partida (otro tramo, como F27).
- Distinguir "vivo y escondido" de "vivo peleando": el `.rec` no trae
  posicion ni dano.

## Diseno

(arquitecto 20261114T0316Z-cwWsU9i) Filtros duros: pasa. Usa `RoundPlayer.survived`,
`team_index` y `Round.my_team_won`, que el import ya escribe para cada jugador
de la ronda; sin red, sin dependencias, sin POST, sin migracion ni
`recompute`; se calcula al consultar como `won_without_me`. No es premisa
falsa: Compañeros solo cuenta quien sigue vivo en las ganadas sin ti (131), y
la 139 (`disenado`) mide **tu** supervivencia en las perdidas por lado y mapa
en Tendencias, no la de cada compañero. Una sola forma obvia (el espejo de
*Quién la sostiene*): sin arena ni consenso.

**Regla** (va tal cual a `metricas.md`). Universo: tus rondas filtradas que
tu equipo perdio, `perdidas = base_queryset(**filters).filter(round__my_team_won=False)`
(`False` deja afuera las sin ganador). *Tú*: de `perdidas`, en cuantas tu fila
tiene `survived=True`. Por compañero habitual (la regla de `won_without_me`:
5 partidas en tu equipo, todo el historial, por `Player`): sus filas con
`is_me=False` en esas rondas y con tu `team_index` (en una ronda en que fue
rival no suma); `lost_rounds` = esas filas, `alive_at_end` = las de
`survived=True`, `pct = _pct(alive_at_end, lost_rounds)`, y al lado
`me_alive` = en cuantas de **esas mismas** rondas terminaste vivo tu y
`me_pct = _pct(me_alive, lost_rounds)`: la comparacion es pareada, ronda por
ronda, y no contra tu promedio general. Conteos sumados, nunca promedio de
partidas. Muestra minima: 10 rondas perdidas juntos (`VIVO_EN_PERDIDAS_MIN`):
no se oculta, se marca con `*`.

Por que 10 y no el 5 de `GANADA_SIN_TI_MIN` (statistical-analysis): aca se
comparan dos proporciones sobre el mismo `n`, y con menos de 10 rondas una
sola ronda mueve cada % 10 puntos o mas, asi que la diferencia entre el y vos
es ruido; ademas un habitual (5 partidas) suele sumar decenas de perdidas
juntos (en `seed_demo`, 42 a 87), asi que con 5 la marca no saldria nunca.
Constante propia, no la de la 131: miden `n` distintos (ganadas sin ti contra
perdidas juntos). No hace falta calibrarlo con la base real.

**Archivos:**
- `backend/replays/analytics/aggregates.py`: `VIVO_EN_PERDIDAS_MIN = 10`
  (comentario con el porque de arriba) y `alive_in_losses(**filters) -> dict`
  justo despues de `won_without_me` (antes de `clutch_detail`). Consultas:
  1) `yo = perdidas.aggregate(lost_rounds=Count("id"), alive_at_end=Count("id", filter=Q(survived=True)))`;
  2) `habituales` copiada de `won_without_me` (misma razon que su comentario:
  la 79 toca esa consulta y un helper chocaria);
  `mia_perdida = perdidas.filter(round_id=OuterRef("round_id"), team_index=OuterRef("team_index"))`
  y `mia_viva = mia_perdida.filter(survived=True)`;
  `RoundPlayer.objects.filter(is_me=False, player_id__in=habituales).filter(Exists(mia_perdida))
  .values("player_id", "player__username").annotate(lost_rounds=Count("id"),
  alive_at_end=Count("id", filter=Q(survived=True)), me_alive=Count("id", filter=Exists(mia_viva)))
  .order_by("-alive_at_end", "-lost_rounds", "player__username")`
  (probado en el scratchpad sobre `seed_demo`: `Count(filter=Exists(...))`
  anda en Django 5.2). Dos consultas en total, constantes. Salida:
  `{"min_rounds": VIVO_EN_PERDIDAS_MIN, "me": {"lost_rounds", "alive_at_end", "pct"},
  "mates": [{"player_id", "username", "lost_rounds", "alive_at_end", "pct",
  "me_alive", "me_pct", "low_sample"}]}`, `low_sample = lost_rounds < VIVO_EN_PERDIDAS_MIN`.
- `backend/replays/views.py`, `teammates()`: clave `"alive_in_losses"` debajo
  de `"won_without_me"`. Sin URL nueva.
- `backend/tests/test_vivo_en_perdidas.py` (Django, `TestCase`, con los
  helpers `partidas_juntas` y `ronda` de `test_ganadas_sin_ti.py` copiados o
  importados de ahi): `test_cuenta_las_perdidas_en_que_el_companero_termino_vivo`
  (vivo en 2 de 3 perdidas -> 3, 2, 66.7; una ganada con el vivo no entra);
  `test_una_ronda_sin_ganador_no_cuenta`;
  `test_tu_tasa_en_las_mismas_rondas` (`me_alive`/`me_pct` por fila: vivo en
  1 de esas 3 -> 1, 33.3);
  `test_tu_tasa_sobre_todas_tus_perdidas` (`me` cuenta tambien perdidas sin
  habituales);
  `test_un_habitual_que_juega_de_rival_no_suma_esa_ronda`;
  `test_un_companero_no_habitual_no_sale` (4 partidas juntas);
  `test_el_filtro_de_lado_va_sobre_tu_fila`;
  `test_marca_muestra_chica_debajo_de_diez_rondas` (9 -> `low_sample`, 10 -> no);
  `test_sin_perdidas_devuelve_ceros_y_sin_filas` (`me` en 0 y `pct` None,
  `mates` vacio);
  `test_consultas_constantes` (`assertNumQueries(2)` con 1 y con 3 habituales);
  `test_teammates_devuelve_vivo_en_perdidas` (`/api/teammates/?side=...`, 200 y la clave).
- `frontend/src/vivoEnPerdidas.js` (nuevo): `filasVivoEnPerdidas(data)` ->
  filas `{clave, playerId, nombre, lost_rounds, alive_at_end, pct, me_pct,
  low_sample, orden}` (calcado de `filasSostienen` de `ganadasSinTi.js`), y
  `textoTuyo(me)` -> "Terminaste vivo en 12 de tus 87 rondas perdidas (14%)."
  (`null` sin perdidas; "1 ronda perdida" en singular).
- `frontend/src/vivoEnPerdidas.test.js` (vitest): orden y forma de las filas;
  `[]` sin datos; `textoTuyo` con 0 (null), 1 (singular) y n (plural, con el %).
- `frontend/src/pages/Teammates.jsx`: Panel "Quién sigue vivo en las
  perdidas" justo debajo de "Rondas que tu equipo ganó sin ti" y antes de
  "Teamkills". `hint`: "Rondas que tu equipo perdió con un compañero habitual
  (5 partidas o más en tu equipo) y en cuántas terminó vivo, al lado de cuántas
  de esas mismas terminaste vivo tú. Seguir vivo no dice si se guardó o si
  peleó: el replay no trae posición ni daño. Las rondas sin ganador no
  cuentan." Arriba de la tabla, `<p className="note">` con `textoTuyo`. Tabla
  con columnas Compañero (enlace a `/jugadores/<id>`, como *Quién la
  sostiene*), "Perdidas juntos" (`help`: "Rondas que tu equipo perdió con este
  compañero en tu equipo."), "Seguía vivo", "%" con la marca `*` y su `title`
  ("Menos de 10 rondas"; `help`: "Un * marca menos de 10 rondas: con tan poca
  muestra el % todavía no dice mucho."), y "Tú, en esas" (`me_pct`; `help`:
  "En esas mismas rondas, en qué % terminaste vivo tú."). `csvName`
  `vivos-en-las-perdidas`. Sin perdidas: "Sin rondas perdidas con estos
  filtros." (y sin tabla); con perdidas y sin habituales: "Ningún compañero
  habitual en esas rondas.".
- `frontend/e2e/humo.spec.js`: test "Compañeros muestra quién sigue vivo en
  las perdidas", al lado del de *ganó sin ti*: panel por su heading, con los
  numeros de `/api/teammates/` (`alive_in_losses`) y no a mano: la nota con
  `me.alive_at_end` y `me.lost_rounds`, la primera fila con nombre,
  `lost_rounds` y `alive_at_end`, enlace a `/jugadores/`; consola limpia. En
  `seed_demo` hoy: tu 12 de 87 (14%); Chamo 29 de 87 y Seba 29 de 87 (tu 12
  en esas), Nico 14 de 42 (tu 6).
- `docs/metricas.md`: fila **Quién sigue vivo en las perdidas** debajo de
  **Rondas que tu equipo ganó sin ti**, con la regla de arriba, y en
  `## Muestra minima`: "Quién sigue vivo en las perdidas | 10 rondas perdidas
  juntos por compañero (`VIVO_EN_PERDIDAS_MIN`): no se oculta, se avisa con *".

**Orden:** tests Django en rojo -> `alive_in_losses` -> clave en `teammates` ->
vitest en rojo -> `vivoEnPerdidas.js` -> panel -> e2e -> `metricas.md` ->
`npm run build`.

**Puede romperse:** `.values()` antes del `.annotate()`: el `GROUP BY` tiene
que ser solo `player_id` y `player__username` (mirar el SQL una vez). Un
compañero con dos filas en la misma ronda (dato raro) contaria dos veces,
como en `won_without_me`. El e2e de *ganó sin ti* busca filas por
`getByRole('row', { name: /^Seba 98 38/ })` dentro de su propio panel: el
panel nuevo va aparte y no lo toca.

**Archivos ocupados:** ninguna rama abierta toca `Teammates.jsx`. En
`aggregates.py`, `views.py`, `humo.spec.js` y `metricas.md` la funcion, la
clave, el test y la fila son nuevos y caen en otra zona que las de la 134, la
136 y la 137 (Duelos y el detalle de partida): sin pisada real, no se frena.
La 79 (`entregado`, espera al humano) pasa `habituales` y la raiz de tus
filas a `rondas_contables()`, y su test AST de `aggregates.py` lo exige: la
que mergee segundo pasa tambien la copia de esta ficha (como `won_without_me`,
que ya esta en dev con la misma copia).

**Verificacion manual:** `seed_demo`, `/companeros`: el panel debajo de
*Rondas que tu equipo ganó sin ti*; Chamo y Seba con 29 de 87, Nico con 14 de
42 y "Terminaste vivo en 12 de tus 87 rondas perdidas (14%)". En el seed
todas tus perdidas son de defensa: con lado Defensa salen los mismos
numeros, y con Ataque, "Sin rondas perdidas con estos filtros." y sin tabla.

Skills: no aplica (conteo sobre filas con precedente `won_without_me`; ni tabla nueva ni migracion).
Skills del repo: statistical-analysis (proporcion con su `n` a la vista, comparacion pareada en las mismas rondas y no contra el promedio general, corte de 10 con el porque, conteos sumados), testing-strategy (regla y API en Django `TestCase`, textos en vitest, panel en e2e con numeros de la API), dataviz no aplica (tabla, sin grafico).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

(nada)
