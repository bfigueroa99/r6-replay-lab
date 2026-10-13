# 36. Primera mitad, segunda mitad y prorroga

estado: aprobado
candado: -
rama: claude/equipo-dev/36-mitades-y-prorroga
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 2
fuente: ALCANCE.md B1; `Round.overtime_number` (`backend/replays/models.py:89`) se guarda en `ingest.py:201` y ninguna vista lo usa
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Trends.jsx, docs/metricas.md, backend/tests/, frontend/e2e/, backend/tests/factories.py
turnos: po 20261013T0511Z, arquitecto 20261013T0611Z, dev 20261013T0711Z, revisor 20261013T0811Z, qa 20261013T0911Z

## PR

(La escribe el Release manager al final: titulo `[equipo-dev][area] Titulo`,
cuerpo segun `.claude/skills/equipo-dev/plantilla-pr.md` y una seccion
"Como probarlo en 2 minutos" con comandos exactos.)

## Que gana quien usa la app

En Tendencias ve su winrate de ronda y su rating en la primera mitad, en la
segunda y en la prorroga, y el winrate de partida segun si arranco atacando o
defendiendo. Hoy solo hay "por numero de ronda", que no dice si te cuesta
cerrar ni como rindes cuando la partida se alarga.

## Criterios de aceptacion

- [ ] `GET /api/trends/` devuelve una clave nueva `by_half` con tres filas
      (`first`, `second`, `overtime`), cada una con los mismos campos que una
      fila de `by_round_number` (`rounds`, `winrate`, rating, etc.). Una fila
      sin rondas sale con `rounds: 0` y metricas `null`, nunca da 500.
- [ ] La mitad se deduce de los datos, no de un numero fijo de rondas por
      modo: `overtime` = rondas con `overtime_number > 0`; `first` = rondas
      sin prorroga cuyo `my_side` es el de la ronda 1 de esa partida;
      `second` = el resto sin prorroga. Test con una partida armada a mano de
      6 rondas (3 y 3) mas 2 de prorroga que afirma 3/3/2.
- [ ] `GET /api/trends/` devuelve `by_start_side` con dos filas
      (`Attack`, `Defense`): partidas y winrate de partida segun el `my_side`
      de su ronda 1. Una partida sin `my_side` en la ronda 1 no cuenta.
- [ ] Los filtros comunes (`map`, `days`, `ranked_only`, `session`...)
      aplican igual que a `by_round_number`; test con `?map=` que cambia el
      conteo.
- [ ] La pagina Tendencias muestra las dos tablas (o barras) con su titulo
      en español, y el e2e la renderiza sin errores de consola.
- [ ] `docs/metricas.md` tiene una fila por cada numero nuevo (mitad,
      prorroga, lado inicial).

## Fuera de alcance

- Rendimiento bajo presion (match point, ir abajo o arriba): es B2, el tramo
  siguiente de la epica.
- Cambiar `by_round_number` o su grafico.
- Reglas del coach sobre mitades: si el Arquitecto ve una obvia, la anota
  como idea en `ALCANCE.md`, no aca.

## Diseno

(Arquitecto 20261013T0611Z, sobre main e5bad5b). Nota del PO (cambiar el seed cambia los numeros de otros e2e): se
respeta, `seed_demo` **no se toca**.

**Definiciones (sin numero fijo de rondas):**

- `overtime`: `Round.overtime_number > 0`.
- Lado inicial de una partida: `my_side` de **su ronda de menor `number`**
  sin prorroga, no de la "ronda 1": el importador guarda `roundNumber` del
  `.rec` y `seed_demo` numera desde 0 (`seed_demo.py:207`), asi que exigir
  `number=1` dejaria partidas sin lado. Si esa ronda tiene `my_side` vacio,
  la partida no tiene lado inicial.
- `first`: sin prorroga y `round.my_side == lado inicial`; `second`: sin
  prorroga y distinto. Rondas de una partida sin lado inicial: no entran en
  `first` ni `second` (se pierden de `by_half`, quedan en el resto de
  Tendencias). Limitacion anotada en `metricas.md`: si faltan los `.rec` de
  la primera mitad, la segunda se lee como primera.

**Backend, `backend/replays/analytics/aggregates.py`** (debajo de
`by_round_number`, linea ~342):

```python
_LADO_INICIAL = Subquery(
    Round.objects.filter(match_id=OuterRef("round__match_id"), overtime_number=0)
    .order_by("number").values("my_side")[:1]
)

def by_half(**filters) -> list[dict]:
    qs = base_queryset(**filters).annotate(lado_inicial=_LADO_INICIAL)
    tramos = {
        "overtime": qs.filter(round__overtime_number__gt=0),
        "first": qs.filter(round__overtime_number=0, round__my_side=F("lado_inicial")).exclude(lado_inicial=""),
        "second": qs.filter(round__overtime_number=0).exclude(lado_inicial="").exclude(lado_inicial=None)
                   .exclude(round__my_side=F("lado_inicial")),
    }
    baseline = rating_baseline()
    return [{"half": k, **totals(tramos[k], baseline)} for k in ("first", "second", "overtime")]
```

`totals` ya devuelve `rounds`, `winrate`, `rating`, `kpr`, etc. con `None`
cuando no hay rondas (verificar que `derive` con `rounds=0` no divide: usa
`_pct`/`_ratio`, que devuelven `None`). Mismo shape que una fila de
`by_round_number` mas `matches` (lo agrega `totals`).

```python
def by_start_side(**filters) -> list[dict]:
```
ids de partida = `base_queryset(**filters).values_list("round__match_id", flat=True).distinct()`;
`Match.objects.filter(id__in=ids).annotate(lado=Subquery(<igual que _LADO_INICIAL con OuterRef("id")>))`;
por `lado in ("Attack", "Defense")`: `matches` (todas las de ese lado),
`decided` (con `won` no nulo), `wins`, `winrate = _pct(wins, decided)`.
Devuelve siempre las dos filas, en ese orden, con `side`. Partidas sin lado
no cuentan. Nota: con `?side=Defense` el filtro limita las rondas, no las
partidas; el lado inicial se lee siempre de la partida entera (por eso el
Subquery va sobre `Round` y no sobre el queryset filtrado). Documentarlo.

**`backend/replays/views.py`** (`trends`, linea ~217): dos claves nuevas
`"by_half": agg.by_half(**filters)` y `"by_start_side": agg.by_start_side(**filters)`.
Sin parametros nuevos.

**`backend/tests/factories.py`**: `make_round` gana `overtime_number: int = 0`
(kwarg con default, no rompe a nadie). Se agrega a `archivos:`.

**Tests nuevos**, archivo nuevo `backend/tests/test_mitades.py`
(`TestCase`, datos con `factories`):

- `test_seis_rondas_y_dos_de_prorroga_dan_tres_tres_y_dos`: partida con
  rondas 1-3 Attack, 4-6 Defense, 7-8 con `overtime_number=1,2` ->
  `rounds` 3/3/2 en `first/second/overtime`.
- `test_el_lado_inicial_sale_de_la_ronda_mas_baja_aunque_no_sea_la_uno`:
  rondas numeradas desde 0 (como `seed_demo`), primera en Defense -> las de
  Defense son `first`.
- `test_una_mitad_sin_rondas_sale_con_cero_y_metricas_nulas`: sin prorroga ->
  fila `overtime` con `rounds: 0`, `winrate: None`, `rating: None`.
- `test_lado_inicial_cuenta_partidas_y_winrate_de_partida`: dos partidas que
  arrancan en Attack (una ganada, una perdida) y una en Defense ganada ->
  Attack `matches 2 winrate 50.0`, Defense `matches 1 winrate 100.0`.
- `test_partida_sin_lado_en_la_primera_ronda_no_cuenta_para_el_lado_inicial`.
- `test_el_filtro_de_mapa_cambia_el_conteo_por_mitad`: dos partidas en mapas
  distintos, `GET /api/trends/?map=<slug>` con el `Client` -> conteos solo de
  ese mapa.
- `test_trends_sin_datos_devuelve_las_filas_vacias_sin_500`: base vacia,
  `GET /api/trends/` -> 200, `by_half` con 3 filas en 0 y `by_start_side`
  con 2.

**Frontend, `frontend/src/pages/Trends.jsx`**: un `Panel` nuevo justo
**antes** de "Por numero de ronda" (linea ~324), titulo `Por mitad de la
partida`, hint `Primera mitad: las rondas en el lado con que arrancaste.
Si la segunda o la prorroga caen, el problema es cerrar, no empezar.` Una
`DataTable` con filas mapeadas `{first: 'Primera mitad', second: 'Segunda
mitad', overtime: 'Prórroga'}` y columnas `Tramo` (`sortable: false`),
`Rondas`, `Ganadas` (%), `Rating` (digits 2), `KPR`, `Aperturas` (%);
`csvName="por-mitad"`, `rowKey` = `half`, orden fijo (sin `initialSort` o con
`sortable: false` en todas). Debajo, en el mismo Panel, una segunda
`DataTable` chica "Según el lado con que arrancas": `Lado` (`Ataque` /
`Defensa`), `Partidas`, `Ganadas` (%), `csvName="por-lado-inicial"`. Los
nulos se pintan con el `fmt` existente (`—`). Sin grafico nuevo: el bar chart
de rondas ya existe y tres barras no agregan. Usar `data.by_half ?? []` para
no romper si el backend es viejo.

**e2e, `frontend/e2e/humo.spec.js`**: un test nuevo
`'Tendencias muestra la tabla por mitad'`: `goto('/tendencias')`,
`getByText('Por mitad de la partida')` visible, la tabla tiene una fila
`Primera mitad` y otra `Segunda mitad`, consola limpia (`vigilarConsola`).
No se afirma la fila de prorroga con numeros: el seed no tiene prorroga
(queda en 0 y se ve `—`). Con el seed: todas las partidas arrancan en Attack
(`seed_demo.py:202`, `n % 2 == 0`), asi que `Defensa` sale con 0 partidas;
el e2e no afirma eso tampoco.

**`docs/metricas.md`**: seccion nueva `## Mitades y prorroga` antes de
`## Sesiones` (linea ~70) con tres filas: **Primera / segunda mitad**
(definicion de arriba y la limitacion de `.rec` faltantes), **Prórroga**
(`overtimeRoundNumber > 0` de la cabecera), **Lado inicial** (lado de tu
ronda mas baja sin prorroga; winrate de partida sobre partidas con
resultado).

**Orden:** `factories.py` -> tests backend (rojos) -> `aggregates.py` ->
`views.py` -> tests verdes -> `Trends.jsx` -> `npm run build` -> e2e ->
`metricas.md`.

**Que puede romperse.** Sin migracion ni recompute. El Subquery corre por
fila de `RoundPlayer`; con `Round` indexado por `match` es barato, pero si
`/api/trends/` se pone lento en la base real (miles de rondas), anotarlo en
`## Para el humano` (no optimizar a ciegas). Rondas con `my_side` vacio en
una partida con lado inicial caen en `second` (distinto de `""`): excluir
`round__my_side=""` tambien en `second`.

**Choque con otras fichas.** Sin ramas de trabajo abiertas hoy. La 37 toca
`aggregates.py`, `views.py`, `metricas.md` y `humo.spec.js` en zonas
distintas: se puede implementar en paralelo; el que llegue segundo a `main`
resuelve un merge trivial.

**Archivos:** los de la cabecera mas `backend/tests/factories.py`.

## Implementacion

(Dev 20261013T0711Z) Quedo todo el diseno:

- `aggregates.py`: `_lado_inicial(match_ref)` (Subquery sobre `Round`, ronda
  mas baja sin prorroga), `by_half` y `by_start_side`. `views.trends` suma
  `by_half` y `by_start_side`, sin parametros nuevos.
- `factories.make_round` gana `overtime_number=0`.
- `backend/tests/test_mitades.py`, 10 tests: los 7 del diseno y 3 mas
  (`test_ronda_sin_lado_no_cae_en_la_segunda_mitad`,
  `test_el_filtro_de_lado_no_cambia_el_lado_inicial`,
  `test_partida_sin_resultado_cuenta_pero_no_entra_al_winrate`). Prueba de
  mutacion: con `number=1` en el Subquery falla el test de la ronda mas baja.
- `Trends.jsx`: Panel "Por mitad de la partida", antes de "Por numero de
  ronda", con las dos tablas (`por-mitad`, `por-lado-inicial`) en orden fijo
  (campo `orden` y columnas `sortable: false`).
- e2e `Tendencias muestra la tabla por mitad` en `humo.spec.js`.
- `docs/metricas.md`: seccion `## Mitades y prorroga` con las tres filas.

Desvios: `by_start_side` devuelve ademas `decided` y `wins` (cuantas partidas
entran al porcentaje). La primera y la segunda mitad tambien excluyen rondas
con `my_side` vacio, como pedia "Que puede romperse".

La revision ciega previa encontro un test que no detectaba lo que su nombre
dice (corregido) y propuso usar `score_before == [0, 0]` para detectar
partidas a las que les faltan las primeras rondas. Eso no se hizo: el diseno
lo deja como limitacion documentada y hacerlo cambia la definicion. Va a
`## Para el humano`.

## Revision 2026-10-13 sobre c46b3e8

(Revisor 20261013T0811Z) Rama ya contiene `origin/main` e5bad5b, sin
conflicto. `check.sh` en `Todo en verde.` sobre c46b3e8 (478 backend, 65
vitest, build, 24 e2e).

Revision ciega (subagente con `revision.md`, sin leer el plan): sin bugs,
reglas rotas ni tests flojos. Un hallazgo de estilo, confirmado:

- [estilo] frontend/src/pages/Trends.jsx:350
  Que pasa: el tooltip de Rating dice "ronda tipica" sin tilde en un texto de UI.
  Por que es cierto: copia el texto de Trends.jsx:221 y :252, Dashboard.jsx:135,
  Matches.jsx:45 y Operators.jsx:75, que ya lo tienen asi en main.
  Arreglo sugerido: "típica" en las seis lineas, en una ficha aparte o al
  pasar. Menor y preexistente: no bloquea.

Mutaciones del Revisor sobre `aggregates.py` (todas caen en `test_mitades`):
sin `.exclude(round__my_side="")` (1 falla), lado inicial sin filtrar
prorroga (8 errores), winrate de lado sin excluir `won` nulo (1 falla),
prorroga con `>= 0` (2 fallas).

Ficha contra el diff:

- Criterio 1 (`by_half` con 3 filas, vacias sin 500):
  `test_una_mitad_sin_rondas_sale_con_cero_y_metricas_nulas`,
  `test_trends_sin_datos_devuelve_las_filas_vacias_sin_500`.
- Criterio 2 (mitad deducida de los datos, 3/3/2):
  `test_seis_rondas_y_dos_de_prorroga_dan_tres_tres_y_dos`,
  `test_el_lado_inicial_sale_de_la_ronda_mas_baja_aunque_no_sea_la_uno`.
- Criterio 3 (`by_start_side`): `test_lado_inicial_cuenta_partidas_y_winrate_de_partida`,
  `test_partida_sin_lado_en_la_primera_ronda_no_cuenta_para_el_lado_inicial`.
- Criterio 4 (filtros): `test_el_filtro_de_mapa_cambia_el_conteo_por_mitad`.
- Criterio 5 (UI y e2e): `Tendencias muestra la tabla por mitad` en `humo.spec.js`, verde.
- Criterio 6 (`metricas.md`): seccion `## Mitades y prorroga` con las tres filas.
- Archivos: el diff toca solo los de `archivos:`. Identificadores sin
  tildes, UI con tildes (salvo el tooltip de arriba), sin `print` ni `console.log`.
- Ficha: un reemplazo de texto habia pegado el bloque `## Para el humano`
  dentro de Diseno e Implementacion; el Revisor lo dejo como referencia.

Observacion para QA: `seed_demo` alterna el lado en cada ronda y gana todas
las de ataque, asi que en la demo "Primera mitad" sale 100 % y "Segunda
mitad" 0 %. Es el seed, no el codigo; el e2e solo afirma etiquetas.

Veredicto: aprobar.

## QA 2026-10-13 sobre 7319395

(QA 20261013T0911Z) Rama ya contiene `origin/main` e5bad5b, sin conflicto
(`git merge-tree --write-tree origin/main HEAD` sale 0).

- `./scripts/check.sh` -> `Todo en verde.`: ruff ok, 478 tests backend
  (4 skipped), 65 vitest, build, 24 e2e.
- Bases de prueba en el scratchpad (`DATA_DIR=<scratch>/vacia` y
  `<scratch>/sembrada`, `manage.py migrate`, siembra con `tests/factories.py`
  via `manage.py shell < sembrar.py`): partida Club House 1-3 Attack, 4-6
  Defense, 7-8 prorroga (ganada); Oregon numerada desde 0 que arranca en
  Defense (perdida); Bank con la ronda mas baja sin `my_side`; Kafe de una
  ronda sin bajas con `won=None`. `runserver 127.0.0.1:8771/8772 --noreload`.

Criterios:

1. `by_half` con 3 filas, vacias sin 500: base vacia
   `curl 127.0.0.1:8771/api/trends/` -> 200, `first/second/overtime` con
   `rounds 0` y `winrate/rating/kpr null`; `by_start_side` dos filas en 0.
   `?map=noexiste`, `?session=foo`, `?days=0`, `?days=-3` -> 200, mismas filas en 0.
2. Mitad deducida de los datos: base sembrada, `?map=club-house` -> 3/3/2
   (winrate 100/33.3/50); `?map=oregon` (numerada desde 0, arranca en
   Defense) -> first 3, second 2, overtime 0; `?map=bank` (ronda mas baja
   sin lado) -> 0/0/0. Total sin filtro: 7/5/2, winrate 57.1/20.0/50.0,
   calculado a mano y coincide.
3. `by_start_side`: sin filtro Attack `matches 2 decided 1 winrate 100.0`
   (Club House ganada + Kafe sin resultado), Defense `matches 1 winrate 0.0`
   (Oregon); Bank no cuenta.
4. Filtros: `?map=` cambia los conteos (arriba); `?side=Defense` -> first 3
   (Oregon), second 3 (Club House 4-6), overtime 1, y `by_start_side` igual
   que sin filtro (el lado inicial se lee de la partida entera). Parametros
   basura (`?until=foo`, `?page=-1`, `?player=nadie`, `?limit=0`, `?map=`)
   -> 200 con los mismos numeros que sin filtro. Vecinos `/api/dashboard/`,
   `/api/matches/`, `/api/coach/`, `/api/operators/` -> 200 en las dos bases.
5. UI: Chromium headless sobre la base sembrada, `/tendencias`: panel "Por
   mitad de la partida" con filas `Primera mitad 7 57% 0.98 0.86 —`,
   `Segunda mitad 5 20% 1.01 1.00 —`, `Prórroga 2 50% 1.01 1.00 —`,
   `Ataque 2 100%`, `Defensa 1 0%`; 0 errores de consola. e2e
   `Tendencias muestra la tabla por mitad` verde en `check.sh`.
6. `docs/metricas.md`: `## Mitades y prorroga` con Primera/segunda mitad,
   Prórroga y Lado inicial.

Chunk inicial: `index-*.js` 185.47 kB en main e5bad5b y en la rama (sin
cambio); `Trends-*.js` lazy 10.67 -> 12.05 kB.

Mutaciones del QA sobre `aggregates.py` (distintas de las del Revisor),
`manage.py test tests.test_mitades`:
- `first` sin filtrar por lado inicial -> 4 fallas.
- lado inicial de la ronda mas alta (`order_by("-number")`) -> 7 fallas.
- filas de `by_start_side` en orden inverso -> 4 fallas.
- `wins` contado sobre todas las partidas del lado: sobrevive, pero es
  equivalente (`won=True` ya implica no nulo).

Sin migracion, sin `recompute`, sin parser: no hay `## Verificar en el PC`.

Veredicto: aprobado.

## Verificar en el PC

(QA, solo si toca migraciones, recompute, parser, Electron o `.ps1`.)

## Pendiente

## Para el humano

- (Dev 20261013T0711Z, aviso) Hoy, si faltan los `.rec` del inicio de una
  partida, la segunda mitad se lee como primera (documentado en
  `metricas.md`). Hay forma de evitarlo: tomar el lado inicial solo de una
  ronda con `score_before == [0, 0]`. Queda como mejora posible para el
  tramo siguiente; no bloquea.
