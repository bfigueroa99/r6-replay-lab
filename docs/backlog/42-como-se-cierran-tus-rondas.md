# 42. Como se cierran tus rondas: por eliminacion o sin ella, por lado

estado: aprobado
candado: release 2026-10-14T14:12Z
rama: claude/equipo-dev/42-como-se-cierran-tus-rondas
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B6 (idea del PO 20261013T0511Z); epica lado-y-marcador en curso (B1, B4 y B2 tramo 1 en main por #25, 39 y 41)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_cierres.py, frontend/src/pages/Trends.jsx, frontend/src/cierres.js, frontend/src/cierres.test.js, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T0911Z, arquitecto 20261014T1012Z, dev 20261014T1115Z, revisor 20261014T1211Z, qa 20261014T1312Z

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

(dev 20261014T1115Z)

Quedo todo el diseno, sin desvios de `archivos:`:

- `aggregates.round_endings(**filters)` con `LADOS_CIERRE = ("Attack", "Defense")`,
  un solo `values("side").annotate(...)` sobre `base_queryset`, `unknown` por
  resta y los dos `*_elimination_pct`. Va en `/api/trends/` como
  `round_endings`.
- `frontend/src/cierres.js`: `filasDeCierre` (etiqueta, complementos exactos y
  `vista` con los enteros que se muestran) y `hayCierres` (oculta el panel si
  los dos lados tienen 0 rondas).
- Panel "Cómo se cierran tus rondas" despues de "Según el marcador", con
  `DataTable`, porcentaje y conteo entre parentesis en cada celda, `help` de
  objetivo o tiempo en las dos columnas sin eliminacion, hint de muestra chica
  y CSV `como-se-cierran`.
- Tests: `backend/tests/test_cierres.py` (los 8 del diseno mas
  `test_base_vacia_y_filtros_raros_dan_200_con_dos_filas_en_cero`),
  `cierres.test.js` (6) y e2e `Tendencias muestra como se cierran tus rondas`.
- Fila en `docs/metricas.md` (Contexto de la ronda) y el corte agregado a la
  fila de muestra minima.

Detalles que el diseno no fijaba:

- Los porcentajes en pantalla son enteros y el de "sin eliminacion" es
  `100 - round(eliminacion)`: redondear 87,5 y 12,5 por separado daba 101 %
  (hallazgo de la revision ciega). El CSV lleva el valor exacto con un decimal
  y el conteo, p. ej. `87,5 (7)`.
- El conteo va dentro de la celda y no en el `help` (el `help` es por columna).

Revision ciega previa: 3 hallazgos (101 % en pantalla, CSV sin conteos, lineas
en blanco en `aggregates.py`), los tres corregidos.

## Revision 2026-10-14 sobre 3b0d7df

(revisor 20261014T1211Z; rama al dia con main 3438ab2, sin merge necesario)

Revision a ciegas (subagente con `revision.md` sobre el diff sin
`docs/backlog`): sin hallazgos. Confirmado por el lider:

- `Round.win_condition` solo toma `KilledOpponents`, `ObjectiveOrTime` o `""`
  al importar (`metrics.py:227-234`); `DefusedBomb`, `Time` y
  `DisabledDefuser` de `pydissect` no llegan a la base, asi que las cuatro
  cuentas mas `unknown` por resta cubren todo.
- `round__my_team_won` en vez de `won`: `test_sin_ganador_o_sin_condicion_va_a_unknown`
  falla si se cuenta con `won` (lo manda a perdidas), asi que prueba lo que dice.

Criterios de aceptacion:

- [x] `round_endings` en `/api/trends/` con las cinco cuentas y `rounds`:
  `test_una_ronda_ganada_por_eliminacion_en_ataque_suma_solo_ahi`.
- [x] Cada fila suma sus rondas; `""` y `my_team_won` nulo a `unknown`:
  `test_cada_fila_suma_todas_tus_rondas_de_ese_lado`, `test_sin_ganador_o_sin_condicion_va_a_unknown`.
- [x] Sin claves de plant ni defuse, rotulo "objetivo o tiempo" en la UI:
  `test_la_respuesta_no_trae_claves_de_plant_ni_de_defuse` y `SIN_ELIMINACION` en `Trends.jsx`.
- [x] Filtros: `test_el_filtro_de_mapa_deja_solo_las_rondas_de_ese_mapa`
  (agregado y API); el resto sale de `base_queryset`.
- [x] Panel en Tendencias despues de "Según el marcador", con banda de muestra
  chica; base vacia lo oculta como a los vecinos
  (`test_base_vacia_y_filtros_raros_dan_200_con_dos_filas_en_cero`); e2e
  `Tendencias muestra como se cierran tus rondas` en verde.
- [x] Fila en `docs/metricas.md` (Contexto de la ronda) y el corte en la tabla
  de muestra minima.

Diff dentro de `archivos:`. Identificadores y comentarios sin tildes, UI con
tildes, sin `print` ni `console.log`. Merge de prueba con la 44: limpio.

`check.sh` en verde sobre 1f70ae1 (ruff, 529 tests backend, 75 vitest, build,
30 e2e).

Veredicto: aprobar -> `revisado`.

## QA 2026-10-14 sobre 00b6007

(qa 20261014T1312Z; rama al dia con main 3438ab2, sin merge necesario)

`check.sh` completo en verde sobre 00b6007 (ruff, 529 tests backend, 75 vitest,
build, 30 e2e).

Base sembrada (script en el scratchpad; `win_condition` y `my_team_won`
puestos con `update`, como en `test_cierres.py`): partida Club House con
ataque 2 ganadas por eliminacion, 1 ganada `ObjectiveOrTime`, 1 perdida por
eliminacion y defensa 1 perdida `ObjectiveOrTime`, 1 ganada por eliminacion,
1 con `my_team_won=None` y 1 con `win_condition=""`; partida Border Unranked
del 09-03 con defensa 3 perdidas sin eliminacion y 1 ganada, y una ronda de
ataque con un companero de nick parecido (`BearF99x`) sin bajas.

```bash
cd backend
DATA_DIR=<tmp> SQLITE_PATH=<tmp>/s.sqlite3 python3 manage.py migrate
DATA_DIR=<tmp> SQLITE_PATH=<tmp>/s.sqlite3 python3 manage.py shell -c "exec(open('<tmp>/sembrar.py').read())"
DATA_DIR=<tmp> SQLITE_PATH=<tmp>/s.sqlite3 python3 manage.py runserver 127.0.0.1:8042 --noreload
curl -s '127.0.0.1:8042/api/trends/?<q>' | python3 -c "import json,sys; print(json.load(sys.stdin)['round_endings'])"
```

- [x] `round_endings` con una fila por lado y las cinco cuentas mas `rounds`.
  Sin filtros: Ataque 5 rondas (3/1/1/0, sin dato 0, 75 % y 100 %), Defensa 8
  (2/0/0/4, sin dato 2, 100 % y 0 %). Coincide con lo sembrado; el companero
  no entra.
- [x] Cada fila suma: 3+1+1+0+0 = 5 y 2+0+0+4+2 = 8; `None` y `""` cayeron en
  sin dato.
- [x] Sin claves de plant ni defuse en la respuesta; en la UI las dos
  columnas "sin eliminacion" llevan el `title` "Objetivo o tiempo: ... se
  infiere del reloj".
- [x] Filtros: `map=club-house` (Ataque 4, Defensa 4 con 2 sin dato),
  `map=border` (Ataque 1, Defensa 4), `side=Defense` (Ataque en 0 con
  porcentajes `null`), `since=2026-09-02`, `match_type=Unranked` y
  `session=0` (solo Border), `operator=Mute` y `since=2030-01-01` (las dos
  filas en 0). `until=foo`, `page=-1`, `map=`: 200 con los numeros sin filtrar.
  Base vacia: 200, dos filas en 0 y porcentajes `null`.
- [x] Panel en Tendencias con la base sembrada (Chromium, captura en el
  scratchpad): `Ataque 5 | 75% (3) | 25% (1) | 100% (1) | 0% (0) | 0`,
  `Defensa 8 | 100% (2) | 0% (0) | 0% (0) | 100% (4) | 2`, banda de muestra
  chica visible, consola sin errores. e2e `Tendencias muestra como se cierran
  tus rondas` en verde con `seed_demo`.
- [x] Fila en `docs/metricas.md` (Contexto de la ronda) y corte en la tabla
  de muestra minima.

Mutacion (`python3 manage.py test tests.test_cierres` y `npx vitest run
src/cierres.test.js`): contar con `won` en vez de `round__my_team_won` ->
caen `test_sin_ganador_o_sin_condicion_va_a_unknown` y
`test_cada_fila_suma_*`; `won_other` contando `KilledOpponents` -> caen 3;
`unknown` fijo en 0 -> caen 2; en `cierres.js` el complemento con
`Math.round(100 - pct)` (el 101 %) -> cae `los enteros que se muestran suman
100 aunque el porcentaje termine en ,5`; complemento `0` sin dato -> cae 1.
Sacar `.filter(side__in=LADOS_CIERRE)` no hace caer nada, pero es un mutante
equivalente: el bucle solo lee `Attack` y `Defense`.

Chunk inicial (`vite build`): `index-*.js` 185,47 kB, igual que main. El
panel vive en el chunk perezoso de Tendencias: 14,6 kB -> 16,6 kB.

Sin migracion, `recompute`, parser, Electron ni `.ps1`: no hay `## Verificar
en el PC`. Sin umbral nuevo (usa `MUESTRA_CORTE`).

Veredicto: `aprobado`.

## Para el humano
