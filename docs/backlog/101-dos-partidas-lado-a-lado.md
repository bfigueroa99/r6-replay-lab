# 101. Dos partidas lado a lado

estado: aprobado
candado: -
rama: claude/equipo-dev/101-dos-partidas-lado-a-lado
tipo: funcionalidad
epica: paridad-referencia
area: frontend
prioridad: 2
fuente: ALCANCE.md R6 (replica/features.csv: la referencia compara partidas)
archivos: docs/metricas.md, frontend/src/compararPartidas.js, frontend/src/compararPartidas.test.js, frontend/src/pages/Comparar.jsx, frontend/src/App.jsx, frontend/src/pages/MatchDetail.jsx, frontend/src/styles.css, frontend/e2e/comparar-partidas.spec.js
turnos: po 20261106T0530Z-ciXX3AM, arquitecto 20261106T0554Z-cFqJHEh, dev 20261106T0621Z-c14zTHs, revisor 20261109T0330Z-c8x1kCc, qa 20261109T0805Z-cTPuCNz

## PR

## Que gana quien usa la app

Elegir dos partidas tuyas (la que ganaste y la que perdiste en el mismo mapa,
o la de hoy contra la de la semana pasada) y ver sus numeros uno al lado del
otro con la diferencia resaltada, sin abrir dos pestañas y comparar de
memoria. Es lo que la referencia hace y la app todavia no.

## Criterios de aceptacion

- [x] Desde el detalle de una partida hay un control "Comparar con..." que
      lista tus otras partidas (mapa, fecha, marcador) y lleva a una vista
      con las dos; la URL lleva las dos (`/partidas/<a>?vs=<b>` o
      `/comparar/<a>/<b>`), asi se puede recargar y volver.
- [x] La vista muestra, por partida: mapa (con version), fecha, tipo,
      marcador, rondas ganadas por lado (ataque y defensa), y de tus totales
      (`my_totals`): bajas, muertes, aperturas ganadas y perdidas, muertes
      sin trade, KST y rating. Una columna "Diferencia" con el signo y el
      color de quien sale mejor.
- [x] El armado de las filas es una funcion pura (sin React) con tests de
      vitest: diferencia con signo, partida sin tu fila (sin `my_totals`) y
      partida sin rondas (ficha 82) devuelven filas con `—` y no rompen.
- [x] Un id inexistente en la segunda partida muestra el mismo aviso de
      "partida no encontrada" que el detalle (ficha 84), no una pantalla en
      blanco.
- [x] Entra al e2e (`frontend/e2e/`): abrir dos partidas de `seed_demo`
      comparadas, ver los dos marcadores y la columna de diferencia, consola
      limpia.

## Fuera de alcance

- Backend nuevo: `/api/matches/<id>/` dos veces ya trae todo.
- Comparar mas de dos partidas, o una partida contra tu promedio (eso es
  Tendencias y E16).
- Comparar jugadores (descartada en ALCANCE.md).
- Comparar ronda por ronda o las timelines.

## Diseno

Arquitecto 20261106T0554Z-cFqJHEh. Pagina nueva y no modo del detalle:
`MatchDetail.jsx` ya tiene 490 lineas y la rama de la 79 lo toca; una pagina
aparte deja el detalle casi igual (un enlace) y la URL recargable sale sola
de la ruta. Sin backend: `/api/matches/<id>/` trae `match`, `rounds` y
`my_totals`, y el selector usa `/api/matches/`.

**Rutas.** `/comparar/:a` (elegir la segunda) y `/comparar/:a/:b` (las dos).
Desde el detalle, un `Link` "Comparar con…" (clase `btn small`, al lado de
"Copiar resumen") a `/comparar/<id>`. Asi el detalle no pide el listado en
cada visita: lo pide solo quien quiere comparar.

**Archivos:**

- `frontend/src/compararPartidas.js` (nuevo, puro, sin React):
  - `opcionesParaComparar(matches, actual)` recibe las filas de
    `/api/matches/` y la partida `a` (`{id, map}`); saca `a` y devuelve
    `{mismoMapa: [...], otras: [...]}`, cada opcion `{id, texto}` con
    `texto = "AAAA-MM-DD HH:MM · <map> · <score> · <result>"`, en el orden
    del listado (mas nueva primero). "Mismo mapa" compara `map` (la etiqueta
    con version de la ficha 70/74), no `map_slug`: Consulate (Y10) y el viejo
    no son el mismo mapa para comparar.
  - `rondasPorLado(rounds)` -> `{Attack: {won, total}, Defense: {won, total}}`
    contando `my_side` y `my_team_won === true`; `won=null` cuenta en `total`
    y no en `won` (igual que la ficha 38).
  - `filasDeComparacion(a, b)` recibe los dos payloads del detalle y devuelve
    `[{clave, etiqueta, a, b, diferencia, mejor}]` con `a`/`b` ya como texto
    para mostrar y `mejor` en `'a' | 'b' | null`. Filas, en este orden:
    Mapa, Fecha (`played_at` a minutos), Tipo (`match_type`), Marcador
    (`score` + `result`), Rondas en ataque (`3 de 6`), Rondas en defensa,
    Bajas (`kills`), Muertes (`deaths`), Aperturas ganadas (`opening_kills`),
    Aperturas perdidas (`opening_deaths`), Muertes sin trade
    (`untraded_deaths`), KST (`kst_pct`, `%`) y Rating (`rating`, 2
    decimales). Las de texto (mapa a marcador) llevan `diferencia: ''` y
    `mejor: null`. Las numericas: `diferencia = a - b` con signo
    (`+3`, `-1`, `0`; KST en puntos `+12`; rating `+0.15`) y `mejor` segun
    una tabla `MAS_ES_MEJOR` (falso para muertes, aperturas perdidas y
    muertes sin trade); con diferencia 0, `mejor: null`. Las de rondas por
    lado comparan el winrate del lado, no el conteo (6 rondas contra 4 no
    es mejor), y su diferencia va en puntos de porcentaje.
  - Sin dato -> `'—'` en la celda y `diferencia: ''`, `mejor: null`: partida
    sin tu fila (`my_totals.rounds === 0`; `my_totals` ausente tambien) y
    partida sin rondas (`rounds: []`, ficha 82; el lado sin rondas da `—`, no
    `0 de 0`). Rating `null` -> `—`.
- `frontend/src/compararPartidas.test.js` (nuevo, vitest).
- `frontend/src/pages/Comparar.jsx` (nuevo): `useParams()` -> `a`, `b`.
  `useApi('/matches/' + a + '/')`; con `b`, otro `useApi` de `b`; sin `b`,
  `useApi('/matches/', {limit: 200})`. Mismo patron que `MatchDetail`
  (componente con `key={a + '-' + (b || '')}` para no arrastrar estado):
  `status === 404` de **cualquiera** de las dos -> `<NoExiste titulo="Esa
  partida no existe" a="/partidas" texto="Ver tus partidas" />` (el mismo de
  la ficha 84). Cabecera: `h1` "Comparar partidas", un `<select>` con
  `aria-label="Comparar con"` (optgroups "Mismo mapa" y "Otras"; sin
  `limit` mayor a 200: `match_list` corta ahi y es suficiente para elegir),
  que al cambiar hace `navigate('/comparar/<a>/<id>')`; enlaces "Ver
  partida" a cada detalle. Con `b`: un `Panel` con tabla simple (no
  `DataTable`: no se ordena ni se exporta) de columnas "", "Partida A",
  "Partida B", "Diferencia"; la celda de diferencia lleva
  `className="mejor-a"` o `"mejor-b"` segun `mejor`. Sin `b`: la nota
  "Elegí la partida con la que comparar." y el selector. `a === b`: se
  muestra igual (todo 0), no es error.
- `frontend/src/App.jsx`: las dos rutas, despues de `/partidas/:id`.
- `frontend/src/pages/MatchDetail.jsx`: solo el `Link` "Comparar con…".
- `frontend/src/styles.css`: `.mejor-a { color: var(--good) }` y
  `.mejor-b { color: var(--bad) }` (la diferencia se lee desde A: verde si A
  sale mejor), mas `td.comparar-dif { text-align: right }` si hace falta.
- `frontend/e2e/comparar-partidas.spec.js` (nuevo).

**Tests (vitest, `compararPartidas.test.js`):**

- `la diferencia lleva signo y respeta si mas es mejor` (bajas 8 vs 5 ->
  `+3`, mejor `a`; muertes 8 vs 5 -> `+3`, mejor `b`).
- `diferencia cero no marca a nadie`.
- `las rondas por lado comparan winrate y no conteo`.
- `una ronda sin ganador cuenta en el total y no en las ganadas`.
- `partida sin tu fila devuelve guiones y no rompe` (`my_totals.rounds: 0`,
  y otro caso sin `my_totals`).
- `partida sin rondas devuelve guiones en los lados` (`rounds: []`).
- `rating nulo es guion`.
- `las opciones sacan la partida actual y separan el mismo mapa`
  (dos versiones del mismo slug con etiqueta distinta caen en "Otras").

**e2e (`comparar-partidas.spec.js`)**, ids desde la API como en
`navegar-partidas.spec.js` (el orden de ids de `seed_demo` no es contrato):
`/api/matches/?limit=2`, abrir `/partidas/<a>`, clic en "Comparar con…",
URL `/comparar/<a>`, elegir `b` en el select "Comparar con", URL
`/comparar/<a>/<b>`, se ven los dos marcadores (`score` de cada uno desde
la API) y el encabezado "Diferencia"; recargar la pagina y seguir viendolos;
`/comparar/<a>/999999` muestra "Esa partida no existe"; consola limpia con
`vigilarConsola`. No afirmar numeros de `seed_demo` mas alla de lo que trae
la API en la misma prueba.

**Orden:** `compararPartidas.js` + tests -> `Comparar.jsx` y rutas -> enlace
en el detalle -> CSS -> e2e -> `npm run build`.

**Que puede romperse:** el `key` del componente (sin el, al cambiar `b` se ve
la comparacion vieja mientras carga); los dos `useApi` con 404 cruzado (el
`status` de `b` tiene que mirarse aunque `a` cargue bien); el `select`
controlado tiene que quedar en `b` actual tras recargar. Conflicto de texto
chico con la rama de la 79 en la cabecera de `MatchDetail.jsx`: si la 79
entra antes, se mergea `dev` y se conserva lo de los dos.

**Metricas:** ninguna nueva (muestra numeros que ya tienen fila en
`docs/metricas.md`). La diferencia de las rondas por lado es la del winrate
de lado, que ya esta definido; no hace falta fila.

**Verificacion manual:** con la base real, comparar una victoria y una
derrota del mismo mapa; abrir una partida de un `.rec` cortado (sin rondas)
como B; cambiar B desde el select y volver con el boton atras del navegador.

Implementar despues de que #79 se mergee si esta lista (prioriza, no
bloquea: solo comparten el enlace de la cabecera de `MatchDetail.jsx`).

Skills: no aplica (una tabla y una ruta nuevas con el patron que el repo ya
usa; sin dominio nuevo, sin busqueda).
Arena: no (la eleccion modo-del-detalle contra pagina es reversible y la
pagina gana por no pisar la 79).
OMC: plan=— · revisión=— · verificación=— (ficha chica, sin consenso)

## Implementacion

Dev 20261106T0621Z-c14zTHs. Hecho el diseño completo, sin backend:

- `frontend/src/compararPartidas.js`: `opcionesParaComparar`, `rondasPorLado` y
  `filasDeComparacion`, como dice el diseño. La diferencia se calcula sobre el
  valor ya redondeado que muestra la celda (un rating de 1.234 contra 1.231
  da `0.00` y no marca a nadie), y `-0` se muestra como `0`.
- `frontend/src/pages/Comparar.jsx`: rutas `/comparar/:a` y `/comparar/:a/:b`
  en `App.jsx`, cargadas en diferido como las demas paginas.
- `MatchDetail.jsx`: solo el `Link` "Comparar con…", al lado de "Copiar resumen".
- `styles.css`: `.mejor-a` en verde y `.mejor-b` en rojo, dentro de
  `table.comparar`, y los encabezados de fila sin mayusculas.
- `docs/metricas.md`: seccion "Comparar partidas" (lo pidio la revision ciega:
  la columna Diferencia es un numero nuevo en la UI).
- Tests: 11 de vitest en `compararPartidas.test.js` (los 8 del diseño, mas
  "kst va en puntos y rating con dos decimales", "las filas de texto van
  primero y sin diferencia" y "sin partida actual o con solo ella en el
  listado no rompe"). El e2e `comparar-partidas.spec.js` va del detalle a
  "Comparar con…", elige B en el select, mira los dos marcadores y la
  columna "Diferencia", recarga, prueba `/comparar/<a>/999999` (el unico 404
  que espera la consola) y exige la consola limpia.

Desvios del diseño:

- **La key del componente es A, y B va en un hijo `ConB` con `key={b}`.** Asi
  al cambiar B desde el selector no se vuelven a pedir A ni el listado de 200
  (lo marco la revision ciega: con la key `a-b` todo se remontaba). Sigue sin
  verse la comparacion vieja mientras carga B. Consecuencia: si B no existe,
  el aviso "Esa partida no existe" sale debajo de la cabecera y del selector,
  no en la pagina entera. Asi se puede elegir otra B sin volver atras. Si A
  no existe, el aviso ocupa la pagina entera, igual que el detalle.
- **Diferencias en puntos con la unidad** (`-33 pts` en los lados, `+12 pts`
  en KST): un `-33` al lado de "4 de 6" contra "3 de 3" se leia como una
  resta de rondas.
- Si B no esta entre las 200 del listado (o es la misma A), el select suma
  una opcion "Partida <id>" para mostrarla elegida despues de recargar.
  `a === b` se muestra con todo en 0, como pide el diseño.

Verificacion: `verificar.sh` VERDE 7abdd640e (1092 tests backend, 287 vitest,
83 e2e).

Verificar en el PC: comparar una victoria y una derrota del mismo mapa con la
base real, y una partida de un `.rec` cortado como B.

Skills: no aplica (la ficha ya decia que no; sin dominio nuevo).
Arena: no (el diseño no deja puntos abiertos).
OMC: plan=— · revisión=5 hallazgos (4 arreglados; `/comparar/5/5` se deja como pide el diseño) · verificación=—

## Revision 2026-11-09 sobre af6eeab

(revisor 20261109T0330Z-c8x1kCc; candado del revisor anterior muerto, 68 h
sin commits sobre la ficha; la rama ya tenia dev entero: 0 commits detras,
`merge-tree` limpio)

Veredicto: **aprobar** -> `revisado`.

Revision en dos ejes hecha por el lider, sin subagente (esta sesion no tiene
la herramienta para lanzar `omc-code-reviewer`): estandares sobre `git diff
origin/dev...<rama>` sin `docs/backlog`, y por tamano (~490 lineas)
intencion contra Que gana / Criterios / Fuera de alcance. Sin CRITICAL, HIGH
ni MEDIUM. Eje de seguridad: no aplica (sin POST, sin `externo/`, sin
`pydissect/`, sin rutas de archivos, sin electron, sin dependencias).

Criterios, uno por uno:

- "Comparar con…" en el detalle lleva a `/comparar/<a>`, el select lista
  las otras partidas (fecha, mapa, marcador, resultado) y la URL lleva las
  dos (`/comparar/<a>/<b>`): e2e `comparar-partidas.spec.js` (clic,
  `selectOption`, URL, recarga y el select sigue en B).
- Mapa con version, fecha, tipo, marcador, rondas por lado y los siete
  totales con columna Diferencia y color: vitest de `filasDeComparacion`
  (orden de filas, signo, `MAS_ES_MEJOR`, winrate de lado y no conteo, KST
  en puntos, rating con dos decimales). Confirmado contra
  `views.match_detail`: `my_totals` sale de `agg.totals` + `derive`, con
  `rounds`, `kills`, `deaths`, `opening_kills`, `opening_deaths`,
  `untraded_deaths`, `kst_pct` y `rating`; `map` usa la misma etiqueta con
  version que `match_list`, asi "Mismo mapa" separa Consulate (Y10).
- Funcion pura con vitest: sin tu fila (`rounds: 0` y sin `my_totals`),
  sin rondas (`rounds: []`) y rating nulo dan `—` y no rompen.
- Id inexistente en B: `NoExiste` "Esa partida no existe" debajo del
  selector (desvio documentado en Implementacion); e2e con
  `/comparar/<a>/999999`. Sonda en Chromium: `/comparar/<a>/abc` da el
  mismo aviso (el atrapa-todo `api_no_existe` contesta 404 en JSON) y
  `/comparar/<a>/<a>` muestra todo en 0 con el select en A.
- e2e con consola limpia salvo el unico 404 esperado.
- Archivos: exactamente los de `archivos:`. Fila en `metricas.md`: si
  ("Comparar partidas"). Identificadores y comentarios sin tildes, UI con
  tildes. Sin `print` ni `console.log`.

Hallazgos (LOW, confirmados; ninguno bloquea):

- [test] [LOW] `frontend/src/compararPartidas.js:9-19` `MAS_ES_MEJOR`:
  ningun test afirmaba el sentido de `opening_deaths` ni de
  `untraded_deaths`; con cualquiera de los dos en `true` las 11 pruebas
  pasaban. **Arreglado por el Revisor** con un test que pasa y que cae con
  cada mutante: `menos aperturas perdidas y menos muertes sin trade es
  mejor` (af6eeab).
- [bug] [LOW] `frontend/src/pages/Comparar.jsx:41-43`: si
  `/api/matches/?limit=200` falla, el select queda deshabilitado para
  siempre con el texto "Cargando partidas…" mientras el `ErrorBox` de abajo
  dice que la API fallo. Reproducido en Chromium con `page.route` devolviendo
  500 a ese listado. Arreglo sugerido: con `listado.error`, la opcion vacia
  dice "No se pudo cargar el listado" (o se oculta el select). No se
  arregla en esta pasada: el error ya se ve y A se sigue mostrando.

verificar.sh: VERDE af6eeabce (1092 tests backend, 288 vitest, 83 e2e).

Skills: no aplica.
OMC: plan=— · revisión=2 hallazgos (1 arreglado) · verificación=— (sin subagentes en esta sesion: la revision la hizo el lider)

## QA 2026-11-09 sobre c2c1656

(qa 20261109T0805Z-cTPuCNz; rama sin commits detras de dev, `merge-tree` limpio)

Veredicto: **aprobado**.

- `check.sh` completo: `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --`
  -> `VERDE c2c165698 en 163s: 1092 tests backend, 288 vitest, 83 e2e`.
- Bases de prueba (scratchpad, nada al repo): sembrada con
  `DATA_DIR=<tmp> SQLITE_PATH=<tmp>/db.sqlite3 python3 manage.py migrate && python3 manage.py seed_demo`
  (29 partidas) mas una partida de `factories.make_match(map_name="Bank", index=900, my_score=0, opponent_score=0)`
  (id 30: sin rondas y `my_totals.rounds == 0`); y una vacia (solo `migrate`).
  `runserver --noreload` en 8031 (sembrada) y 8032 (vacia), bajados al terminar.
- API (sin backend nuevo, vecinos): `curl -s -o /dev/null -w %{http_code}` ->
  `/api/matches/1/` 200, `/30/` 200, `/abc/` 404, `/999999/` 404, `/-1/` 404,
  `/api/matches/?limit=200|-1|foo` 200; base vacia `?limit=200` ->
  `{"total": 0, ..., "matches": []}`.
- App real en Chromium (playwright, script en el scratchpad), consola sin
  errores salvo los 404 esperados:
  - `/partidas/1` -> clic "Comparar con…" -> `/comparar/1`; el select tiene
    "Mismo mapa" (9) y "Otras" (20) y no lista la partida A.
  - `/comparar/1/2`: ataque `4 de 4`/`4 de 4` `0 pts`, defensa `0 de 3`,
    aperturas perdidas `2`/`1` `+1` en rojo (`mejor-b`), rating
    `0.38`/`0.44` `-0.06` en rojo; cotejado con `my_totals` y `rounds` de
    `/api/matches/1/` y `/2/`: coinciden.
  - `/comparar/1/30` (B sin rondas ni fila): toda la columna B `—`,
    diferencia vacia, sin color. `/comparar/30/30`: todo `—`, sin error.
  - `/comparar/1/999999` y `/comparar/1/abc`: cabecera + "Esa partida no
    existe" (desvio documentado). `/comparar/abc`, `/comparar/-1/2` y la base
    vacia: la pagina entera "Esa partida no existe".
  - Cambiar B a 30 en el select -> `/comparar/1/30`; atras -> `/comparar/1/2`
    con el select en 2 y la tabla visible.
  - Viewport 375 px: `scrollWidth` 375, sin scroll horizontal.
  - Listado con 500 (`page.route`): el select queda "Cargando partidas…"
    deshabilitado con el `ErrorBox` debajo. Es el LOW que ya anoto el
    Revisor; no bloquea (A se ve y el error se avisa).
- Chunk inicial (`npx vite build --outDir <tmp>`): dev `index` 195.34 kB ->
  rama 195.52 kB (+0.09 %); `Comparar` va diferido (5.15 kB).
- Mutacion sobre `src/compararPartidas.js` con
  `npx vitest run src/compararPartidas.test.js` (12 tests), cada mutante con
  `sed` y `git checkout` despues: `my_team_won === true` -> `!== false`
  (1 falla), `deaths: true` en `MAS_ES_MEJOR` (1), no excluir la partida
  actual de las opciones (2), mismo mapa por `map_slug` (1). Mueren los 4.
- e2e `comparar-partidas.spec.js` afirma los dos marcadores (desde la API),
  el encabezado "Diferencia", el select en B tras recargar y un unico 404.

Verificar en el PC: lo de `## Implementacion` (victoria contra derrota del
mismo mapa y un `.rec` cortado como B, con la base real).

OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, 0 bloqueantes; 1 LOW ya anotado)

## Para el humano

(nada: la forma de la URL es reversible; el Arquitecto elige entre modo del
detalle y pagina nueva)
