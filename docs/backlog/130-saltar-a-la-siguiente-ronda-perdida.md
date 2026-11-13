# 130. Saltar a la siguiente ronda perdida

estado: aprobado
candado: -
rama: claude/equipo-dev/130-saltar-a-la-siguiente-ronda-perdida
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F24
archivos: frontend/src/navegacionRondas.js (siguientePerdida, pideSiguientePerdida), frontend/src/navegacionRondas.test.js, frontend/src/pages/MatchDetail.jsx (DetallePartida: teclado y panel Rondas), frontend/e2e/humo.spec.js
turnos: po 20261113T1858Z-cxQ3TuB, arquitecto 20261113T1926Z-cq9nfTP, dev 20261113T2003Z-c3vr7mZ, revisor 20261113T2157Z-chbMW9r, qa 20261113T2223Z-c24t16L

## PR

## Que gana quien usa la app

En el detalle de partida, un boton "Siguiente ronda perdida" (y la tecla
`p`) lleva a la proxima ronda que tu equipo perdio desde la elegida, dando la
vuelta al final. Revisar solo lo que salio mal sin recorrer las rondas una por
una con las flechas.

## Criterios de aceptacion

- [x] Logica pura (en `navegacionRondas.js` o un modulo vecino): dado el
      indice elegido y `rounds`, devuelve el indice de la proxima ronda con
      `my_team_won === false` despues de la elegida, dando la vuelta; las
      rondas sin ganador (`my_team_won` nulo) no cuentan como perdidas; sin
      ninguna perdida (o con la elegida como unica perdida) devuelve null o la
      misma, segun se fije en el diseno. vitest con vuelta al final, ronda sin
      ganador salteada y partida sin perdidas.
- [x] La tecla `p` hace el salto con las mismas exclusiones que las flechas
      (`pasoDeTecla`: no en campos, no con modificadores, no si otro widget
      la tomo). vitest.
- [x] En `MatchDetail.jsx`, un boton con nombre accesible junto a las
      pestañas de ronda; deshabilitado (o ausente) en una partida sin rondas
      perdidas; el salto actualiza el ancla `#ronda-N` como cambiar de ronda
      a mano. e2e sobre `seed_demo`: elegir R1, apretar el boton, la ronda
      elegida es la primera perdida que da `/api/matches/<id>/`; con `p`
      igual; consola limpia.
- [x] El atajo figura donde la pagina ya explica las flechas (hint o
      `title`), con tildes.

## Fuera de alcance

- Saltar a la anterior perdida (Shift+p) o a la siguiente ganada.
- Filtrar las pestañas para que solo queden las perdidas.
- La misma navegacion en la comparacion de dos partidas.

## Diseno

(arquitecto 20261113T1926Z-cq9nfTP, sobre `origin/dev@c332e72`) Filtros duros: pasa (solo frontend sobre `rounds[].my_team_won`, que `/api/matches/<id>/` ya trae; sin red, sin dependencias, sin POST, sin migracion). Una forma obvia, ~150 lineas: sin arena ni consenso.

**Decisiones que fija el diseno** (criterio 1 y 3):
- Sin ninguna perdida: `null` y el boton queda **deshabilitado** (no ausente: la fila no salta de alto entre partidas). Con la elegida como unica perdida devuelve **la misma** (el salto no hace nada visible; no es un error).
- "Actualiza el ancla como cambiar de ronda a mano": hoy un clic en una pestaña o una flecha **no** tocan el hash (solo `setSelected`). El salto hace lo mismo: solo `setSelected`, sin tocar el hash. Asi se ve igual que cambiar a mano, y `#ronda-N` sigue siendo solo una entrada a la pagina.

**`frontend/src/navegacionRondas.js`** (el modulo de navegacion de rondas, no uno nuevo):
- `export function siguientePerdida(actual, rounds)` -> indice o `null`. Recorre `rounds` desde `actual + 1` dando la vuelta (`(actual + k) % n`, `k` de 1 a `n`) y devuelve el primer indice con `my_team_won === false` (estricto: `null`/`undefined` no cuentan). `rounds` vacio o ausente: `null`. `actual` fuera de rango: se normaliza con `Math.min(Math.max(actual, 0), n - 1)` como `rondaVecina`.
- Las exclusiones de `pasoDeTecla` salen a una funcion interna `teclaLibre(evento)` (defaultPrevented, Alt/Ctrl/Meta/Shift, campo o `contentEditable`, dentro de `CON_SCROLL`) que usan las dos: `pasoDeTecla` queda igual por fuera (sus tests no cambian).
- `export function pideSiguientePerdida(evento)` -> boolean: `teclaLibre(evento) && (evento.key === 'p' || evento.key === 'P')` (`P` por el Bloq Mayus: Shift ya quedo afuera).

**Tests, `frontend/src/navegacionRondas.test.js`**:
- `describe('siguientePerdida')`: `salta a la proxima perdida despues de la elegida`; `da la vuelta al final` (perdida solo antes de la elegida); `una ronda sin ganador no cuenta como perdida` (`my_team_won: null` entre medio, salteada); `sin perdidas devuelve null` (y con `[]` y `undefined`); `con la elegida como unica perdida devuelve la misma`.
- `describe('pideSiguientePerdida')`: `la p pide el salto` (`p` y `P`); `con modificadores, en un campo o con la tecla tomada no` (un caso por exclusion, como los de `pasoDeTecla`); `otra tecla no` (`o`, `ArrowRight`).

**`frontend/src/pages/MatchDetail.jsx`** (`DetallePartida`):
- Import en la linea existente: `import { indiceDeAncla, pasoDeTecla, pideSiguientePerdida, rondaVecina, siguientePerdida } from '../navegacionRondas.js'`.
- En `alApretar` (mismo `useEffect`), antes del `pasoDeTecla`: si `pideSiguientePerdida(e)` y hay rondas, `e.preventDefault()` y `setSelected((s) => siguientePerdida(s, data.rounds) ?? s)`. El efecto pasa a depender de `[total, data]` (necesita `rounds`; `total` sigue para las flechas).
- En el `Panel id="rondas"`, antes de `.round-tabs`, un `<button type="button" className="btn small" onClick=... disabled={siguientePerdida(selected, rounds) === null} title="Próxima ronda que tu equipo perdió (tecla P)">Siguiente ronda perdida</button>`. El texto visible es el nombre accesible. Sin CSS nuevo (`btn small` como "Copiar resumen").
- `hint` del panel: `"Clic en una ronda, ← → para moverte o P para la siguiente perdida."` (criterio 4).

**e2e, `frontend/e2e/humo.spec.js`**, test nuevo `el detalle salta a la siguiente ronda perdida` (despues de `el timeline marca la apertura de cada ronda`): tomar de `/api/matches/?limit=50` la primera partida cuyo detalle tenga al menos una ronda con `my_team_won === false` (`seed_demo` tiene derrotas); calcular el indice esperado con la misma regla desde el indice 0 (en el test, sin importar el modulo: un `findIndex` desde 1 y vuelta). Abrir `/partidas/<id>`, panel Rondas (`.round-tab` contado dentro del panel: la matriz de duelos tambien lo usa), clic en la primera pestaña; clic en `getByRole('button', { name: 'Siguiente ronda perdida' })` -> la pestaña de ese indice tiene `active`. Volver a la primera pestaña, `page.keyboard.press('p')` -> igual. La URL no cambia de hash. Consola limpia. Con la respuesta interceptada (patron de `una partida sin rondas muestra su cabecera y un aviso`) poniendo `my_team_won: true` en todas las rondas: el boton esta `toBeDisabled()`.

**Orden.** vitest (rojo) -> `navegacionRondas.js` -> `MatchDetail.jsx` -> e2e -> `npm run build` -> `verificar.sh`.

**Que puede romperse.** El `useEffect` del teclado gana una tecla: `p` dentro de un campo (no hay en la pagina) o con modificadores no se toma. La fila de botones del panel Rondas suma uno arriba de las pestañas: los e2e que cuentan `.round-tab` no cambian; el que cuenta botones por nombre ("Copiar ronda", "Copiar resumen") usa nombre exacto.

**Archivos ocupados.** 125 (`implementado`) toca `MatchDetail.jsx` en el import de `aperturas.js` y en `Timeline`; 79 (espera al humano) en el import de `api.js`, los `useState` de `DetallePartida` y el `page-head`. Este diseno toca el import de `navegacionRondas.js` (otra linea), el `useEffect` del teclado y el inicio del `Panel id="rondas"`: hunks distintos, aunque el `useEffect` queda a pocas lineas de los `useState` de la 79; si `git merge-tree` da conflicto con la 79 al implementar, se resuelve a mano (P3). `humo.spec.js` en otras zonas que 123 y 125. No se frena.

**Verificacion manual.** `seed_demo`, abrir una partida perdida: "Siguiente ronda perdida" recorre solo las rojas y vuelve al principio; `p` igual; en un campo de busqueda (si lo hubiera) `p` escribe.

Skills: no aplica (un boton y una tecla sobre una navegacion que el repo ya tiene).
Skills del repo: testing-strategy (vitest para la regla y la tecla, e2e para el boton y la tecla en la app real; sin Django: no toca el backend), ux-copy (boton en infinitivo/sustantivo como "Copiar resumen", `title` y `hint` con tildes).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T2003Z-c3vr7mZ) Diseno completo, sobre `origin/dev@72df8f9`:

- `navegacionRondas.js`: `siguientePerdida(actual, rounds)` (vuelta al final, `my_team_won === false` estricto, `actual` acotado como `rondaVecina`, `null` sin perdidas, la misma si es la unica); `pideSiguientePerdida(evento)` (`p`/`P`); las exclusiones de `pasoDeTecla` salen a `teclaLibre`.
- `MatchDetail.jsx` (`DetallePartida`): la `p` en el mismo `useEffect` del teclado (deps `[total, data]`), boton `btn small` "Siguiente ronda perdida" antes de `.round-tabs`, deshabilitado sin perdidas, con `title` "Próxima ronda que tu equipo perdió (tecla P)"; `hint` "Clic en una ronda, ← → para moverte o P para la siguiente perdida.". Solo `setSelected`, sin tocar el hash (como cambiar a mano).
- e2e `el detalle salta a la siguiente ronda perdida` (boton y tecla desde R1 contra la regla calculada sobre `/api/matches/<id>/`, la pestaña queda `active` y `loss`, hash igual, hint visible) y `sin rondas perdidas el boton de la siguiente perdida queda deshabilitado` (respuesta interceptada con todo ganado; `p` no mueve).

Tests vistos en rojo antes del codigo: los 9 nuevos de `navegacionRondas.test.js` (`siguientePerdida is not a function`). Criterios -> tests: 1 `describe('siguientePerdida')` (6); 2 `describe('pideSiguientePerdida')` (4, incluida la tabla con scroll); 3 los dos e2e; 4 el `hint` y el `title`, afirmados en el primer e2e. Mutaciones: sin la rama de la `p` en `alApretar` cae el primer e2e; con `disabled={false}` cae el segundo.

Desvio del diseno: `CON_SCROLL` no entra a `teclaLibre`; queda solo en `pasoDeTecla`. El diseno lo metia en las exclusiones comunes, pero esa exclusion existe para no robarle las flechas al scroll horizontal y la `p` no desplaza nada: con el foco en una celda del scoreboard la `p` no hacia nada sin aviso (LOW de la revision ciega). Test `dentro de una tabla con scroll la p igual pide el salto`.

Revision ciega (`omc-code-reviewer`, `revision.md`, eje de estandares): aprobar, 3 LOW. Arreglados 2: el de `CON_SCROLL` (arriba) y el e2e, que con una partida cuya unica perdida fuera R1 esperaba el indice 0 y pasaba sin moverse (ahora busca `k < n`). No arreglado, por decision del diseno: con la elegida como unica perdida el boton queda habilitado y no hace nada visible.

verificar.sh: VERDE 5b41042bf (1284 backend, 421 vitest, 114 e2e). Nota: el commit 5b41042 se empujo minutos antes de que terminara esa corrida; el verde es sobre ese mismo commit.

Skills: no aplica.
Skills del repo: testing-strategy (vitest para la regla y la tecla, e2e para el boton y la tecla en la app real, mutaciones), ux-copy (boton como "Copiar resumen", `title` y `hint` con tildes), modern-web-guidance no leida (sin CSS ni componente nuevo: `btn small` existente).
OMC: plan=— · revisión=3 hallazgos LOW (2 arreglados) · verificación=—

## Revision 2026-11-13 sobre 1b1b2bc

(revisor 20261113T2157Z-chbMW9r, rol del turno qa en su fallback "sin trabajo": la 129 tenia candado de otra corrida de QA) Rama al dia con `origin/dev@72df8f9` (nada que mergear).

verificar.sh: VERDE 1b1b2bcb5 en 155s (1284 backend, 421 vitest, 114 e2e).

Revision a ciegas, dos ejes (`omc-code-reviewer` con `revision.md`; diff de 200 lineas, por eso tambien el eje de intencion). `omc-security-reviewer` no aplica: solo frontend, sin POST, red ni rutas.

- Estandares: aprobar, 2 LOW.
  - [bug] LOW `MatchDetail.jsx:167`: con la elegida como unica perdida el boton queda habilitado y no mueve nada. Confirmado leyendo `disabled={siguientePerdida(selected, rounds) === null}`. No se corrige: es la decision explicita del Diseno ("devuelve la misma ... no es un error"), que el criterio 1 permite.
  - [bug] LOW `navegacionRondas.js`: `pideSiguientePerdida` no mira `isComposing`. Descartado: fuera de un campo no hay composicion de IME y los campos ya quedan afuera por `teclaLibre`.
- Intencion: aprobar, 1 MEDIUM y el mismo LOW.
  - MEDIUM criterio 3, "el salto actualiza el ancla `#ronda-N` como cambiar de ronda a mano": la implementacion no toca el hash y el e2e afirma que la URL no cambia. Confirmado: la pestaña hace solo `setSelected(i)` (`MatchDetail.jsx:178`) y en `frontend/src` nadie escribe `location.hash`. Rebajado a no-hallazgo: el Diseno fijo esta lectura ("hoy un clic o una flecha no tocan el hash ... el salto hace lo mismo"), y es la que mantiene el salto igual que el cambio a mano. Si el humano quiere el hash vivo, es una ficha aparte para pestañas, flechas y salto juntos (va a `## Para el humano`).
  - Criterios 1, 2 y 4 cumplidos con evidencia; nada fuera de alcance.

Ficha contra el diff: los 4 archivos son los de `archivos:`; el desvio (`CON_SCROLL` fuera de `teclaLibre`) esta explicado en Implementacion y tiene test. Sin numero nuevo en la UI (no hace falta fila en `metricas.md`). Identificadores y comentarios sin tildes; `title` y `hint` con tildes. Sin `console.log`. Criterios: 1 -> `describe('siguientePerdida')` (6 tests); 2 -> `describe('pideSiguientePerdida')` (4); 3 -> los dos e2e (`el detalle salta a la siguiente ronda perdida`, `sin rondas perdidas el boton ... deshabilitado`); 4 -> `hint` y `title`, afirmados en el primer e2e.

Veredicto: aprobar -> `revisado`.

OMC: plan=— · revisión=4 hallazgos (0 arreglados: 2 decisiones del diseno, 1 descartado, 1 duplicado) · verificación=—
Skills del repo: ninguna (revision de codigo con `revision.md`)

## QA 2026-11-13 sobre cc63536

(qa 20261113T2223Z-c24t16L) Rama al dia con `origin/dev@72df8f9`. Solo frontend: sin migracion, parser, `recompute`, Electron ni `.ps1` (no hay `## Verificar en el PC`); sin numero nuevo en la UI (`validate-data` no aplica) ni pagina o panel nuevo (`design-critique` no aplica).

- check.sh: `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --` -> exit 0, `VERDE cc63536fc en 180s: 1284 tests backend, 421 vitest, 114 e2e`.
- Servidores: `SQLITE_PATH=<scratch>/vacia.sqlite3 manage.py migrate && runserver 127.0.0.1:8111` (base vacia) y `SQLITE_PATH=<scratch>/sembrada.sqlite3 manage.py migrate && seed_demo && runserver 127.0.0.1:8112` (29 partidas, 203 rondas). `curl`: `/api/matches/?limit=-1`, `?page=-1`, `?until=foo` -> 200; `/api/matches/999999/` y `/abc/` -> 404; base vacia `/api/matches/1/` -> 404 y `/partidas/1` -> 200 con "Esa partida no existe", apretar `p` ahi no tira errores.
- Criterios 1-3 en la app (Playwright, script `prueba130.cjs` en el scratchpad): en las 29 partidas sembradas, desde cada ronda y por tres caminos (clic en "Siguiente ronda perdida", tecla `p`, foco en el boton + Enter) -> 609 saltos, todos a la ronda que da la regla sobre `/api/matches/<id>/` (primera `my_team_won === false` despues de la elegida, con vuelta). `Shift+P` y `Alt+p` no mueven. La URL no cambia. Consola sin errores ni warnings.
- Bordes con `/api/matches/<id>/` interceptada (`borde130.cjs`): unica perdida en R3 -> boton habilitado, desde R1 boton y `p` van a R3 y ahi se quedan; R2 con `my_team_won: null` y R4 perdida -> desde R1 va a R4 (el nulo no cuenta); partida de una sola ronda, perdida -> se queda en R1, sin errores. Todo ganado -> deshabilitado (ya lo afirma el e2e).
- Criterio 4: el hint del panel tiene "P para la siguiente perdida" y el `title` "Próxima ronda que tu equipo perdió (tecla P)".
- Bundle (`vite build` de `origin/dev` y de la rama): chunk inicial `index` 200.00 -> 200.34 kB (+0.17 %); `MatchDetail` 19.37 -> 19.66 kB.
- accessibility-review (Chromium, base sembrada): el boton es `<button>` con nombre "Siguiente ronda perdida" (rol y nombre por el texto visible), se alcanza con Tab, foco visible (`outline: auto`), se activa con Enter; contraste del texto medido 12.92:1 (`rgb(230,237,243)` sobre `rgb(29,38,50)`), 28 px de alto. Sin Critical ni Major.
- Mutaciones en `navegacionRondas.js` con `npx vitest run src/navegacionRondas.test.js`: nulo contado como perdida -> caen 2 (`una ronda sin ganador no cuenta como perdida`, `sin perdidas devuelve null`); `k <= n` -> `k < n` -> cae `con la elegida como unica perdida devuelve la misma`; sin `'P'` -> cae `la p pide el salto`. Restaurado.
- `omc-verifier` (receta 3) con criterios, comandos y diff: PASS, los 4 criterios VERIFIED; gaps LOW ya conocidos (unica perdida con boton habilitado, ancla sin seguir la ronda: decisiones del Diseno, en `## Para el humano`).

Veredicto: `aprobado`.

Skills del repo: accessibility-review (0 Critical, 0 Major, 0 Minor en lo agregado; contraste 12.92:1), testing-strategy (mutaciones: 3 de 3 caen). Valores recalculados: no aplica (sin numero nuevo).
OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

- (revisor 2026-11-13) Ancla `#ronda-N`: hoy ni las pestañas, ni las flechas, ni este salto la actualizan; la URL solo sirve para entrar parado en una ronda. Si se quiere que la URL siga a la ronda elegida (para recargar o compartir), es una ficha aparte que cambia los tres caminos juntos.
