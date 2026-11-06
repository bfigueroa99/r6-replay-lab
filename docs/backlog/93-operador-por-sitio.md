# 93. Operador por sitio contra el resto del sitio

estado: implementado (espejo; manda la rama)
candado: -
rama: claude/equipo-dev/93-operador-por-sitio
tipo: funcionalidad
epica: paridad-referencia
area: fullstack
prioridad: 3
fuente: O1 de ALCANCE.md; `replica/features.csv` "Delta de win rate de un operador contra la base, por mapa y sitio" (must, partial: la ficha 65 da el delta contra tu lado, falta el corte por mapa y sitio); [aurelix](https://aurelix.app/blog/how-to-analyse-r6-siege-replays)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/tests/test_operador_por_sitio.py, frontend/src/operadorSitio.js, frontend/src/operadorSitio.test.js, frontend/src/pages/Operators.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261105T1945Z-cvqUYh1, arquitecto 20261106T0109Z-cMAPx7f

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

## Revision

## QA

## Pendiente

## Para el humano
