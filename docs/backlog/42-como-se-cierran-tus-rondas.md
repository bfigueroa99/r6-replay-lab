# 42. Como se cierran tus rondas: por eliminacion o sin ella, por lado

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B6 (idea del PO 20261013T0511Z); epica lado-y-marcador en curso (B1, B4 y B2 tramo 1 en main por #25, 39 y 41)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_cierres.py, frontend/src/pages/Trends.jsx, frontend/src/cierres.js, frontend/src/cierres.test.js, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T0911Z, arquitecto 20261014T1012Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver, por lado, cuantas de tus rondas ganadas y perdidas se cierran eliminando
al otro equipo y cuantas sin eliminacion (objetivo o tiempo): si en defensa
pierdes porque te quedas sin gente o porque no llegas a tiempo. Hoy la
condicion solo se ve ronda por ronda en el detalle de una partida.

## Criterios de aceptacion

- [ ] `GET /api/trends/` devuelve una lista nueva (nombre a eleccion del
  Arquitecto, p. ej. `round_endings`) con una fila por lado (`Attack`,
  `Defense`) y por cada fila: `won_elimination`, `won_other`,
  `lost_elimination`, `lost_other`, `unknown` y el total de rondas. Test con
  factories: una ronda ganada con `win_condition="KilledOpponents"` en ataque
  suma 1 a `won_elimination` de `Attack` y a nada mas.
- [ ] Cada fila suma todas tus rondas de ese lado: `won_* + lost_* + unknown
  == rounds`. Ronda con `win_condition=""` o `my_team_won` nulo va a
  `unknown`. Test con una ronda de cada caso.
- [ ] "Sin eliminacion" se lee de `win_condition="ObjectiveOrTime"`, que hoy
  siempre llega con `win_condition_certain=False`: la UI lo rotula como
  inferido ("objetivo o tiempo") y nunca lo parte en plant, defuse o tiempo
  (`docs/formato-rec.md`). Test que afirma que la respuesta no trae claves de
  plant ni de defuse.
- [ ] Respeta los filtros de siempre (`map`, `operator`, `side`, `since`,
  `match_type`, `session`): test con dos mapas y `map=` que deja uno.
- [ ] Tendencias muestra el panel "Cómo se cierran tus rondas" con porcentajes
  por lado y la banda de muestra chica que ya usan los paneles vecinos; base
  vacia: estado vacio, sin error en consola. El e2e (`humo.spec.js`) lo ve con
  `seed_demo`.
- [ ] Fila nueva en `docs/metricas.md` con la definicion de cada columna.

## Fuera de alcance

- Separar plant, defuse y tiempo: el `.rec` de temporadas nuevas no lo trae.
- Cruce por mapa o sitio: el filtro `map=` ya lo da; una tabla mapa x lado
  seria otra ficha.
- Cambiar como `metrics.py` calcula `win_condition`.

## Diseno

(arquitecto 20261014T1012Z, sobre main 3438ab2)

Filtros duros: pasa. Lee `Round.win_condition` y `Round.my_team_won`, que la
ingesta ya guarda (`metrics.py:226-235`); no hay red, ni dependencia, ni
migracion, ni datos que el `.rec` no traiga. "Sin eliminacion" nunca se parte en
plant, defuse o tiempo.

**Archivos y por que:**

- `backend/replays/analytics/aggregates.py`: `round_endings(**filters)` al
  lado de `by_score_state`. Parte de `base_queryset(**filters)` (asi respeta
  `map`, `operator`, `side`, `since`, `match_type`, `session` sin codigo
  propio) y agrega por `side` con un solo `.values("side").annotate(...)`:
  - `won_elimination`: `Count("id", filter=Q(round__my_team_won=True, round__win_condition="KilledOpponents"))`
  - `won_other`: lo mismo con `"ObjectiveOrTime"`
  - `lost_elimination` / `lost_other`: lo mismo con `round__my_team_won=False`
  - `rounds`: `Count("id")`
  - `unknown = rounds - (las cuatro)`, calculado en Python: cubre
    `my_team_won` nulo, `win_condition=""` y cualquier valor futuro. Asi
    la suma cierra por construccion.
  Se usa `round__my_team_won` y no `RoundPlayer.won`, porque `won` es `False`
  cuando la ronda no tiene ganador y la mandaria a perdidas.
  Salida, dos filas en orden fijo `("Attack", "Defense")` (constante
  `LADOS_CIERRE`), aunque una tenga 0 rondas, con:
  `side, rounds, won_elimination, won_other, lost_elimination, lost_other,
  unknown, won_elimination_pct, lost_elimination_pct`.
  `won_elimination_pct = _pct(won_elimination, won_elimination + won_other)`
  (de tus ganadas con dato, cuantas fueron por eliminacion); igual para
  `lost_elimination_pct`. Las rondas sin `side` (`""`) no entran en ninguna
  fila: es el mismo criterio que `by_map`.
- `backend/replays/views.py`: `"round_endings": agg.round_endings(**filters)`
  en `trends`. GET, lectura, sin parametro nuevo.
- `frontend/src/pages/Trends.jsx`: panel **"Cómo se cierran tus rondas"**
  justo despues de "Según el marcador". Usa `DataTable` directo (no
  `TablaDeCorte`, que tiene columnas fijas de rendimiento), columnas: Lado
  (`LADOS`), Rondas, "Ganadas por eliminación" (`won_elimination_pct` con
  `%` y el conteo en el `help`), "Ganadas sin eliminación", "Perdidas por
  eliminación", "Perdidas sin eliminación", "Sin dato". Las dos columnas
  "sin eliminación" llevan `help: 'Objetivo o tiempo: el .rec de temporadas
  nuevas no separa plant, defuse ni tiempo agotado; se infiere del reloj.'`.
  Los conteos se muestran como numeros; los porcentajes, como el
  `*_elimination_pct` (sin eliminacion = 100 - ese, calculado en el front
  solo si el pct no es `null`). `csvName="como-se-cierran"`. Hint con
  `filasConPocaMuestra` igual que los paneles vecinos; texto sin muestra
  chica: `'Si en defensa pierdes casi todo por eliminación, el problema son
  los duelos; si pierdes sin eliminación, es el tiempo o el objetivo.'`. Se
  oculta si las dos filas tienen 0 rondas.
- `frontend/src/cierres.js` (nuevo) + `frontend/src/cierres.test.js`: la
  funcion pura `filasDeCierre(filas)` que arma las filas de la tabla
  (etiqueta, porcentajes complementarios, `null` cuando no hay dato). Asi la
  logica tiene test en vitest sin montar la pagina.
- `frontend/e2e/humo.spec.js`: test `Tendencias muestra como se cierran tus
  rondas`: el panel es visible, tiene las celdas `Ataque` y `Defensa`, y la
  consola queda limpia. `seed_demo` no se toca: todas sus rondas son
  `KilledOpponents`, asi que el e2e no afirma porcentajes; los numeros los
  cubren los tests de backend.
- `backend/tests/test_cierres.py` (nuevo).
- `docs/metricas.md`: fila **"Como se cierran tus rondas"** en
  `## Contexto de la ronda`, debajo de "Segun el marcador".

**Tests (backend, `test_cierres.py`, con `factories.py`; `make_round` fija
`win_condition="KilledOpponents"`, asi que los casos de otra condicion hacen
`Round.objects.filter(pk=rnd.pk).update(win_condition=..., win_condition_certain=False)`):**

- `test_una_ronda_ganada_por_eliminacion_en_ataque_suma_solo_ahi`
- `test_las_dos_filas_salen_en_orden_fijo_aunque_una_este_vacia`
- `test_ganada_y_perdida_sin_eliminacion_van_a_other`
- `test_sin_ganador_o_sin_condicion_va_a_unknown` (una ronda con
  `my_team_won=None`, otra con `win_condition=""`)
- `test_cada_fila_suma_todas_tus_rondas_de_ese_lado` (mezcla de los cinco
  casos; `won_* + lost_* + unknown == rounds`)
- `test_la_respuesta_no_trae_claves_de_plant_ni_de_defuse` (por
  `/api/trends/`: ninguna clave de las filas contiene `plant` ni `defuse`)
- `test_el_filtro_de_mapa_deja_solo_las_rondas_de_ese_mapa`
- `test_los_porcentajes_son_nulos_sin_rondas_ganadas_o_perdidas`

Frontend (`cierres.test.js`): `filasDeCierre` etiqueta los lados, deja
`null` los porcentajes sin dato y el complemento suma 100.

**Orden:** aggregates + tests de backend -> vista -> `cierres.js` + vitest ->
panel -> e2e -> `metricas.md`.

**Que puede romperse:** el contrato de `/api/trends/` crece con una clave;
nada la consume todavia. Si alguien filtra por `side=`, la otra fila sale en
0 rondas: es lo esperado y el panel la muestra vacia.

**Fila de `metricas.md`** (texto sugerido): "Rondas tuyas de cada lado segun
como terminaron. *Por eliminacion*: el equipo perdedor termino con todos
muertos (`KilledOpponents`). *Sin eliminacion*: hubo ganador sin que nadie
quedara eliminado del todo; el `.rec` de temporadas nuevas no dice si fue
plant, defuse o tiempo, asi que es inferido y nunca se separa. Un plant
seguido de la eliminacion de los atacantes y un defuse cuenta como
eliminacion. *Sin dato*: ronda sin ganador o sin condicion. Los porcentajes
son sobre tus ganadas (o perdidas) con dato. Las cinco columnas suman todas
tus rondas de ese lado."

**Verificacion manual:** `seed_demo`, `/tendencias`, el panel aparece con
Ataque y Defensa al 100 % por eliminacion. Con una base real, mirar que
Defensa tenga perdidas sin eliminacion (rondas perdidas por plant).

**Umbral:** ninguno nuevo; usa `MUESTRA_CORTE`.

## Implementacion

## Para el humano
