# 51. Matriz de duelos de la partida

estado: implementado
candado: -
rama: claude/equipo-dev/51-matriz-de-duelos-de-la-partida
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F7 ([CS Demo Manager v3.5.0](https://cs-demo-manager.com/changelog), "players duels matrix"; selector de aperturas de [vlr.gg](https://www.vlr.gg/188013/velaris-vs-clg-red-complexity-paradox-invitational-playoffs-lr3/?game=all&tab=performance))
archivos: frontend/src/matrizDuelos.js, frontend/src/matrizDuelos.test.js, frontend/src/components/MatrizDuelos.jsx, frontend/src/pages/MatchDetail.jsx, frontend/src/styles.css, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261015T1711Z, arquitecto 20261015T1811Z, dev 20261015T2004Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En el detalle de una partida, una tabla 5x5 de quien mato a quien (filas tu
equipo, columnas el rival, y al reves), con los headshots: de un vistazo se
ve que rival te paso por encima esa partida y a quien le ganaste todos los
duelos. Duelos agrega entre partidas; esto es una sola, y no necesita
backend: `/api/matches/<id>/` ya trae el feed de cada ronda.

## Criterios de aceptacion

- [ ] Funcion pura en `frontend/src/` que recibe las rondas de
      `/api/matches/<id>/` y devuelve la matriz: por par (autor, victima)
      bajas y headshots, con el equipo de cada uno sacado de las filas de
      jugadores de la ronda (`team_index`); test vitest con una partida de 2
      rondas.
- [ ] Las bajas entre compañeros (teamkills) y las que no tienen autor no
      entran en la matriz (test).
- [ ] Selector "Todas / Solo aperturas": con aperturas, solo cuenta la
      primera baja de cada ronda (test).
- [ ] Una partida sin eventos de baja muestra un texto vacio, no una tabla
      de ceros ni un error.
- [ ] La tabla aparece en `MatchDetail.jsx` y el e2e (`frontend/e2e/`) la
      ve en una partida de `seed_demo` sin errores de consola.

## Fuera de alcance

- Matriz entre partidas (eso es Duelos).
- Endpoint nuevo o columnas nuevas: se arma en el navegador.
- Flechas de ronda y navegacion de PR #14: disenar sin pisar ese diff.

## Diseno

(Arquitecto 20261015T1811Z, sobre main 2a6c86b)

Todo en el navegador: `/api/matches/<id>/` ya trae por ronda `players` (`username`,
`team_index`, `is_me`) y `events` (`kind`, `actor`, `target`, `headshot`, `order`,
`elapsed`), ver `views.py:match_detail`. Los eventos solo traen nombres: el equipo de
cada uno se saca de los `players` **de la misma ronda** (un nick repetido entre equipos
es imposible dentro de una ronda; entre rondas no importa).

**Archivos**

- `frontend/src/matrizDuelos.js` (nuevo; no `duelos.js` para no confundir con
  `pages/Duelos.jsx`). Exporta `matrizDeDuelos(rondas, { soloAperturas = false,
  miEquipo })`:
  1. Por ronda, `equipo = Map(username -> team_index)` desde `round.players`.
  2. Bajas = `events` con `kind === 'Kill'`, ordenados por `order`. Con `soloAperturas`
     solo la primera de ellas que pase el filtro del paso 3 (la apertura es la primera
     baja valida entre rivales; un teamkill no abre la ronda).
  3. Se descartan: sin `actor` o sin `target`, autor o victima fuera de `equipo` (sin
     equipo conocido), y mismo `team_index` (teamkill).
  4. Acumula en `celdas[`${autor}|${victima}`] = { bajas, headshots }`.
  5. Devuelve `{ mios: [...nombres de miEquipo], rivales: [...], celdas, total }`.
     Orden de filas/columnas: por bajas totales desc y nick asc como desempate, para que
     sea estable. `miEquipo` lo pasa la pagina (la funcion `myTeam` que ya existe en
     `MatchDetail.jsx` se aplica a la primera ronda; si no hay, `match.my_team_index`).
  Tambien `celda(matriz, autor, victima)` -> `{ bajas: 0, headshots: 0 }` si no existe.
- `frontend/src/matrizDuelos.test.js` (vitest). Tests:
  - `arma la matriz de una partida de dos rondas con bajas y headshots`
  - `ignora teamkills y bajas sin autor`
  - `solo aperturas cuenta la primera baja entre rivales de cada ronda`
  - `un teamkill no cuenta como apertura`
  - `una partida sin eventos devuelve total cero`
- `frontend/src/components/MatrizDuelos.jsx` (nuevo, componente aparte para que
  `MatchDetail.jsx` cambie lo minimo y no choque con PR #14). Props `rounds`,
  `miEquipo`. Estado local `soloAperturas`; dos botones "Todas" / "Solo aperturas"
  dentro de un `div.round-tabs` (`styles.css:344`, el mismo contenedor de las pestañas de ronda), con el mismo marcado de boton activo que usan esas pestañas en `MatchDetail.jsx`. Dos tablas `<table className="matriz">`: "Tu equipo
  contra el rival" (filas `mios`, columnas `rivales`) y "El rival contra tu equipo"
  (al reves). Celda: `bajas` y, si hay, `(n HS)` en texto chico; 0 se muestra como `·`
  para que se lean las celdas con dato. `title` en la celda: "X mató a Y n veces".
  `total === 0` -> `<p className="note">Esta partida no registró bajas entre equipos.</p>`.
  Textos de UI con tildes.
- `frontend/src/pages/MatchDetail.jsx`: un `import` y un `<Panel title="Matriz de duelos"
  hint="Quién mató a quién en esta partida. Filas: el que mata.">` con
  `<MatrizDuelos rounds={match.rounds} miEquipo={...} />`, **entre** el panel "Rondas" y
  el "Scoreboard de la partida" (linea ~157 de main). Ahi PR #14 no tiene hunk (los
  suyos estan en 145-152 y 164-170): minimiza el conflicto. No tocar `Timeline` ni las
  flechas de ronda.
- `frontend/src/styles.css`: regla `.matriz` minima (celdas centradas, `tabular-nums`,
  cabecera de columna que no rompa en mobile: `overflow-x: auto` en un `div` contenedor).
  Al final del archivo, para no chocar con los 53 lineas que PR #14 agrega.
- `frontend/e2e/humo.spec.js`: `test('el detalle de una partida muestra la matriz de
  duelos')`: abre `/partidas/<id>` de la primera partida de `/api/matches/`, ve el panel
  "Matriz de duelos" con al menos una celda con numero, clic en "Solo aperturas", la
  tabla sigue visible, consola limpia. `seed_demo` crea bajas tuyas y contra ti con
  `actor_name`/`target_name` de jugadores con `team_index` distinto
  (`seed_demo.py:273-289`), asi que la matriz no sale vacia.

Sin backend, sin metrica nueva: los numeros son conteos crudos de bajas del feed; igual
una fila en `docs/metricas.md`, seccion `## Duelos`: **Matriz de duelos (partida)** =
bajas del feed entre jugadores de equipos distintos en esa partida; solo aperturas =
primera de esas bajas por ronda; teamkills y bajas sin autor no cuentan.

**Orden:** matrizDuelos.js + test -> MatrizDuelos.jsx -> MatchDetail.jsx -> css -> e2e ->
metricas.md -> `npm run build` -> `check.sh`.

**Que puede romperse:** build (import nuevo); e2e del detalle de partida existente
(solo agrega un panel, no cambia los que ya cuenta). Si PR #14 se mergea antes, el Dev
mergea main y resuelve el import de `MatchDetail.jsx` (unica zona compartida).

**Verificacion manual:** `npm run dev`, abrir una partida de `seed_demo`, comparar una
celda con el timeline de sus rondas contando a mano.

**Archivos ocupados:** ninguna rama de trabajo abierta.

## Implementacion

(Dev 20261015T2004Z)

Quedo todo el diseno, todo en el navegador (sin backend):

- `frontend/src/matrizDuelos.js`: `matrizDeDuelos(rondas, { soloAperturas, miEquipo })`
  y `celda(matriz, direccion, autor, victima)`.
- `frontend/src/components/MatrizDuelos.jsx`: botones "Todas / Solo aperturas"
  en un `div.round-tabs` con `round-tab active` (el marcado de las pestañas de
  ronda), dos tablas `table.matriz`, `·` para cero, `(n HS)` chico, `title` en
  cada celda, texto vacio si `total === 0`.
- `MatchDetail.jsx`: un import y el panel "Matriz de duelos" entre "Rondas" y
  "Scoreboard de la partida". `miEquipo` = `myTeam(rounds[0])` si da >= 0, si no
  `match.my_team_index`.
- `styles.css`: `.matriz` y `.matriz-scroll` al final del archivo.
- Fila **Matriz de duelos (partida)** en `docs/metricas.md`, seccion Duelos.

**Desvio del diseno** (por la revision ciega previa, hallazgo real): el diseno
asignaba cada nick a un grupo una sola vez y comparaba con el equipo de
`rounds[0]`. Si un nick cambia de `team_index` entre rondas (el parser reparte
equipos por orden de lectura, `pydissect/events.py`), una baja se contaba en
`total` y no aparecia en ninguna tabla. Ahora el lado de cada baja se decide
ronda por ronda con tu `team_index` de esa ronda (tu fila; si no esta, el
`miEquipo` de la partida), y la matriz guarda dos direcciones: `aFavor` y
`enContra`. Por eso `celda` recibe la direccion; un nick puede aparecer en las
dos tablas si jugo en los dos lados.

Tests (`src/matrizDuelos.test.js`, 7): matriz de dos rondas con HS; teamkills y
bajas sin autor; solo aperturas; teamkill no abre; sin eventos; nick que cambia
de equipo entre rondas; ronda sin tu fila usa el equipo de la partida. E2e:
`el detalle de una partida muestra la matriz de duelos`.

Criterios -> tests: 1 `arma la matriz de una partida de dos rondas con bajas y
headshots`; 2 `ignora teamkills y bajas sin autor`; 3 `solo aperturas cuenta la
primera baja entre rivales de cada ronda` + `un teamkill no cuenta como
apertura`; 4 `una partida sin eventos devuelve total cero` (el componente
muestra el texto); 5 e2e.

Revision ciega previa: corregir (el bug de arriba, corregido) y un menor de doc
(la fila de metricas ahora dice que el teamkill tampoco abre la matriz, a
diferencia de Duelos de apertura).

