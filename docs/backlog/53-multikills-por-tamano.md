# 53. Multikills por tamaño: 2K, 3K, 4K y ace

estado: implementado
candado: -
rama: claude/equipo-dev/53-multikills-por-tamano
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F10 ([CS Demo Manager](https://cs-demo-manager.com/changelog), [vlr.gg](https://www.vlr.gg/188013/velaris-vs-clg-red-complexity-paradox-invitational-playoffs-lr3/?game=all&tab=performance))
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, backend/tests/test_multikills.py, backend/tests/test_player_stats.py, backend/tests/test_api.py, frontend/src/multikills.js, frontend/src/multikills.test.js, frontend/src/pages/MatchDetail.jsx, frontend/src/pages/Jugador.jsx, frontend/src/pages/Dashboard.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261017T1204Z, arquitecto 20261017T1603Z, dev 20261017T2004Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver cuantas rondas de 2, 3 y 4 bajas hiciste y cuantos aces, en el
scoreboard de cada partida y en la pagina de un jugador. Hoy existe
`multikill_rounds` (2 o mas) y `triple_plus_rounds` (3 o mas) en
`AGGREGATES` (`aggregates.py:147`), pero ninguna pantalla muestra multikills:
`grep -i multi frontend/src` no encuentra nada.

## Criterios de aceptacion

- [ ] `_match_scoreboard` (`views.py:515`) agrega por fila `k2`, `k3`, `k4`
      y `aces`: rondas de ese jugador con exactamente 2, 3, 4 y 5 o mas
      bajas. Test con un jugador con una ronda de cada tamaño y una de 6
      bajas (cuenta como ace).
- [ ] `/api/matches/<id>/` las devuelve en `scoreboard` y en `my_totals`;
      el scoreboard de `MatchDetail.jsx` muestra una columna "Multikills"
      con el formato `2K·3K·4K·ACE` solo con los tamaños mayores que 0
      (vacio si no hubo ninguno), ordenable por el total de rondas con 2 o
      mas bajas.
- [ ] El perfil de jugador (`player_profile`, pagina Jugador) muestra los
      mismos cuatro conteos sobre todas las rondas filtradas de ese jugador,
      y los mismos para vos en el Resumen (`overview`). Las claves nuevas
      salen de `AGGREGATES`/`derive` para que cualquier tabla agrupada las
      tenga sin codigo extra.
- [ ] Teamkills no suman: `RoundPlayer.kills` ya los excluye o no; el test
      fija el comportamiento actual de `kills` y la fila de `docs/metricas.md`
      lo dice.
- [ ] `docs/metricas.md` cambia la fila **Multikill** a la definicion por
      tamaño (2K, 3K, 4K exactos; ace = 5 o mas) sin cambiar `multikill_pct`.
- [ ] El e2e abre una partida de `seed_demo` y encuentra la columna
      "Multikills"; consola limpia.

## Fuera de alcance

- Duracion del multikill (F8) y records por tamaño (E4 ya tiene "mas bajas
  en una ronda").
- Filtro de rondas por tamaño (va con el buscador F1).
- Cambiar `multikill_pct` o el rating.

## Diseno

(Arquitecto 20261017T1603Z, sobre main 9e3d660)

**Filtros de CLAUDE.md.** Pasa todos: sin dependencias, sin red, sin POST nuevo, la
API sigue de lectura con `JsonResponse`, las metricas salen de `RoundPlayer.kills` que
ya se escribe al importar (no hay columna nueva ni migracion ni recompute), y el dato
existe en el `.rec` (bajas por ronda del kill feed; no depende de coordenadas, armas ni
Ubisoft). Nada de overlay.

**Premisas verificadas contra main 9e3d660**

- `multikill_rounds` y `triple_plus_rounds`: `aggregates.py:147-148`, dentro de
  `AGGREGATES` (`:132-153`). Correcto. `derive` (`:168`) solo usa `multikill_rounds`
  para `multikill_pct` (`:200`); `triple_plus_rounds` no lo lee nadie mas que el
  passthrough.
- Sin UI: `grep -ri multi frontend/src` no encuentra nada. Correcto.
- `_match_scoreboard` esta en `views.py:515` (correcto). **No usa `AGGREGATES`**: tiene
  su propio `.values("player_id","username","team_index","is_me").annotate(...)` con
  `kills=Sum("kills")` como alias (`:521`). Consecuencia (verificada en una base de
  `seed_demo`): si se agrega `k2=Count("id", filter=Q(kills=2))` **despues** de ese
  alias en el mismo `annotate`, el `Q(kills=2)` resuelve al alias y SQLite da
  `OperationalError: misuse of aggregate function SUM()`. Antes del alias, o en un
  `.annotate()` previo, funciona. Es la misma trampa que ya comenta `match_list`
  (`views.py:366`).
- `my_totals` = `agg.totals(agg.base_queryset().filter(round__match=match))`
  (`views.py:487`): pasa por `AGGREGATES`/`derive`, asi que las claves nuevas llegan
  solas.
- Jugador: `/api/players/<id>/` -> `agg.player_profile` (`aggregates.py:1810`). La
  pagina muestra los numeros de esa persona desde `theirs` = `totals(suyas)` (sus
  filas en tus rondas filtradas, `:1849`, sin rating). Las claves nuevas llegan solas.
  `with`/`without`/`against` (tus numeros con/sin/contra) tambien las ganan.
- Resumen: `/api/overview/` -> `agg.overview` (`:241`) -> `overall`/`attack`/`defense`
  con `totals`. `Dashboard.jsx:31` lee `overview.data.overall`. Llegan solas.
- **`kills` SI incluye teamkills (premisa del criterio 4 al reves).**
  `pydissect/stats.py:81-85` (`player_round_stats`) suma 1 al autor de todo evento
  `KILL` sin mirar el equipo de la victima; `metrics.analyse_round` (`metrics.py:150`)
  lo copia tal cual e `ingest.py:250` lo guarda. Las secciones Duelos y Matriz de
  duelos descartan teamkills por su cuenta (`metricas.md:196,207`), pero `Bajas`,
  K/D, KPR, rating y `multikill_rounds` los cuentan hoy. El criterio ya preve el
  caso ("el test fija el comportamiento actual"): se fija que un teamkill **suma** y
  `metricas.md` lo dice. Excluirlos solo en multikills haria que `2K` no cuadre con
  la columna Bajas de la misma fila; excluirlos en `kills` cambia K/D, KPR y rating
  de todo el historial (otra ficha, con recompute).
- Ace: no existe nada (`grep -rn "ace\b\|aces" backend frontend/src` sin resultados
  relevantes). En `seed_demo` el maximo es 2 bajas por ronda.
- Efecto de agregar claves a `AGGREGATES` (todo aditivo, nada se rompe):
  - Toda fila de `totals`/`group_by`/`recent_form`/`personal_records`/
    `trend_by_day`/`trend_by_match`/`_por_partida` gana 4 claves. `_fold`
    (`:1165`, sesiones) suma toda clave de `AGGREGATES` que no este en `_PROMEDIOS`:
    son conteos, se suman bien.
  - CSV de `/api/export/` (`export.py`): las tablas que pasan por `group_by`/
    `trend_by_*`/`sessions` ganan 4 columnas al final (`_columnas` hace union de
    claves; `_PRIMERAS` no cambia). Ningun test compara la cabecera de esas tablas
    (`test_export.py:28,48` prueban `to_csv` con filas fijas; `test_dates.py:75`
    cuenta lineas).
  - Los CSV del navegador (`DataTable`) exportan solo las columnas declaradas: no
    cambian.
  - Ningun test compara el set exacto de claves de un `totals` (`grep keys()\|
    assertEqual(set(` en `backend/tests`: solo coach e insights). `DeriveTests`
    (`test_aggregates.py:14`) arma un dict sin las claves nuevas: `derive` tiene que
    tolerarlo (ver abajo).

**Datos de `seed_demo` (corrido contra una base temporal en el scratchpad)**

Tu fila (`BearF99`) es la unica con multikills: `bajas = 2 if indice % 5 == 0` y nunca
mas de 2 (`seed_demo.py:227`). 14 rondas de 2 bajas sobre 203 (`multikill_pct` 6.9),
cero 3K/4K/ace; compañeros y rivales tienen 0 o 1 baja por ronda. Por partida: 2×2K en
`demo-17` (Border), `demo-22` y `demo-27` (Bank); 1×2K en `demo-5`, `-8`, `-9`, `-13`,
`-14`, `-16`, `-18`, `-23`. **La primera de la lista de Partidas (`demo-28`, Bank) no
tiene ninguno**, asi que el e2e no puede usar "la primera fila": busca `demo-17` por
`match_id` en `/api/matches/`. No hace falta tocar `seed_demo` (y no conviene: cambiar
`bajas` mueve los numeros que afirman otros e2e, p.ej. "Primero en caer" y records).

**Formato de la columna**

`<rondas>×<tamaño>` por cada tamaño con rondas > 0, de menor a mayor tamaño, separados
por ` · `: `2×2K · 1×3K · 1×ACE`. Se lee "dos rondas de 2K, una de 3K, un ace". Sin
ninguno: cadena vacia (criterio 2). El `title` de la celda da la version larga
("2 rondas de 2 bajas · 1 de 3 · 1 de 5 o más"). Se ordena por `multikill_rounds`
(rondas con 2 o mas = suma de los cuatro), que viaja en la fila.

**Archivos**

- `backend/replays/analytics/aggregates.py`, justo antes de `AGGREGATES` (`:132`):
  ```python
  #: Rondas por cantidad de bajas. Separado de AGGREGATES porque el scoreboard de
  #: la partida tiene su propio annotate y tiene que contar exactamente igual.
  MULTIKILLS = {
      "k2": Count("id", filter=Q(kills=2)),
      "k3": Count("id", filter=Q(kills=3)),
      "k4": Count("id", filter=Q(kills=4)),
      "aces": Count("id", filter=Q(kills__gte=5)),
      "multikill_rounds": Count("id", filter=Q(kills__gte=2)),
  }
  ```
  En `AGGREGATES` la linea `:147` (`"multikill_rounds": ...`) se reemplaza por
  `**MULTIKILLS,` (queda en el mismo lugar; `triple_plus_rounds` se deja igual: no se
  usa en UI, pero sacarlo cambia el CSV de export sin motivo). Ace es `>= 5` y no `== 5`:
  con revives o un teamkill una ronda puede pasar de 5.
  En `derive` (`:168`), antes del `row.update`: `for clave in ("k2", "k3", "k4",
  "aces"): row[clave] = row.get(clave) or 0` y lo mismo para `multikill_rounds`. Asi
  una fila armada a mano (tests, `_fold`) siempre trae las 4 claves con entero, que es
  lo que el criterio 3 pide ("salen de AGGREGATES/derive").
- `backend/replays/views.py`, `_match_scoreboard` (`:515`): agregar
  `.annotate(**agg.MULTIKILLS)` **antes** del `.annotate(...)` existente, con el
  comentario de por que (el alias `kills=Sum("kills")` de abajo pisa el campo en los
  `Q` que vengan despues: SQLite revienta con `misuse of aggregate function`). No se
  renombra el alias `kills` porque el frontend lo usa como columna y como
  `initialSort`. `match_detail` (`:413`) no cambia: `scoreboard` y `my_totals` ya
  llevan las claves.
- `backend/tests/test_multikills.py` (nuevo; estilo de `test_margen.py`, con
  `factories.make_match/make_round/make_round_player`). setUp: una partida con tu fila
  en 6 rondas de 0, 2, 3, 4, 5 y 6 bajas, mas un compañero (`team_index=0`) con una
  ronda de 2 y un rival (`team_index=1`) sin multikills. Tests:
  - `test_el_scoreboard_cuenta_rondas_por_tamano_y_seis_es_ace` (tu fila: `k2=1,
    k3=1, k4=1, aces=2, multikill_rounds=5`; si el annotate queda mal ordenado este
    test es el que explota con `OperationalError`)
  - `test_el_scoreboard_no_mezcla_jugadores` (compañero `k2=1`, rival todo en 0)
  - `test_los_cuatro_tamanos_suman_multikill_rounds`
  - `test_totals_trae_los_cuatro_conteos` (`agg.totals(agg.base_queryset())`)
  - `test_overview_trae_los_conteos_en_overall_y_por_lado`
  - `test_el_perfil_trae_los_conteos_del_jugador_en_theirs` (el compañero: `k2=1`)
  - `test_el_filtro_de_lado_recorta_los_conteos` (`base_queryset(side="Attack")`)
  - `test_group_by_mapa_trae_los_conteos` (prueba el "cualquier tabla agrupada")
  - `test_derive_sin_las_claves_las_deja_en_cero`
  - `test_multikill_pct_no_cambia` (mismo valor que `multikill_rounds / rounds`)
- `backend/tests/test_player_stats.py`, en `PlayerRoundStatsTests`:
  `test_un_teamkill_suma_a_las_bajas_del_autor` (`kill("A0","A1")` + `kill("A0","B0")`
  -> `A0.kills == 2`, o sea una ronda que hoy cuenta como 2K). Fija el comportamiento
  actual de `kills` con el `LectorFalso` que ya existe; si alguien despues decide
  excluir teamkills, este test es el que tiene que cambiar a proposito.
- `backend/tests/test_api.py`, junto a `test_detalle_de_partida` (`:98`):
  `test_detalle_de_partida_trae_multikills_en_scoreboard_y_my_totals` (las 5 claves en
  cada fila del scoreboard y en `my_totals`).
- `frontend/src/multikills.js` (nuevo, puro, como `margen.js`):
  - `TAMANOS = [['k2', '2K', 2], ['k3', '3K', 3], ['k4', '4K', 4], ['aces', 'ACE', 5]]`
  - `partesMultikills(fila)` -> `[{ clave, etiqueta, rondas }]` solo con `rondas > 0`,
    en orden de tamaño; fila `null`/`undefined` o sin claves -> `[]`.
  - `textoMultikills(fila)` -> `'2×2K · 1×ACE'` o `''`.
  - `detalleMultikills(fila)` -> `'2 rondas de 2 bajas · 1 de 5 o más'` o `''` (para el
    `title`; "1 ronda" en singular si la primera parte es 1).
  - `rondasConMultikill(fila)` -> `fila.multikill_rounds` si viene, si no la suma de
    las cuatro (respuesta vieja cacheada no rompe el orden).
- `frontend/src/multikills.test.js` (vitest). Tests:
  - `arma el texto solo con los tamaños mayores que cero, de menor a mayor`
  - `sin multikills devuelve texto vacío`
  - `una fila ausente o sin las claves no rompe`
  - `el detalle usa singular y plural`
  - `rondasConMultikill usa multikill_rounds y si falta suma los cuatro`
- `frontend/src/pages/MatchDetail.jsx`, columnas del scoreboard (`:167-195`): despues
  de `{ key: 'clutches', label: '1vX' }` agregar
  `{ key: 'multikill_rounds', label: 'Multikills', help: 'Rondas con 2, 3, 4 y 5 o más bajas. Ordena por el total de rondas con 2 o más.', render: (row) => <span title={detalleMultikills(row)}>{textoMultikills(row)}</span>, csv: textoMultikills }`.
  La clave de la columna es `multikill_rounds` para que `ordenarFilas` ordene por el
  total sin tocar `DataTable`. Los KPIs de arriba (`Mini`, `:56-70`) no cambian: tu
  fila del scoreboard ya lo muestra (la ficha no pide un `Mini`).
- `frontend/src/pages/Jugador.jsx`, panel "Sus numeros" (`:146-173`): un `stat` mas
  despues de "Sobrevive": label "Multikills", value `theirs.multikill_rounds`, sub
  `textoMultikills(theirs) || 'ninguna ronda de 2 o más bajas'`. Son los conteos sobre
  las rondas filtradas de esa persona en tus partidas (lo que pide el criterio 3).
- `frontend/src/pages/Dashboard.jsx`, fila de KPIs (`:58-77`): un `Stat3` despues de
  "Sobrevives": label "Multikills", value `String(total.multikill_rounds)`, sub
  `` `${textoMultikills(total) || 'ninguna'} · ${pct(total.multikill_pct)} de tus rondas` ``,
  `value_={null}` (sin color: no hay umbral bueno/malo definido). `.kpis` es
  `auto-fit minmax(150px)`: un noveno stat entra solo.
- `frontend/e2e/humo.spec.js`, despues de `el detalle de una partida muestra la matriz
  de duelos` (`:243`):
  - `test('el scoreboard de la partida muestra multikills', ...)`: `GET
    /api/matches/?limit=200`, toma el `id` de `match_id === 'demo-17'`, `goto
    /partidas/<id>`; panel `Scoreboard de la partida` tiene `th` "Multikills"; la fila
    `tr` con "BearF99" contiene `2×2K`; la de "Chamo" no contiene `×`; click en el
    encabezado "Multikills" (orden desc) deja BearF99 en la primera fila; consola
    limpia.
  - `test('el Resumen muestra tus multikills', ...)`: `goto /`, el `.stat` con label
    "Multikills" muestra `14` y `14×2K · 7% de tus rondas`; consola limpia.
  - En `tu perfil enlaza a los trackers...` (`:287`) una linea mas: el panel "Sus
    numeros" contiene `14×2K`. (Sale de `theirs` de BearF99: sus 203 rondas.)
- `docs/metricas.md`, `## Impacto`, fila `:222` **Multikill** pasa a:
  `| **Multikill (2K, 3K, 4K, ace)** | Rondas con exactamente 2, 3 y 4 bajas, y ace = 5 o
  mas (con revives o un teamkill una ronda puede pasar de 5). Las bajas son las de la
  columna Bajas: todo evento Kill del feed con tu nick como autor, **teamkills
  incluidos**. El scoreboard de la partida las muestra como `2×2K · 1×ACE` (rondas ×
  tamaño, solo los tamaños con alguna ronda) y ordena por el total de rondas con 2 o
  mas. `multikill_pct` (rondas con 2 o mas / rondas) no cambia. |`
  Sugerido (una frase, mismo PR): en **Bajas / muertes** (`:13`) agregar "Incluye
  teamkills; Duelos y la Matriz de duelos los descartan."

**Orden:** aggregates (`MULTIKILLS`, `derive`) + `test_multikills` (totals/overview/
perfil/derive) -> `_match_scoreboard` + tests de scoreboard + `test_api` ->
`test_player_stats` (teamkill) -> `multikills.js` + test -> MatchDetail, Jugador,
Dashboard -> `npm run build` -> e2e -> `metricas.md` -> `scripts/check.sh` (o
`check.ps1`). Un solo tramo: ~40 lineas de backend, ~130 de tests backend, ~60 de
modulo+vitest, ~30 de paginas, ~40 de e2e, 3 de docs (unas 300).

**Que puede romperse**

- El orden de los `annotate` en `_match_scoreboard` (ver premisas): lo cubre
  `test_el_scoreboard_cuenta_rondas_por_tamano_y_seis_es_ace`.
- CSV de `/api/export/`: 4 columnas mas al final en mapas, sitios, spawns,
  operadores, por-ronda, por-dia, por-partida y sesiones. Aditivo; un script de
  usuario que lea por posicion no se rompe porque van al final, uno que lea por nombre
  tampoco.
- Sin migracion ni recompute: `kills` ya esta en cada `RoundPlayer`.
- `seed_demo` no se toca: ningun numero de otro e2e cambia.
- `_fold` (sesiones): las claves nuevas son conteos y se suman; no van a `_PROMEDIOS`.
- Payload un poco mas grande (5 enteros por fila agregada); irrelevante.

**Verificacion manual:** sobre `seed_demo`, `curl -s localhost:8000/api/overview/ |
python -m json.tool | grep -E '"(k2|k3|k4|aces|multikill_rounds)"'` -> en `overall`
`k2: 14`, resto 0, `multikill_rounds: 14`. Abrir `demo-17` desde Partidas (Border):
columna Multikills con `2×2K` solo en tu fila, hover con el detalle, orden por la
columna. Resumen: KPI "Multikills" 14. Tu perfil: "Sus numeros" con `14×2K`. 375 px:
la tabla scrollea dentro de `.table-wrap`, sin scroll horizontal de pagina.

**Archivos ocupados:** no hay ramas abiertas. En paralelo: la 52 agrega
`by_round_length` en `aggregates.py` y toca `views.trends` y `Trends.jsx`; la 54 toca
`views.teammates`, `Teammates.jsx` y `aggregates.py`. Esta ficha toca en
`aggregates.py` solo el bloque `AGGREGATES`/`derive` (`:132-213`) y en `views.py`
solo `_match_scoreboard` (`:515`): sin solape de lineas con ninguna de las dos. Ojo
cruzado: si la 52 o la 54 escriben un test que compara el set exacto de claves de una
fila de `totals`, el que mergee segundo tiene que sumar `k2, k3, k4, aces`. Las dos
fichas que usen `totals`/`group_by` reciben las claves nuevas sin hacer nada.

## Implementacion

(Dev 20261017T2004Z, sobre main 9e3d660)

Quedo el diseno completo: `MULTIKILLS` en `aggregates.py` (dentro de `AGGREGATES` en el
lugar de `multikill_rounds`) y `derive` completa las cinco claves en entero;
`_match_scoreboard` hace `.annotate(**agg.MULTIKILLS)` antes de su annotate con el alias
`kills`; `multikills.js` con su test; columna "Multikills" en el scoreboard (ordena por
`multikill_rounds`, CSV con el texto), stat en "Sus numeros" de Jugador y `Stat3` en el
Resumen; tres e2e; filas **Multikill (2K, 3K, 4K, ace)** y **Bajas / muertes** en
`docs/metricas.md`.

Desvios del diseno:

- El e2e del scoreboard prueba el orden con dos clics (flecha y BearF99 primero en
  desc, ultimo en asc): BearF99 ya encabezaba el orden inicial por bajas, asi que un
  solo clic no probaba nada (hallazgo de la revision ciega).
- El comentario y `metricas.md` ya no dicen "con revives": en Siege un revive no suma
  baja. Pasar de 5 sale de un teamkill o de un modo con respawn; con un teamkill entre
  las 5 la ronda sale ACE sin haber matado a los 5 rivales. Va documentado (ver Para el
  humano del Arquitecto: `kills` incluye teamkills).
- `test_el_scoreboard_cuenta_rondas_por_tamano_y_seis_es_ace` tambien fija que el alias
  `kills` del scoreboard sigue siendo la suma.

Tests por criterio: 1 `test_el_scoreboard_cuenta_rondas_por_tamano_y_seis_es_ace`,
`test_el_scoreboard_no_mezcla_jugadores`, `test_los_cuatro_tamanos_suman_multikill_rounds`;
2 `test_detalle_de_partida_trae_multikills_en_scoreboard_y_my_totals`, e2e `el scoreboard
de la partida muestra multikills`, `multikills.test.js`; 3 `test_totals_trae_los_cuatro_conteos`,
`test_overview_trae_los_conteos_en_overall_y_por_lado`,
`test_el_perfil_trae_los_conteos_del_jugador_en_theirs`, `test_el_filtro_de_lado_recorta_los_conteos`,
`test_group_by_mapa_trae_los_conteos`, `test_derive_sin_las_claves_las_deja_en_cero`, e2e
`el Resumen muestra tus multikills` y la linea `14×2K` en el e2e del perfil; 4
`test_un_teamkill_suma_a_las_bajas_del_autor`; 5 `test_multikill_pct_no_cambia` y la fila
de `metricas.md`; 6 e2e del scoreboard.

Revision ciega previa (subagente con `revision.md`): aprobar, con tres hallazgos menores
corregidos (orden del e2e, tildes en comentarios y nombres de test de `multikills*.js`,
"con revives").

`check.sh`: Todo en verde (656 tests backend, 104 frontend, build ok, 41 e2e).

## Para el humano

- Arquitecto 2026-10-17: `RoundPlayer.kills` **incluye** teamkills (`pydissect/stats.py:81-85`). El diseno lo mantiene para que 2K/3K cuadren con la columna Bajas y lo documenta. Excluirlos de `kills` cambiaria K/D, KPR y rating de todo el historial (P10, decision tuya; seria otra ficha).
