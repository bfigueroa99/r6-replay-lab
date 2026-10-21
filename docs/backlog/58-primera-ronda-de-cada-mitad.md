# 58. Primera ronda de cada mitad

estado: entregado
candado: -
rama: claude/equipo-dev/58-primera-ronda-de-cada-mitad
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 2
fuente: ALCANCE.md B8
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_mitades.py, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0325Z, arquitecto 20261019T0404Z, dev 20261020T1205Z, revisor 20261020T1604Z, qa 20261020T2004Z, release 20261021T0004Z

## PR

Titulo: `[equipo-dev][fullstack] Primera ronda de cada lado en Tendencias`

### Que cambia

Tendencias suma, dentro del panel "Por mitad de la partida", la tabla
"Primera ronda de cada lado": tu winrate, rating, KPR y aperturas en la
ronda 1, en la primera ronda tras el cambio de lado y en el resto de tus
rondas sin prorroga. Sirve para ver si arrancas frio cada mitad.
`/api/trends/` trae el agregado nuevo `by_half_opener`.

### Por que esto y no otra cosa

Ficha 58, tramo de la epica `lado-y-marcador` (ALCANCE.md B8). Se descarto
corregir con `score_before` las partidas con `.rec` faltantes: vale para las
dos tablas de mitades a la vez y va en ficha aparte.

### Como se probo

- `./scripts/check.sh` sobre la rama fusionada con `main` (6c3e640):
  `Todo en verde.` (721 tests backend, 115 frontend, build ok, 44 e2e).
- Tests nuevos en `backend/tests/test_mitades.py`, clase `PrimeraRondaTests`
  (10): seis rondas con cambio en la 4, prorroga fuera, filtro de lado,
  partida sin cambio, partida sin lado inicial, base vacia, primera ronda que
  no es la 1, ronda sin lado entre arranque y cambio, la fila del cambio es
  la primera ronda del otro lado (de QA), y el orden fijo por API.
- e2e: `Tendencias muestra la tabla por mitad` afirma las tres filas.
- QA: `runserver` con base sembrada y vacia, `curl` con filtros borde, cero
  500; mutaciones sobre `aggregates.py` caen los tests.

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser. Chunk inicial sin cambio
(187.63 kB); `Trends-*.js` 23.80 -> 24.36 kB (lazy). Fuera: la primera ronda
de la prorroga, la correccion por marcador y una senal del Coach.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py seed_demo --force; python manage.py runserver
```

Abrir http://127.0.0.1:8000/tendencias: debajo de la tabla de mitades aparece
"Primera ronda de cada lado" con "Ronda 1", "Primera tras el cambio" y
"Resto" (29 / 29 / 145 rondas con el seed). `/api/trends/` trae
`by_half_opener` con esas tres filas.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En Siege no hay ronda de pistola, pero la primera ronda de cada lado se
juega sin informacion y marca el tono de la mitad. Con esta tabla se ve si
arrancas frio: tu winrate y rating en la ronda 1 y en la primera ronda
despues del cambio de lado, contra el resto de tus rondas.

## Criterios de aceptacion

- [x] Agregado nuevo `by_half_opener` en `replays/analytics/aggregates.py`,
  servido en `/api/trends/` como `by_half_opener`: tres filas en orden fijo
  (`match_start`, `side_switch`, `rest`) con las metricas de `totals()`
  (rondas, ganadas, winrate, rating, KPR, aperturas). `match_start` = la
  ronda sin prorroga de numero mas bajo de la partida (la misma que lee
  `_lado_inicial`); `side_switch` = la ronda sin prorroga de numero mas bajo
  cuyo `my_side` difiere del lado inicial; `rest` = todas tus demas rondas
  sin prorroga con lado. Las rondas de prorroga no entran en ninguna fila.
  Test de Django con una partida armada (6 rondas, cambio en la 4): la 1 cae
  en `match_start`, la 4 en `side_switch` y las otras 4 en `rest`.
- [x] La ronda de apertura se lee de la partida entera, como en `by_half`:
  con `?side=defense` la fila `match_start` solo cuenta las partidas que
  arrancaste en defensa, pero cual es la primera ronda no cambia. Test con
  `?side=`.
- [x] Una partida sin lado inicial (todas sus rondas con `my_side` vacio) no
  aporta a ninguna fila, ni da 500. Test con base vacia y con esa partida.
- [x] En Tendencias, dentro del panel "Por mitad de la partida", una tabla
  "Primera ronda de cada lado" con las tres filas ("Ronda 1", "Primera tras
  el cambio", "Resto"), las mismas columnas que la tabla de mitades, boton
  CSV y el aviso de muestra chica que ya usa el panel. Entra al e2e con los
  datos de `seed_demo` (las tres filas visibles y consola limpia).
- [x] Fila nueva en `docs/metricas.md` ("Primera ronda de cada lado") con la
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

Arquitecto 20261019T0404Z. `by_half_opener` debajo de `by_half` en
`aggregates.py` (reusa `_lado_inicial` y `_filas_por_tramo`), con subqueries
`_primera_ronda` y `_primera_tras_el_cambio`; `rest` usa
`~Q(round__number=F("cambio")) | Q(cambio__isnull=True)` para no perder las
partidas sin cambio. Tabla en `Trends.jsx`, fila en `docs/metricas.md`. El
detalle completo queda en `git log`.

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

Revisor 20261020T1604Z, revision ciega con `revision.md` y contra la ficha.
Veredicto: aprobar. Un hallazgo menor (el e2e solo afirma las etiquetas, no
que las filas tengan rondas); QA confirmo con `seed_demo` que las tres filas
tienen rondas (29 / 29 / 145). Cada criterio con test nombrado.

## QA 2026-10-20 sobre 41b208c

QA 20261020T2004Z. `check.sh` en verde (721 backend, 115 frontend, 44 e2e).
Base sembrada (4 partidas, esperado a mano 3 / 2 / 9): sin filtros 3 / 2 / 9;
`?side=Defense` 2 / 1 / 6; `?side=Attack` 1 / 1 / 3; `?map=bank` 1 / 0 / 3;
filtros invalidos o sin datos -> 200 y filas en 0. Base vacia -> 200.
Mutacion `order_by("-number")` en el cambio sobrevivia: agrego
`test_la_fila_del_cambio_es_la_primera_ronda_del_otro_lado_y_no_otra`.
Sin migracion, parser, Electron ni `.ps1`: nada que verificar en el PC.
Veredicto: aprobado.
