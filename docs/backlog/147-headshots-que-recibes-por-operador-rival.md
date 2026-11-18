# 147. Headshots que recibes por operador rival

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D20 (Fuera de alcance de la ficha 137: "Partirlo por operador rival (otro tramo)")
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_headshot_por_operador.py, frontend/src/muertesHeadshot.js, frontend/src/muertesHeadshot.test.js, frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261114T0316Z-cwWsU9i, arquitecto 20261118T1211Z-cMNRUxv

## PR

## Que gana quien usa la app

En Duelos, de tus muertes a manos de cada operador rival, que % fueron
headshot, al lado de tu % general: que operadores te enganchan la cabeza mas
que el resto, y contra cuales te asomas expuesto. Es el segundo tramo de la
137 (Muertes por headshot, por lado y contra tus compañeros), que da el
numero general; este lo parte por el operador que te mato. Implementar
despues de #137.

## Criterios de aceptacion

- [ ] Por operador rival que te mato (el operador de su fila en esa ronda,
      `op_rival` de `_solo_rivales`, como **Operador rival** de
      `metricas.md`): `deaths`, `with_data` (`headshot` no nulo),
      `headshots` y `pct` = headshots / with_data, con las reglas de la 137
      (sin teamkills ni bajas sin autor; un `headshot` nulo cuenta como
      muerte y no entra en el %). Test con dos operadores y una muerte sin
      dato.
- [ ] Cada fila trae tambien la diferencia en puntos contra tu % general
      (el `total` de *Tú* de la 137, con los mismos filtros). Test.
- [ ] Muestra minima con el selector "Muestra mínima" de Duelos
      (`min_duels`) sobre `with_data`, como la tabla *Por operador rival*:
      debajo la fila no sale. Test en el borde (n - 1 y n).
- [ ] Los filtros globales aplican sobre tu fila de la ronda; test con
      filtro de lado.
- [ ] Se ve en Duelos, dentro o debajo del panel "Muertes por headshot",
      como tabla Operador / Muertes con dato / % headshot / vs. tu %; sin
      filas, una nota. e2e con `seed_demo`, numeros de la API y consola
      limpia. Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Señal del Coach ("te enganchan la cabeza contra X").
- Partirlo por mapa o por tu operador.
- Las muertes de tus compañeros por operador rival.

## Diseno

(arquitecto 20261118T1211Z-cMNRUxv, sobre dev 2611d85, con la 137 ya en dev)
Filtros duros: pasa (`Event.headshot`, `Event.target`, el operador del
autor en su fila de la ronda, que ya se guardan al importar; sin red, sin
dependencias, sin POST, sin migracion ni `recompute`; se calcula al consultar
como `duels_by_operator` y `headshot_deaths`: es conteo de eventos, no
columna nueva). Una sola forma obvia: sin arena ni consenso. La 137 ya esta
en dev: nada que esperar.

**Regla** (va tal cual a `metricas.md`). Universo: tus muertes a manos de
rivales en tus rondas filtradas, exactamente las de *Tú* de **Muertes por
headshot**: `contra_mi` de `_duelos(base_queryset(**filters), me_ids)`
(autor con fila en la ronda y en el equipo contrario: fuera teamkills y bajas
sin autor). Operador = `op_rival` de `_solo_rivales`, el de la fila del
autor en esa ronda (**Operador rival**). Por operador: `deaths`,
`with_data` (`headshot` no nulo), `headshots` (`headshot=True`) y
`pct = _pct(headshots, with_data)`. `base` = los mismos cuatro sobre todas
esas muertes, operador vacio incluido: es el total de *Tú* de la 137 con los
mismos filtros. `diff` = `pct - base.pct` en puntos, redondeado a un
decimal (None si alguno es None). Una muerte con operador vacio cuenta en
`base` y no sale como fila. Sale la fila con `with_data >= min_deaths`
(el selector "Muestra mínima" de Duelos, `min_duels`), como *Por operador
rival*; debajo no sale. Conteos sumados, nunca promedio de partidas.

**Numero (statistical-analysis):** el denominador son las muertes con dato
y el `n` va a la vista en cada fila; la diferencia es contra tu % general,
no contra el promedio de los operadores (eso seria promedio de promedios y
pesaria igual un operador de 3 muertes que uno de 40). Sin banda de ruido,
como **vs. promedio** de *Contra que operadores*: con 10 a 30 muertes con
dato, 10 o 15 puntos todavia pueden ser azar; se avisa con la nota de
muestra chica (`MUESTRA_CORTE` = 30 muertes con dato por fila, regla de 30
eventos por grupo), no se oculta mas alla del selector. Sin umbral nuevo.

**Archivos:**
- `backend/replays/analytics/aggregates.py`:
  `headshot_deaths_by_operator(min_deaths: int = 3, **filters) -> dict`,
  justo despues de `headshot_deaths`. `me_ids = _me_ids()`; sin ids,
  `{"min_deaths": min_deaths, "base": _celda_headshot(), "operators": []}`.
  Una consulta: `contra_mi.values("op_rival").annotate(deaths=Count("id"),
  with_data=Count("id", filter=Q(headshot__isnull=False)),
  headshots=Count("id", filter=Q(headshot=True)))`, sin excluir el operador
  vacio (va a `base`); `base` se suma en Python sobre todas las filas, las
  filas con `op_rival` vacio no salen, y el corte y el orden (`-with_data`,
  `-deaths`, `operator`) tambien en Python. Forma:
  `{"min_deaths": n, "base": {"deaths", "with_data", "headshots", "pct"},
  "operators": [{"operator", "deaths", "with_data", "headshots", "pct",
  "diff"}]}`. Agrupar solo por `op_rival`: las otras anotaciones de
  `_solo_rivales` partirian el conteo (el mismo cuidado de la 137).
- `backend/replays/views.py`, `duels()`: clave `"headshot_operators":
  agg.headshot_deaths_by_operator(min_deaths=min_duels, **filters)`. Sin URL
  nueva.
- `backend/tests/test_headshot_por_operador.py` (Django, `factories.py`;
  el armado de rondas 5v5 de `test_muertes_headshot.py`, con el operador de
  cada rival por ronda):
  `test_cuenta_por_operador_rival_sobre_las_muertes_con_dato` (Ash te mata
  con headshot dos veces y sin headshot una; Thermite una con y una sin
  dato -> Ash 3/3/2 66.7, Thermite 2/1/1 100.0);
  `test_la_base_es_tu_total_de_muertes_por_headshot` (`base` igual a
  `headshot_deaths()["me"]["total"]`, con filtro de lado tambien);
  `test_la_diferencia_es_contra_tu_porcentaje_general` (puntos, un decimal,
  negativa cuando el operador te engancha menos);
  `test_un_teamkill_y_una_baja_sin_autor_no_cuentan`;
  `test_operador_vacio_cuenta_en_la_base_y_no_sale_como_fila`;
  `test_el_operador_es_el_de_esa_ronda` (el mismo rival con Ash en una
  ronda y Thermite en otra: una muerte en cada fila);
  `test_muestra_minima_en_el_borde` (`min_deaths` igual a `with_data` sale,
  uno mas no; el corte mira `with_data`, no `deaths`);
  `test_filtro_de_lado_aplica_sobre_tu_fila`;
  `test_sin_muertes_no_rompe`; `test_consultas_constantes`
  (`assertNumQueries(2)`: tus ids y la agrupada, con 1 y con 6 rondas);
  `test_api_duels_trae_headshot_operators_con_min_duels`
  (`min_duels=1` deja salir una fila de una muerte; el default 3 no).
- `frontend/src/muertesHeadshot.js`: `filasHeadshotPorOperador(data)` ->
  `data.operators` con `orden` (el de la API) o `[]`; y
  `conPocaMuestraPorOperador(filas)` (alguna fila con `0 < with_data <
  MUESTRA_CORTE`). `muertesHeadshot.test.js` (vitest): sin datos `[]`; el
  orden de la API se conserva; aviso de muestra en 29 y no en 30.
- `frontend/src/pages/Duelos.jsx`: dentro del panel "Muertes por headshot",
  debajo de la tabla Tú / Tus compañeros, `<h3>` "Por operador rival" y una
  `DataTable`: Operador (`left`), Muertes con dato (`with_data`), % headshot
  (`pct`, `digits: 0`, `suffix: '%'`), vs. tu % (`diff`, con el componente
  `Diferencia` que ya esta en la pagina y `mejorSiSube={false}`: que te
  enganchen menos es lo bueno; `help`: "Puntos contra tu % headshot de todas
  tus muertes con dato (Tú, Total). Sin banda de ruido."). `initialSort`
  por `orden`, `rowKey` el operador, `csvName`
  `muertes-por-headshot-por-operador`, `empty`: "Ningún operador rival llega a
  {minDuels} muertes con dato con estos filtros." Nota de muestra chica con
  `conPocaMuestraPorOperador` ("Ojo: algún operador tiene menos de 30
  muertes con dato; la diferencia puede ser varianza."). Usa el selector
  "Muestra mínima" que ya tiene la pagina; el panel no lleva otro. Si la
  tabla de arriba esta vacia (sin muertes con dato), tampoco se muestra
  esta. Sin grafico (dataviz: no aplica).
- `frontend/e2e/humo.spec.js`: test "Duelos muestra los headshots que
  recibes por operador rival": panel por `section.panel` + heading
  "Muertes por headshot", la tabla de `h3` "Por operador rival" con tantas
  filas como `headshot_operators.operators` de `/api/duels/?min_duels=3`
  (con `seed_demo`: 6, Rook primero con 39 muertes con dato, 28 % y +3
  contra 24,9 %), la primera fila con los numeros de la API formateados a
  mano, consola limpia.
- `docs/metricas.md`: fila **Headshots que recibes por operador rival**
  justo debajo de **Muertes por headshot** (tabla de Duelos), con la regla
  de arriba, y en `## Muestra minima` la fila "Headshots por operador
  rival": el selector de Duelos sobre muertes con dato para salir, 30 para el
  aviso.

**Orden:** tests Django en rojo -> `headshot_deaths_by_operator` -> clave en
`duels()` -> vitest -> helpers -> tabla en el panel -> e2e -> `metricas.md`
-> `npm run build`.

**Puede romperse:** el e2e de la 137 cuenta `table tbody tr` dentro del
panel "Muertes por headshot" (`toHaveCount(2)`): con una segunda tabla en el
panel ese locator toma las dos; el Dev lo acota a la primera tabla
(`panel.locator('table').first()`) en el mismo cambio. Si una sesion cambia
`_solo_rivales`, este agregado y `duels_by_operator` cambian juntos (es lo
buscado).

**Archivos ocupados:** `aggregates.py`, `views.py`, `humo.spec.js` y
`metricas.md` los tocan la 138, la 139 y la 79 con cambios aditivos en otros
lugares (otras funciones, otras vistas, otros tests, otras filas):
no frena. `Duelos.jsx` y `muertesHeadshot.js` no los toca ninguna rama
abierta.

**Verificacion manual:** `seed_demo` + `runserver`, `/duelos`: debajo de la
tabla Tú / Tus compañeros, "Por operador rival" con 6 filas, Rook arriba
(28 %, +3); con "Muestra mínima" en 40, la nota de vacio; con "Solo
defensa", los operadores son los de ataque.

Skills: no aplica (agregado con precedentes `duels_by_operator` y `headshot_deaths`).
Skills del repo: statistical-analysis (denominador = muertes con dato, `n` a la vista, diferencia contra tu total y no promedio de promedios, sin banda de ruido como vs. promedio, aviso con 30 eventos por grupo), testing-strategy (regla, corte y API en `TestCase`, helpers en vitest, tabla en e2e sobre `seed_demo`).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

(nada)
