# 125. Teamkill marcado en la timeline de la ronda

estado: en curso 2026-11-13T19:42Z
candado: -
rama: claude/equipo-dev/125-teamkill-marcado-en-la-timeline
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F14
archivos: frontend/src/aperturas.js (esTeamkill), frontend/src/aperturas.test.js, frontend/src/pages/MatchDetail.jsx (Timeline), frontend/src/textoRonda.js, frontend/src/textoRonda.test.js, frontend/e2e/humo.spec.js
turnos: po 20261113T1703Z-ctZvzXQ, arquitecto 20261113T1830Z-cTivbSq

## PR

## Que gana quien usa la app

En la timeline de una ronda del detalle de partida, una baja entre
compañeros lleva un chip "TK" y no se pinta como baja de tu equipo ni del
rival: desde la ficha 67 los teamkills no suman a las bajas, y hoy el feed
los muestra igual que cualquier baja, asi que el numero de la ronda no
cuadra con lo que se lee.

## Criterios de aceptacion

- [ ] Funcion pura nueva en el frontend que dice si un evento es teamkill:
      `kind == "Kill"` y autor y victima estan en `players` de la ronda con
      el mismo `team_index` (la misma comparacion por nick que `_teamkills`
      de `aggregates.py`). Vitest: teamkill, baja a un rival, autor o
      victima que no esta entre los jugadores de la ronda (no es teamkill) y
      evento `Death` (no es teamkill).
- [ ] La linea de un teamkill en la timeline lleva el chip `TK` con
      `title` "Baja entre compañeros: no suma a las bajas", junto a `HS` y
      `tradeada`, y no lleva la clase `mine` ni `against`.
- [ ] Una ronda sin teamkills se ve igual que hoy (el e2e
      `el timeline marca la apertura de cada ronda` sigue verde sin cambios).
- [ ] e2e: con la respuesta de `/api/matches/<id>/` interceptada (como
      `una partida sin rondas muestra su cabecera y un aviso`) para que una
      baja de la primera ronda sea entre dos jugadores del mismo equipo, el
      chip `TK` aparece en esa linea y en ninguna otra; consola limpia.
- [ ] Si la ficha 121 (copiar una ronda como texto) ya esta en dev al
      implementar, el texto copiado marca la misma baja con `TK` entre sus
      marcas; vitest. Si no esta, esta casilla no aplica y la 121 queda
      avisada en `## Para el humano` de esta ficha.

## Fuera de alcance

- Cambiar como se cuentan los teamkills (ficha 67) o la matriz de duelos.
- Marcar teamkills fuera del detalle de partida.
- Backend: `/api/matches/<id>/` ya trae `team_index` de cada jugador y
  autor y victima de cada evento.

## Diseno

(arquitecto 20261113T1830Z-cTivbSq, sobre `origin/dev@ed7bb52`, con la 121
ya en dev) Filtros duros: pasa. Solo frontend sobre lo que
`/api/matches/<id>/` ya trae (`rounds[].players[].team_index`, `events[]`
con `actor`/`target` por nick); sin red, sin dependencias, sin POST, sin
migracion. Una forma obvia, ~120 lineas: sin arena ni consenso. El criterio
5 aplica: la 121 esta en dev (PR #121).

**Donde va la regla: `frontend/src/aperturas.js`**, no un archivo nuevo. Ese
modulo ya es "las marcas de la timeline" y ya lo importan `MatchDetail.jsx` y
`textoRonda.js`: asi ninguno suma una linea de `import` (la 79, que espera al
humano, toca el bloque de imports de `MatchDetail.jsx`; con esto no hay hunk
cerca).

- `export function esTeamkill(ronda, evento)` -> boolean. `true` solo si
  `evento.kind === 'Kill'`, `actor` y `target` no vacios, `actor !== target`
  (un suicidio no es teamkill, como `_teamkills` de `aggregates.py`, que
  excluye `actor_id == target_id`), los dos estan en `ronda.players` y tienen
  el mismo `team_index`. Mismo `Map` nick -> `team_index` que
  `marcasDeApertura` (un nick no puede estar en los dos lados de una ronda).
  Marca los teamkills de **los dos** equipos: la timeline muestra el feed
  entero, y un TK rival tampoco es una baja tuya. (El backend cuenta solo los
  de tu equipo en `teamkills()`; eso no cambia, ficha 67/57.)
- No cambia `marcasDeApertura`: un teamkill sigue pudiendo ser apertura y
  entry (regla de `metrics.py` que `casosApertura.json` fija de los dos lados).

**Tests, `frontend/src/aperturas.test.js`**, `describe('esTeamkill')` con una
ronda armada a mano (`A`, `B` equipo 0; `C` equipo 1):
- `una baja entre companeros es teamkill` (`Kill` A->B).
- `una baja a un rival no lo es` (`Kill` A->C).
- `un nick que no esta entre los jugadores no lo es` (`Kill` A->`Fantasma`, y
  `Fantasma`->A).
- `un Death no lo es` (`Death` con actor A) y `un suicidio no lo es` (`Kill`
  A->A).
- `sin players no lo es` (`players` ausente: `false`, sin tirar).

**`frontend/src/pages/MatchDetail.jsx`, `Timeline`:**
- `import { marcasDeApertura } from '../aperturas.js'` pasa a
  `import { esTeamkill, marcasDeApertura } from '../aperturas.js'` (misma
  linea, no es la zona de la 79).
- En el `map`: `const tk = esTeamkill(round, event)`; la clase pasa a
  `event.kind === 'Kill' && !tk ? (actorIsMine ? 'mine' : 'against') : ''`
  (un TK no pinta la barra de tu equipo ni la del rival, como `Death`).
- Chip despues de `tradeada`: `{tk ? <span className="chip" title="Baja entre
  compañeros: no suma a las bajas">TK</span> : null}`. Sin CSS nuevo: el
  `.chip` neutro alcanza y la linea queda sin color, que es la señal.

**`frontend/src/textoRonda.js`** (criterio 5): en `lineaDeBaja`, que recibe
la ronda (`lineaDeBaja(evento, marcas, ronda)`; se le pasa desde
`textoRonda`), la marca `esTeamkill(ronda, evento) ? 'TK' : null` despues de
`tradeada`, el mismo orden que los chips. El comentario "Un teamkill sale
como mató a ... la timeline tampoco los distingue" pasa a decir que el
teamkill sale como "mató a" con la marca `TK`, como el chip. Import:
`import { esTeamkill, marcasDeApertura } from './aperturas.js'`.

**`frontend/src/textoRonda.test.js`**: el test `un teamkill y una muerte sin
autor usan la etiqueta de la timeline` ya arma `Yo mató a Socio` con los dos
en el equipo 0: su linea esperada pasa a `2:49 Yo mató a Socio (apertura, TK)`
(cambio de valor esperado por pedido de la ficha, no un test debilitado).
Test nuevo `una baja a un rival no lleva TK` si ningun otro lo cubre ya (el
de tres bajas lo cubre: verificar que sigue igual sin tocarlo).

**e2e, `frontend/e2e/humo.spec.js`**, test nuevo `la timeline marca un
teamkill con TK`, despues de `el timeline marca la apertura de cada ronda`,
con el patron de `una partida sin rondas muestra su cabecera y un aviso`
(`page.route` + `route.fetch` + `route.fulfill` con el json cambiado):
tomar `matches[0]`; en el detalle, la primera ronda con algun `Kill`; a su
primer `Kill` se le cambia `target` por el nick de otro jugador del mismo
`team_index` que el `actor` (de `players` de esa ronda; si el equipo del
autor tiene un solo jugador, usar la ronda siguiente que tenga dos). Abrir
`/partidas/<id>`, clic en la pestaña de esa ronda (dentro del panel Rondas:
la matriz de duelos tambien usa `.round-tab`), y: exactamente un
`.timeline .chip` con texto `TK` en el panel; esa `li` contiene
`<actor> mató a <target nuevo>`, no tiene clase `mine` ni `against`; el chip
tiene `title` "Baja entre compañeros: no suma a las bajas". Consola limpia.
El criterio 3 lo cubre `el timeline marca la apertura de cada ronda` sin
cambios (seed_demo no tiene teamkills: ningun `TK` en ninguna ronda); el
test nuevo suma una linea: en una ronda sin la baja cambiada, 0 chips `TK`.

**`docs/metricas.md`**: sin numero nuevo. La fila de teamkills (ficha 57)
puede sumar al final "En la timeline de la ronda, el chip TK marca la baja"
si el Dev la encuentra; no es obligatorio.

**Orden.** `esTeamkill` + vitest (rojo, verde) -> `Timeline` -> `textoRonda`
y su vitest -> e2e -> `npm run build` -> `verificar.sh`.

**Que puede romperse.** El chip `TK` dentro de `.tags` lo leen los e2e que
cuentan `.chip` por texto exacto (`^apertura$`, `^entry$`): no lo tocan.
Una linea TK pierde la clase `mine`/`against`: ningun e2e cuenta esas clases
en `seed_demo` (sin TK, nada cambia). Copiar ronda: solo cambia la linea de
un TK.

**Archivos ocupados.** 79 (espera al humano): `MatchDetail.jsx` en el import
de `api.js`, los `useState` de `DetallePartida` y el `page-head`; este diseno
toca el import de `aperturas.js` (otra linea, no contigua) y `Timeline`:
hunks separados. 120, 122 y 126: `humo.spec.js` en otras zonas; ninguna toca
`aperturas.js`, `textoRonda.js` ni `MatchDetail.jsx`. No se frena.

**Verificacion manual.** `seed_demo` no trae teamkills: con una base real
que tenga uno (la ficha 57 los lista en su panel), abrir esa partida y esa
ronda: chip `TK`, sin barra de color; "Copiar ronda" lo marca `(TK)`.

Skills: no aplica (un chip mas sobre una regla que el repo ya tiene en el
backend).
Skills del repo: testing-strategy (vitest para la regla y el texto, e2e con
respuesta interceptada porque `seed_demo` no tiene teamkills; sin Django: no
toca el backend).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano

- (arquitecto 2026-11-13, no bloquea) Se marcan con `TK` los teamkills de los dos equipos (el feed muestra los dos); el panel de teamkills sigue contando solo los de tu equipo.
