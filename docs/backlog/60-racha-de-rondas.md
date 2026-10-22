# 60. Racha de rondas dentro de la partida

estado: revisado
candado: qa 2026-10-22T00:04Z
rama: claude/equipo-dev/60-racha-de-rondas
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B13
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_rachas.py, frontend/src/rachas.js, frontend/src/rachas.test.js, frontend/src/records.js, frontend/src/records.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0325Z, arquitecto 20261019T0404Z, dev 20261021T0404Z, revisor 20261021T0804Z, qa 20261021T1204Z, dev 20261021T1605Z, revisor 20261021T2004Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Un 0-4 seguido dice mas que el 3-4 final: en el detalle de cada partida se
ve la racha mas larga de rondas ganadas y la de perdidas seguidas, y en
Records queda tu mejor racha de rondas de todo el historial con enlace a la
partida.

## Criterios de aceptacion

- [ ] Funcion pura en `replays/analytics/aggregates.py` que recibe las
  rondas de una partida (`number`, `my_team_won`) y devuelve la racha mas
  larga de ganadas y la de perdidas, cada una con la ronda en que empieza.
  Cortan la racha: una ronda con `my_team_won` nulo y un hueco en la
  numeracion (falta un `.rec`). Tests: `G G P G G G` da 3 ganadas desde la
  4 y 1 perdida; `G G (hueco) G` da 2; `G nulo G` da 1.
- [ ] `/api/matches/<id>/` agrega `round_streaks` con `wins` y `losses`
  (`{length, from_round_label}` o `null` si no hay ninguna). Test de Django
  sobre una partida de `seed_demo` o armada.
- [ ] `personal_records` agrega `longest_round_streak`: la racha de rondas
  ganadas mas larga entre tus partidas filtradas, con `match_id`, mapa,
  fecha, `value` y `round_label` de la primera ronda; a igual largo gana la
  partida mas reciente, como los demas records. Test con dos partidas.
- [ ] La UI muestra las dos rachas en el encabezado del detalle de partida
  ("Racha: 4 ganadas desde R3 · 3 perdidas desde R8") y el record nuevo en
  Records ("Racha de rondas", `records.js`) con el enlace de siempre. Entra
  al e2e con `seed_demo` (detalle de una partida y Resumen).
- [ ] Fila nueva en `docs/metricas.md` ("Racha de rondas") con lo que corta
  una racha.

## Fuera de alcance

- La racha de partidas (ganadas o perdidas seguidas): la tiene PR #14.
- Rachas de compañeros o rivales y rachas de prorroga aparte.
- Calcularla al importar: se arma al consultar, sin migracion.

## Diseno

Arquitecto 20261019T0404Z. ~200 lineas con tests, sin migracion (se arma al
consultar). Toca `aggregates.py`, `views.py`, `metricas.md` y `humo.spec.js`
como 55 y 58, en lugares distintos.

### Regla (funcion pura)

`backend/replays/analytics/aggregates.py`, al lado de `_record_de_ronda`:

```python
def rachas_de_rondas(rondas: list[tuple[int, bool | None]]) -> dict:
    """Racha mas larga de rondas ganadas y de perdidas seguidas de una partida."""
```

- Recibe `(number, my_team_won)` en cualquier orden; ordena por `number`.
- Una racha sigue mientras `my_team_won` es igual al anterior **y** el
  `number` es el anterior + 1. Un `None` corta y no empieza racha; un hueco
  en la numeracion corta.
- Devuelve `{"wins": {"length": n, "from_number": k} | None, "losses": ...}`.
  A igual largo gana la primera (la mas temprana de la partida). Sin rondas
  ganadas, `wins` es `None`.
- La prorroga cuenta como cualquier ronda (es la misma partida); `number`
  sigue corriendo en prorroga.

### Detalle de partida

`backend/replays/views.py`, `match_detail`: despues de armar `rounds`,
`rachas = agg.rachas_de_rondas([(r["number"], r["my_team_won"]) for r in rounds])`
y en el payload `"round_streaks": {k: (None if v is None else {"length": v["length"], "from_round_label": f"R{v['from_number'] + 1}"}) for k, v in rachas.items()}`
(o un helper `_racha_con_etiqueta` en la vista, para no repetir el formato).

`frontend/src/pages/MatchDetail.jsx`, en el encabezado (debajo del `<h1>` con
mapa y marcador): `<p className="note">` con el texto que arma una funcion
pura nueva `textoDeRachas(round_streaks)` en `frontend/src/rachas.js`:
`"Racha: 4 ganadas desde R3 · 3 perdidas desde R8"`; singular "1 ganada" /
"1 perdida"; si una es `null` se omite su mitad; si las dos son `null`, no se
muestra el parrafo (devuelve `''`).

### Record

`personal_records`: `ids = qs.values_list("round__match_id", flat=True).distinct()`;
`Round.objects.filter(match_id__in=ids).values_list("match_id", "number", "my_team_won")`,
agrupar por partida en Python, `rachas_de_rondas` por partida y quedarse con
la de `wins` mas larga. Desempate: la partida mas reciente
(`played_at`), igual que los demas records; necesitar el `played_at` y el
mapa del ganador: un `Match.objects.get(pk=...)` solo para el ganador. La
racha se calcula sobre **todas** las rondas de la partida (el filtro elige
partidas, no rondas: con `?side=attack` una racha de solo ataque no existe,
porque los lados alternan). Clave nueva `longest_round_streak` con la misma
forma de `_record_de_ronda`: `match_id`, `played_at`, `map`, `value` (largo)
y `round_label` (primera ronda de la racha). Sin rondas ganadas: `None`.
Constante: no hay umbral; una racha de 1 ya es record.

`frontend/src/records.js`: fila nueva despues de `biggest_clutch`:
`['longest_round_streak', 'Racha de rondas', (r) => \`${r.value} ${r.value === 1 ? 'ronda ganada' : 'rondas ganadas seguidas'}\`]`.
`detalle()` ya arma "ronda R3 · mapa · fecha" con `round_label`: alcanza.

### Docs

`docs/metricas.md`, seccion `## Records`, fila **Racha de rondas**: las
rondas ganadas seguidas mas largas de una partida, sobre todas sus rondas
(prorroga incluida); la cortan una ronda perdida, una ronda sin resultado y un
hueco en la numeracion (falta un `.rec`). El filtro elige partidas, no rondas.
A igual largo, la partida mas reciente. En el detalle de partida se muestran
tambien las perdidas seguidas, con la misma regla.

### Tests

`backend/tests/test_rachas.py` (nuevo):

- Pura: `test_g_g_p_g_g_g_da_tres_ganadas_desde_la_cuatro_y_una_perdida`,
  `test_un_hueco_en_la_numeracion_corta_la_racha` (`G G _ G` -> 2),
  `test_una_ronda_sin_resultado_corta_la_racha` (`G None G` -> 1),
  `test_a_igual_largo_gana_la_primera`, `test_sin_rondas_da_dos_nulos`,
  `test_el_orden_de_entrada_no_importa`.
- API: `test_el_detalle_de_partida_trae_round_streaks` (partida armada con
  factories, `from_round_label` en formato `R<n>`).
- Record: `test_el_record_de_racha_es_la_partida_con_la_racha_mas_larga`
  (dos partidas, 3 y 4 seguidas), `test_a_igual_racha_gana_la_partida_mas_reciente`,
  `test_sin_rondas_ganadas_no_hay_record`.

`frontend/src/rachas.test.js` (nuevo): las dos rachas, singular, una nula,
las dos nulas. `frontend/src/records.test.js`: agregar `longest_round_streak`
al fixture `RECORDS` y al orden esperado (el test de orden fijo hoy lista las
claves: hay que sumarla ahi).

`frontend/e2e/humo.spec.js`: en el test que abre el detalle de una partida,
afirmar el texto `Racha:`; en el del Resumen, la celda `Racha de rondas`. En
`seed_demo` el resultado alterna (ganas las pares), asi que todas las rachas
son de 1: "Racha: 1 ganada desde R1 · 1 perdida desde R2" en cualquier
partida, y el record dice "1 ronda ganada". No cambiar el seed por esto.

### Orden

Funcion pura + tests, detalle de partida, record, frontend (`rachas.js`,
`records.js`, `MatchDetail.jsx`) + vitest, e2e, docs, `check.sh`.

### Que puede romperse

- `records.test.js` verifica el orden fijo de las claves: si no se suma la
  clave nueva, vitest falla (bien).
- `personal_records` con base vacia: `ids` vacio, la clave es `None`, no 500.
- El texto del encabezado no debe romper el `<h1>` que ya busca el e2e.

### Verificacion manual

`seed_demo --force`, abrir cualquier partida: debajo del titulo "Racha: 1
ganada desde R1 · 1 perdida desde R2"; Resumen -> Tus records muestra
"Racha de rondas".

## Implementacion

Dev 20261021T0404Z.

- Hecho segun el diseno, sin desvios de forma: `rachas_de_rondas` en
  `aggregates.py`; `round_streaks` en `/api/matches/<id>/` (helper
  `_racha_con_etiqueta` en la vista); `longest_round_streak` en
  `personal_records` via `_record_de_racha` (una query de rondas por las
  partidas filtradas, una de fechas, un `get` para el ganador); el empate se
  resuelve con `max` sobre `(largo, played_at, match_id)`.
- Frontend: `rachas.js` (`textoDeRachas`) + `rachas.test.js`; fila
  "Racha de rondas" en `records.js` despues del clutch; parrafo `.note` debajo
  del encabezado de `MatchDetail.jsx`.
- Tests backend (`test_rachas.py`, 12): los 6 puros del diseno, 2 de API
  (incluye `losses` nulo), 4 de record (incluye que el filtro de lado elige
  partidas y la racha usa todas sus rondas). `test_records.py`: el test de base
  vacia lista la clave nueva.
- e2e (`humo.spec.js`): el detalle abierto desde la lista afirma "Racha: 1
  ganada desde R1 · 1 perdida desde R2"; el test de records del Resumen
  afirma la fila "Racha de rondas" con "1 ronda ganada".
- `docs/metricas.md`: fila **Racha de rondas** en `## Records`.
- Revision ciega con `revision.md`: sin hallazgos.
- `check.sh`: Todo en verde (733 tests backend, 120 vitest, build ok, 44 e2e).

### Correccion de hallazgos (dev 20261021T1605Z)

- QA (bloqueante, e2e inestable): en `humo.spec.js` la fila "Racha de
  rondas" se afirma antes del clic al enlace del record y se quita el segundo
  `page.goto('/')`, que cortaba el `/api/trends/` en vuelo. Se eligio esto y
  no `networkidle`: no agrega una espera y no recarga. El test repetido 10
  veces: 10 de 10 en verde.
- Revision (menor): `records.js` muestra "desde R3 · mapa · fecha" para
  `longest_round_streak` (la ronda donde empieza la racha), y
  `records.test.js` lo afirma.
- Delta de 10 lineas revisado por el lider; sin revision ciega por subagente
  esta vez (la del diff completo se hizo en la implementacion).
- `check.sh`: Todo en verde (733 tests backend, 120 vitest, build ok, 44 e2e).

## Revision 2026-10-21 sobre 51815b8

Revisor 20261021T0804Z. Revision ciega con `revision.md` (subagente) y
confirmacion del lider.

- Criterios de aceptacion: los cinco cubiertos. Funcion pura con los casos
  del diseno (`G G P G G G`, hueco, nulo, empate, vacio, orden) en
  `test_rachas.py`; `round_streaks` con test de API (incluye `losses`
  nulo); `longest_round_streak` con dos partidas, desempate por fecha
  (fecha intermedia en el indice 2: fallaria si desempatara por id), sin
  ganadas y filtro de lado; UI en `MatchDetail.jsx` y `records.js` con
  vitest y e2e; fila en `docs/metricas.md`.
- Diff dentro de `archivos:` salvo `backend/tests/test_records.py` (una
  linea: la clave nueva en el test de base vacia), explicado en
  Implementacion.
- Etiquetas `R<n>` con `number + 1`, igual que `_record_de_ronda` y el
  detalle de rondas. `played_at` no es nulo: el `max` del desempate no
  rompe. Sin dependencias, sin escrituras, sin tildes en identificadores,
  UI con tildes, sin `print` ni `console.log`.
- Hallazgo menor (no bloquea, no cambia numeros):
  - [estilo] frontend/src/records.js:20 (`detalle`)
    Que pasa: la fila "Racha de rondas" muestra "ronda R3 · mapa · fecha",
    que en "Mas bajas en una ronda" significa la ronda donde paso; aca es la
    ronda donde empieza la racha.
    Como reproducirlo: racha de 5 desde R3 -> "5 rondas ganadas seguidas |
    ronda R3 · Oregon · 2026-09-02"; el detalle de partida dice "desde R3".
    Arreglo sugerido: para `longest_round_streak`, "desde R3 · mapa ·
    fecha" y ajustar `records.test.js` (y el e2e si afirma el detalle).
- `check.sh`: Todo en verde (733 tests backend, 120 vitest, build ok, 44 e2e).

Veredicto: aprobar -> `revisado`. El hallazgo menor puede viajar en esta
entrega si alguien vuelve a tocar la rama, o quedar para despues.

## QA 2026-10-21 sobre 98648c1

QA 20261021T1204Z. Veredicto: **con hallazgos** (un e2e inestable deja
`check.sh` en rojo; la funcionalidad en si esta bien).

### Hallazgo (bloquea: check.sh rojo)

- [e2e] frontend/e2e/humo.spec.js:261 (`el Resumen muestra tus records y enlaza a la partida`)
  Que pasa: el `page.goto('/')` nuevo recarga la pagina mientras el
  `/api/trends/?limit=25` de la primera carga del Resumen sigue en vuelo; la
  navegacion lo corta y `vigilarConsola` anota
  `request fallida: http://127.0.0.1:8099/api/trends/?limit=25 (net::ERR_ABORTED)`.
  Como reproducirlo: `./scripts/check.sh` (fallo en la primera corrida:
  43 passed, 1 failed), o
  `cd frontend && for i in $(seq 1 10); do npx playwright test e2e/humo.spec.js -g "tus records" | grep -E "^\s+1 (passed|failed)"; done`
  -> en esta rama fallo 8 de 16 corridas; con el `humo.spec.js` de
  `origin/main` (sin las dos lineas nuevas) paso 10 de 10.
  Arreglo sugerido (probado en el scratchpad, 12 de 12 en verde): esperar a
  que la primera carga termine antes de recargar:
  ```js
  // seed_demo alterna el resultado ronda a ronda: toda racha es de una
  await page.waitForLoadState('networkidle')
  await page.goto('/')
  ```
  (o afirmar "Racha de rondas" antes de hacer clic en el enlace, sin el
  segundo `goto`). Despues, `check.sh` completo.

### Evidencia por criterio

Base sembrada con `factories.py` (script en el scratchpad, no commiteado):
A `P P G G G G P P P` (Oregon), B `G G _ G G nulo G` (Bank, hueco en el
indice 2), C `P P P` (Border), D sin rondas (Chalet), E `G G G G P` (Villa,
mas reciente que A). `runserver` con esa base y con una base vacia migrada.

- Funcion pura: `curl /api/matches/<id>/`:
  A `wins 4 desde R3, losses 3 desde R7` (2 desde R1 queda atras);
  B `wins 2 desde R1, losses null` (hueco y nulo cortan); C `wins null,
  losses 3 desde R1`; D las dos `null`; id 999 -> 404. OK.
- `round_streaks` en el detalle: formato `{length, from_round_label}` o
  `null`, `R<n>` con `number + 1`. OK.
- `longest_round_streak`: `/api/overview/` -> Villa, 4, R1 (empate 4-4 con
  Oregon: gana la mas reciente). `?side=Attack` -> 4 (el filtro elige
  partidas). `?map=chalet` y `?since=2030-01-01` -> `null`, 200.
  `?until=foo`, `?page=-1`, `?map=` -> 200 sin cambio. Base vacia -> `null`,
  200. (`?side=attack` en minuscula da todo vacio en todos los records: es
  el comportamiento previo del filtro, no de esta ficha.) OK.
- UI: el e2e afirma el parrafo "Racha: 1 ganada desde R1 · 1 perdida desde
  R2" y la fila "Racha de rondas" (pasan cuando el test no se cae por el
  hallazgo de arriba). OK salvo el hallazgo.
- `docs/metricas.md`: fila "Racha de rondas" en `## Records`. OK.
- Mutacion (4 de 4 caen): quitar `numero == anterior[0] + 1` (1 falla en
  `test_rachas`); desempate por id en vez de fecha (1 falla); `>=` en vez
  de `>` en la mejor racha (2 fallan); singular con `=== 0` en `rachas.js`
  (1 falla en vitest).
- Chunk inicial de `vite build`: `index-*.js` 187,63 kB en main -> 187,75
  kB (+0,1 %). `MatchDetail` 9,41 -> 9,75 kB.
- Sin migracion, sin parser, sin Electron ni `.ps1`: no hay `## Verificar en
  el PC`.
- `check.sh`: rojo en e2e por el hallazgo (733 tests backend y vitest en
  verde, build ok, 43 de 44 e2e).

El hallazgo menor de la Revision (`records.js`, "ronda R3" vs "desde R3")
sigue abierto; puede viajar en el mismo arreglo.

## Revision 2026-10-21 sobre 0611577

Revisor 20261021T2004Z (segunda pasada, despues de la correccion del dev
20261021T1605Z). Revision ciega con `revision.md` (subagente) sobre el diff
completo y confirmacion del lider.

- Revision ciega: sin hallazgos (`rachas_de_rondas`, `_record_de_racha`,
  `round_streaks`, `rachas.js`, `records.js`, tests y `metricas.md`).
  Anota que la racha se arma al consultar sobre `Round.my_team_won`, que ya
  se guarda al importar: agregacion como "Mejor dia", no una columna nueva.
- Hallazgo de QA (e2e inestable): resuelto. La fila "Racha de rondas" se
  afirma antes del clic y sin el segundo `page.goto('/')`. El test
  `tus records` repetido 8 veces: 8 de 8 en verde, mas la corrida de
  `check.sh`.
- Hallazgo menor de la revision anterior: resuelto. `records.js` dice
  "desde R3 · mapa · fecha" para `longest_round_streak` y
  `records.test.js` lo afirma; los demas records siguen con "ronda R<n>".
- Diff dentro de `archivos:` salvo `backend/tests/test_records.py` (ya
  explicado). Sin dependencias, sin escrituras, sin tildes en
  identificadores, UI con tildes, sin `print` ni `console.log`.
- `check.sh`: Todo en verde (733 tests backend, 120 vitest, build ok, 44 e2e).

Veredicto: aprobar -> `revisado`.
