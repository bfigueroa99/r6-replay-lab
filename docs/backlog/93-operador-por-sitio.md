# 93. Operador por sitio contra el resto del sitio

estado: implementado
candado: -
rama: claude/equipo-dev/93-operador-por-sitio
tipo: funcionalidad
epica: paridad-referencia
area: fullstack
prioridad: 3
fuente: O1 de ALCANCE.md; `replica/features.csv` "Delta de win rate de un operador contra la base, por mapa y sitio" (must, partial: la ficha 65 da el delta contra tu lado, falta el corte por mapa y sitio); [aurelix](https://aurelix.app/blog/how-to-analyse-r6-siege-replays)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/tests/test_operador_por_sitio.py, frontend/src/operadorSitio.js, frontend/src/operadorSitio.test.js, frontend/src/pages/Operators.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261105T1945Z-cvqUYh1, arquitecto 20261106T0109Z-cMAPx7f, dev 20261106T0135Z-cYfUHhx, revisor 20261106T0200Z-cC8Xgpa, dev 20261106T0228Z-c6PJnck

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Operadores, una tabla por mapa y sitio que dice con que operador ganas mas
o menos rondas en ese sitio que con el resto de tus operadores ahi: que
operador te rinde en Cocina de Oregon y cual te hunde. Hoy el winrate por
operador (ficha 65) y por sitio van por separado, y la referencia los cruza.

## Criterios de aceptacion

- [ ] Endpoint (o clave nueva en `/api/operators/`, a eleccion del
      Arquitecto) con filas `mapa (version) / sitio / lado / operador`:
      rondas, winrate, winrate del resto del sitio (mismas mapa, sitio y lado,
      otros operadores), delta y margen de ruido. Respeta los filtros globales.
- [ ] Solo filas con al menos 10 rondas del operador en ese sitio y al menos
      10 rondas del resto; el minimo vive en una constante y en
      `docs/metricas.md`.
- [ ] La comparacion es contra el resto del sitio, no contra el total del
      sitio (el operador esta dentro del total: mismo motivo que
      `_contra_el_resto` de la ficha 80), con banda de ruido de proporcion
      combinada (`_ruido_combinado`): veredicto `rinde`, `hunde` o `ruido`.
      Test con numeros fijos de `factories.py` para los tres veredictos.
- [ ] Rondas sin ganador (`my_team_won` nulo) y rondas sin sitio u operador
      quedan fuera del numerador y del denominador; test.
- [ ] En Operadores se ve la tabla nueva, ordenada por |delta|, con texto
      cuando no hay filas con muestra suficiente; e2e con los numeros de
      `seed_demo` (o el texto vacio si el seed no llega a 10 rondas: el
      Arquitecto decide si baja el minimo por parametro en el e2e o ajusta el
      seed).
- [ ] Fila nueva en `docs/metricas.md` con la definicion y el minimo.

## Fuera de alcance

- Señal nueva del Coach sobre esto (si sirve, otra ficha).
- Operadores rivales por sitio (D2, otra idea).
- Corte por temporada (A3).

## Diseno

(arquitecto 20261106T0109Z-cMAPx7f)

Una sola forma obvia (repite el patron "zona contra el resto" de la ficha 80):
sin arena ni consenso. Skills: no aplica (tabla `DataTable` y chip de
veredicto que el repo ya tiene; ningun dominio nuevo).

### Decisiones

- **Endpoint propio, no clave en `/api/operators/`:** `GET /api/operators/sites/`
  con `min_rounds` (default `OPERADOR_SITIO_MIN_RONDAS = 10`). `Operators.jsx`
  ya pide `/operators/` con `min_rounds: 1` para las filas de operador; meter
  la tabla nueva ahi obligaria a un segundo parametro de minimo, y el e2e y
  los tests leen mejor un endpoint con su propio minimo.
- **El filtro `operator` no recorta el resto.** El resto son, por
  definicion, los otros operadores en ese mapa, sitio y lado: si se aplicara
  a la base, el resto quedaria vacio y la tabla vacia. Se calcula la base con
  todos los demas filtros (`side`, `map`, `site`, `match_type`, fechas,
  `session`) y, si viene `operator`, se dejan solo las filas de ese operador
  al final. Va en `metricas.md`.
- **Solo rondas decididas:** la base excluye `operator=""`,
  `round__site=""`, `side=""` y `round__my_team_won__isnull=True`. Ganada =
  `round__my_team_won=True`. Asi el numerador y el denominador son los
  mismos rondas y una ronda sin ganador no cuenta como perdida (a diferencia
  de `RoundPlayer.won`, que si la cuenta).
- **Mapa por version:** agrupar con `_MAPA` + `round__site` + `side` +
  `operator` y etiquetar con `_etiquetar` (mismo criterio que `by_site`,
  ficha 70/74).
- **Ruido:** `_margen_y_veredicto(delta, ganadas_op, rondas_op,
  ganadas_sitio, rondas_sitio, ("rinde", "hunde"))`. Ojo: el docstring de esa
  funcion dice `(peor, mejor)`, pero lo que hace es `nombres[0]` cuando
  `delta > margen`; para winrate el positivo es `rinde`. Corregir el
  docstring a "(delta positivo, delta negativo)" en el mismo cambio (una
  linea, sin tocar la logica). Bandas: `POSICION_BANDAS` (2), la misma
  constante; no se inventa otra.

### Archivos

- `backend/replays/analytics/aggregates.py`: constante
  `OPERADOR_SITIO_MIN_RONDAS = 10` (comentario: por que 10, muestra minima
  del operador y del resto) y funcion `operator_by_site(min_rounds=..., **filters)`
  junto a `by_operator`. Pasos:
  1. `filtros = {k: v for k, v in filters.items() if k != "operator"}`;
     `qs = base_queryset(**filtros)` con las exclusiones de arriba.
  2. Una consulta `values(*_MAPA, "round__site", "side", "operator")
     .annotate(rounds=Count("id"), won=Count("id", filter=Q(round__my_team_won=True)))`.
  3. Totales del sitio en Python sumando esas filas por
     `(slug, map_id, map_name, site, side)` (sin segunda consulta; mismo
     motivo que `spawn_exits`: el total se cuenta antes del minimo, ocultar
     una fila no mueve las demas).
  4. Por fila: `rest_rounds = total - rounds`, `rest_won`, `winrate =
     _pct(won, rounds)`, `rest_winrate = _pct(rest_won, rest_rounds)`,
     `winrate_delta = _delta(winrate, rest_winrate)`, `margin`, `verdict`.
  5. Filtrar `rounds >= min_rounds and rest_rounds >= min_rounds`, y por
     `operator` si vino en `filters`.
  6. `_etiquetar`, renombrar `round__site` -> `site`, ordenar por
     `(winrate_delta is None, -abs(winrate_delta or 0), -rounds, operator)`.
  Devuelve `{"rows": [...], "min_rounds": min_rounds, "bands": POSICION_BANDAS}`.
  Claves de cada fila: `map`, `slug`, `map_id`, `site`, `side`, `operator`,
  `rounds`, `rounds_won`, `winrate`, `rest_rounds`, `rest_winrate`,
  `winrate_delta`, `margin`, `verdict`.
- `backend/replays/views.py`: vista `operators_by_site` con `@require_GET`,
  `_ok(agg.operator_by_site(min_rounds=_min_rounds(request,
  agg.OPERADOR_SITIO_MIN_RONDAS), **_filters(request)))`.
- `backend/replays/urls.py`: `path("operators/sites/", views.operators_by_site,
  name="operators-by-site")`, debajo de `operators/catalog/`.
- `backend/tests/test_operador_por_sitio.py` (nuevo). Helper que crea N
  rondas de un operador en un sitio con K ganadas (patron `zona()` de
  `test_posicion.py`, con `make_round(..., site=...)` y
  `make_round_player(..., operator=...)`; el ganador va en
  `make_round(..., won=True|False|None)` -> `Round.my_team_won`; para una
  ronda sin ganador pasar tambien `won=False` a `make_round_player`, que si no
  copia el `None`). Tests:
  - `test_un_operador_que_gana_mas_que_el_resto_del_sitio_rinde`: Ash 20/20
    vs Zofia 4/20 en el mismo sitio y lado -> Ash `rinde`, delta +80.0,
    Zofia `hunde`.
  - `test_una_diferencia_chica_es_ruido`: 11/20 vs 10/20 -> `ruido`.
  - `test_compara_contra_el_resto_y_no_contra_el_total`: con numeros fijos,
    `rest_winrate` es el del resto (sin el operador) y `rest_rounds =
    total - rounds`.
  - `test_sin_muestra_del_operador_o_del_resto_no_hay_fila`: 9 rondas del
    operador (o 9 del resto) -> sin fila; con `?min_rounds=5` aparece.
  - `test_las_rondas_sin_ganador_no_cuentan`: rondas con `my_team_won=None`
    no suman ni en `rounds` ni en `rest_rounds`.
  - `test_rondas_sin_sitio_u_operador_quedan_fuera`.
  - `test_otro_lado_u_otro_sitio_no_es_el_resto`: el resto es mismo mapa,
    sitio y lado.
  - `test_las_versiones_de_un_mapa_van_separadas`: mismo slug, `map_id`
    distinto -> dos filas con etiqueta de version (como en
    `test_mapa_de_la_partida.py` o el de la ficha 74).
  - `test_el_filtro_de_operador_no_vacia_el_resto`: `?operator=Ash` devuelve
    solo filas de Ash y con `rest_rounds` de los demas.
  - `test_respeta_el_filtro_de_lado`.
- `frontend/src/operadorSitio.js` (nuevo, logica pura): `VEREDICTOS_SITIO =
  {rinde: 'Te rinde', hunde: 'Te hunde', ruido: 'Sin señal'}`,
  `etiquetaSitio(v)`, `claseSitio(v)` (`win` / `loss` / `''`) y
  `textoSinFilas(datos)` -> `Ningún operador llega a ${min} rondas en un sitio
  (ni el resto del sitio).` Reusar `conSigno` y `comoMargen` de
  `posicion.js` importandolos; no copiarlos.
- `frontend/src/operadorSitio.test.js` (vitest): etiqueta y clase de los tres
  veredictos y de uno desconocido; `textoSinFilas` usa el minimo que manda la
  api y cae en 10 si no viene.
- `frontend/src/pages/Operators.jsx`: segundo `useApi('/operators/sites/',
  filters)` y un `Panel` "Por sitio" debajo de Ataque/Defensa con hint
  "Winrate con el operador en ese sitio contra el resto de tus operadores ahí
  (mismo mapa, sitio y lado)." `DataTable` con columnas Mapa, Sitio, Lado
  (`SideChip`), Operador, Rondas, Ganadas (`pct`), Resto (`pct` de
  `rest_winrate`, help con `rest_rounds`), Diferencia (`conSigno`),
  Margen (`comoMargen`), Veredicto (chip con `claseSitio`, `csv:` con la
  etiqueta), `csvName="operadores-por-sitio"`, `rowKey` con
  `slug-map_id-site-side-operator`, sin `initialSort` (el orden del backend
  es por |delta|). Sin filas: `<p className="note">{textoSinFilas(data)}</p>`
  dentro del panel. Un error de esta request no tumba la pagina: `ErrorBox`
  solo dentro del panel.
- `docs/metricas.md`, tabla `## Cortes`, debajo de **vs. tu lado**: fila
  **Operador por sitio** con la definicion: rondas decididas, mismo mapa
  (por version), sitio y lado; resto = otros operadores; minimo 10 del
  operador y 10 del resto (`OPERADOR_SITIO_MIN_RONDAS`); banda
  `2 x error estandar` con proporcion combinada (como "Fuera de posicion");
  el filtro de operador recorta las filas, no el resto.
- `frontend/e2e/humo.spec.js`: test `Operadores muestra el operador por
  sitio`. `seed_demo` no llega a 10 rondas de un operador en un sitio (el
  maximo es 8: Ash y Zofia en Club House B, ataque; medido con el seed
  actual), y todo su ataque se gana y su defensa se pierde, asi que el delta
  es siempre 0. El e2e entonces: (1) en `/operadores` ve el panel "Por
  sitio" con el texto `Ningún operador llega a 10 rondas en un sitio`;
  (2) `page.request.get('/api/operators/sites/?min_rounds=5')` devuelve
  filas y todas con `verdict === 'ruido'` y `winrate_delta === 0`; consola
  limpia. No se toca `seed_demo` (cambiaria numeros de otros e2e).

### Orden

1. `aggregates.py` + tests de Django (rojo -> verde).
2. Vista y url; test de la vista con `?min_rounds=`.
3. `operadorSitio.js` + vitest.
4. `Operators.jsx`, `npm run build`.
5. e2e, `metricas.md`.

### Que puede romperse

- `Operators.jsx` hoy muestra `EmptyState`/`SinRondasFiltradas` segun
  `/operators/`; la segunda request no debe cambiar eso (la vista vacia la
  sigue decidiendo `/operators/`).
- El e2e "Operadores muestra presencia y delta" busca `section.panel` por el
  heading `Ataque` exacto: el panel nuevo se llama "Por sitio", no lo pisa.
- `_margen_y_veredicto` lo usan la 80 y la 89: solo cambia su docstring.

### Verificacion manual

Con la base real: Operadores, panel Por sitio. Elegir un mapa en la barra y
ver que las filas son de ese mapa; filtro Lado = Defensa deja solo defensa.
Una fila `Te rinde` tiene que cuadrar con contar a mano en Partidas.

### Umbral

`10` es el de la ficha; con la base real puede dejar la tabla corta. Si queda
vacia, el humano puede bajarlo (constante y `metricas.md`), no el Dev.

### Archivos ocupados

`aggregates.py`, `views.py` y `metricas.md` los tocan tambien las ramas 79,
92 y 94 (secciones distintas: merge sin conflicto probable). `humo.spec.js`
lo toca la 94. Sin migracion. Prioriza, no bloquea.

OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261106T0135Z-cYfUHhx)

Quedo el diseno completo, en su orden:

- `aggregates.py`: `OPERADOR_SITIO_MIN_RONDAS = 10` y `operator_by_site()`
  junto a `by_operator`. Una consulta agrupada por mapa (version), sitio,
  lado y operador; los totales del sitio se suman en Python antes del minimo;
  resto = total - operador; `_margen_y_veredicto(..., ("rinde", "hunde"))`.
  Docstring de `_margen_y_veredicto` corregido a "(delta positivo, delta
  negativo)", sin tocar la logica.
- `views.py` + `urls.py`: `GET /api/operators/sites/` (`?min_rounds=`).
- `tests/test_operador_por_sitio.py`: 13 tests. Cada criterio:
  - rinde / hunde: `test_un_operador_que_gana_mas_que_el_resto_del_sitio_rinde`
    (Ash 20/20 vs Zofia 4/20, delta +80 / -80, orden por |delta|);
  - ruido: `test_una_diferencia_chica_es_ruido` (11/20 vs 10/20);
  - resto y no total: `test_compara_contra_el_resto_y_no_contra_el_total`
    (35 % y no 50 %);
  - minimo: `test_sin_muestra_del_operador_o_del_resto_no_hay_fila` (con 9
    del operador o 9 del resto no hay fila; `?min_rounds=5` las trae);
  - rondas sin ganador: `test_las_rondas_sin_ganador_no_cuentan`;
  - sin sitio, lado u operador: `test_rondas_sin_sitio_lado_u_operador_quedan_fuera`
    (verificado con un mutante: sin el `exclude(side="")` falla);
  - resto = mismo mapa, sitio y lado: `test_otro_lado_u_otro_sitio_no_es_el_resto`;
  - versiones: `test_las_versiones_de_un_mapa_van_separadas` (Consulate Y7/Y10);
  - filtros: `test_el_filtro_de_operador_no_vacia_el_resto`,
    `test_respeta_el_filtro_de_lado`, `test_respeta_el_filtro_de_mapa`;
  - `test_sin_rondas_devuelve_lista_vacia`, `test_solo_acepta_get`.
- `frontend/src/operadorSitio.js` + vitest (5 tests): etiquetas, clases y
  `textoSinFilas` con el minimo de la api (10 por defecto). Reusa `conSigno`
  y `comoMargen` de `posicion.js`.
- `Operators.jsx`: componente `PorSitio` con su propio `useApi`, panel "Por
  sitio" al final de la pagina; error y vacio quedan dentro del panel.
- `docs/metricas.md`: fila **Operador por sitio** en `## Cortes`, debajo de
  **vs. tu lado**.
- e2e `Operadores muestra el operador por sitio` en `humo.spec.js`: texto
  vacio con el seed, la api con `min_rounds=5` da todo `ruido` y delta 0, y
  ademas (desvio, ver abajo) la tabla renderizada.

Desvios del diseno:

- El e2e suma un paso: intercepta `/api/operators/sites/` con `page.route`
  y le pone `min_rounds=5`, recarga y comprueba que la tabla tiene tantas
  filas como la api y que dice "Sin señal". Sin eso el e2e nunca renderizaba
  `TablaPorSitio` (lo marco el revisor ciego). `seed_demo` no se toco.
- Test extra de filtro de mapa y de 405 al POST.
- La celda Resto muestra las rondas del resto en el `title` (tooltip), no en
  una columna aparte.

No quedo nada sin hacer. Revision ciega `omc-code-reviewer` (revision.md):
aprobar, con 2 hallazgos (MEDIUM: el e2e no renderizaba la tabla; LOW: el
`exclude(side="")` sin test), los dos corregidos.

verificar.sh: VERDE 7086bcc74 (1013 tests backend, 215 vitest, 68 e2e).

Skills: no aplica (patron del repo, ningun dominio nuevo).
OMC: plan=— · revisión=2 hallazgos (2 arreglados) · verificación=—

## Revision 2026-11-06 sobre 5bcfc11

(revisor 20261106T0200Z-cC8Xgpa)

Veredicto: **corregir**. Un HIGH confirmado (eje de intencion) y un LOW.

verificar.sh: VERDE 5bcfc1133 (1013 tests backend, 215 vitest, 68 e2e),
la rama ya contiene `origin/dev`.

Hallazgos:

- [intencion] [HIGH] `frontend/src/pages/Operators.jsx` (`TablaPorSitio`)
  Que pasa: la tabla "Por sitio" no sale ordenada por |delta|, como pide el
  criterio 5. Sale ordenada por Mapa, descendente.
  Por que es cierto: `DataTable` se llama sin `initialSort` y su default es
  `{ key: columns[0].key, dir: 'desc' }` (`components/ui.jsx:166`), con
  `columns[0]` = `map`. `ordenarFilas` vuelve a ordenar y se pierde el orden
  del backend. El e2e no lo ve porque en el seed todos los deltas son 0.
  Arreglo sugerido: el patron de `Trends.jsx:205-221`:
  `rows.map((row, orden) => ({ ...row, orden }))` e
  `initialSort={{ key: 'orden', dir: 'asc' }}`. Un test que lo cubra: en el
  e2e, `route.fulfill` con dos filas de delta distinto y comprobar que la
  de mayor |delta| sale primero (o una funcion pura con vitest).
- [test] [LOW] `backend/tests/test_operador_por_sitio.py:112`
  (`test_rondas_sin_sitio_lado_u_operador_quedan_fuera`)
  Que pasa: si se quita `.exclude(round__site="")` de `operator_by_site`,
  el test sigue pasando. Lo confirme con el mutante: 13 tests OK.
  Por que es cierto: la tanda `rondas("Ash", 5, 0, site="")` forma su propio
  grupo de sitio `""` con 5 rondas, por debajo del minimo, y no entra al
  resto de SITIO_A.
  Arreglo sugerido: dos tandas de 10 sin sitio, por ejemplo
  `rondas("Ash", 10, 0, site="")` y `rondas("Zofia", 10, 10, site="")`, asi
  sin el exclude aparece una fila con `site == ""`.

Criterios: 1, 2, 3, 4 y 6 cubiertos por tests (los de la lista de
Implementacion; los conte y pasan). El 5 esta cubierto a medias: el panel,
el texto vacio y el e2e estan, pero falta el orden (HIGH). Ninguna regla de
`CLAUDE.md` rota: endpoint solo GET con test de 405, sin dependencias, fila
en `metricas.md`, identificadores sin tildes y UI con tildes, sin
`console.log`. El diff no toca archivos fuera de `archivos:`. Fuera de
alcance: nada. El docstring de `_margen_y_veredicto` estaba pedido en el
diseno.

Skills: no aplica.
OMC: plan=— · revisión=2 hallazgos (0 arreglados; 1 HIGH, 1 LOW, los dos confirmados) · verificación=—

## Correccion 2026-11-06

(dev 20261106T0228Z-c6PJnck)

Los dos hallazgos de la revision sobre 5bcfc11, corregidos:

- [HIGH] Orden de la tabla: `operadorSitio.js` suma `conOrdenDelBackend(filas)`
  (numera las filas en una columna `orden`, el patron de `Trends.jsx`) y
  `TablaPorSitio` la usa con `initialSort={{ key: 'orden', dir: 'asc' }}`.
  Test: el e2e `Operadores muestra el operador por sitio` suma un paso con
  `route.fulfill` y dos filas fijas (Bank -30 `hunde`, Oregon +5 `ruido`):
  con el default de `DataTable` (mapa descendente) Oregon saldria primero; el
  e2e exige Bank primero. Vitest de `conOrdenDelBackend` (numeracion y lista
  vacia).
- [LOW] `test_rondas_sin_sitio_lado_u_operador_quedan_fuera`: la tanda sin
  sitio paso a dos de 10 (Ash 10/0 y Zofia 10/10). Mutante: sin
  `.exclude(round__site="")` el test falla (lo corri: FAILED failures=1).

Merge de `origin/dev` (8f3fb74) en la rama, sin conflictos.

Revision ciega `omc-code-reviewer` (revision.md) sobre el diff: aprobar, 1
LOW (el nombre del vitest prometia probar la tabla; renombrado).

verificar.sh: VERDE 2f0fa51f5 (1029 tests backend, 227 vitest, 69 e2e).

Skills: no aplica.
OMC: plan=— · revisión=1 hallazgo (1 arreglado) · verificación=—

## QA

## Pendiente

## Para el humano
