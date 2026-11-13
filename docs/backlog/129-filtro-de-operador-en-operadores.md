# 129. Filtro de operador en la pagina Operadores

estado: implementado
candado: revisor 2026-11-13T20:32Z
rama: claude/equipo-dev/129-filtro-de-operador-en-operadores
tipo: funcionalidad
epica: operadores
area: frontend
prioridad: 3
fuente: ALCANCE.md O14 (friccion que vio la QA de la 113)
archivos: frontend/src/operadorElegido.js (nuevo), frontend/src/operadorElegido.test.js (nuevo), frontend/src/pages/Operators.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261113T1858Z-cxdASk3, arquitecto 20261113T1926Z-ce4Pmp6, dev 20261113T1954Z-cfZTvvE

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

## Revision

## QA

## Para el humano

(nada)
