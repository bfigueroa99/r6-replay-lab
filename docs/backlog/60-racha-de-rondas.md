# 60. Racha de rondas dentro de la partida

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B13
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_rachas.py, frontend/src/rachas.js, frontend/src/rachas.test.js, frontend/src/records.js, frontend/src/records.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261019T0325Z, arquitecto 20261019T0404Z

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
