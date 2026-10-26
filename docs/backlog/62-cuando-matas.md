# 62. Cuando matas

estado: aprobado
candado: -
rama: claude/equipo-dev/62-cuando-matas
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B11 ([tracker.gg](https://tracker.gg/r6siege/articles/r6-ow-v3-0), "number of kills in the first 30 seconds")
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_deaths.py, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261024T1204Z, arquitecto 20261024T1605Z, dev 20261026T1206Z, revisor 20261026T1605Z, qa 20261026T2004Z

## Que gana quien usa la app

En Tendencias ya esta "Cuando mueres"; falta el otro lado: en que momento de
la fase de accion sacas tus bajas. Dice si tu impacto esta en la apertura o
en el cierre de la ronda, y en defensa cuantas bajas tempranas consigues.

## Criterios de aceptacion

- [ ] `/api/trends/` trae una clave nueva `kills_by_time`: tramos de 30 s
  (`DEATH_BUCKET`) con el ultimo abierto en `DEATH_CAP` (150s+), igual
  que `deaths_by_time`, cada uno con `start`, `end`, `label`, `kills`,
  `attack`, `defense` y `pct`. Lee `Event.elapsed` de los eventos
  `Kill` cuyo autor es tu jugador en las rondas del `base_queryset`; el
  lado sale de tu fila `RoundPlayer` de esa ronda. Test con bajas en 10 s,
  45 s y 200 s que caen en 0-30s, 30-60s y 150s+.
- [ ] Los teamkills no cuentan (mismo criterio que `_solo_rivales`): test
  con una baja a un compañero que no aparece en ningun tramo.
- [ ] La suma de `kills` de todos los tramos es igual al total de bajas a
  rivales del feed con los mismos filtros; un filtro `side=Defense` deja
  `attack` en 0 en todos los tramos (test).
- [ ] Base vacia: 200 y `kills_by_time: []`.
- [ ] Tendencias: panel "Cuando matas" al lado de "Cuando mueres", mismo
  grafico apilado por lado y mismo texto sobre segundos de fase de accion;
  e2e sobre `seed_demo` que lo encuentra.
- [ ] Fila nueva en `docs/metricas.md` al lado de "Cuando mueres".

## Fuera de alcance

- Cruzar con el winrate de la ronda o con la primera baja: eso es la ficha 63.
- Columna nueva al importar: se calcula al consultar desde `Event`, como
  Duelos. Si el Arquitecto ve que `RoundPlayer` lo necesita, es otra ficha.

## Diseno

(arquitecto 20261024T1605Z) Una forma obvia: el histograma de
`deaths_by_time` alimentado por las bajas de `_duelos`. Sin arena, sin
migracion, se calcula al consultar como Duelos (la ficha ya lo dice y
`RoundPlayer` no guarda el segundo de cada baja; no hace falta).

**Archivos y por que**

- `backend/replays/analytics/aggregates.py`, seccion `# muertes`:
  - Extraer `_tramo_vacio(inicio, bucket, cap) -> dict` con `start`, `end`,
    `label` (los tres calculos que hoy estan inline en `deaths_by_time`) y
    usarlo en `deaths_by_time` agregando sus claves propias. La salida de
    `deaths_by_time` no cambia ni en el orden de claves que importa: los
    tests de `test_deaths.py` existentes lo cuidan.
  - `kills_by_time(bucket=DEATH_BUCKET, cap=DEATH_CAP, **filters) -> list[dict]`:
    `me_ids = _me_ids()`; sin ids, `[]`. `_, a_favor = _duelos(base_queryset(**filters), me_ids)`
    (ya excluye teamkills con `_solo_rivales(..., "target_id")` y limita a
    las rondas filtradas). Anotar el lado con
    `mi_lado=Subquery(RoundPlayer.objects.filter(round_id=OuterRef("round_id"), is_me=True).values("side")[:1])`
    (mismo patron que `_MI_EQUIPO`; si se usa en un solo lugar puede quedar
    inline) y `tramo=ExpressionWrapper(Floor(F("elapsed") / bucket) * bucket, output_field=IntegerField())`,
    `.values("tramo", "mi_lado").annotate(kills=Count("id")).order_by("tramo")`.
    Mismo colapso al tope que `deaths_by_time` (`min(tramo, cap)`). Cada
    fila: `start`, `end`, `label`, `kills`, `attack`, `defense`, `pct` (de
    `kills` sobre el total). Tramos sin bajas no salen (igual que
    `deaths_by_time`).
  - Docstring con el por que: el promedio de cuando matas esconde si el
    impacto esta en la apertura o en el cierre.
- `backend/replays/views.py`, `trends`: `"kills_by_time": agg.kills_by_time(**filters)` junto a `deaths_by_time`.
- `backend/tests/test_deaths.py`: clase nueva `CuandoMatasTests` (feed con
  `Event` `Kill`, `RoundPlayer` tuyo y del rival con `team_index` distinto,
  como arman los tests de duelos; mirar `test_duels.py` para el helper).
  Tests:
  - `test_bajas_a_los_10_45_y_200_caen_en_tres_tramos` (0-30s, 30-60s,
    150s+)
  - `test_un_teamkill_no_cuenta_en_ningun_tramo`
  - `test_la_suma_de_tramos_es_igual_a_las_bajas_de_duel_totals` (mismo
    filtro, compara con `agg.duel_totals(**filtros)["kills"]`)
  - `test_con_side_defense_el_ataque_queda_en_cero`
  - `test_base_vacia_devuelve_lista_vacia_en_la_api` (`/api/trends/`: 200 y
    `kills_by_time == []`)
  - `test_las_muertes_por_tiempo_no_cambian_con_el_tramo_compartido` solo
    si los tests existentes no afirman `start`/`end`/`label` de
    `deaths_by_time`; si ya los afirman, no hace falta.
- `frontend/src/pages/Trends.jsx`: `const matas = data.kills_by_time || []`
  junto a `muertes`; panel `title="Cuándo matas"` **inmediatamente antes**
  del panel "Cuando mueres" (su titulo no se toca en esta ficha; el
  nuevo va con tilde porque es texto de UI),
  envuelto en `{matas.length ? ... : null}`. Mismo `BarChart` apilado
  (`attack` Ataque `#ff8a3d`, `defense` Defensa `#4aa8ff`) y `DataTable`
  con Tramo, Bajas, Del total (%), Ataque, Defensa,
  `initialSort={{ key: 'start', dir: 'asc' }}`, `csvName="cuando-matas"`.
  Hint: "En qué momento de la fase de acción sacas tus bajas a rivales. Si
  se juntan al principio tu impacto está en la apertura; si están al final,
  en el cierre. Los segundos son de fase de acción, no del reloj de la
  ronda." Sin KPIs: los extremos son de "Cuando mueres".
- `frontend/e2e/humo.spec.js`: `test('Tendencias muestra cuando matas', ...)`:
  panel con heading "Cuándo matas" (exact), tabla con al menos una fila,
  consola limpia. Numeros exactos solo sacados de `seed_demo` corriendo.
- `docs/metricas.md`, la tabla donde esta "Cuando mueres": fila **Cuando
  matas** justo arriba: bajas a rivales (`Event` `Kill` con autor tuyo y
  victima del otro equipo en esa ronda; teamkills afuera) por tramos de 30 s
  de `Event.elapsed`, el ultimo abierto en 150s+, separadas por tu lado en
  la ronda. La suma es la de Bajas de Duelos con los mismos filtros.

**Orden:** helper + `deaths_by_time` (correr `test_deaths` y ver verde
igual), `kills_by_time` + tests, views, Trends.jsx, build, e2e, metricas,
`check.sh`.

**Que puede romperse:** el refactor de `deaths_by_time` (lo cubre su suite);
`Event.elapsed` vale `0.0` cuando el evento no trae reloj (`metrics.py`,
linea `e["elapsed"] = ... else 0.0`): esas bajas caen en 0-30s, igual que
pasa hoy con `death_elapsed`. No se corrige aca: es el mismo criterio que
"Cuando mueres" y cambiarlo seria otra ficha. Rendimiento: dos subqueries
por evento como Duelos; con miles de rondas es lo mismo que ya paga
`/api/duels/`.

**Verificacion manual:** `/tendencias` con la base demo: los dos paneles
juntos, las barras de matar con la misma escala visual de colores;
`curl -s 'localhost:8000/api/trends/?side=Defense'` deja `attack: 0` en
cada tramo de `kills_by_time`.

**Paralelo:** 63 toca el mismo panel de `Trends.jsx` y la misma seccion de
`aggregates.py`: 63 se implementa despues de que 62 se mergee (prioriza, no
bloquea). Con 61 no se pisan funciones.

## Implementacion

(dev 20261026T1206Z) Diseno completo, sin desvios.

- `aggregates.py`: `_tramo_vacio` (start/end/label) compartido por
  `deaths_by_time` (salida igual; la suite de `test_deaths` lo cubre) y
  `kills_by_time` nueva, sobre `a_favor` de `_duelos` con el lado de tu
  `RoundPlayer` como subquery inline.
- `views.py`: `kills_by_time` en `/api/trends/`.
- `test_deaths.py`, `CuandoMatasTests` (8 tests): los 5 del diseno mas
  `test_las_muertes_tuyas_no_cuentan_como_bajas`,
  `test_separa_por_tu_lado_en_la_ronda` y `test_la_api_de_tendencias_lo_expone`.
  El de suma compara con `duel_totals` sin filtro y con `side=Defense`.
  El primero afirma `start`/`end`, asi que el test extra de
  `deaths_by_time` no hizo falta.
- `Trends.jsx`: panel "Cuándo matas" justo antes de "Cuando mueres".
- e2e `Tendencias muestra cuando matas`: `seed_demo` da 4 tramos (30-60s a
  120-150s, 99 bajas = Bajas de Duelos); afirma la fila 90-120s
  `53 · 54% · 34 · 19` (sacada corriendo el seed).
- `metricas.md`: fila **Cuando matas** arriba de Cuando mueres.

Revision ciega previa (subagente con `revision.md`): sin hallazgos.
`check.sh`: `Todo en verde.` (778 tests backend, 120 frontend, build ok,
49 e2e).

## Revision 2026-10-26 sobre 9926b27

(revisor 20261026T1605Z) Rama al dia con main (main ya incluido, sin merge).
`check.sh`: `Todo en verde.` (778 tests backend, 120 frontend, build ok,
49 e2e).

Revision ciega (subagente con `revision.md` sobre el diff sin
`docs/backlog`): sin hallazgos, veredicto aprobar. Confirmado por el lider:

- Criterios: tramos 0-30/30-60/150s+ (`test_bajas_a_los_10_45_y_200_caen_en_tres_tramos`),
  teamkills afuera (`test_un_teamkill_no_cuenta_en_ningun_tramo`), suma =
  `duel_totals` sin filtro y con `side=Defense`, ataque en 0 con
  `side=Defense`, base vacia 200 con `[]`, panel "Cuándo matas" con e2e
  (`Tendencias muestra cuando matas`), fila en `metricas.md`. Los numeros
  del e2e (90-120s: 53 · 54% · 34 · 19, total 99) se recalcularon sobre una
  base `seed_demo` y coinciden.
- Mutaciones: correr el colapso al tope (`cap + 30`) y invertir el lado
  (`!= "Attack"`) hacen caer `CuandoMatasTests` (1 y 2 fallos).
- Diff dentro de `archivos:`; identificadores sin tildes, UI con tildes;
  sin `print` ni `console.log`; `deaths_by_time` sin cambios de salida.

Veredicto: **aprobar**. Sin hallazgos.

## QA 2026-10-26 sobre b6a5cbb

(qa 20261026T2004Z) Rama al dia con main (`git merge origin/main`: already up
to date). Base borde: `$S/sembrar_qa62.py` en el scratchpad (no va al repo),
corrido con `SQLITE_PATH=<scratch>/qa62.sqlite3 python manage.py migrate` y
`python manage.py shell < sembrar_qa62.py`: una partida Border con bajas tuyas
a 10, 45 y 200 s en ataque (clock_start 240), un teamkill a los 210 s, una
baja a los 20 s en defensa, una ronda sin bajas y una partida Unranked con un
rival que repite nick con otro perfil (baja a los 80 s).

- **Tramos y lado:** `curl -s localhost:8765/api/trends/` da
  `0-30s 2 (1 at, 1 def) 40%`, `30-60s 1 at 20%`, `60-90s 1 def 20%`,
  `150s+ 1 at 20%`; el teamkill no aparece. Esperado a mano: igual.
- **Suma = Duelos:** `?map=border` 4 = 4, `?side=Defense` 2 = 2,
  `?match_type=Unranked` 1 = 1 (`kills_by_time` contra `totals.kills` de
  `/api/duels/`).
- **side=Defense:** `attack` en 0 en los dos tramos que quedan.
- **Bordes:** `until=foo`, `page=-1`, `side=`, `map=`, `days=999999999999`,
  `player=Rival1` (nick repetido): 200 y lo mismo que sin filtro;
  `since=2099-01-01` y `side=Bogus`: 200 con `[]`. Cero 500 en el log del
  runserver.
- **Base vacia:** `/api/trends/`, `?side=Defense` y `?until=foo`: 200 con
  `kills_by_time: []`.
- **Chunk inicial:** `index-*.js` 187.83 kB en main y en la rama (sin
  cambio); `Trends-*.js` 25.84 -> 26.94 kB (lazy, +4 %).
- **Mutaciones** (`python manage.py test tests.test_deaths.CuandoMatasTests`):
  tramo sin `Floor` (5 fallos), defensa sumada a ataque (2), la vista sin
  `kills_by_time` (1 error): caen. Dos sobrevivian a los unit tests:
  `_pct(kills, 1)` (solo lo atrapaba el e2e, `54%` -> `+1`) y el lado leido de
  `is_me=False` en vez de tu fila (sobrevivia tambien al e2e: los fixtures y
  `seed_demo` cargan al compañero antes que al rival, asi que cualquier fila
  ajena del mismo equipo daba el mismo lado). QA agrego dos tests de borde en
  `CuandoMatasTests`: `test_el_lado_sale_de_tu_fila_aunque_el_rival_este_primero`
  y `test_el_porcentaje_es_sobre_el_total_de_tramos`; con ellos los dos
  mutantes caen (1 fallo cada uno).
- **check.sh** con los tests nuevos: `Todo en verde.` (780 tests backend,
  120 frontend, build ok, 49 e2e).

Sin migracion, sin parser, sin `recompute`: no hay nada para verificar en el
PC. Los tramos de 30 s son los de "Cuando mueres" (no son un umbral nuevo).

Veredicto: **aprobado**.
