# 143. Quien cierra la ronda

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 3
fuente: ALCANCE.md K7
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/replays/urls.py, backend/tests/test_quien_cierra.py, frontend/src/cierreDeRonda.js, frontend/src/cierreDeRonda.test.js, frontend/src/components/CierreDeRonda.jsx, frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261114T0040Z-chQsvnq, arquitecto 20261118T1211Z-cMNRUxv

## PR

## Que gana quien usa la app

En las rondas que se cierran por eliminacion, cuantas veces la ultima baja
fue tuya cuando ganan, y cuantas fuiste la ultima victima de tu equipo
cuando pierden, por lado: separa al que remata del que abre, que es lo
unico que hoy mide Duelos de apertura.

## Criterios de aceptacion

- [ ] Agregado nuevo sobre tus rondas filtradas con
      `Round.win_condition == "KilledOpponents"`: en las ganadas, la ultima
      baja del feed (`Kill` de mayor `order`, sin teamkills) y si su autor
      eres tu (`closed`); en las perdidas, si la victima de esa ultima baja
      eres tu (`last_to_fall`). `rounds`, conteo y `pct` por lado y total.
      Test con una ronda ganada que cierras, una que cierra un compañero y
      una perdida en que caes ultimo.
- [ ] Las rondas ganadas por objetivo o tiempo (o con `win_condition`
      vacio) no entran. Test.
- [ ] Una ultima baja que es teamkill o muerte sin autor deja la ronda
      fuera del conteo de cierre, no la cuenta como tuya ni ajena. Test.
- [ ] Los filtros globales aplican sobre tu fila; test con filtro de lado.
- [ ] Se ve en Duelos o en el Resumen (el arquitecto elige) como tabla chica
      por lado con el `n` de rondas a la vista y aviso si es chico; sin dato,
      una nota. e2e con `seed_demo` y consola limpia. Fila nueva en
      `docs/metricas.md`.

## Fuera de alcance

- Partirlo por operador (otro tramo).
- Usarlo en el Rating.

## Diseno

(arquitecto 20261118T1211Z-cMNRUxv, sobre dev 2611d85) Filtros duros: pasa
(`Round.win_condition`, `Round.my_team_won`, el feed `Event` con `kind`,
`order`, autor y victima, y `team_index` por ronda: todo se guarda al
importar; sin red, sin dependencias, sin POST, sin migracion ni `recompute`;
se calcula al consultar como `kill_state` y `thrown_advantage`, porque es
una lectura del feed por ronda y no una columna). Una sola forma obvia: sin
arena ni consenso.

**Regla** (va tal cual a `metricas.md`). Universo: tus filas de
`base_queryset(**filters)` (todos los filtros globales aplican, lado
incluido) cuya ronda termino por eliminacion (`round__win_condition ==
"KilledOpponents"`) y tiene ganador (`round__my_team_won` no nulo). La
*ultima baja* de la ronda es su ultimo evento de baja del feed por `order`,
de cualquier tipo (`Kill`, `Death` o `PlayerLeave`), para no premiar con el
cierre una baja que no fue la ultima. Ganada: cuenta si esa ultima baja es
un `Kill` de alguien de tu equipo (con fila en la ronda) sobre un rival (con
fila en la ronda); *la cerraste* si el autor eres tu (`_me_ids()`).
Perdida: cuenta si es un `Kill` de un rival sobre alguien de tu equipo;
*caiste ultimo* si la victima eres tu. Si la ultima baja es un teamkill, una
muerte sin autor, un `Death`, un `PlayerLeave`, o la ronda no tiene feed, la
ronda queda fuera de los dos lados de la division y se cuenta aparte
(`unknown`). Por lado de tu fila (`Attack`, `Defense`) y total:
`won_rounds`, `closed`, `closed_pct = _pct(closed, won_rounds)`,
`lost_rounds`, `last_to_fall`, `last_to_fall_pct`. Conteos sumados; una fila
sin lado cuenta en el total y no en ningun lado. Sin referencia de "1 de 5":
partidas con menos jugadores o abandonos la vuelven falsa; el numero se lee
contra tu propio historial y el de tus otras paginas.

**Numero (statistical-analysis):** proporcion sobre las rondas que cuentan
(no sobre todas las ganadas: una ronda sin dato no es "no la cerraste"), con
el `n` a la vista; muestra minima `MUESTRA_CORTE` = 30 rondas por celda: no
se oculta, se avisa. Sin umbral nuevo.

**Archivos:**
- `backend/replays/analytics/aggregates.py`, junto a `kill_state`:
  `_ULTIMA_BAJA` (`Subquery` del `id` del ultimo `Event` con `kind__in=
  (Event.KILL, Event.DEATH, metrics.PLAYER_LEAVE)` de la ronda, por
  `-order`, espejo de `_PRIMER_EVENTO`) y `closing_kills(**filters) -> dict`.
  Dos consultas mas los ids tuyos: (1) `mine.values("side",
  "round__my_team_won").annotate(n=Count("id"))` para el universo por lado
  y resultado; (2) `Event.objects.filter(Exists(mine.filter(round_id=
  OuterRef("round_id"))), id=_ULTIMA_BAJA)` con `mi_equipo=_MI_EQUIPO`,
  `eq_autor=_equipo_de("actor_id")`, `eq_victima=_equipo_de("target_id")`,
  `lado=_MI_LADO` y el resultado de la ronda, `.values(...)` de una fila por
  ronda; la clasificacion va en Python (es una regla de cinco ramas, mas
  clara que un `Case`). `unknown` = universo menos las que cuentan.
  Devuelve `{"sides": [{"side": "Attack", ...}, {"side": "Defense", ...},
  {"side": "total", ...}], "unknown": n}`, las tres filas siempre.
- `backend/replays/views.py` + `urls.py`: `GET /api/duels/closing/`
  (`views.closing_kills`, url `closing`) al lado de `duels/kill-state/`.
  Endpoint propio, como Estado al matar: `/api/duels/` ya es grande.
- `backend/tests/test_quien_cierra.py` (Django, `factories.py`, rondas 5v5
  como `test_muertes_headshot.py` con `make_event(..., kind=...)` y
  `win_condition` puesto a mano en el `Round`):
  `test_cierras_una_ganada_y_otra_la_cierra_un_companero` (dos ganadas por
  eliminacion -> `won_rounds 2`, `closed 1`, 50.0);
  `test_caes_ultimo_en_una_perdida` (dos perdidas, en una caes ultimo y en
  otra cae un compañero -> 2, 1, 50.0);
  `test_las_ganadas_por_objetivo_o_tiempo_no_entran` (tambien
  `win_condition` vacio y ronda sin ganador);
  `test_una_ultima_baja_que_es_teamkill_queda_fuera_y_suma_a_unknown`;
  `test_una_muerte_sin_autor_o_un_abandono_al_final_quedan_fuera` (`Death`
  y `PlayerLeave` despues del ultimo `Kill`);
  `test_la_ultima_baja_es_la_de_mayor_order` (tu baja primero y la de un
  compañero despues: no la cerraste);
  `test_ronda_sin_feed_suma_a_unknown`;
  `test_parte_por_lado_y_suma_el_total` (una fila sin lado solo al total);
  `test_filtro_de_lado_aplica_sobre_tu_fila`;
  `test_sin_rondas_no_rompe` (tres filas en cero, `pct` None);
  `test_consultas_constantes` (`assertNumQueries(3)` con 1 y con 6 rondas);
  `test_api_duels_closing_responde_con_filtros` (`until=foo`).
- `frontend/src/cierreDeRonda.js` + `cierreDeRonda.test.js` (vitest):
  `hayCierres(data)` (alguna fila con `won_rounds` o `lost_rounds`),
  `filasDeCierre(data)` (Ataque, Defensa, Total con `orden` y `poca` en
  `0 < n < MUESTRA_CORTE` para cada mitad) y `textoCelda(conteo, n, pct)`
  -> "12 de 30 (40%)", raya con `n` 0. Tests: sin datos; orden y
  etiquetas; aviso en 29 y no en 30; raya sin rondas.
- `frontend/src/components/CierreDeRonda.jsx`: panel "Quién cierra la
  ronda" con su `useApi('/duels/closing/', filters)`, tabla Lado / Ganadas:
  la cerraste / Perdidas: caíste último (celdas de `textoCelda`), nota de
  muestra chica, nota con `unknown` ("N rondas por eliminación no entran:
  su última baja no se puede atribuir (teamkill, muerte sin autor, abandono o
  sin feed).") y, sin datos, "Con estos filtros no hay rondas ganadas o
  perdidas por eliminación con su última baja en el feed." Hint: "En las
  rondas que terminan por eliminación, si la última baja fue tuya cuando
  ganan y si fuiste el último de tu equipo en caer cuando pierden. Separa al
  que remata del que abre, que es lo que mide Duelos de apertura." CSV
  `quien-cierra-la-ronda`. Componente aparte y no dentro de `Duelos.jsx`
  porque la 147 toca el panel de headshots de esa pagina: aca `Duelos.jsx`
  cambia en dos lineas (import y `<CierreDeRonda filters={filters} />`
  despues de `<EstadoAlMatar />`).
- `frontend/src/pages/Duelos.jsx`: esas dos lineas.
- `frontend/e2e/humo.spec.js`: test "Duelos muestra quién cierra la ronda":
  panel por heading, numeros de las tres filas contra
  `/api/duels/closing/` formateados a mano, nota de `unknown` si la API la
  trae, consola limpia. Con `seed_demo` (medido sobre la base del e2e, dev
  2611d85): 202 rondas por eliminacion; Ataque ganadas 49 que cuentan, las
  49 cerradas por ti; Defensa perdidas 52, en las 52 caes ultimo; 101 en
  `unknown` (la semilla ordena el feed como dice T7): el test afirma contra
  la API y no contra estos numeros, y no se toca `seed_demo`.
- `docs/metricas.md`: fila **Quién cierra la ronda** en la tabla de Duelos
  junto a **Estado al matar**, con la regla de arriba; y en `## Muestra
  minima` "Quién cierra la ronda | 30 rondas por celda: no se oculta, se
  avisa".

**Orden:** tests Django en rojo -> `_ULTIMA_BAJA` y `closing_kills` ->
vista/URL -> vitest -> helper -> componente y las dos lineas de Duelos ->
e2e -> `metricas.md` -> `npm run build`.

**Puede romperse:** un e2e de Duelos que cuente paneles por posicion (el
nuevo va despues de Estado al matar); `PLAYER_LEAVE` vive en
`metrics.py`: importarlo de ahi, no repetir el literal.

**Archivos ocupados:** `aggregates.py`, `views.py`, `urls.py`,
`humo.spec.js` y `metricas.md` los tocan la 138, la 139 y la 79 con
cambios aditivos en otros lugares; `Duelos.jsx` lo tocara la 147 (disenada)
en el panel de headshots, y esta solo suma dos lineas en otro bloque: no
frena.

**Verificacion manual:** en una base real, Ganadas que cuentan + Perdidas
que cuentan + `unknown` = rondas por eliminacion de *Como se cierran tus
rondas* (Tendencias) con los mismos filtros; con "Solo ataque", Defensa
queda en raya.

Skills: no aplica (lectura del feed con precedentes `kill_state` y `_PRIMER_EVENTO`).
Skills del repo: statistical-analysis (denominador = rondas que se pueden atribuir, `unknown` aparte y no como "no la cerraste", `n` a la vista, `MUESTRA_CORTE` reusado), testing-strategy (regla y API en `TestCase`, helper en vitest, panel en e2e).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

(nada)
