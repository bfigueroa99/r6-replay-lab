# 129. Filtro de operador en la pagina Operadores

estado: revisado
candado: qa 2026-11-14T00:00Z
rama: claude/equipo-dev/129-filtro-de-operador-en-operadores
tipo: funcionalidad
epica: operadores
area: frontend
prioridad: 3
fuente: ALCANCE.md O14 (friccion que vio la QA de la 113)
archivos: frontend/src/operadorElegido.js (nuevo), frontend/src/operadorElegido.test.js (nuevo), frontend/src/pages/Operators.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1858Z-cxdASk3, arquitecto 20261113T1926Z-ce4Pmp6, dev 20261113T1954Z-cfZTvvE, revisor 20261113T2003Z-c3vr7mZ, qa 20261113T2156Z-cQ8Kk3s, dev 20261113T2223Z-c24t16L, revisor 20261113T2252Z-cSo9yHH, dev 20261113T2318Z-cpCpgff, revisor 20261113T2345Z-c5J2BqJ

## PR

## Que gana quien usa la app

Operadores monta `Filters` con `showOperator={false}`, asi que los paneles
que si usan `operator` (Repetir o cambiar tras perder, A qué operador
cambias, Por sitio) solo lo reciben por la URL o heredado de otra pagina. Un
selector propio deja usar ese filtro sin editar la URL.

## Criterios de aceptacion

- [ ] Operadores muestra el selector de operador de `Filters`; elegir uno
      pone `?operator=<nombre>` en la URL y los paneles que leen `operator`
      recargan con el. e2e: elegir un operador del seed y ver la URL y la
      tabla Repetir o cambiar con solo filas de ese operador (numeros de la API).
- [ ] Las tablas por operador de la pagina (Todos y los grupos por lado) no
      se vacian con el filtro: la fila del operador elegido queda resaltada
      (clase y `aria-current` o equivalente) y las demas siguen. vitest o e2e.
- [ ] Quitar el filtro (opcion "Todos") vuelve a la vista sin resaltado y
      saca `operator` de la URL. e2e.
- [ ] La vista "sin rondas filtradas" de Operadores tambien muestra el
      selector, para poder quitar un operador que deja la pagina vacia. e2e.
- [ ] Consola limpia en todo el recorrido; sin cambios de backend (los
      endpoints ya aceptan `operator`).

## Fuera de alcance

- Selector de varios operadores a la vez.
- Cambiar como filtran `operator` los endpoints.
- El mismo resaltado en otras paginas.

## Diseno

(arquitecto 20261113T1926Z-ce4Pmp6, sobre `origin/dev@84c575b`) Filtros duros: pasa. Solo
frontend: sin red, sin dependencias, sin POST, sin numero nuevo (ninguna fila
de `metricas.md`). Una forma obvia, ~150 lineas: sin arena ni consenso.

**Implementar despues de que #126 se mergee**: la 126
(`claude/equipo-dev/126-a-que-operador-cambias-tras-perder`, `revisado`)
toca `frontend/src/pages/Operators.jsx` y `frontend/e2e/humo.spec.js` en la
misma zona (agrega el panel "A qué operador cambias"). Ese panel nuevo
recibe `filters` completos, como los demas paneles de abajo.

**Por que no basta con `showOperator`.** `/api/operators/` aplica `operator`
(`base_queryset`, `aggregates.py:72`): con el filtro puesto, Ataque/Defensa
quedarian con una sola fila. El criterio pide que no se vacien, asi que esa
request va **sin** `operator` y la fila elegida se resalta. `/operators/pool/`
ya ignora `operator` (`operator_pool`, `aggregates.py:774`): no cambia.
`/operators/sites/`, `/operators/after-result/` (y el panel de la 126)
reciben `filters` enteros: son los que usan `operator` segun la ficha.

**`frontend/src/operadorElegido.js`** (logica pura, nuevo):
- `sinOperador(filtros)`: copia de `filtros` sin la clave `operator` (sin
  ella, una copia igual). No muta el original.
- `claseFilaOperador(fila, operador)`: `'me'` si `operador` no es vacio y
  `fila.operator === operador`; si no `''`. Reusa el estilo existente
  `tbody tr.me` (`frontend/src/styles.css:315`, el de tu fila en
  MatchDetail): sin CSS nuevo.
- `textoOperadorElegido(operador)`: `''` sin operador; con uno,
  `` `Con ${operador} elegido, Ataque y Defensa siguen mostrando todo tu pool y lo resaltan; los paneles de abajo se filtran a ${operador}.` ``

**vitest `frontend/src/operadorElegido.test.js`**:
- `sinOperador quita operator y deja el resto` (`{side:'Attack', operator:'Ash'}`
  -> `{side:'Attack'}`; el original sigue con `operator`).
- `sinOperador sin operator devuelve los mismos filtros`.
- `claseFilaOperador marca solo la fila elegida` (`Ash` -> `'me'`, `Zofia`
  -> `''`, operador `''` o `undefined` -> `''`).
- `textoOperadorElegido vacio sin operador y con el nombre si hay uno`.

**`frontend/src/pages/Operators.jsx`**:
- `useApi('/operators/', { ...sinOperador(filters), min_rounds: 1 })`.
- `vistaSinRondas` sigue recibiendo `filters` completos: un `operator` en la
  URL cuenta como filtro puesto y la vista "filtrado" ofrece quitarlo.
- Las dos `<Filters ... showOperator={false} />` (la de la pagina y la de
  `SinRondasFiltradas`) pasan a `<Filters value={filters} onChange={setFilters} />`
  (el default de `showOperator` es `true`; el selector y sus opciones de
  `/api/filters/` ya existen, y la URL la escribe `filtrosUrl.js`, ficha 96).
- `Table` recibe `operador={filters.operator}` y pasa
  `rowClass={(row) => claseFilaOperador(row, operador)}` a `DataTable`; en la
  columna `operator`, `render: (row) => row.operator === operador ? <strong
  aria-current="true">{row.operator}</strong> : row.operator` (el nombre
  accesible del resaltado: `DataTable` no expone atributos por fila y no se
  toca `ui.jsx`). Con `render` la columna sigue ordenando por `key`.
- En el `page-head`, debajo del `<p>` actual, la nota
  `<p className="note">{textoOperadorElegido(filters.operator)}</p>` solo si
  el texto no es vacio.
- `TuPool` sin cambios; `PorSitio`, `TrasResultado` y el panel de la 126
  siguen con `filters`.

**e2e `frontend/e2e/humo.spec.js`**, junto a los de `/operadores`:
- `Operadores filtra por operador desde su propio selector`: `/operadores`,
  `page.getByLabel('Operador').selectOption('Ash')`;
  `expect(page).toHaveURL(/operator=Ash/)`; el panel Ataque sigue con 3 filas
  (seed: Zofia, Ash, Thermite) y la de Ash tiene clase `me` y un
  `[aria-current="true"]` con `Ash`; Defensa sigue con 3 filas sin `me`; la
  tabla "Repetir o cambiar tras perder" coincide con
  `/api/operators/after-result/?operator=Ash` leida con `page.request` (hoy
  la fila Ataque, columna 4, da 29: el test existente lo afirma por URL); la
  nota de operador elegido visible. Despues `selectOption('')` (Todos): URL
  sin `operator`, ninguna fila `me`, sin la nota. Consola limpia.
- `Operadores sin rondas deja quitar el operador`:
  `/operadores?operator=Ash&until=2000-01-01` -> subtitulo `0 rondas con
  estos filtros` y `getByLabel('Operador')` con valor `Ash`;
  `selectOption('')` -> URL sin `operator`. Consola limpia.

**Orden.** vitest (rojo) -> `operadorElegido.js` -> `Operators.jsx` -> e2e ->
`npm run build` -> `verificar.sh`.

**Que puede romperse.** El e2e existente `Operadores muestra si repites o
cambias de operador` (`?operator=Ash` sobre Repetir o cambiar) no cambia:
ese panel sigue filtrado. Los e2e de Operadores que cuentan filas de
Ataque/Defensa sin `operator` no cambian. Con un operador del otro lado que
el filtro `side` (Ash con `side=Defense`), Ataque no sale y nada se resalta:
correcto, y los paneles de abajo dicen su propio vacio. `/api/operators/`
deja de recibir `operator` solo desde esta pagina.

**Verificacion manual.** `seed_demo` + `runserver`, `/operadores`: elegir Ash
en el selector; fila resaltada en Ataque, las otras dos visibles, URL con
`operator=Ash`, Repetir o cambiar filtrado; volver a Todos.

Skills: no aplica (un selector existente y un resaltado con el estilo de
MatchDetail).
Skills del repo: testing-strategy (logica pura en vitest; selector -> URL ->
paneles y la vista vacia en e2e, con numeros de la API),
accessibility-review (el resaltado no depende solo del color: `strong` con
`aria-current`; el selector ya tiene su `label`).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

(dev 20261113T1954Z-cfZTvvE) Diseno completo, sobre `origin/dev@c332e72`:

- `operadorElegido.js` (nuevo): `sinOperador`, `claseFilaOperador` (clase `me`, el estilo de tu fila en MatchDetail, sin CSS nuevo) y `textoOperadorElegido`.
- `Operators.jsx`: `/api/operators/` se pide con `sinOperador(filters)`; las dos `<Filters>` (pagina y `SinRondasFiltradas`) sin `showOperator={false}`; `Table` resalta la fila elegida con `rowClass` y un `<strong aria-current="true">` en la celda; nota de operador elegido en el `page-head`. `vistaSinRondas`, Tu pool, Por sitio y Repetir o cambiar siguen con los filtros enteros.
- e2e `Operadores filtra por operador desde su propio selector` (elegir Ash -> URL, Ataque y Defensa con 3 filas, solo la de Ash con `me` y `aria-current`, ningun pedido a `/api/operators/` con `operator=`, "Cambia" de ataque igual a `/api/operators/after-result/?operator=Ash`, volver a Todos sin resaltado ni nota, y con `side=Defense&operator=Ash` sin nota) y `Operadores sin rondas deja quitar el operador`.

Desvios del diseno, por la revision ciega (3 LOW, los 3 arreglados): la nota nombra los paneles que se filtran (Por sitio y Repetir o cambiar) y dice que Tu pool no cambia (`operator_pool` ignora `operator`); la nota solo sale si el operador esta en las filas (con `side=Defense&operator=Ash` prometia un resaltado que no hay); `docs/metricas.md`, filas Presencia y vs. tu lado: el "100 %" y el "0" con filtro de operador valen para `/api/operators/`, no para la pagina (archivo sumado a `archivos:`).

Tests vistos en rojo antes del codigo: vitest `operadorElegido.test.js` (4, modulo inexistente). Criterios -> tests: selector y URL, paneles filtrados y tablas sin vaciarse con resaltado (e2e "propio selector"), Todos (mismo e2e), vista sin rondas (e2e "sin rondas deja quitar"), consola limpia (los dos), sin backend (diff). Mutaciones: sin `sinOperador` cae el e2e (toHaveCount 3; antes de esperar la recarga el mutante sobrevivia, por eso el test espera la respuesta y vigila los pedidos), sin `rowClass` cae (toHaveClass), con `showOperator={false}` en la vista vacia cae (toHaveValue).

verificar.sh: VERDE 15345ab1c (1279 backend, 409 vitest, 111 e2e).

Skills: no aplica.
Skills del repo: testing-strategy (logica pura en vitest, selector -> URL -> paneles en e2e con numeros de la API y mutaciones), accessibility-review (resaltado con `aria-current`, no solo color; selector con su `label`), ux-copy (nota con tildes, nombra los paneles reales), modern-web-guidance no leida (sin CSS nuevo; clase y markup existentes).
OMC: plan=— · revisión=3 hallazgos (3 LOW; 3 arreglados) · verificación=—

## Revision 2026-11-13 sobre fe2b837

(revisor 20261113T2003Z-c3vr7mZ) Punto de partida: la rama no contenia `origin/dev` (entraron 123, 124 y 125); `git merge origin/dev` limpio (fe2b837) y `verificar.sh`: VERDE fe2b83780 (1284 backend, 415 vitest, 114 e2e).

**Eje de estandares** (`omc-code-reviewer` ciego, prompt de `revision.md`, sin leer la ficha): aprobar, 1 MEDIUM y 2 LOW propuestos.
- [test] MEDIUM propuesto -> **LOW confirmado a medias** `frontend/e2e/humo.spec.js:218-223`: el listener de `pedidosPool` se registra despues de `page.goto`, y elegir Ash no cambia el `serialized` de `useApi` (`sinOperador` quita `operator`), asi que `pedidosPool.length > 0` podria depender de una carrera. No se reproduce: `E2E_CHROMIUM=<headless_shell> npx playwright test -g "filtra por operador desde su propio selector" --repeat-each 25 --workers 4` -> 25 passed. Arreglo sugerido: registrar `page.on('request')` antes de `goto` y ajustar el comentario "mientras recarga". No bloquea.
- [bug] LOW `frontend/src/pages/Operators.jsx:44-46`: con un operador sin rondas bajo los demas filtros (ej. `?operator=Zofia&map=<mapa donde no la jugaste>`) no hay nota ni fila resaltada y Por sitio / Repetir o cambiar se vacian sin decir por que. Arreglo: nota corta "Sin rondas con <op> con estos filtros", excluyendo el lado filtrado que no es el del operador.
- [estilo] LOW `frontend/src/pages/Operators.jsx:97-98`: `aria-current="true"` en un `<strong>` dentro de una celda no es el uso tipico de `aria-current` (item actual de un conjunto). Alternativa: texto oculto "elegido". Confianza baja.

Sin eje de seguridad: el diff no toca red, POST, rutas ni dependencias. Sin eje de intencion aparte: los criterios se contrastaron abajo.

**Ficha.** Criterio 1 (selector, URL, Repetir o cambiar con numeros de la API): e2e `Operadores filtra por operador desde su propio selector`; 2 (tablas sin vaciarse, resaltado con clase y `aria-current`): mismo e2e (3 filas por lado, una sola `tr.me`) y vitest `operadorElegido.test.js`; 3 (Todos): mismo e2e; 4 (vista sin rondas con selector): e2e `Operadores sin rondas deja quitar el operador`; 5 (consola limpia, sin backend): `vigilarConsola` en los dos y diff sin `backend/`. Diff dentro de `archivos:` (`metricas.md` sumado y explicado en Implementacion); identificadores sin tildes, UI con tildes; sin `console.log`.

Veredicto: aprobar.

Skills del repo: ninguna (revision con `revision.md`).
OMC: plan=— · revisión=3 hallazgos (1 MEDIUM rebajado a LOW, 2 LOW; 0 arreglados: no bloquean) · verificación=—

## QA 2026-11-13 sobre 5c4006a

(qa 20261113T2156Z-cQ8Kk3s) Con hallazgos: 1 MEDIUM (test e2e intermitente). Todo lo demas pasa.

**Hallazgo (MEDIUM, bloquea): el e2e `Operadores sin rondas deja quitar el operador` es intermitente.** En `frontend/e2e/humo.spec.js:271`, `page.getByRole('heading', { name: 'Defensa', exact: true })` resuelve a **dos** encabezados con `side=Defense` (el `h2` del panel Defensa y el `h3` Defensa de Tu pool). Pasa solo si la aserción corre antes de que llegue el segundo; si llegan los dos, strict mode violation. Ademas, cuando gana la carrera, la linea siguiente (`Con Ash elegido` en 0) se mira con un solo panel cargado.
- Repro (desde `frontend/`, con el build de la rama): `E2E_CHROMIUM=/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell npx playwright test -g "sin rondas deja quitar el operador" --trace off --repeat-each 30 --workers 4` -> **6 failed, 24 passed** (`Error: strict mode violation: getByRole('heading', { name: 'Defensa', exact: true }) resolved to 2 elements`). Con `--workers 1` (lo de `playwright.config.js` y `check.sh`): 30 passed; depende de la carga de la maquina, y con 5 corridas simultaneas o un PC lento es un rojo al azar.
- Arreglo verificado aca (no empujado: QA no arregla): cambiar esa linea por `await expect(page.locator('section.panel h2', { hasText: /^Defensa$/ })).toBeVisible()`. Con el: `--repeat-each 40 --workers 4` -> 40 passed; con el mutante de abajo (nota sin la condicion `rows.some`) -> 10 failed de 10.

**Criterios de aceptacion** (sobre el build de la rama y `seed_demo`, `runserver` en 127.0.0.1:8129; script Playwright en el scratchpad):
1. Selector y URL: elegir Ash -> `/operadores?operator=Ash`; Repetir o cambiar filtrado (e2e "propio selector" verde). Pasa.
2. Tablas sin vaciarse: con `?operator=Ash`, `tbody tr.me` = 1, `[aria-current="true"]` = `["Ash"]`, Ataque y Defensa con sus 3 filas. Pasa.
3. Todos: `selectOption('')` -> `/operadores`, `tr.me` = 0. Pasa.
4. Vista sin rondas: `?operator=Ash&until=2000-01-01` -> selector con `Ash`. Pasa.
5. Consola limpia en las 7 URLs de abajo y el recorrido: `consola: limpia`. Diff sin `backend/`. Pasa.

**Bordes en la UI** (`sel` = valor del selector): `?operator=NoExiste` -> sel `''` (Todos), sin resaltado ni nota; `?operator=Ash&side=Defense` -> sel Ash, sin `tr.me` ni nota; `?operator=Ash&until=foo` -> igual que sin `until`; `?operator=%3Cb%3Ex%3C%2Fb%3E` -> sin resaltado, texto escapado, sin errores.

**API** (sin cambios de backend; vecinos con bordes, base sembrada y base vacia en :8130): `/api/operators/?operator=` , `?operator=NoExiste`, `?operator=Ash&until=foo`, `?page=-1&operator=Ash`, `?operator=Ash%00`, `/operators/after-result/?operator=NoExiste`, `/operators/sites/?operator=Ash`, `/operators/pool/?operator=Ash`: todos HTTP 200 con JSON; base vacia: `{"operators": []}` HTTP 200.

**Chunk inicial**: `index-*.js` 200116 bytes en la rama y en `origin/dev` (build en worktree): +0 %. `Operators-*.js` 9946 -> 10474 (lazy).

**Accesibilidad** (skill accessibility-review, Chromium sobre la base sembrada): teclado: Tab 15 llega a `SELECT` con label "Operador", ArrowDown -> `?operator=Ash`. Nombre y rol: selector con `label`; el resaltado no depende del color (`strong` con `aria-current`, LOW del Revisor sobre ese uso sigue en pie). Contraste: nota 6.45:1 (`rgb(139,152,169)` sobre `rgb(13,17,23)`); fila `me` 13.19:1 (texto `rgb(230,237,243)` sobre `rgba(255,138,61,.133)` compuesto con el fondo = `rgb(45,33,28)`). Sin Critical ni Major.

**Mutaciones**: (a) `claseFilaOperador` devuelve `me` con cualquier operador -> vitest `marca solo la fila elegida` cae; (b) `sinOperador` devuelve los filtros enteros -> vitest `quita operator y deja el resto` cae; (c) nota sin `rows.some(...)` -> e2e `sin rondas deja quitar el operador` cae 5 de 5 (el test lo cubre cuando no se rompe por la carrera de arriba).

**Observado de paso, no es de la ficha**: un e2e viejo (`Operadores muestra tu pool por lado`) fallo 1 vez con 4 workers y no se reprodujo en 3x40 corridas mas; sin causa.

verificar.sh: VERDE 5c4006af3 (1284 backend, 415 vitest, 114 e2e).

Skills del repo: accessibility-review (0 Critical, 0 Major; contraste medido 6.45 y 13.19), testing-strategy (mutaciones: 3 de 3 caen; un test intermitente con repro), validate-data no aplica (sin numero nuevo: `metricas.md` solo aclara Presencia y vs. tu lado), design-critique no aplica (sin pagina ni panel nuevo).
OMC: plan=— · revisión=— · verificación=— (sin `aprobado`: no se corrio omc-verifier)

## Implementacion (hallazgos de QA)

(dev 20261113T2223Z-c24t16L) Arreglado el MEDIUM de la QA 2026-11-13: en `frontend/e2e/humo.spec.js` (`Operadores sin rondas deja quitar el operador`), el encabezado se busca con `getByRole('heading', { level: 2, name: 'Defensa', exact: true })`: sin el nivel resolvia tambien al h3 Defensa de Tu pool y caia en strict mode cuando ya habian cargado los dos. La segunda carrera que anotaba la QA no existe: la nota sale de la misma respuesta (`/operators/`) que el h2 (lo marco la revision ciega).

- Repro de la QA con el arreglo, desde `frontend/`: `E2E_CHROMIUM=/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell npx playwright test -g "sin rondas deja quitar el operador" --trace off --repeat-each 40 --workers 4` -> 40 passed (antes 6 de 30 caian).
- Mutante de la QA (nota sin `rows.some`, `Operators.jsx:46`) con el arreglo: 10 failed de 10. Restaurado.
- Revision ciega (`omc-code-reviewer`, eje de estandares) sobre una primera version (`toHaveCount(2)` atado a Tu pool): aprobar, 3 LOW; arreglados 2 (usar `level: 2` en vez de depender de Tu pool, comentario con el motivo real). No arreglado: los `toHaveCount(0)` siguientes no acotan a la seccion Defensa (ya estaba; hoy esos paneles quedan vacios con Ash en defensa).
- Los 3 LOW del Revisor (`## Para el humano`) siguen sin tomar: no bloquean.
- Rama al dia con `origin/dev@39e22c0` (merge). verificar.sh: VERDE 50ddfaaa8 (1284 backend, 425 vitest, 116 e2e).

Skills: no aplica.
Skills del repo: testing-strategy (repro en paralelo y mutante antes y despues del arreglo).
OMC: plan=— · revisión=3 hallazgos LOW (2 arreglados) · verificación=—

## Revision 2026-11-13 sobre 82ad2f3

(revisor 20261113T2252Z-cSo9yHH) Segunda revision, despues de los hallazgos de QA. La rama ya contiene `origin/dev@39e22c0`. verificar.sh: VERDE 82ad2f319 (1284 backend, 425 vitest, 116 e2e).

**Eje de estandares** (`omc-code-reviewer` ciego, prompt de `revision.md`, sin leer la ficha): aprobar, 1 MEDIUM. Lo reproduje y lo subo a bloqueante, con el mismo criterio que la QA aplico al otro e2e intermitente.

- [test] MEDIUM **confirmado, bloquea** `frontend/e2e/humo.spec.js:216-222` y `:241`: en `Operadores filtra por operador desde su propio selector`, `page.on('request')` se registra despues de `page.goto('/operadores')`. Elegir Ash no genera un pedido nuevo a `/api/operators/` (`sinOperador` deja la misma query y `useApi` no vuelve a pedir). Entonces el unico pedido que se cuenta es el de la carga inicial, y si sale antes de que `goto` devuelva el control, `pedidosPool` queda vacio y `expect(pedidosPool.length).toBeGreaterThan(0)` cae sin que haya un bug. La revision anterior no lo pudo reproducir con 4 workers.
  - Repro, desde `frontend/` con el build de la rama: `E2E_CHROMIUM=/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell npx playwright test -g "filtra por operador desde su propio selector" --trace off --repeat-each 50 --workers 8`. Cayo 6 veces en 190 corridas, en cinco tandas (2/40, 0/40, 1/50, 1/50, 2/50); las 6 en la linea 241 (`Received: 0`). Con 5 corridas simultaneas en la nube o un PC lento es un rojo al azar en `check.sh`.
  - Arreglo, verificado aca y no empujado (el Revisor no arregla): mover `const pedidosPool = []` y `page.on('request', ...)` antes de `await page.goto('/operadores')`, y sacar el comentario "mientras recarga, la tabla vieja sigue a la vista", que ya no describe nada. Con el arreglo, el mismo comando dio 50/50 tres veces (150 de 150). Sigue detectando la regresion: con `operator` en el pedido, la ultima asercion (`pedidosPool` sin `operator=`) cae.

**Ficha.** Los criterios siguen cubiertos como en la primera revision (los dos e2e, el vitest `operadorElegido.test.js` y el diff sin `backend/`). El arreglo de la QA (`level: 2` en el encabezado Defensa) es correcto: el e2e `sin rondas deja quitar el operador` pasa dentro de `check.sh`. El diff no se sale de `archivos:`. Identificadores sin tildes, UI con tildes, sin `console.log`.

Veredicto: corregir (el MEDIUM de arriba: e2e intermitente en `check.sh`).

Skills del repo: testing-strategy (repro en paralelo antes y despues del arreglo).
OMC: plan=— · revisión=1 hallazgo (1 MEDIUM confirmado, 0 arreglados: lo arregla el Dev) · verificación=—

## Implementacion (hallazgos de la segunda revision)

(dev 20261113T2318Z-cpCpgff) Sobre `origin/dev@2b7f715` (merge limpio, 31 commits).

- MEDIUM bloqueante (e2e intermitente): en `Operadores filtra por operador desde su propio selector`, `pedidosPool` y `page.on('request')` se registran antes de `page.goto('/operadores')`; fuera el comentario de la tabla vieja. Repro de la revision, antes del arreglo cayo 6 de 190; despues: `E2E_CHROMIUM=<headless shell> npx playwright test -g "filtra por operador desde su propio selector" --trace off --repeat-each 50 --workers 8` -> 50/50, y con `--repeat-each 100` -> 100/100.
- LOW del filtro ciego de este turno: la fila "Ataque" de Repetir o cambiar se fija tambien con `hasText: 'Tras ganar'` y `toHaveCount(1)`; si `seed_demo` diera a Ash pares tras perder, la de Ataque ya no seria una sola y el test leia la fila equivocada sin avisar. 20/20 repetido.
- No tomados (LOW de la primera revision, no bloquean): operador sin rondas sin aviso, `aria-current` en una celda.

Revision ciega (`omc-code-reviewer`, `revision.md`, eje de estandares): aprobar, 1 LOW (arriba, arreglado).

Skills: no aplica.
Skills del repo: testing-strategy (repro en paralelo antes y despues, 170 corridas del e2e).
OMC: plan=— · revisión=1 hallazgo (1 arreglado) · verificación=—

## Revision 2026-11-13 sobre 5a72366

(revisor 20261113T2345Z-c5J2BqJ) Tercera pasada. La rama contiene `origin/dev@2b7f715`. verificar.sh: VERDE 5a72366b6 (1321 backend, 435 vitest, 117 e2e).

**Eje de estandares** (`omc-code-reviewer` ciego, prompt de `revision.md`, sin leer la ficha): aprobar, 2 LOW, los dos confirmados leyendo el codigo; ninguno bloquea.
- [test] LOW `frontend/e2e/humo.spec.js:226`: `expect(nota).toHaveCount(0)` justo despues del `goto` corre con la pagina en `<Loading />` y pasaria aunque la nota saliera sin operador. Arreglo: esperar las 3 filas de Ataque antes de afirmarlo.
- [bug] LOW `frontend/src/operadorElegido.js:17`: con `?side=Attack&operator=Ash` la nota dice "Ataque y Defensa siguen mostrando todo tu pool" pero solo se ve Ataque. Arreglo: pasar `filters.side` a `textoOperadorElegido` y nombrar solo la tabla visible.

**Arreglo del MEDIUM anterior** (listener antes del `goto`): confirmado. Repro en paralelo de los dos e2e de la ficha, desde `frontend/`: `E2E_CHROMIUM=<headless shell> npx playwright test -g "Operadores (filtra por operador desde su propio selector|sin rondas deja quitar)" --trace off --repeat-each 30 --workers 8` -> 60 passed.

**Ficha.** Criterios cubiertos como en las revisiones anteriores (los dos e2e, vitest `operadorElegido.test.js`, diff sin `backend/`). Diff dentro de `archivos:`; identificadores sin tildes, UI con tildes; sin `console.log`. Sin eje de seguridad (no toca red, POST, rutas ni dependencias); sin eje de intencion aparte (diff de un tema, 147 lineas).

Veredicto: aprobar. Tercera pasada con solo LOW: `revisado`, los LOW a `## Para el humano`.

Skills del repo: testing-strategy (repro en paralelo del e2e antes intermitente).
OMC: plan=— · revisión=2 hallazgos LOW (0 arreglados: no bloquean) · verificación=—

## Para el humano

- (revisor 2026-11-13, no bloquea) Tres LOW en la 129 (listener del e2e despues del `goto`, operador sin rondas sin aviso, `aria-current` en una celda; detalle en `## Revision`): los puede sumar un Dev despues.
- (revisor 2026-11-13, tercera pasada, no bloquea) Dos LOW mas: nota de operador que nombra Defensa con `side=Attack`, y un `toHaveCount(0)` del e2e que corre antes de la carga.
