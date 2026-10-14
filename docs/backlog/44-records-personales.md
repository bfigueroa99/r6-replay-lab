# 44. Records personales en el Resumen

estado: aprobado
candado: -
rama: claude/equipo-dev/44-records-personales
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E4 (idea del PO 20261013T1915Z); epica progreso en curso (E3 en main por la ficha 40)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_records.py, frontend/src/pages/Dashboard.jsx, frontend/src/records.js, frontend/src/records.test.js, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261014T0911Z, arquitecto 20261014T1012Z, dev 20261014T1115Z, revisor 20261014T1211Z, qa 20261014T1312Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver de un vistazo tus mejores marcas (mejor partida, mas bajas en una
partida y en una ronda, el clutch mas grande, el mejor dia), cada una con un
enlace para volver a mirarla. Marca el techo a superar y saca provecho del
historial acumulado, que es lo que ningun tracker de API tiene ronda por
ronda.

## Criterios de aceptacion

- [ ] Un agregado nuevo en `analytics/aggregates.py` (expuesto en
  `/api/overview/` o en un endpoint GET propio, a eleccion del Arquitecto)
  devuelve, cada uno con `match_id`, fecha, mapa y el valor: mejor rating de
  partida (solo partidas con al menos 6 rondas tuyas), mas bajas en una
  partida, mas bajas en una ronda (con el numero de ronda), 1vX ganado mas
  grande (`one_vx`) y mejor dia por rondas ganadas (con minimo de rondas, el
  dia sin `match_id`). Test con factories que afirma cada record y su
  `match_id`.
- [ ] Empates: gana la partida mas reciente, para que el record cambie cuando
  lo igualas. Test con dos partidas de igual cantidad de bajas.
- [ ] Respeta los filtros de siempre (`map`, `operator`, `side`, `since`,
  `match_type`): test con `map=` que cambia el record de bajas.
- [ ] Base vacia o sin clutches: el record que no existe es `null` (no 500, no
  0 inventado). Test sobre base vacia.
- [ ] El Resumen (`Dashboard.jsx`) muestra el panel "Tus récords" con un
  enlace `/partidas/<id>` en cada uno; el e2e (`humo.spec.js`) lo ve con
  `seed_demo`, sigue un enlace y no ensucia la consola.
- [ ] Fila nueva en `docs/metricas.md` para cada record (que cuenta, minimos y
  desempate).

## Fuera de alcance

- La racha actual: es de PR #14, no se duplica.
- Historial de records (cuando se batio cada uno) o avisos de record nuevo.
- Records de otros jugadores o de compañeros.

## Diseno

(arquitecto 20261014T1012Z, sobre main 3438ab2)

Filtros duros: pasa. Todo sale de columnas que `metrics.py` ya escribe en
`RoundPlayer` (`kills`, `one_vx`, `won`, los del rating) y de `Match`
(`played_at`, `map_name`); se agrega al consultar, como el resto de
`aggregates.py`. Sin migracion, sin red, sin dependencia. No toca la racha
(PR #14).

**Donde se expone:** en `/api/overview/`, clave `records`, agregada en la
**vista** (`views.overview`, igual que `data_health`) y no dentro de
`agg.overview`: `coach.py:44` llama a `agg.overview` y no necesita pagar
estas consultas. El Resumen ya pide `/overview/` y se ahorra una request.

**Archivos y por que:**

- `backend/replays/analytics/aggregates.py`: `personal_records(**filters) ->
  dict` y sus constantes, despues de `recent_form`:
  - `RECORD_MIN_RONDAS_PARTIDA = 6`, `RECORD_MIN_RONDAS_DIA = 20` (unas
    tres partidas: un dia de una sola partida ganada 4-0 no es un record).
  - Base: `qs = base_queryset(**filters)`, `baseline = rating_baseline()`.
  - Por partida: el mismo `qs.values(*_MATCH_FIELDS).annotate(**AGGREGATES)`
    de `recent_form`, pasado por `derive`. Se hace una vez y de ahi salen
    dos records en Python:
    - `best_match_rating`: max de `rating` entre las de `rounds >=
      RECORD_MIN_RONDAS_PARTIDA`; desempate `played_at` mas reciente.
      `value` = rating (2 decimales), mas `rounds`.
    - `most_kills_match`: max de `kills`; desempate el mas reciente;
      `value` = bajas, mas `rounds`. Con 0 bajas en todo: `null`.
  - `most_kills_round`: `qs.filter(kills__gt=0).order_by("-kills",
    "-round__match__played_at", "-round__number").first()`; `value` = bajas,
    mas `round_label` = `f"R{number + 1}"` (la misma etiqueta que
    `views.py:454` usa en el detalle de partida).
  - `biggest_clutch`: `qs.filter(one_vx__gt=0, won=True)` con el mismo orden
    sobre `one_vx`; `value` = X de 1vX, mas `round_label`. Sin clutches:
    `null`.
  - `best_day`: `qs.values("round__match__played_at__date")` con `rounds` y
    `rounds_won`, solo dias con `rounds >= RECORD_MIN_RONDAS_DIA`; max de
    winrate de rondas, desempate mas rondas ganadas y despues el dia mas
    reciente. `value` = winrate (1 decimal), mas `rounds`, `rounds_won` y
    `day` (ISO). Sin `match_id` ni `map`.
  - Cada record con partida: `{"match_id", "played_at" (ISO), "map",
    "value", ...extras}`. Si no hay candidato: `null`. Base vacia: los cinco
    `null`, nunca 0.
  - "El mas reciente gana el empate" es a proposito: igualar tu record lo
    mueve a la partida nueva. Va en `metricas.md`.
- `backend/replays/views.py`: `payload["records"] = agg.personal_records(**filters)` en `overview`.
- `frontend/src/records.js` (nuevo) + `frontend/src/records.test.js`:
  `filasDeRecords(records)` devuelve la lista para el panel en orden fijo
  (mejor partida, mas bajas en una partida, mas bajas en una ronda, clutch
  mas grande, mejor dia), con etiqueta, valor formateado (`1v3`, `5 bajas`,
  `1.62`, `78 %`), detalle (`mapa · fecha` o `ronda R4 · mapa`) y `href`
  (`/partidas/<id>` o `null` para el dia). Deja afuera los `null`. Es logica
  pura y se prueba en vitest.
- `frontend/src/pages/Dashboard.jsx`: panel **"Tus récords"** despues de
  "Ultimas partidas", lista de filas con un `Link` a la partida en las que
  tienen `href`. Si `filasDeRecords` devuelve vacio, el panel no se muestra.
  Hint: `'Tus mejores marcas con los filtros activos. Si igualas una, cuenta
  la más reciente.'`.
- `frontend/e2e/humo.spec.js`: test `el Resumen muestra tus records y enlaza
  a la partida`: el panel "Tus récords" es visible, tiene "Más bajas en una
  partida", se hace clic en su enlace, la URL es `/partidas/\d+$` y el `h1`
  contiene un mapa de `seed_demo` (`/Club House|Border|Bank/`, como el test
  del detalle); consola limpia. `seed_demo` no se toca: tiene clutches
  (`indice % 17 == 0`), partidas de 7 rondas y dias con mas de 20 rondas.
- `backend/tests/test_records.py` (nuevo).
- `docs/metricas.md`: seccion nueva **`## Records`** despues de `## Sesiones`,
  una fila por record.

**Tests (`test_records.py`, con `factories.py`):**

- `test_mejor_rating_ignora_partidas_de_menos_de_seis_rondas`
- `test_mas_bajas_en_una_partida_trae_su_match_id`
- `test_mas_bajas_en_una_ronda_trae_la_etiqueta_de_la_ronda`
- `test_el_clutch_mas_grande_es_el_1vx_ganado_mayor`
- `test_mejor_dia_exige_el_minimo_de_rondas_y_no_trae_partida`
- `test_en_un_empate_gana_la_partida_mas_reciente`
- `test_el_filtro_de_mapa_cambia_el_record_de_bajas`
- `test_base_vacia_devuelve_todos_los_records_nulos`
- `test_sin_clutches_el_record_de_clutch_es_nulo_y_los_demas_no`
- `test_overview_trae_los_records` (por `/api/overview/`)

Frontend (`records.test.js`): orden fijo, `null` fuera, el dia sin `href`,
formato de cada valor.

**Orden:** agregado + tests de backend -> vista -> `records.js` + vitest ->
panel -> e2e -> `metricas.md`.

**Que puede romperse:** `/api/overview/` hace cinco consultas mas; con una
base grande la de por partida es la misma que `recent_form` sin el `limit`.
Es aceptable (se agrega por partida, no por ronda); si QA ve la respuesta
por encima de ~300 ms con 2.000 partidas sinteticas, se anota. Ningun test
existente afirma las claves exactas de `overview`.

**Filas de `metricas.md`** (texto sugerido): *Mejor partida*: rating de
partida mas alto (el de 'Rating') entre las partidas con al menos 6 rondas
tuyas con los filtros activos. *Mas bajas en una partida / en una ronda*:
maximo de bajas tuyas. *Clutch mas grande*: el 1vX ganado de X mas alto.
*Mejor dia*: winrate de rondas mas alto en un dia con al menos 20 rondas;
empata a favor de mas rondas ganadas. En todos, a igual valor gana la
partida (o el dia) mas reciente. Sin candidato, el record no aparece.

**Verificacion manual:** `seed_demo`, `/`, el panel muestra los cinco
records y cada enlace abre su partida; con `?map=Border` cambian.

**Umbrales:** 6 rondas por partida y 20 por dia son a ojo; calibrar con la
base real (a `## QA 2026-10-14 sobre af000a3

(qa 20261014T1312Z; rama al dia con main 3438ab2, sin merge necesario)

`check.sh` completo en verde dos veces: sobre af000a3 y con el e2e reforzado
(ruff, 532 tests backend, 74 vitest, build, 30 e2e).

Base sembrada (script en el scratchpad, `DATA_DIR` y `SQLITE_PATH`
temporales): `build_dataset(matches=12)` del 2026-09-01/02 mas tres partidas a
mano: A Bank 3 rondas con 5 bajas por ronda; B Border 7 rondas con dos rondas
de 4 bajas, un 1v3 ganado (R2) y un 1v4 perdido (R7); C Club House 4 rondas
perdidas sin bajas.

```bash
cd backend
DATA_DIR=<tmp> SQLITE_PATH=<tmp>/q.sqlite3 python3 manage.py migrate
DATA_DIR=<tmp> SQLITE_PATH=<tmp>/q.sqlite3 python3 manage.py shell -c "exec(open('<tmp>/sembrar.py').read())"
DATA_DIR=<tmp> SQLITE_PATH=<tmp>/q.sqlite3 python3 manage.py runserver 127.0.0.1:8044 --noreload
curl -s '127.0.0.1:8044/api/overview/?<q>' | python3 -c "import json,sys; print(json.load(sys.stdin)['records'])"
```

- [x] Cinco records con `match_id`, fecha, mapa y valor (`?` sin filtros):
  mejor partida = B (1.71, 7 rondas; A queda fuera por 3 rondas), mas bajas en
  partida = A (15), mas bajas en ronda = A R3 (5; R1-R3 empatan y gana la
  ronda mas nueva), clutch = B R2 1v3 (el 1v4 perdido no cuenta), mejor dia =
  2026-09-02 (50 %, 48 rondas; empata en winrate con el 09-01 de 24 rondas y
  gana por mas rondas ganadas), sin `match_id`. Coincide con lo calculado a
  mano.
- [x] Empate a la mas reciente: lo de arriba (ronda y dia) y mutacion abajo.
- [x] Filtros: `map=bank` deja A en bajas; `map=border` lleva bajas a B (13);
  `side=Defense` -> bajas B 6, ronda B R6, mejor partida `null` (3 rondas de
  defensa); `since=2026-09-06` -> mejor dia `null`; `until=2026-09-04` ->
  clutch `null`; `operator=Mute` -> solo mejor dia. Ojo: `map=` toma el slug
  (`border`), no el nombre; `map=Border` da todo `null`, igual que el resto de
  la app (comportamiento de main, no de esta ficha).
- [x] Base vacia: los cinco `null`. `until=foo`, `page=-1`, `map=`,
  `since=2030-01-01`, `map=Nada`, `days=999999999999`, `session=abc`,
  `side=Attack&operator=Zofia`: 200 en vacia y en sembrada.
- [x] Panel y enlace: e2e en verde. Reforce el e2e (hallazgo de test de la
  revision): ahora lee `records.most_kills_match` de `/api/overview/` y exige
  `/partidas/<ese id>` y su mapa en el `h1`. Mutacion: con `href` a
  `match_id + 1` el e2e nuevo cae (`expected /partidas/28$`, `received
  /partidas/29`); el original pasaba igual.
- [x] `docs/metricas.md`: seccion `## Records` con cada record, minimos y
  desempate (sigue el hallazgo de ubicacion del Revisor, abajo).

Mutacion sobre `aggregates.py` (`python3 manage.py test tests.test_records`),
las cinco caen: orden de partidas `reverse=False` y orden de rondas sin `-`
en `played_at` -> `test_en_un_empate_gana_la_partida_mas_reciente`; clutch sin
`won=True` -> `test_el_clutch_mas_grande_es_el_1vx_ganado_mayor`; sin minimo
de 6 rondas -> `test_mejor_rating_ignora_partidas_de_menos_de_seis_rondas`;
sin minimo de dia -> `test_mejor_dia_exige_*` y `test_sin_clutches_*`.

Rendimiento (lo que pedia el diseno): 2.000 partidas sinteticas de 7 rondas
(14.000 filas), `/api/overview/` en 0,28-0,30 s; `personal_records` solo,
0,16 s; `agg.overview` 0,12 s. Justo en el borde de ~300 ms: aceptable,
anotado abajo.

Chunk inicial (`vite build`): `index-*.js` 185,47 kB en main -> 186,80 kB
(+0,7 %).

Sin migracion, `recompute`, parser, Electron ni `.ps1`: no hay `## Verificar
en el PC`.

Veredicto: `aprobado`.

## Para el humano` si QA lo confirma solo con sinteticos).

## Implementacion

(dev 20261014T1115Z)

Quedo todo el diseno, sin desvios de `archivos:`:

- `aggregates.personal_records(**filters)` despues de `recent_form`, con
  `RECORD_MIN_RONDAS_PARTIDA = 6` y `RECORD_MIN_RONDAS_DIA = 20`. Por partida
  usa el mismo `values(*_MATCH_FIELDS).annotate(**AGGREGATES)` + `derive` de
  `recent_form`, ordenado de la mas reciente a la mas vieja para que `max()`
  le de el empate a la mas reciente. Ronda y clutch con `order_by` sobre
  `-kills`/`-one_vx`, `-played_at`, `-number`. Mejor dia por
  `played_at__date`, con desempate rondas ganadas y despues dia mas reciente.
  Sin candidato, `None`; sin bajas en ninguna ronda, tambien `None`.
- `views.overview` agrega `records` (en la vista, no en `agg.overview`, para
  que el coach no pague las consultas).
- `frontend/src/records.js` (`filasDeRecords`) + `records.test.js` (5 tests).
- Panel "Tus récords" en el Resumen despues de "Ultimas partidas": tabla
  Récord / Marca / Dónde, con `Link` a `/partidas/<id>` salvo el mejor dia.
- Tests: `backend/tests/test_records.py`, los 10 del diseno mas
  `test_sin_bajas_no_inventa_un_record_de_cero` y
  `test_base_vacia_y_filtros_raros_dan_200_con_records_nulos`; e2e
  `el Resumen muestra tus records y enlaza a la partida`.
- Seccion `## Records` en `docs/metricas.md` despues de `## Sesiones`.

Revision ciega previa: un hallazgo (E501 en `aggregates.py`, dejaba rojo el
lint) y lineas en blanco fuera del estilo; corregidos.

Choque esperado con la 42 (`claude/equipo-dev/42-como-se-cierran-tus-rondas`):
las dos agregan bloques en `aggregates.py`, `views.py`, `humo.spec.js` y
`metricas.md`, en lugares distintos. La que se mergee segunda hace
`git merge origin/main` y queda con los dos bloques.

## Revision 2026-10-14 sobre 1f48922

(revisor 20261014T1211Z; rama al dia con main 3438ab2, sin merge necesario)

Revision a ciegas (subagente con `revision.md` sobre el diff sin
`docs/backlog`): sin bugs; dos hallazgos menores, los dos confirmados por el
lider:

- [estilo] `docs/metricas.md:104-118`
  Que pasa: la seccion `## Records` quedo entre la tabla de Sesiones y su
  parrafo de cierre ("El corte de la 3a partida esta fijo a proposito..."),
  que ahora se lee como si hablara de los records.
  Como reproducirlo: leer la doc justo debajo de la tabla de records.
  Arreglo sugerido: mover `## Records` debajo de ese parrafo, antes de
  `## Cuando juegas`.
- [test] `frontend/e2e/humo.spec.js:150-155`
  Que pasa: el e2e dice "enlaza a la partida" pero pasaria con un enlace a
  cualquier otra partida: afirma `/partidas/\d+$` y un `h1` con
  `Club House|Border|Bank`, que son todos los mapas de `seed_demo`.
  Arreglo sugerido: leer el mapa de la celda "Dónde" antes del clic y
  esperarlo en el `h1`, o comparar el id de la URL con
  `records.most_kills_match.match_id` de `/api/overview/`.

Ninguno cambia un dato que ve el usuario: van al Dev como pendientes si la
ficha vuelve, o al Release para que los arrastre al PR.

Confirmado ademas: empates por orden previo (partidas) y `-played_at,
-number` (rondas); `R{number+1}` igual que el detalle de partida;
`played_at__date` correcto con `USE_TZ=False` y `played_at` no nulo; `one_vx`
con `won=True`.

Criterios de aceptacion:

- [x] `personal_records` en `/api/overview/` (clave `records`) con los cinco
  records, `match_id`, fecha, mapa y valor; el dia sin `match_id`: los
  `test_mejor_rating_*`, `test_mas_bajas_*`, `test_el_clutch_*`,
  `test_mejor_dia_*` y `test_overview_trae_los_records`.
- [x] Empate a la mas reciente: `test_en_un_empate_gana_la_partida_mas_reciente`
  (tres records).
- [x] Filtros: `test_el_filtro_de_mapa_cambia_el_record_de_bajas`.
- [x] Nulos sin candidato, sin 500: `test_base_vacia_devuelve_todos_los_records_nulos`,
  `test_sin_clutches_*`, `test_sin_bajas_no_inventa_un_record_de_cero`,
  `test_base_vacia_y_filtros_raros_dan_200_con_records_nulos`.
- [x] Panel "Tus récords" con enlaces; e2e en verde (ver hallazgo de test:
  sigue el enlace, pero no afirma que sea la partida correcta).
- [x] Seccion `## Records` en `docs/metricas.md` con cada record, minimos y
  desempate (ver hallazgo de estilo sobre su ubicacion).

Diff dentro de `archivos:`. Identificadores y comentarios sin tildes, UI con
tildes, sin `print` ni `console.log`. Merge de prueba con la 42: limpio.

`check.sh` en verde sobre cf60533 (ruff, 532 tests backend, 74 vitest, build,
30 e2e).

Veredicto: aprobar -> `revisado` (hallazgos menores, no bloquean).

## Para el humano

- Umbrales a ojo (6 rondas por partida, 20 por dia): QA los probo solo con
  datos sinteticos; calibrar con la base real.
- `/api/overview/` con 2.000 partidas sinteticas tarda ~0,29 s (los records
  suman ~0,16 s). Si con la base real se siente lento, mover los records a su
  propia request.
- Hallazgo menor del Revisor sin corregir: en `docs/metricas.md` la seccion
  `## Records` quedo entre la tabla de Sesiones y su parrafo de cierre. El
  Release puede moverla al armar el PR.
