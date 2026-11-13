# 125. Teamkill marcado en la timeline de la ronda

estado: entregado
candado: -
rama: claude/equipo-dev/125-teamkill-marcado-en-la-timeline
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F14
archivos: frontend/src/aperturas.js (esTeamkill), frontend/src/aperturas.test.js, frontend/src/pages/MatchDetail.jsx (Timeline), frontend/src/textoRonda.js, frontend/src/textoRonda.test.js, frontend/e2e/humo.spec.js
turnos: po 20261113T1703Z-ctZvzXQ, arquitecto 20261113T1830Z-cTivbSq, dev 20261113T1926Z-cq9nfTP, revisor 20261113T1926Z-cNCxUZs, qa 20261113T2003Z-c3vr7mZ, release 20261113T2003Z-c3vr7mZ

## PR

Titulo: `[equipo-dev][frontend] Partida: teamkill marcado en la timeline`

### Que cambia

En el detalle de partida, una baja entre compañeros lleva en la timeline el chip `TK` ("Baja entre compañeros: no suma a las bajas") y ya no se pinta como baja de tu equipo ni del rival. Marca los teamkills de los dos equipos. El texto de "copiar ronda" (ficha 121) suma la misma marca `TK`.

### Por que esto y no otra cosa

Ficha 125. Desde la ficha 67 los teamkills no suman a las bajas, pero el feed los mostraba como cualquier baja y el numero de la ronda no cuadraba con lo que se leia. Solo frontend, con lo que `/api/matches/<id>/` ya trae. Descartado: cambiar como se cuentan los teamkills (67) o la matriz de duelos, marcarlos fuera del detalle.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE a398816ff, 1284 tests backend, 411 vitest, 112 e2e (rama fusionada con `origin/dev@d5595cb`).
- Tests nuevos: 6 vitest de `esTeamkill` (teamkill, rival, nick ausente en los dos sentidos, `Death`, suicidio, ronda sin players); vitest de `textoRonda` con `(apertura, TK)`; e2e `la timeline marca un teamkill con TK` con respuesta interceptada (un solo `TK`, su `title`, sin `mine`/`against`, consola limpia).
- Verificacion manual (QA): base sembrada desde `factories.py` con un teamkill de cada equipo; Playwright en `/partidas/1`: 2 `TK` en la ronda 1, 0 en la 2, teclado, contraste 12.92:1, consola limpia; 3 mutaciones, cada una cae en su test.
- OMC: plan=— · revisión=0 hallazgos · verificación=—
- OMC: plan=— · revisión=2 hallazgos LOW (0 arreglados: al humano) · verificación=—
- OMC: plan=— · revisión=— · verificación=PASS
- Skills del repo: testing-strategy, ux-copy (implementacion), accessibility-review (0 Critical, 0 Major), validate-data (sin numero nuevo).

### Riesgos y lo que no entra

Sin backend, sin migracion. Dos LOW del Revisor sin arreglar: con el mismo nick en los dos equipos de una ronda la regla por nick puede marcar mal (misma limitacion que la marca de apertura), y el e2e confirma la ausencia de `TK` en una sola ronda mas. El `title` del chip solo se ve con mouse, como el chip `apertura`.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py runserver
```
Con la base real, abrir una partida con un teamkill (Inicio o Duelos los cuentan): en la timeline de esa ronda la linea lleva `TK` y no tiene barra de color; pasar el mouse por `TK` muestra "Baja entre compañeros: no suma a las bajas". "Copiar ronda" escribe `TK` en esa baja. `seed_demo` no trae teamkills: lo cubre el e2e con respuesta interceptada.

### Para el humano

Nada que decidir. Avisos: se marcan los teamkills de los dos equipos (el panel de teamkills sigue contando solo los tuyos); dos LOW del Revisor los puede sumar un Dev despues.

## Que gana quien usa la app

En la timeline de una ronda del detalle de partida, una baja entre
compañeros lleva un chip "TK" y no se pinta como baja de tu equipo ni del
rival: desde la ficha 67 los teamkills no suman a las bajas, y hoy el feed
los muestra igual que cualquier baja, asi que el numero de la ronda no
cuadra con lo que se lee.

## Criterios de aceptacion

- [x] Funcion pura nueva en el frontend que dice si un evento es teamkill:
      `kind == "Kill"` y autor y victima estan en `players` de la ronda con
      el mismo `team_index` (la misma comparacion por nick que `_teamkills`
      de `aggregates.py`). Vitest: teamkill, baja a un rival, autor o
      victima que no esta entre los jugadores de la ronda (no es teamkill) y
      evento `Death` (no es teamkill).
- [x] La linea de un teamkill en la timeline lleva el chip `TK` con
      `title` "Baja entre compañeros: no suma a las bajas", junto a `HS` y
      `tradeada`, y no lleva la clase `mine` ni `against`.
- [x] Una ronda sin teamkills se ve igual que hoy (el e2e
      `el timeline marca la apertura de cada ronda` sigue verde sin cambios).
- [x] e2e: con la respuesta de `/api/matches/<id>/` interceptada (como
      `una partida sin rondas muestra su cabecera y un aviso`) para que una
      baja de la primera ronda sea entre dos jugadores del mismo equipo, el
      chip `TK` aparece en esa linea y en ninguna otra; consola limpia.
- [x] Si la ficha 121 (copiar una ronda como texto) ya esta en dev al
      implementar, el texto copiado marca la misma baja con `TK` entre sus
      marcas; vitest. Si no esta, esta casilla no aplica y la 121 queda
      avisada en `## Para el humano` de esta ficha.

## Fuera de alcance

- Cambiar como se cuentan los teamkills (ficha 67) o la matriz de duelos.
- Marcar teamkills fuera del detalle de partida.
- Backend: `/api/matches/<id>/` ya trae `team_index` de cada jugador y
  autor y victima de cada evento.

## Diseno

(arquitecto 20261113T1830Z-cTivbSq) `esTeamkill(ronda, evento)` en `aperturas.js` (ya lo importan `MatchDetail.jsx` y `textoRonda.js`): `Kill`, autor y victima distintos, los dos en `ronda.players` con el mismo `team_index`; los dos equipos. Sin cambiar `marcasDeApertura`. Chip `TK` en `Timeline` sin `mine`/`against`; `TK` en `lineaDeBaja` de `textoRonda.js`; e2e con respuesta interceptada. Sin backend ni CSS nuevo.

## Implementacion

(dev 20261113T1926Z-cq9nfTP) Diseno completo, sobre `origin/dev@c332e72`:

- `aperturas.js`: `esTeamkill(ronda, evento)`: `Kill`, autor y victima no vacios, distintos, los dos en `ronda.players` y con el mismo `team_index`; los dos equipos. Tolera `ronda` o `players` ausentes.
- `MatchDetail.jsx` (`Timeline`): import en la misma linea; un TK no lleva `mine` ni `against` y suma el chip `TK` con `title` "Baja entre compañeros: no suma a las bajas", despues de `tradeada`. Sin CSS nuevo.
- `textoRonda.js`: `lineaDeBaja(evento, marcas, ronda)` suma `TK` despues de `tradeada`; comentario al dia.
- e2e `la timeline marca un teamkill con TK`: intercepta `/api/matches/<id>/`, cambia la victima del primer `Kill` de la primera ronda donde el autor tiene compañero; un solo chip `TK`, su `title`, la linea "<autor> mató a <compañero>" sin `mine`/`against`, y 0 `TK` en otra ronda; consola limpia.

Tests vistos en rojo antes del codigo (7: los 6 de `describe('esTeamkill')` en `aperturas.test.js` por funcion inexistente, y `un teamkill y una muerte sin autor usan la etiqueta de la timeline` de `textoRonda.test.js`, que pasa a esperar `(apertura, TK)` por pedido de la ficha). Criterios -> tests: 1 los 6 vitest de `esTeamkill`; 2 e2e nuevo; 3 `el timeline marca la apertura de cada ronda` sin cambios y la ronda sin TK del e2e nuevo; 4 e2e nuevo; 5 (la 121 esta en dev) el vitest de `textoRonda`. El caso "baja a un rival no lleva TK" en el texto lo cubren los tests de `textoRonda` existentes, que siguen igual.

Desvio: ninguno. `metricas.md` sin tocar (opcional en el diseno; sin numero nuevo). Chunk inicial `index-*.js` 200.00 kB; `MatchDetail` lazy 19.37 kB.

verificar.sh: VERDE e3194ddaa (1266 backend, 408 vitest, 108 e2e). Un primer intento cayo en el e2e nuevo por un locator (`has:` con `.timeline .chip` relativo al `li`); corregido.

Revision ciega (`omc-code-reviewer`, `revision.md`, 122 lineas): aprobar, 0 hallazgos.

Skills: no aplica.
Skills del repo: testing-strategy (vitest para la regla y el texto, e2e con respuesta interceptada), ux-copy (`title` con tildes, chip corto como `HS`), modern-web-guidance (no aplica: un `.chip` existente, sin CSS ni componente nuevo).
OMC: plan=— · revisión=0 hallazgos · verificación=—

## Revision 2026-11-13 sobre 0de38f5

(revisor 20261113T1926Z-cNCxUZs) Aprobar. Dos LOW sin arreglar (al humano): L1 `esTeamkill` usa un `Map` por nick, y un nick en los dos equipos puede marcar mal (como `marcasDeApertura`); L2 el e2e confirma la ausencia de `TK` en una sola ronda mas.
OMC: plan=— · revisión=2 hallazgos LOW (0 arreglados: al humano) · verificación=—

## QA 2026-11-13 sobre a398816

(qa 20261113T2003Z-c3vr7mZ) Rama con `origin/dev@d5595cb` fusionado (entraron 123 y 124), merge limpio.

- `verificar.sh`: VERDE a398816ff en 192 s (1284 tests backend, 411 vitest, 112 e2e).
- Base sembrada con `factories.py` (script en el scratchpad), `runserver 8125`: ronda 1 con yo/amigo (team 0) y rival/rival2 (team 1), `Kill` yo->rival, amigo->yo, rival->rival2, amigo->rival; ronda 2 sin teamkills. `/api/matches/1/` 200, `/api/matches/999/` y `/api/matches/abc/` 404, `?side=Attack` 200.
- Playwright en `/partidas/1`: ronda 1 -> "yo mató a rival" (`mine`, apertura), "amigo mató a yo" (sin clase, `TK` con el `title` exacto), "rival mató a rival2" (sin clase, `TK`), "amigo mató a rival" (`mine`, sin chips): 2 `TK`, los dos equipos, como dice el diseno. Ronda 2 por teclado (`.round-tab` es `button`, Enter): 0 `TK`. Consola sin errores ni warnings.
- accessibility-review: chip `TK` con contraste 12.92:1; 0 Critical, 0 Major. El `title` solo se ve con mouse y el chip no es enfocable: mismo patron que el chip `apertura` ya existente (WCAG 1.3.1/4.1.2, LOW), va como idea.
- Mutacion (vitest `aperturas.test.js` + `textoRonda.test.js`, 34 tests): quitar el chequeo de suicidio -> 1 failed; `return true` en vez de comparar equipos -> 3 failed; no exigir que autor y victima esten en `players` -> 1 failed.
- validate-data: sin numero nuevo (TK es una marca; la fila *Teamkills* de `metricas.md` no cambia).
- Los dos LOW del Revisor (nick repetido en los dos equipos; e2e que mira una sola ronda mas) siguen sin arreglar: no bloquean.

Veredicto: aprobado.

Skills del repo: accessibility-review (0 Critical, 0 Major; title solo con mouse, preexistente), validate-data (sin numero nuevo).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

- (arquitecto 2026-11-13, no bloquea) Se marcan con `TK` los teamkills de los dos equipos (el feed muestra los dos); el panel de teamkills sigue contando solo los de tu equipo.

- (revisor 2026-11-13, no bloquea) Dos LOW en la 125 (nick repetido en los dos equipos; e2e que mira una sola ronda más, detalle en `## Revision`): los puede sumar un Dev después.
