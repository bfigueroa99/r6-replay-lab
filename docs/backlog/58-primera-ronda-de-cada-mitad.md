# 58. Primera ronda de cada mitad

estado: aprobado
candado: -
rama: claude/equipo-dev/58-primera-ronda-de-cada-mitad
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 2
fuente: ALCANCE.md B8
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_mitades.py, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0325Z, arquitecto 20261019T0404Z, dev 20261020T1205Z, revisor 20261020T1604Z, qa 20261020T2004Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Siege no hay ronda de pistola, pero la primera ronda de cada lado se
juega sin informacion y marca el tono de la mitad. Con esta tabla se ve si
arrancas frio: tu winrate y rating en la ronda 1 y en la primera ronda
despues del cambio de lado, contra el resto de tus rondas.

## Criterios de aceptacion

- [ ] Agregado nuevo `by_half_opener` en `replays/analytics/aggregates.py`,
  servido en `/api/trends/` como `by_half_opener`: tres filas en orden fijo
  (`match_start`, `side_switch`, `rest`) con las metricas de `totals()`
  (rondas, ganadas, winrate, rating, KPR, aperturas). `match_start` = la
  ronda sin prorroga de numero mas bajo de la partida (la misma que lee
  `_lado_inicial`); `side_switch` = la ronda sin prorroga de numero mas bajo
  cuyo `my_side` difiere del lado inicial; `rest` = todas tus demas rondas
  sin prorroga con lado. Las rondas de prorroga no entran en ninguna fila.
  Test de Django con una partida armada (6 rondas, cambio en la 4): la 1 cae
  en `match_start`, la 4 en `side_switch` y las otras 4 en `rest`.
- [ ] La ronda de apertura se lee de la partida entera, como en `by_half`:
  con `?side=defense` la fila `match_start` solo cuenta las partidas que
  arrancaste en defensa, pero cual es la primera ronda no cambia. Test con
  `?side=`.
- [ ] Una partida sin lado inicial (todas sus rondas con `my_side` vacio) no
  aporta a ninguna fila, ni da 500. Test con base vacia y con esa partida.
- [ ] En Tendencias, dentro del panel "Por mitad de la partida", una tabla
  "Primera ronda de cada lado" con las tres filas ("Ronda 1", "Primera tras
  el cambio", "Resto"), las mismas columnas que la tabla de mitades, boton
  CSV y el aviso de muestra chica que ya usa el panel. Entra al e2e con los
  datos de `seed_demo` (las tres filas visibles y consola limpia).
- [ ] Fila nueva en `docs/metricas.md` ("Primera ronda de cada lado") con la
  definicion exacta y la misma advertencia de `.rec` faltantes que tiene
  "Primera / segunda mitad".

## Fuera de alcance

- La primera ronda de la prorroga: es otra ronda de decision y ya la cubre
  la fila "Prorroga" de la tabla de mitades.
- Mirar el marcador (`score_before`) para corregir partidas con `.rec`
  faltantes: es la mejora anotada en la ficha 36 y vale para las dos tablas
  a la vez; ficha aparte.
- Una señal del Coach sobre la ronda 1.

## Diseno

Arquitecto 20261019T0404Z. Chico (~150 lineas con tests), sin migracion. Toca
`aggregates.py`, `views.py`, `Trends.jsx`, `humo.spec.js` y `metricas.md`, que
tambien tocan 55 y 60: son agregados en lugares distintos de cada archivo, el
conflicto posible es de contexto y se resuelve a mano.

### Backend

`backend/replays/analytics/aggregates.py`, justo debajo de `by_half` (reusa
`_lado_inicial` y `_filas_por_tramo`):

```python
#: Orden fijo de las filas de `by_half_opener`.
APERTURAS_DE_MITAD = ("match_start", "side_switch", "rest")

def _primera_ronda(match_ref: str) -> Subquery: ...
def _primera_tras_el_cambio(match_ref: str, lado_ref: str) -> Subquery: ...
def by_half_opener(**filters) -> list[dict]: ...
```

- `_primera_ronda`: `Round.objects.filter(match_id=OuterRef(match_ref), overtime_number=0).order_by("number").values("number")[:1]`
  (la misma ronda que lee `_lado_inicial`).
- `_primera_tras_el_cambio`: igual, mas `.exclude(my_side="").exclude(my_side=OuterRef(lado_ref))`.
  `lado_ref` es la anotacion `lado_inicial` del queryset de afuera: anotar
  primero `lado_inicial` y despues esta subquery.
- `by_half_opener`: arma `con_lado` exactamente como `by_half` (sin
  prorroga, con `lado_inicial` no nulo ni vacio, `round__my_side` no vacio),
  anota `primera=_primera_ronda("round__match_id")` y
  `cambio=_primera_tras_el_cambio("round__match_id", "lado_inicial")`, y:
  - `match_start`: `con_lado.filter(round__number=F("primera"))`
  - `side_switch`: `con_lado.filter(round__number=F("cambio"))` (una partida
    sin cambio de lado deja `cambio` nulo y no aporta)
  - `rest`: `con_lado.exclude(round__number=F("primera")).exclude(round__number=F("cambio"))`
    — ojo: `exclude` con `F` sobre un nulo en SQLite descarta la fila;
    usar `.filter(~Q(round__number=F("cambio")) | Q(cambio__isnull=True))`
    para que las partidas sin cambio sigan sumando a `rest`.
  - `return _filas_por_tramo("opener", {t: tramos[t] for t in APERTURAS_DE_MITAD})`.
- `backend/replays/views.py`, `trends`: `"by_half_opener": agg.by_half_opener(**filters)`
  debajo de `by_half`.

### Frontend

`frontend/src/pages/Trends.jsx`, dentro del Panel "Por mitad de la partida",
entre la tabla de mitades y el `<h3>Según el lado con que arrancas`:

- Constante `APERTURAS = { match_start: 'Ronda 1', side_switch: 'Primera tras el cambio', rest: 'Resto' }`
  junto a `MITADES`; `const porApertura = (data.by_half_opener ?? []).map((row, orden) => ({ ...row, orden, tramo: APERTURAS[row.opener] || row.opener }))`.
- `<h3 style={{ margin: '16px 0 8px' }}>Primera ronda de cada lado</h3>`, un
  `DataTable` con las mismas columnas que la de mitades,
  `rowKey={(row) => row.opener}`, `csvName="primera-ronda-de-cada-lado"`.
- Debajo, el aviso de muestra chica como lo usa el panel de ronda anterior
  (`filasConPocaMuestra(porApertura).length ? <p className="note">Ojo: alguna fila tiene menos de {MUESTRA_CORTE} rondas; la diferencia puede ser varianza.</p> : null`).
  `match_start` y `side_switch` tienen una ronda por partida: con pocas
  partidas el aviso va a salir casi siempre, y esta bien.

### Docs

`docs/metricas.md`, seccion `## Mitades y prorroga`, fila nueva debajo de
**Lado inicial**: **Primera ronda de cada lado** — Ronda 1: tu ronda sin
prorroga de numero mas bajo; Primera tras el cambio: la ronda sin prorroga de
numero mas bajo cuyo lado no es el inicial; Resto: tus demas rondas sin
prorroga con lado. La prorroga no entra. Se lee de la partida entera (el
filtro de lado limita las rondas, no cual es la primera). Misma advertencia:
si faltan los `.rec` del arranque, la primera ronda que quedo se lee como
"Ronda 1".

### Tests

En `backend/tests/test_mitades.py` (reusa `_partida`, con `primera=1`), clase
nueva `PrimeraRondaTests`:

- `test_seis_rondas_con_cambio_en_la_cuatro_dan_uno_uno_y_cuatro`
  (lados `A A A D D D`: R1 en `match_start`, R4 en `side_switch`, 4 en `rest`).
- `test_la_prorroga_no_cae_en_ninguna_fila` (`prorroga=2`, los totales no cambian).
- `test_el_filtro_de_lado_no_cambia_cual_es_la_primera` (`side="Defense"`:
  `match_start` 0 rondas, `side_switch` 1, `rest` 2).
- `test_una_partida_sin_cambio_de_lado_suma_al_resto` (todo `Attack`:
  `side_switch` 0, `rest` = n - 1).
- `test_una_partida_sin_lado_inicial_no_aporta` (rondas con `side=""`) y
  `test_base_vacia_da_tres_filas_en_cero`.
- Por API: `test_trends_trae_by_half_opener_en_orden_fijo` (`/api/trends/`,
  las tres claves en orden).

`frontend/e2e/humo.spec.js`: ampliar `Tendencias muestra la tabla por mitad`
(o test hermano) con las celdas `Ronda 1`, `Primera tras el cambio` y `Resto`
visibles en el panel. En `seed_demo` el lado alterna cada ronda, asi que la
primera tras el cambio es R2: las tres filas tienen rondas.

### Orden

Agregado + tests de Django, vista, UI, e2e, docs, `check.sh`.

### Que puede romperse

- El `exclude` con `F` sobre nulo (arriba): sin el `Q` las partidas sin
  cambio desaparecen de `rest` en silencio. El test de "sin cambio" lo cubre.
- `OuterRef` a una anotacion del queryset de afuera: anotar en dos
  `.annotate()` seguidos, `lado_inicial` primero.

### Verificacion manual

`seed_demo --force`, `/api/trends/` trae `by_half_opener` con 3 filas y
`match_start.rounds` = cantidad de partidas del seed; Tendencias muestra la
tabla debajo de las mitades.

## Implementacion

Dev 20261020T1205Z. Quedo todo el diseno, sin desvios de alcance.

- `aggregates.py`: `APERTURAS_DE_MITAD`, `_primera_ronda`,
  `_primera_tras_el_cambio` y `by_half_opener` debajo de `by_half`, con el
  `~Q(...) | Q(cambio__isnull=True)` para que las partidas sin cambio sigan
  sumando a `rest`. `views.py`: `by_half_opener` en `/api/trends/`.
- `Trends.jsx`: tabla "Primera ronda de cada lado" dentro del panel de
  mitades, con CSV y el aviso de muestra chica. Desvio menor: las columnas de
  la tabla de mitades pasaron a una constante `COLUMNAS_POR_TRAMO` que usan
  las dos tablas, en vez de duplicar el arreglo.
- Tests (`test_mitades.py`, clase `PrimeraRondaTests`, 9): los 7 del diseno,
  mas `test_la_primera_ronda_es_la_mas_baja_aunque_no_sea_la_uno` y
  `test_una_ronda_sin_lado_no_es_el_cambio` (de la revision ciega). El test
  de API usa `?side=Defense` y cubre el criterio 2 por la vista.
  Mutaciones probadas: sin `.exclude(my_side="")` en el cambio cae
  `test_una_ronda_sin_lado_no_es_el_cambio`; con `exclude(F("cambio"))` en
  vez del `Q` cae `test_una_partida_sin_cambio_de_lado_suma_al_resto`.
- e2e: `Tendencias muestra la tabla por mitad` afirma el titulo y las celdas
  `Ronda 1`, `Primera tras el cambio` y `Resto`.
- `docs/metricas.md`: fila "Primera ronda de cada lado" debajo de "Lado
  inicial", con la advertencia de `.rec` faltantes del arranque y del cambio.

Revision ciega (subagente con `revision.md`): aprobar, dos hallazgos menores
(test de ronda sin lado entre arranque y cambio; doc del `.rec` faltante en
el cambio), los dos corregidos.

## Revision 2026-10-20 sobre 3c91fb2

Revisor 20261020T1604Z. Revision ciega (subagente con `revision.md` sobre el
diff sin `docs/backlog`) y despues contra la ficha. main ya estaba fusionado.

- [test] frontend/e2e/humo.spec.js:57 (menor, no bloquea)
  Que pasa: el comentario dice que las tres filas tienen rondas, pero el e2e
  solo afirma que estan las celdas de etiqueta, que salen igual con 0 rondas.
  Como reproducirlo o por que es cierto: si `by_half_opener` devolviera
  `rounds=0` en las tres filas, la tabla se dibuja igual y el e2e pasa.
  Arreglo sugerido: afirmar que la celda Rondas de cada fila no es 0, o
  sacar esa afirmacion del comentario. El backend ya lo cubre con
  `test_seis_rondas_con_cambio_en_la_cuatro_dan_uno_uno_y_cuatro`.

Contra la ficha:
- Criterio 1 (agregado y orden fijo): `test_seis_rondas_con_cambio_en_la_cuatro_dan_uno_uno_y_cuatro`,
  `test_la_prorroga_no_cae_en_ninguna_fila`, `test_trends_trae_by_half_opener_en_orden_fijo`.
- Criterio 2 (`?side=`): `test_el_filtro_de_lado_no_cambia_cual_es_la_primera` y el test de API con `?side=Defense`.
- Criterio 3 (sin lado inicial, base vacia): `test_una_partida_sin_lado_inicial_no_aporta`, `test_base_vacia_da_tres_filas_en_cero`.
- Criterio 4 (UI y e2e): tabla, CSV y aviso de muestra en `Trends.jsx`; e2e `Tendencias muestra la tabla por mitad` (ver hallazgo menor).
- Criterio 5: fila en `docs/metricas.md` con la advertencia de `.rec` faltantes.
- Diff dentro de `archivos:`; el desvio (`COLUMNAS_POR_TRAMO` compartida) esta explicado en Implementacion.
- Sin tildes en identificadores, UI con tildes, sin `print` ni `console.log`.

`check.sh`: Todo en verde (720 tests backend, 115 frontend, build ok, 44 e2e).

Veredicto: aprobar.

## QA 2026-10-20 sobre 41b208c

QA 20261020T2004Z. Ejercite la app, no relei el diff. Bases en el scratchpad
(`SQLITE_PATH` y `R6_ENV_FILE` apuntando ahi; nada al repo).

- **check.sh**: `./scripts/check.sh` -> `Todo en verde.` antes y despues de
  agregar el test de borde (721 tests backend, 115 frontend, build ok, 44 e2e).
- **Base sembrada desde `factories.py`** (script `sembrar.py`): partida A
  `A A A D D D` + 2 de prorroga; partida B toda en defensa numerada desde 0;
  partida C sin lado; partida D `D, "", D, A, A` con un segundo jugador
  `BearF99x` y rondas sin bajas. Esperado a mano: 3 / 2 / 9.
  `python3 manage.py runserver 8811` y `curl /api/trends/<params>`:
  - sin filtros: `match_start 3, side_switch 2, rest 9` (= 14 rondas sin prorroga con lado; la prorroga no entra). OK.
  - `?side=Defense`: `2, 1, 6`; `?side=Attack`: `1, 1, 3` (la primera no cambia con el filtro). OK.
  - `?map=bank` (partida sin cambio): `1, 0, 3`; `?map=Oregon`, `?side=foo`, `?since=2030-01-01`, `?session=foo`: tres filas en 0, winrate `null`. OK.
  - `?until=foo`, `?days=abc`, `?page=-1`, `?side=&map=&until=`, `?operator=Zofia`, `?ranked_only=1`: 200, mismos numeros que sin filtro.
  - Base vacia (`runserver 8812`): `/api/trends/`, `?side=Defense`, `?until=foo` -> 200, tres filas en 0.
  - `/api/summary/`, `/api/matches/`: 200. Cero 500 en los dos logs.
- **seed_demo** (`seed_demo --force` en base temporal): 29 partidas;
  `match_start 29, side_switch 29, rest 145`, que suman las 203 rondas de
  `by_half` (116 + 87). Las tres filas del e2e tienen rondas: el comentario
  que marco el Revisor es cierto con estos datos.
- **Bundle**: chunk inicial `index-*.js` 187.63 kB en main y en la rama (sin
  cambio); `Trends-*.js` 23.80 -> 24.36 kB (lazy).
- **Mutaciones** sobre `aggregates.py` (`python3 manage.py test tests.test_mitades`):
  - `match_start` con `F("primera") + 1`: cae `test_una_ronda_sin_lado_no_es_el_cambio`.
  - `rest` sin el `exclude` de la primera: caen 5 tests.
  - `_primera_tras_el_cambio` con `order_by("-number")` (toma la ULTIMA ronda del otro lado): **sobrevivia**; los tests solo cuentan rondas y la R6 tambien es una. Agregue `test_la_fila_del_cambio_es_la_primera_ronda_del_otro_lado_y_no_otra` (solo la R4 se pierde: winrate 100 / 0 / 100); con la mutacion cae, sin ella pasa.
  - `_primera_ronda` sin `overtime_number=0`: sobrevive, pero es equivalente (la prorroga siempre se numera despues de las rondas normales).
- Sin migracion, sin parser, sin Electron ni `.ps1`: no hace falta Verificar en el PC.

Veredicto: aprobado.
