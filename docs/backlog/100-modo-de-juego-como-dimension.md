# 100. Modo de juego como dimension

estado: aprobado
candado: release 2026-11-06T06:01Z
rama: claude/equipo-dev/100-modo-de-juego-como-dimension
tipo: funcionalidad
epica: temporada-y-modo
area: fullstack
prioridad: 3
fuente: A7 de ALCANCE.md; sigue a la ficha 77 (selector de tipo de partida) y a la 96 (filtros en la URL)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/modoDeJuego.js, frontend/src/modoDeJuego.test.js, frontend/src/components/Filters.jsx, frontend/src/filtrosUrl.js, frontend/src/filtrosUrl.test.js, frontend/src/pages/Trends.jsx, backend/tests/test_modo_de_juego.py, frontend/e2e/modo-de-juego.spec.js, docs/metricas.md
turnos: po 20261106T0319Z-cqz8j6p, arquitecto 20261106T0438Z-c2U4Qx9, dev 20261106T0503Z-cNnHCRB, revisor 20261106T0530Z-cjYLw9e, qa 20261106T0554Z-c7uH5QP

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En partidas rapidas y no clasificatorias se juega Bomba, Rehen y Area
segura, y hoy todo se mezcla: los sitios, el winrate de ataque y la duracion
de las rondas de Bomba suman rondas de Rehen. Con un selector "Modo" en la
barra y una tabla "Por modo" en Tendencias se separa el modo que te va bien
del que no.

## Criterios de aceptacion

- [x] `_filters` acepta `gamemode` (texto, como `match_type`) y
      `base_queryset` y `match_queryset` filtran por `Match.gamemode`; un
      modo que no existe da listas vacias y 200, no 500. Test con una partida
      `Bomb` y una `Hostage`: `/api/overview/?gamemode=Hostage` cuenta solo
      las rondas de la segunda.
- [x] `GET /api/filters/` devuelve `gamemodes` (los valores presentes,
      ordenados, sin vacios) y la barra muestra el selector "Modo" con
      "Todos" y nombres en castellano para los conocidos (Bomba, Rehén, Área
      segura, Bomba rápida; un `Unknown(...)` sale tal cual). Con un solo
      modo en la base el selector no aparece. Vitest de la funcion que arma
      las opciones.
- [x] `gamemode` entra a `CLAVES_DE_URL` de `filtrosUrl.js` (ficha 96), con
      la misma validacion de texto que `match_type`. Vitest: la query
      `?gamemode=Hostage` sobrevive ida y vuelta.
- [x] `GET /api/trends/` agrega `by_gamemode`: por modo, partidas,
      winrate de partida (`won=None` fuera del %), winrate de ronda, K/D y
      rating con `derive`; Tendencias lo muestra en una tabla "Por modo"
      solo si hay mas de un modo. Test con los numeros a mano.
- [x] El e2e cambia el selector de modo con `seed_demo` (si el seed tiene
      un solo modo, el Arquitecto decide si suma una partida de otro modo y
      ajusta los numeros que afirman las pruebas) y la consola queda limpia.

## Fuera de alcance

- Reglas propias por modo (sitios de Rehen, condicion de victoria de Area
  segura): el corte es solo de filtro y tabla.
- Temporada como dimension (A3): idea aparte.
- Cambiar el selector "Tipo" (ficha 77).
- Coordinar con la ficha 79 (PR #81, espera al humano), que tambien toca
  `base_queryset` y `match_queryset`: orden de merge, no decision.

## Diseno

Revisado contra `origin/dev@f0444b5`. Una sola forma obvia: copia el camino
del selector "Tipo" (ficha 77) y la fila por grupo de `by_stack` (ficha 54).
Sin migracion, sin `recompute`, sin parser: `Match.gamemode` ya existe
(`models.py:80`) y `ingest.py:166` lo llena con el nombre de
`pydissect/constants.py:GAME_MODES` (`Bomb`, `SecureArea`, `Hostage`,
`QuickMatchBomb`) o `Unknown(<id>)`. Sin arena ni consenso (chica, de una
forma, reversible). Sin cambio de `seed_demo`: el e2e mete el segundo modo
interceptando la API, como ya hace el de la 77 con `Unranked`
(`humo.spec.js:931`), asi ningun numero que afirman las pruebas se mueve.

### Backend

1. `backend/replays/analytics/aggregates.py`
   - `FILTER_KEYS`: agregar `"gamemode"` despues de `"match_type"`.
   - `base_queryset`: `if filters.get("gamemode"): qs = qs.filter(round__match__gamemode=filters["gamemode"])`,
     justo debajo del de `match_type`.
   - `match_queryset`: `if filters.get("gamemode"): qs = qs.filter(gamemode=filters["gamemode"])`,
     idem. Un modo inexistente da querysets vacios: el 200 sale solo.
   - Funcion nueva `by_gamemode(**filters) -> list[dict]`, al lado de
     `by_start_side` (misma familia: dato de la partida, no de la ronda).
     Calco de `by_stack` sin los habituales:
     ```python
     por_partida = _por_partida(**filters)
     datos = dict(Match.objects.filter(id__in=list(por_partida)).values_list("id", "gamemode"))
     won = dict(Match.objects.filter(id__in=list(por_partida)).values_list("id", "won"))
     baseline = rating_baseline()
     grupos: dict[str, list[int]] = {}
     for mid in por_partida: grupos.setdefault(datos.get(mid) or "", []).append(mid)
     ```
     (una sola query con `values_list("id", "gamemode", "won")` esta bien
     tambien.) Por grupo: `t = _fold([por_partida[m] for m in mids], baseline)`
     y la fila
     `{"gamemode", "matches", "matches_decided", "matches_won", "match_winrate", "rounds", "rounds_won", "winrate", "kd", "rating"}`
     con `match_winrate = _pct(ganadas, decididas)` sobre `won is not None`
     (como `by_stack`). Orden: `-matches`, despues `gamemode`. El modo vacio
     (`""`, partidas viejas sin cabecera de modo) sale como su propia fila con
     `gamemode: ""`; la UI lo llama "Sin modo". Ojo con el `IN`: `por_partida`
     puede tener cientos de ids; mismo patron que `by_stack` (`id__in` sobre
     una lista de ids de partidas, no de rondas), aceptado ahi.
     Docstring: el modo es de la partida; con filtro de lado, el winrate de
     partida sigue siendo el de la partida entera, como `by_start_side`.
2. `backend/replays/views.py`
   - `_filters`: agregar `"gamemode"` a la tupla de claves de texto
     (`views.py:59`).
   - `filter_options`: `"gamemodes": sorted({g for g in Match.objects.values_list("gamemode", flat=True).distinct() if g})`,
     al lado de `match_types`.
   - `trends`: `"by_gamemode": agg.by_gamemode(**filters)`.

### Frontend

3. `frontend/src/modoDeJuego.js` (nuevo, logica pura, para vitest):
   - `NOMBRES_DE_MODO = { Bomb: 'Bomba', Hostage: 'Rehén', SecureArea: 'Área segura', QuickMatchBomb: 'Bomba rápida' }`.
   - `nombreDeModo(modo)`: el nombre en castellano; `''` -> `'Sin modo'`;
     cualquier otro (incluido `Unknown(123)`) tal cual.
   - `opcionesDeModo(gamemodes)`: `[{value:'', label:'Todos'}, ...]`, sin
     vacios ni repetidos, en el orden de la API, label con `nombreDeModo`.
     Mismo contrato que `opcionesDeTipo` de `tipoPartida.js`.
   - `mostrarSelectorDeModo(gamemodes, elegido)`: `true` si hay 2 o mas
     modos distintos **o** si hay uno elegido (un enlace con `?gamemode=X`
     y una base de un solo modo tiene que mostrar que esta filtrando, si no el
     usuario ve 0 rondas sin selector que lo explique).
   - `filasPorModo(byGamemode)`: agrega `modo: nombreDeModo(row.gamemode)` a
     cada fila; `hayVariosModos(byGamemode)`: `(byGamemode ?? []).length > 1`.
4. `frontend/src/components/Filters.jsx`: `<label>Modo <select>` despues de
   "Tipo", `value={value.gamemode || ''}`, `onChange={set('gamemode')}`,
   opciones de `opcionesDeModo(data?.gamemodes)`, renderizado solo si
   `mostrarSelectorDeModo(data?.gamemodes, value.gamemode)`. "Limpiar" ya lo
   cubre (`hayFiltros`).
5. `frontend/src/filtrosUrl.js`: `'gamemode'` en `CLAVES_DE_URL` despues de
   `'match_type'`. Cae en el `default` de `validar` (texto de hasta 64): la
   misma validacion que `match_type`, nada que agregar al switch.
6. `frontend/src/pages/Trends.jsx`: Panel nuevo `title="Por modo"` con
   `hint="Partidas, rondas y rendimiento en cada modo de juego. Las partidas sin resultado no entran en Ganadas."`,
   **inmediatamente antes** del Panel "Por hora del día" (linea ~910 en
   dev), renderizado solo si `hayVariosModos(data.by_gamemode)`. `DataTable`
   con columnas `modo` (left, "Modo"), `matches` ("Partidas"),
   `match_winrate` ("Ganadas", `%`, help "Partidas ganadas sobre las que
   tienen resultado."), `winrate` ("Rondas ganadas", `%`), `kd` ("K/D", 2
   digitos), `rating` ("Rating", 2 digitos), `rowKey={(r) => r.gamemode || 'sin-modo'}`,
   `csvName="por-modo"`, `initialSort={{ key: 'matches', dir: 'desc' }}`.
   Se elige ese lugar y no junto a "Por mitad" porque las ramas 98 y 99
   tocan Trends.jsx en las lineas 18-21, 229-265, 468-516 y 678-700: abajo
   de 900 no choca con ninguna.

### Tests

- `backend/tests/test_modo_de_juego.py` (nuevo), `ModoDeJuegoTests` con
  `make_match(gamemode=...)` (la factory ya lo acepta): una `Bomb` de 3
  rondas ganada 3-0, una `Bomb` de 2 rondas perdida 0-2 (`my_score=0,
  opponent_score=2`) y una `Hostage` de 2 rondas; kills a mano.
  - `test_filtrar_por_hostage_cuenta_solo_sus_rondas` (`/api/overview/?gamemode=Hostage` -> 2 rondas; sin filtro -> 7).
  - `test_un_modo_que_no_existe_da_cero_rondas_y_no_500` (overview, trends, matches con `?gamemode=Nada`: 200 y 0).
  - `test_el_listado_de_partidas_respeta_el_modo` (lo que usa `match_queryset`: `GET /api/matches/`, `views.py:415`, con `?gamemode=Bomb` devuelve 2).
  - `test_las_opciones_listan_cada_modo_una_vez_sin_vacios` (con una partida `gamemode=""` extra: `["Bomb", "Hostage"]`).
  - `test_por_modo_suma_partidas_winrate_y_rating_por_modo`: `by_gamemode` con los numeros a mano (Bomb: 2 partidas, 1 de 2 ganadas = 50.0, rondas 5; Hostage: 1 partida); `rating` igual al de `agg.overview(gamemode="Bomb")["overall"]["rating"]`.
  - `test_por_modo_deja_fuera_del_porcentaje_las_partidas_sin_resultado` (una `won=None`: cuenta en `matches`, no en `matches_decided`).
  - `test_por_modo_con_filtro_de_lado_mantiene_el_resultado_de_la_partida`.
- `frontend/src/modoDeJuego.test.js`: `opcionesDeModo` (castellano, `Unknown(9)` tal cual, sin vacios ni repetidos, "Todos" primero); `mostrarSelectorDeModo` (1 modo -> false, 2 -> true, 1 modo y elegido -> true); `nombreDeModo('')` -> "Sin modo".
- `frontend/src/filtrosUrl.test.js`: un caso nuevo, `?gamemode=Hostage` ida y vuelta, y uno de 65 caracteres descartado.
- `frontend/e2e/modo-de-juego.spec.js` (nuevo, archivo propio para no chocar con `humo.spec.js`, que tocan 98 y 99): con `page.route('**/api/filters/**')` agrega `'Hostage'` a `gamemodes` (el seed es todo `Bomb`): el selector "Modo" aparece con "Rehén"; elegirlo dispara `/api/overview/?...gamemode=Hostage`, la URL lleva `gamemode=Hostage` y la pagina muestra el estado de 0 rondas filtradas; "Limpiar" lo saca. Segundo test: Tendencias sin intercepcion **no** muestra "Por modo" (un solo modo); con `page.route('**/api/trends/**')` sumando una fila `Hostage` a `by_gamemode`, el panel "Por modo" aparece con "Bomba" y "Rehén". Los dos con la consola limpia (`consola.js`, como el resto).

### Orden de implementacion

backend (aggregates -> views -> test_modo_de_juego) -> `modoDeJuego.js` y su
vitest -> `filtrosUrl.js` -> `Filters.jsx` -> `Trends.jsx` -> `metricas.md` ->
e2e -> `verificar.sh`.

### docs/metricas.md

Seccion nueva `## Modo de juego` despues de `## Mitades y prorroga`, una tabla:

| Metrica | Definicion |
|---|---|
| **Por modo** | Tus partidas agrupadas por el modo de la cabecera del `.rec` (Bomba, Rehén, Área segura, Bomba rápida; un id que el parser no conoce sale como `Unknown(<id>)`, y una partida sin modo como "Sin modo"). Partidas = partidas con alguna ronda tuya que pasa los filtros. Ganadas = partidas ganadas sobre las que tienen resultado; se lee de la partida entera, como "Lado inicial". Rondas ganadas, K/D y rating: las de siempre sobre las rondas de ese modo. |

`## Base` no describe los filtros de la barra; no se agrega nada ahi.

### Que puede romperse

- Conflicto de texto con ramas abiertas: 79 (PR #81, espera al humano) toca
  `base_queryset`, `match_queryset` y `views.py`; 98 y 99 tocan
  `aggregates.py`, `Trends.jsx` y `metricas.md`. Son lineas distintas, pero
  **Implementar despues de que #98 y #99 se mergeen** (prioriza, no
  bloquea; las dos estan `implementado`). Con 79 no se espera: espera al
  humano y el choque, si lo hay, es de dos `if` contiguos.
- `CLAVES_DE_URL` tiene orden fijo y la query sale canonica: un test de
  `filtrosUrl.test.js` que afirme la query entera con todas las claves puede
  necesitar la clave nueva. Correr vitest antes del e2e.
- Ningun numero existente cambia: sin `?gamemode` los querysets son los
  mismos. Nada que verificar en el PC (sin migracion, recompute, parser ni
  Electron).

### Verificacion manual

`manage.py seed_demo`, `runserver`; `curl -s localhost:8000/api/filters/ | python -m json.tool | grep -A2 gamemodes`
-> `["Bomb"]`; `curl -s "localhost:8000/api/overview/?gamemode=Hostage"` ->
`overall.rounds` 0 y 200; `curl -s localhost:8000/api/trends/ | python -c "import json,sys;print(json.load(sys.stdin)['by_gamemode'])"`
-> una fila `Bomb`. En la UI: con la base del seed no aparece el selector
"Modo" ni el panel "Por modo"; con `?gamemode=Hostage` en la URL el selector
aparece con "Rehén" elegido.

Skills: no aplica (filtro y tabla ya resueltos en el repo: `opcionesDeTipo`, `DataTable`, `by_stack`; sin busqueda).
OMC: plan=— · revisión=— · verificación=— (ficha chica de una forma, sin consenso)

## Implementacion

(dev 20261106T0503Z-cNnHCRB)

Quedo el diseno completo, sin cambio de `seed_demo`:

- Backend: `gamemode` en `FILTER_KEYS`, `_filters`, `base_queryset` y
  `match_queryset`; `GET /api/filters/` devuelve `gamemodes`;
  `agg.by_gamemode` (calco de `by_stack`, con `kd`) en `/api/trends/` como
  `by_gamemode`.
- Frontend: `modoDeJuego.js` (nombres en castellano, opciones, cuando mostrar
  el selector, filas), selector "Modo" en `Filters.jsx`, `gamemode` en
  `CLAVES_DE_URL`, panel "Por modo" en Tendencias antes de "Por hora del día".
- `docs/metricas.md`: seccion `## Modo de juego` despues de `## Mitades y prorroga`.

Criterios -> tests:

- filtro y 200 con modo inexistente: `test_filtrar_por_hostage_cuenta_solo_sus_rondas`,
  `test_un_modo_que_no_existe_da_cero_rondas_y_no_500`, `test_el_listado_de_partidas_respeta_el_modo`.
- opciones: `test_las_opciones_listan_cada_modo_una_vez_sin_vacios`; vitest
  `opcionesDeModo` y `mostrarSelectorDeModo` (`modoDeJuego.test.js`).
- URL: vitest `gamemode sobrevive ida y vuelta y uno demasiado largo se descarta`.
- `by_gamemode`: `test_por_modo_suma_partidas_winrate_y_rating_por_modo`,
  `test_por_modo_deja_fuera_del_porcentaje_las_partidas_sin_resultado`,
  `test_por_modo_con_filtro_de_lado_mantiene_el_resultado_de_la_partida`,
  `test_por_modo_deja_la_partida_sin_modo_en_su_propia_fila`.
- e2e `modo-de-juego.spec.js`: sin selector con un modo; selector con
  intercepcion, filtra (`/api/overview/?...gamemode=Hostage`, URL, "0 rondas
  con estos filtros") y Limpiar lo saca; enlace `/?gamemode=Hostage` con base
  de un modo; Partidas manda el modo; Tendencias con y sin "Por modo".

Desvios del diseno:

- **`partidas.js`**: `gamemode` entra a `CLAVES_DE_PARTIDA`. El diseno no lo
  nombraba y sin eso Partidas mostraba el selector en "Rehén" pero listaba
  todas las partidas (lo encontro la revision ciega). Test vitest en
  `partidas.test.js` y paso e2e.
- **`opcionesDeModo(gamemodes, elegido)`**: suma el modo elegido aunque la
  base no lo tenga. Sin eso, con `?gamemode=Hostage` y base de un solo modo,
  el `<select>` aparecia pero mostraba "Todos" filtrando (lo vio el e2e).
- e2e: el selector se busca con `getByRole('combobox', { name: 'Modo', exact: true })`;
  `getByLabel(..., { exact: true })` compara con el texto entero del `<label>`,
  opciones incluidas, y no encuentra nada (el test "no aparece" pasaba por eso).
- No se espero a la 99 (el diseno decia "prioriza, no bloquea"). La 98 entro a
  dev durante el turno: merge de `origin/dev` con conflicto en
  `aggregates.py` y `views.py` (by_start_side_map y by_gamemode conviven).
  Contra la rama 99 mergea limpio (se movio el import de `modoDeJuego.js`
  en Trends.jsx para no chocar con el suyo).

Revision ciega (omc-code-reviewer, eje de estandares): 1 HIGH (partidas.js,
arreglado), 3 LOW: `datos.get` redundante (arreglado), frase de metricas.md
sobre cuando aparece el selector (arreglada), `matches_decided` vs `decided`
de `by_start_side` (se deja: es el nombre de `by_stack`, la familia que el
diseno manda copiar).

verificar.sh: VERDE 8827e49b7 (1085 tests backend, 273 vitest, 81 e2e), con
dev ya fusionado.

Skills: no aplica (el Arquitecto no busco y el repo ya resuelve filtro y tabla).
OMC: plan=— · revisión=4 hallazgos (3 arreglados) · verificación=—

## Revision 2026-11-06 sobre e6fb3b3

(revisor 20261106T0530Z-cjYLw9e; dev fusionado: 98 y 99 ya en la rama, sin conflicto)

Veredicto: **aprobar** -> `revisado`.

Revision ciega en dos ejes (omc-code-reviewer, sin leer la ficha): estandares
y, por tamano del diff (~460 lineas), intencion contra Que gana / Criterios /
Fuera de alcance. Los dos dieron `aprobar`, sin CRITICAL, HIGH ni MEDIUM.
Eje de seguridad: no aplica (ni POST nuevo, ni externo/, ni pydissect, ni
rutas, ni electron, ni dependencias).

Criterios, uno por uno:

- filtro en `_filters`, `base_queryset` y `match_queryset`, 200 con modo
  inexistente: `test_filtrar_por_hostage_cuenta_solo_sus_rondas`,
  `test_un_modo_que_no_existe_da_cero_rondas_y_no_500`,
  `test_el_listado_de_partidas_respeta_el_modo`. Confirmado leyendo: toda
  vista con filtros de la barra pasa por `_filters`; las consultas directas
  a `Match` en `aggregates.py` usan `id__in` de ids ya filtrados.
- `gamemodes` y selector: test de opciones + vitest de `opcionesDeModo`;
  nombres iguales a `pydissect/constants.py:GAME_MODES`.
- URL: vitest de ida y vuelta y de 65 caracteres.
- `by_gamemode`: tests con numeros a mano (confirmados: Bomb 2 partidas,
  50 %, 5 rondas, 60 %, K/D 4.0).
- e2e `modo-de-juego.spec.js` con consola limpia, sin tocar `seed_demo`.
- Archivos fuera de `archivos:`: `partidas.js` y su test, explicados en
  Implementacion. Fila en `metricas.md`: si. Sin `print`/`console.log`.

Hallazgos (todos LOW, confirmados leyendo el codigo; ninguno bloquea):

- [test] [LOW] `backend/tests/test_modo_de_juego.py`: el test de "filtro de
  lado mantiene el resultado" pasaba tambien si `by_gamemode` leyera el
  resultado de las rondas filtradas (las dos Bomb del setUp ganan/pierden su
  ronda de defensa igual que la partida). **Arreglado por el Revisor** con
  un test que pasa:
  `test_por_modo_con_filtro_de_lado_cuenta_ganada_la_partida_que_perdio_su_defensa`
  (SecureArea 2-1 que pierde su unica defensa sigue contando ganada).
- [intencion] [LOW] `frontend/src/modoDeJuego.js` `hayVariosModos` cuenta
  filas, no modos: una base con Bomb y partidas de `gamemode=""` muestra
  "Por modo" con "Bomba" y "Sin modo" mientras la barra no muestra el
  selector (que descarta vacios). Arreglo sugerido si se quiere unificar:
  `new Set(filas.map(f => f.gamemode).filter(Boolean)).size > 1`. Se deja:
  la tabla con "Sin modo" sigue diciendo algo cierto.
- [estilo] [LOW] `aggregates.py` docstring de `by_gamemode` y fila de
  `metricas.md`: atribuyen "Sin modo" a "cabeceras viejas", pero
  `header._int` da 0 sin `gamemodeid` y el parser lo nombra `Unknown(0)`;
  `ingest.py:166` solo deja `""` si el dict `gamemode` falta entero.
  Arreglo sugerido: "partidas sin dato de modo en la base".
- [intencion] [LOW] `mostrarSelectorDeModo` muestra el selector con un solo
  modo si hay uno elegido; desvio consciente y documentado (sin eso el enlace
  `?gamemode=X` filtra a 0 rondas sin explicacion). Correcto, no se cambia.

verificar.sh: VERDE e6fb3b3 (1092 tests backend, 276 vitest, 82 e2e), con dev fusionado.

Skills: no aplica.
OMC: plan=— · revisión=4 hallazgos (1 arreglado) · verificación=—

## QA 2026-11-06 sobre c77651c

(qa 20261106T0554Z-c7uH5QP; dev sin commits nuevos sobre la rama, merge-tree limpio)

Veredicto: **aprobado**.

`SP` = scratchpad de la sesion; `PY` = interprete del venv. La base sembrada
sale de `sembrar.py` (temporal, no se commitea): `build_dataset(matches=4)`
(4 Bomb 3-3) mas, con `make_match`/`make_round`/`make_round_player` en
Oregon: Hostage 3-1, SecureArea 1-3, `Unknown(7)` 2-2 con `won=None`,
`gamemode=""` 2-0 y una Hostage sin rondas.

- `check.sh` completo: `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --`
  -> `VERDE c77651c04 en 146s: 1092 tests backend, 276 vitest, 82 e2e`.
- Base vacia (`SQLITE_PATH=$SP/vacia.sqlite3 manage.py migrate`, `runserver 8765`):
  `/api/filters/` -> `gamemodes: []`; `/api/overview/?gamemode=Hostage` ->
  rounds 0; `/api/trends/` -> `by_gamemode: []`;
  `/api/matches/?gamemode=Nada&page=-1` -> total 0. Todo 200.
- Base sembrada, `curl localhost:8765/api/overview/?<q>`: sin filtro 38
  rondas; `gamemode=Hostage` 4; `SecureArea` 4; `Unknown(7)` 4; `Nada` 0;
  `Hostage&side=Attack` 2; `Hostage&until=foo` 4; `Hostage&map=oregon` 4;
  `Bomb&match_type=Unranked` 0; `%27%3BDROP` 0; un modo de 300 caracteres 0.
  Todo 200.
- `/api/filters/` -> `['Bomb', 'Hostage', 'SecureArea', 'Unknown(7)']`,
  sin el vacio.
- `/api/trends/` `by_gamemode`: Bomb 4 partidas 0 % (todas 3-3), winrate 50,
  K/D 0.5; `""` 1 partida 100 %; Hostage 1 partida 100 %, winrate 75, K/D 1.5;
  SecureArea 0 %, winrate 25; `Unknown(7)` matches 1, `matches_decided` 0,
  `match_winrate` null. Con `?side=Defense` las rondas bajan a la mitad y el
  % de partidas no cambia (es el de la partida entera, como pide el diseno).
  Con `?gamemode=SecureArea` sale una sola fila.
- `/api/matches/?gamemode=Hostage` -> total 2 (incluida la que no tiene
  rondas); `gamemode=` -> 9 (sin filtro); `gamemode=Unknown(7)` -> 1;
  `page=-1` y `limit=foo` no rompen nada.
- Endpoints vecinos con `gamemode=Hostage`: positioning, operators,
  operators/sites, compare, export?table=maps, players/1, sessions, coach,
  duels, teammates -> todos 200. Cero `Traceback` en los logs de runserver.
- Chromium (playwright sobre la base sembrada): en `/tendencias` el selector
  "Modo" ofrece `Todos, Bomba, Rehén, Área segura, Unknown(7)`. El panel
  "Por modo" muestra las celdas Bomba, Rehén, Área segura, Unknown(7) y Sin
  modo. Al elegir SecureArea la URL queda en `?gamemode=SecureArea`, y con
  esa URL el panel no aparece. `/partidas?gamemode=Unknown(7)` lista 1
  partida. Consola sin errores ni warnings.
- Mutaciones (se rompe el codigo y se corre
  `manage.py test tests.test_modo_de_juego` o
  `vitest run src/modoDeJuego.test.js src/filtrosUrl.test.js src/partidas.test.js`):
  las 8 caen.
  - Sin el filtro de `match_queryset`: 2 fallos.
  - `base_queryset` filtrando por `match_type`: 2.
  - `by_gamemode` sacando el resultado de las rondas: 1.
  - `filter_options` sin descartar los vacios: 1.
  - `mostrarSelectorDeModo` ignorando el modo elegido: 1.
  - `opcionesDeModo` sin el modo elegido: 1.
  - `gamemode` fuera de `CLAVES_DE_PARTIDA`: 1.
  - `gamemode` fuera de `CLAVES_DE_URL`: 1.
- Chunk inicial de `vite build`: 195.34 kB en la rama contra 194.59 kB en
  `origin/dev` (+0.4 %).
- Sin migracion, `recompute`, parser, Electron ni `.ps1`: no hay nada que
  verificar en el PC.

Los dos LOW abiertos de la Revision (`hayVariosModos` cuenta filas, y la
frase "cabeceras viejas") se reproducen tal cual: con Bomb mas `""` aparece
la tabla y no el selector. No bloquean. Quedan para una ficha de pulido si
el PO quiere.

Skills: no aplica.
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier: 6/6 criterios VERIFIED, 2 huecos LOW ya conocidos)
