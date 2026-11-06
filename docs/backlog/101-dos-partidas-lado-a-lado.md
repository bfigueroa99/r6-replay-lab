# 101. Dos partidas lado a lado

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: paridad-referencia
area: frontend
prioridad: 2
fuente: ALCANCE.md R6 (replica/features.csv: la referencia compara partidas)
archivos: frontend/src/compararPartidas.js, frontend/src/compararPartidas.test.js, frontend/src/pages/Comparar.jsx, frontend/src/App.jsx, frontend/src/pages/MatchDetail.jsx, frontend/src/styles.css, frontend/e2e/comparar-partidas.spec.js
turnos: po 20261106T0530Z-ciXX3AM, arquitecto 20261106T0554Z-cFqJHEh

## PR

## Que gana quien usa la app

Elegir dos partidas tuyas (la que ganaste y la que perdiste en el mismo mapa,
o la de hoy contra la de la semana pasada) y ver sus numeros uno al lado del
otro con la diferencia resaltada, sin abrir dos pestañas y comparar de
memoria. Es lo que la referencia hace y la app todavia no.

## Criterios de aceptacion

- [ ] Desde el detalle de una partida hay un control "Comparar con..." que
      lista tus otras partidas (mapa, fecha, marcador) y lleva a una vista
      con las dos; la URL lleva las dos (`/partidas/<a>?vs=<b>` o
      `/comparar/<a>/<b>`), asi se puede recargar y volver.
- [ ] La vista muestra, por partida: mapa (con version), fecha, tipo,
      marcador, rondas ganadas por lado (ataque y defensa), y de tus totales
      (`my_totals`): bajas, muertes, aperturas ganadas y perdidas, muertes
      sin trade, KST y rating. Una columna "Diferencia" con el signo y el
      color de quien sale mejor.
- [ ] El armado de las filas es una funcion pura (sin React) con tests de
      vitest: diferencia con signo, partida sin tu fila (sin `my_totals`) y
      partida sin rondas (ficha 82) devuelven filas con `—` y no rompen.
- [ ] Un id inexistente en la segunda partida muestra el mismo aviso de
      "partida no encontrada" que el detalle (ficha 84), no una pantalla en
      blanco.
- [ ] Entra al e2e (`frontend/e2e/`): abrir dos partidas de `seed_demo`
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

## Revision

## QA

## Para el humano

(nada: la forma de la URL es reversible; el Arquitecto elige entre modo del
detalle y pagina nueva)
