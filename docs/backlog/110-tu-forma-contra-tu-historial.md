# 110. Tu forma contra tu historial

estado: revisado
candado: -
rama: claude/equipo-dev/110-tu-forma-contra-tu-historial
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E16
archivos: backend/replays/analytics/aggregates.py (compare_periods against, _periodo_por_partidas), backend/replays/views.py (compare), backend/tests/test_compare.py, frontend/src/components/Delta.jsx (nuevo, sale de Trends.jsx), frontend/src/pages/Trends.jsx (import), frontend/src/formaHistorial.js (nuevo), frontend/src/formaHistorial.test.js (nuevo), frontend/src/pages/Dashboard.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1128Z-cKKCvKD, arquitecto 20261113T0003Z-cVnayJ8, dev 20261113T0804Z-cJw5MQs, revisor 20261113T1203Z-cWfR3tT

## PR

## Que gana quien usa la app

En el Inicio, un panel junta tus ultimas 10 partidas y las compara con el
resto de tu historial: rating, winrate de rondas, KST y muertes sin trade,
cada uno con la diferencia y si sale del ruido. Hoy "Forma reciente" lista
las 10 partidas una por una; esto dice si estas en racha o en bajon por algo
mas que el resultado.

## Criterios de aceptacion

- [ ] `/api/overview/` (o la clave que elija el diseno) devuelve un bloque
      `form` con `recent` (las mismas partidas que `recent_form()`, mismo
      orden por `played_at`) y `rest` (todas tus otras rondas con los
      mismos filtros), cada uno con `rounds`, `rating`, `winrate`, `kst`
      y el % de muertes sin trade, mas `delta` y `margin` por metrica
      (banda de `_ruido_combinado` donde la metrica es una proporcion).
      Test con historial armado: 10 partidas recientes ganadas contra 10
      viejas perdidas dan `delta` de winrate positivo y fuera del margen.
- [ ] Con 10 partidas o menos no hay `rest`: el bloque dice por que
      (`rest: null`) y el panel muestra una nota, no ceros. Test.
- [ ] Los filtros de la barra aplican a los dos lados de la comparacion
      (test con `?map=`).
- [ ] El panel se ve en el Inicio; el e2e de humo lo afirma con los numeros
      del `seed_demo` y la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Forma contra tu historial").

## Fuera de alcance

- Ventana configurable (10 queda como constante en `aggregates.py`).
- Un grafico: solo numeros con signo, como "vs. tu lado" de Operadores.
- Señal del Coach sobre la racha (seria otra ficha).

## Diseno

(arquitecto 20261113T0003Z-cVnayJ8) Filtros duros: pasa. Agrega columnas que ya existen
(`winrate`, `rating`, `kst_pct`, `untraded_death_pct` de `derive`); sin red,
sin dependencias, sin POST, sin migracion. Una forma obvia (~250 lineas):
sin arena ni consenso.

**Correccion de premisa.** La comparacion con delta y banda de ruido ya
existe: `compare_periods` (`aggregates.py`, `GET /api/compare/`), panel
**Progreso** de Tendencias, que pone las ultimas N partidas contra las **N
anteriores**. Lo nuevo de esta ficha es la referencia (**todo el resto** de
tu historial, no las N anteriores) y el lugar (el Inicio). Asi que no hay
bloque `form` aparte en `/api/overview/`: se extiende `compare_periods` con
`against="rest"` y el Inicio lo pide aparte, con su propia request (un error
no tumba el Inicio). El criterio 1 queda cumplido con esa forma: `current` =
las mismas partidas que `recent_form()` (mismo orden por `played_at`),
`previous` = el resto, `metrics` con `delta` y `noise` (la banda de `_ruido`,
la que la ficha llama `_ruido_combinado`) y `verdict`.

**Backend, `backend/replays/analytics/aggregates.py`.**
- `_periodo_por_partidas(filters, n, resto=False)`: con `resto=True` devuelve
  `ordenados[:n], ordenados[n:]` (todas las anteriores) en vez de
  `ordenados[n : n * 2]`.
- `compare_periods(..., against: str = "previous", **filters)`: con
  `against == "rest"`:
  - `by="matches"`: `_periodo_por_partidas(filters, n, resto=True)`;
    etiquetas `f"Ultimas {len(recientes)} partidas"` y
    `f"El resto ({len(anteriores)} partidas)"`.
  - `by="days"`: `previo = base_queryset(until=inicio_actual, **filters)`
    (sin `since`); etiqueta `f"Antes de los ultimos {n} dias"`.
  - Todo lo demas igual (`enough_sample`, `metrics`, filtros de tiempo
    ignorados como hoy: el periodo lo define la comparacion). La respuesta
    suma `"against": against`.
  Cualquier otro valor de `against` es `"previous"` (el comportamiento de hoy).
- Con 10 partidas o menos el resto queda vacio: `previous.rounds == 0`,
  metricas `previous`/`delta` en `None`, `enough_sample` false. Es el
  `rest: null` del criterio 2 con la forma existente; la UI lo lee asi.

**`backend/replays/views.py`, `compare`**: `against = "rest" if
request.GET.get("against") == "rest" else "previous"` y pasarlo.

**Tests backend, `backend/tests/test_compare.py`**, clase nueva
`ContraElRestoTests` (con el helper `partida` del archivo):
- `test_contra_el_resto_toma_todas_las_partidas_anteriores`: 25 partidas ->
  `current.matches == 10`, `previous.matches == 15`, etiqueta
  `El resto (15 partidas)`.
- `test_las_recientes_son_las_de_la_forma_reciente`: los `match_id` de
  `current` (por `round__match_id` del queryset, o comparando `matches` y el
  rango `from`/`to`) coinciden con los `id` de `recent_form()`.
- `test_diez_recientes_ganadas_contra_diez_viejas_perdidas_salen_del_ruido`:
  10 viejas `ganadas=0`, 10 recientes `ganadas=6` (6 rondas): `delta` de
  `winrate` positivo, `verdict == "mejor"`, `abs(delta) > noise`.
- `test_con_diez_partidas_o_menos_no_hay_resto`: 10 partidas ->
  `previous.rounds == 0`, `delta` de winrate `None`, `enough_sample` false.
- `test_el_filtro_de_mapa_aplica_a_los_dos_lados`: partidas en dos mapas;
  con `map=` solo cuentan las de ese mapa en `current` y en `previous`.
- `test_sin_against_sigue_comparando_contra_las_anteriores`: 25 partidas sin
  `against` -> `previous.matches == 10` (regresion del modo de hoy).
- `test_la_vista_acepta_against_rest_e_ignora_otro_valor`: `GET
  /api/compare/?against=rest` 15 en `previous.matches`; `?against=foo` 10.

**Frontend.**
- `frontend/src/components/Delta.jsx` (nuevo): mover `Delta` de
  `Trends.jsx` tal cual (export default) y que Tendencias lo importe; el
  Inicio usa el mismo chip.
- `frontend/src/formaHistorial.js` (logica pura, nuevo):
  `METRICAS_FORMA = ['winrate', 'rating', 'kst_pct', 'untraded_death_pct']`;
  `filasDeForma(data)` -> las metricas de `data.metrics` con esas claves y
  en ese orden (las demas no; `[]` sin datos); `estadoDeForma(data)` ->
  `'sin-datos'` si no hay `data` o `current.rounds` es 0, `'sin-resto'` si
  `previous.rounds` es 0, `'poca-muestra'` si `!enough_sample`, si no `null`.
- `frontend/src/formaHistorial.test.js` (vitest): orden y filtro de
  metricas; cada estado (`sin-datos`, `sin-resto`, `poca-muestra`, `null`).
- `frontend/src/pages/Dashboard.jsx`: componente `PanelForma({ filters })`
  con `useApi('/compare/', { ...filters, by: 'matches', n: 10, against: 'rest' })`,
  despues del panel "Ultimas partidas". `ErrorBox` / `Loading` como los
  paneles del Coach. `<Panel title="Tu forma contra tu historial"
  hint="Tus últimas 10 partidas contra todas las anteriores, con los filtros de
  mapa, lado, tipo y modo. Si el cambio no pasa la banda de ruido, no es un
  cambio.">`. Estados: `sin-datos` -> nada (el Inicio ya muestra su vacio);
  `sin-resto` -> `<p className="note">Todavía no hay historial para comparar:
  hacen falta más de 10 partidas.</p>`; `poca-muestra` -> la tabla igual con
  la nota `Muestra chica: los números están, pero no alcanzan para decir que
  algo cambió.` (como Progreso, aviso y no recorte). Tabla `DataTable` con
  `filasDeForma`: Métrica, `previous.label`, `current.label`, Cambio
  (`<Delta>`), Ruido (`±x` o `—`), con el mismo `fmt` de Progreso; sin CSV
  (son 4 filas; Progreso ya exporta la tabla completa).

**e2e, `frontend/e2e/humo.spec.js`**, test `el Inicio compara tu forma con tu
historial` junto a `el Resumen muestra tus records y enlaza a la partida`:
leer `/api/compare/?by=matches&n=10&against=rest` (seed: 29 partidas -> 10
contra 19); en `/`, el panel "Tu forma contra tu historial" muestra las
cabeceras `Ultimas 10 partidas` y `El resto (19 partidas)` (de la API, no a
mano) y 4 filas (`Rondas ganadas`, `Rating`, `KST`, `Muertes sin trade`).
Consola limpia. Recalcular los numeros con `seed_demo` si cambia el seed.

**`docs/metricas.md`**, seccion `## Progreso`: fila **Forma contra tu
historial**: las ultimas 10 partidas contra todas las anteriores con los
filtros activos salvo fechas y sesion (el periodo lo define la comparacion);
mismo cambio, banda de ruido y veredicto que Progreso; las rondas de cada
lado son el `n` de la banda; con 10 partidas o menos no hay resto y no se
compara.

**Orden.** aggregates + tests backend, vista, `Delta.jsx` (mover y probar que
Tendencias sigue), `formaHistorial.js` + vitest, `Dashboard.jsx`, e2e,
`metricas.md`, `npm run build`.

**Que puede romperse.** El modo de hoy de `/api/compare/` (Progreso):
`test_sin_against_sigue_comparando_contra_las_anteriores` y los tests
existentes de `test_compare.py` lo fijan. El resto puede tener cientos de
partidas contra 10: la banda la domina el lado chico, que es lo correcto
(no promedio de promedios: son totales de rondas). Mover `Delta` cambia un
import de `Trends.jsx`: lo cubre el e2e de Tendencias.

**Archivos ocupados.** La 112 (`implementado`) toca `humo.spec.js` (otro
test) y `aggregates.py` (records, otra funcion); la 113 (`revisado`)
`aggregates.py`, `views.py` (otras funciones) y `humo.spec.js`. Ninguna toca
`compare_periods`, `Dashboard.jsx`, `Trends.jsx` ni `test_compare.py`. Merge
trivial; no se frena.

**Verificacion manual.** `seed_demo`, `/`: panel con "Ultimas 10 partidas"
contra "El resto (19 partidas)"; `?map=bank` cambia los dos lados; Tendencias
-> Progreso sigue diciendo "Las 10 anteriores".

Para el humano (no frena): las fechas y la sesion de la barra no aplican a
esta comparacion, igual que en Progreso (el periodo lo define ella). Si
preferis que "el resto" respete "Desde/Hasta", es un cambio de una linea.

Skills: no aplica (el repo ya resuelve la comparacion y su banda en `compare_periods`).
Skills del repo: statistical-analysis (denominador: rondas de cada lado; banda `_ruido` sobre totales, no promedio de promedios; sin `n` minimo nuevo: usa `COMPARE_MIN_ROUNDS`), testing-strategy (Django para el corte y la vista, vitest para filas y estados, e2e para el panel).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T0804Z-cJw5MQs) Diseno completo:

- `aggregates.py`: `_periodo_por_partidas(..., resto=False)` y
  `compare_periods(..., against="previous")`; con `against="rest"` la
  referencia es todo lo anterior (por partidas: etiqueta `El resto (N
  partidas)`; por dias: `Antes de los últimos N días`). La respuesta suma
  `against`; cualquier otro valor es `previous`. `views.compare` lo pasa.
- `components/Delta.jsx`: `Delta` sale de `Trends.jsx` tal cual.
- `formaHistorial.js`: `METRICAS_FORMA`, `filasDeForma` (las 4 metricas en
  orden fijo) y `estadoDeForma` (`sin-datos`, `sin-resto`,
  `poca-muestra`, `null`).
- `Dashboard.jsx`: `PanelForma`, con su propia request, despues del bloque
  de "Últimas partidas". Fila "Forma contra tu historial" en `metricas.md`
  (seccion Progreso).

Desvios del diseno:
- Etiquetas con tildes (`Últimas 10 partidas`, `Antes de los últimos N
  días`), como las de Progreso: son texto de UI.
- Con `resto`, el periodo previo es `exclude(match_id__in=recientes)` y no
  `IN` con todo el historial (revision ciega, LOW: limite de variables de
  SQLite con miles de partidas).
- Hint del panel: "con tus filtros salvo fecha y sesión (con esos, las 10 no
  son las de arriba)", y `metricas.md` lo dice igual (revision ciega,
  MEDIUM: `recent_form` respeta fecha y sesion y `compare_periods` no).
- Test extra `test_contra_el_resto_por_dias_toma_todo_lo_anterior`.

Tests: backend `ContraElRestoTests` (8; vistos en rojo antes del codigo:
5 de 8 caian). El de "sale del ruido" usa 2/6 contra 5/6 y fija la banda en
7.8 (con 0 % contra 100 % la banda era 0 y no probaba nada). vitest
`formaHistorial.test.js` (6, en rojo antes del modulo). e2e `el Inicio
compara tu forma con tu historial` (etiquetas de la API, 4 filas en orden,
consola limpia). Criterios -> tests: bloque con delta y banda
(`test_contra_el_resto_toma_todas...`, `test_diez_recientes...`,
`test_las_recientes_son_las_de_la_forma_reciente`); sin resto
(`test_con_diez_partidas_o_menos_no_hay_resto` + vitest `sin-resto`);
filtros (`test_el_filtro_de_mapa_aplica_a_los_dos_lados`); panel en el Inicio
(e2e); fila en `metricas.md`. Regresion de Progreso:
`test_sin_against_sigue_comparando_contra_las_anteriores` y
`test_la_vista_acepta_against_rest_e_ignora_otro_valor`.

verificar.sh: VERDE 86e38cc12 (1173 backend, 340 vitest, 96 e2e; el commit siguiente solo toca esta ficha).

Skills: no aplica (la comparacion y su banda ya estaban en `compare_periods`).
Skills del repo: ninguna (modern-web-guidance y ux-copy no se leyeron: el panel reusa `Panel`, `DataTable` y `Delta` sin CSS nuevo, y los textos son los del diseno en voseo y con tildes).
OMC: plan=— · revisión=5 hallazgos (5 arreglados; 0 CRITICAL/HIGH) · verificación=—

## Revision 2026-11-13 sobre 5c49845

(revisor 20261113T1203Z-cWfR3tT) La rama trae `origin/dev` (e7cd7b1, con la
117) sin conflictos. verificar.sh: VERDE 5c49845a7 (1173 backend, 340
vitest, 96 e2e). Revision a ciegas en dos ejes (`omc-code-reviewer`
estandares y `omc-code-reviewer` intencion; sin POST, red ni parser: sin
eje de seguridad). Confirmados por el lider:

- [test] MEDIUM `frontend/e2e/humo.spec.js` (el Inicio compara tu forma):
  el criterio 4 pide afirmar el panel con los numeros del seed y el test
  solo miraba cabeceras y nombres de fila; con las columnas cruzadas pasaba
  igual. **Corregido por el Revisor (test que pasa):** afirma valor previo,
  actual y ruido de "Rondas ganadas" y "Rating", sacados de la API.
  Mutacion: con `previous` y `current` cruzados en `PanelForma`, el test
  cae (`1 failed`); restaurado, `1 passed`.
- [intencion] MEDIUM, no frena: con fecha o sesion en la barra, el panel
  ignora esos filtros y "Ultimas partidas" no (`_FILTROS_DE_TIEMPO` en
  `compare_periods`). Es la decision del diseno, igual que Progreso, y el
  hint y `metricas.md` lo dicen; sigue en `## Para el humano`.
- LOW, no frenan: etiqueta `El resto (1 partidas)` con 11 partidas (mismo
  patron que `Las 1 anteriores` de Progreso);
  `test_diez_recientes_ganadas_contra_diez_viejas_perdidas_salen_del_ruido`
  usa 10 contra 10, donde resto y anteriores coinciden (el modo resto lo
  fijan los otros tests); con `against=rest` se calculan `by_map` y
  `by_operator` que el panel no usa; sin desempate por `played_at` igual en
  `recent_form` y `_periodo_por_partidas`.

Criterios: bloque con delta y banda (tests de `ContraElRestoTests`), sin
resto (backend + vitest `sin-resto`), `?map=` a los dos lados, panel en el
Inicio con numeros (e2e, ahora con valores), fila en `metricas.md`: cubiertos.
Reglas: GET, sin dependencias, identificadores sin tildes y UI con tildes,
sin `console.log`. Diff dentro de `archivos:`.

Veredicto: aprobar -> `revisado`.

Skills: no aplica.
OMC: plan=— · revisión=8 hallazgos (1 arreglado; 0 CRITICAL/HIGH) · verificación=—

## QA

## Para el humano

- Aviso, no frena (arquitecto): las fechas y la sesion de la barra no aplican a
  esta comparacion, igual que en Progreso. Si preferis que "el resto" respete
  "Desde/Hasta", es un cambio de una linea.
