# 77. Selector de tipo de partida en la barra de filtros

estado: en curso 2026-11-05 (implementado en su rama)
candado: -
rama: claude/equipo-dev/77-selector-de-tipo-de-partida
tipo: funcionalidad
epica: temporada-y-modo
area: frontend
prioridad: 2
fuente: ALCANCE.md A1; replica/features.csv ("Soporte de ranked, unranked y custom", must, clone partial: falta el selector en Filters.jsx); PR #14 cerrado sin merge el 2026-11-05 ya no lo cubre
archivos: frontend/src/tipoPartida.js, frontend/src/tipoPartida.test.js, frontend/src/components/Filters.jsx, frontend/src/pages/Dashboard.jsx, backend/tests/test_tipo_de_partida.py, frontend/e2e/humo.spec.js
turnos: po 20261105T0230Z-c8Ahepa, arquitecto 20261105T0247Z-cSs57wh

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy la barra de filtros solo deja elegir "Solo ranked": quien juega unranked,
rapidas o customs no puede ver sus numeros de ese tipo sin mezclarlos con el
resto. Con un selector "Tipo" (Todos, Ranked, Unranked, la que haya en la base)
todo lo que usa la barra (Inicio, Coach, Operadores, Compañeros, Tendencias...)
se filtra por tipo de partida, y la app cierra un `must` de la referencia que
estaba en `partial`.

## Criterios de aceptacion

- [ ] La barra de filtros muestra un `<select>` "Tipo" con "Todos" y una opcion
      por cada valor de `match_types` de `/api/filters/` (sembrado: al menos
      Ranked y uno mas); elegir uno manda `match_type=<valor>` a la API (vitest
      sobre la funcion que arma los parametros, o e2e mirando la request).
- [ ] Con `match_type=Ranked`, `/api/overview/` da los mismos numeros que con
      `ranked_only=1` sobre la base sembrada (test backend: los dos caminos ya
      existen en `base_queryset`; el test fija que coinciden).
- [ ] "Solo ranked" y el selector no se contradicen: o el checkbox desaparece
      reemplazado por el selector, o marcarlo fija el selector en Ranked y
      elegir otro tipo lo desmarca (la eleccion es del Arquitecto; la variante
      conservadora es reemplazar el checkbox y aceptar `ranked_only` en la
      API como hasta ahora).
- [ ] "Limpiar" vuelve el selector a "Todos".
- [ ] e2e: en Chromium, elegir un tipo en el Inicio cambia el total de rondas
      que muestra y la consola queda limpia.

## Fuera de alcance

- Filtro por modo de juego (bomba, rehenes...): es A7, otra ficha.
- Filtros en la URL (A10) y filtros en el listado de Partidas (F16, ficha 78).
- Etiquetas legibles para tipos desconocidos: ya las da Datos (A2).
- (arquitecto) El mismo callejon sin filtros a la vista en Coach,
  Operadores, Compañeros, Duelos y Tendencias (0 rondas filtradas ->
  "Todavía no hay replays importados"): idea para `ALCANCE.md`, otra ficha.
  Esta solo arregla el Inicio, que es donde mira el e2e.
- Sembrar partidas de otro tipo en `seed_demo`: cambia los numeros del e2e.

## Diseno

El backend ya filtra por tipo: `_filters` (`views.py`) lee `match_type` y
`base_queryset` (`aggregates.py:73`) lo aplica a todo agregado; `/api/filters/`
ya devuelve `match_types` (distintos y no vacios de `Match`). La ficha es casi
toda frontend, mas tests que fijan el contrato que ya existe. Sin migracion,
sin `recompute`, sin metrica nueva (no hay fila de `docs/metricas.md`).

**Decision del criterio 3: el selector reemplaza al checkbox.** "Solo ranked"
desaparece de la barra; la API sigue aceptando `ranked_only` como hasta ahora
(no se toca `_filters` ni `base_queryset`). Los filtros viven en `useState` de
`App.jsx`, sin `localStorage` ni URL, asi que no hay estado viejo con
`ranked_only` que migrar; igual la funcion pura lo tolera (abajo), por si A10
(filtros en la URL) llega despues con enlaces viejos.

**Ajuste al criterio 5 (e2e).** `seed_demo` siembra todo `Ranked` y no se
toca: sumar partidas de otro tipo cambia los numeros que afirma media suite
(203 rondas, match point, rachas). El e2e arma el segundo tipo interceptando
`/api/filters/`, como ya hace `Datos lista modos y tipos de partida sin
nombre` con `/api/unknown/`. Elegir ese tipo deja el Inicio en 0 rondas, y
hoy el Inicio con 0 rondas muestra "Todavía no hay replays importados" y
**esconde la barra de filtros**: el usuario no puede ni apretar "Limpiar".
Con un selector de tipo ese callejon pasa a ser facil de pisar (tipo +
mapa + periodo), asi que el Inicio entra en la ficha (abajo, paso 4). Las
demas paginas que hacen lo mismo (Coach, Operadores, Compañeros, Tendencias,
Duelos) quedan fuera: ver `## Fuera de alcance` agregado abajo.

### Archivos

1. **`frontend/src/tipoPartida.js`** (nuevo), logica pura, sin React:
   - `opcionesDeTipo(matchTypes)` -> `[{ value: '', label: 'Todos' }, ...]`
     con una opcion por valor no vacio, sin repetidos, en el orden que manda
     la API (ya viene ordenado); `label` = el valor tal cual (los nombres de
     tipos desconocidos ya los arregla Datos, A2). `null`/`undefined` -> solo
     "Todos".
   - `tipoElegido(filtros)` -> `filtros.match_type || (filtros.ranked_only ?
     'Ranked' : '')`. Es lo que muestra el `<select>`.
   - `conTipo(filtros, tipo)` -> `{ ...filtros, match_type: tipo, ranked_only:
     false }`. Elegir un tipo apaga `ranked_only` siempre, asi nunca viajan
     los dos contradiciendose (`ranked_only=1&match_type=Unranked` daria 0
     rondas sin explicacion). `false` lo saca `qs()` y no prende "Limpiar"
     (`Object.values(value).some(Boolean)`).
   - `hayFiltros(filtros)` -> `Object.values(filtros || {}).some(Boolean)`;
     lo usan `Filters.jsx` (boton Limpiar, reemplaza la expresion inline) y
     `Dashboard.jsx`.
2. **`frontend/src/tipoPartida.test.js`** (nuevo, vitest, mismo estilo que
   `mapas.test.js`):
   - `opciones de tipo arrancan con Todos y siguen el orden de la API`
   - `opciones de tipo sin datos dejan solo Todos`
   - `opciones de tipo sacan vacios y repetidos`
   - `el tipo elegido sale de match_type`
   - `solo ranked viejo se lee como Ranked`
   - `elegir un tipo apaga solo ranked`
   - `elegir Todos deja match_type vacio y qs no lo manda` (usa `qs` de
     `api.js`: `qs(conTipo({ ranked_only: true }, ''))` es `''`)
   - `hay filtros ignora vacios y false`
3. **`frontend/src/components/Filters.jsx`**: se borra el `<label
   className="check">` de "Solo ranked" y en su lugar (despues de Periodo y
   del rango Desde/Hasta) va
   `<label>Tipo<select value={tipoElegido(value)} onChange={(e) =>
   onChange(conTipo(value, e.target.value))}>` con
   `opcionesDeTipo(data?.match_types)`. Se muestra siempre, como Mapa, aunque
   haya un solo tipo: el usuario ve que filtro existe. "Limpiar" ya hace
   `onChange({})`, que deja el selector en "Todos"; su condicion pasa a
   `hayFiltros(value)`.
4. **`frontend/src/pages/Dashboard.jsx`**: hoy `if (!total ||
   !total.rounds) return <EmptyState .../>`. Pasa a: si no hay rondas **y**
   `hayFiltros(filters)`, se pinta el `page-head` (h1 "Resumen", subtitulo
   `0 rondas con estos filtros`), la `<Filters>` y un
   `<p className="note">Ninguna ronda con estos filtros. Cambia alguno o
   usa Limpiar.</p>`, y `return` ahi (sin KPIs ni paneles). Sin filtros sigue
   el `EmptyState` de siempre (base vacia de verdad). No usar la clase
   `empty-state` en el caso filtrado: el e2e de "todas las paginas cargan"
   la busca en 0.
5. **`backend/tests/test_tipo_de_partida.py`** (nuevo), con `factories.py`
   (`make_match(match_type=...)`, `build_dataset` o rondas a mano): una base
   con 2 partidas Ranked y 1 Unranked, rondas tuyas en las tres.
   - `test_filtrar_por_ranked_da_lo_mismo_que_solo_ranked`: `overall`,
     `attack` y `defense` de `/api/overview/?match_type=Ranked` iguales a los
     de `?ranked_only=1`.
   - `test_filtrar_por_unranked_deja_afuera_las_ranked`: `overall.rounds` =
     rondas de la Unranked.
   - `test_las_opciones_listan_cada_tipo_una_vez`: `/api/filters/` da
     `match_types == ["Ranked", "Unranked"]`, y una partida con `match_type=""`
     no agrega una opcion vacia.
   - `test_un_tipo_que_no_existe_da_cero_rondas_y_no_500`:
     `?match_type=Nada` -> 200 y `overall.rounds == 0`.
   - `test_ranked_only_con_otro_tipo_no_da_500`: `?ranked_only=1&match_type=Unranked`
     -> 200 (documenta que la API los aplica juntos; la UI ya no los manda
     juntos).
6. **`frontend/e2e/humo.spec.js`**, test nuevo `el selector de tipo filtra
   el Inicio`, con `vigilarConsola`:
   - `page.route('**/api/filters/', async (route) => { const r = await
     route.fetch(); const json = await r.json(); route.fulfill({ response:
     r, json: { ...json, match_types: [...json.match_types, 'Unranked'] } })
     })`, antes del `goto('/')`.
   - La barra no tiene "Solo ranked" (`getByText('Solo ranked')` en 0) y el
     `<select>` de `getByLabel('Tipo')` tiene "Todos", "Ranked", "Unranked".
   - Elegir "Ranked" con `page.waitForRequest(/\/api\/overview\/\?.*match_type=Ranked/)`;
     el subtitulo sigue `29 partidas · 203 rondas analizadas` (todo el seed
     es Ranked).
   - Elegir "Unranked": se ve `Ninguna ronda con estos filtros`, la barra
     sigue en pantalla y `.empty-state` en 0.
   - "Limpiar": vuelve `203 rondas analizadas` y el selector a `''`.
   - Consola limpia.

### Orden

1. `tipoPartida.js` + su test (`npm test`).
2. `test_tipo_de_partida.py` (pasa sin tocar backend: si alguno falla, es un
   bug real del filtro y se arregla en `_filters`/`base_queryset`, no en el
   test).
3. `Filters.jsx`, despues `Dashboard.jsx`.
4. e2e, `npm run build`, `verificar.sh`.

### Que puede romperse

- Otro e2e que use "Solo ranked": hoy ninguno (`git grep "Solo ranked"`
  solo da `Filters.jsx`). Si el Dev encuentra uno al implementar, se cambia a
  `getByLabel('Tipo')`.
- `Filters` la usan Inicio, Coach, Operadores, Compañeros, Duelos y
  Tendencias: el selector aparece en todas; el e2e de "todas las paginas
  cargan" cubre que ninguna rompa.
- Pisa archivos de ramas abiertas: `Dashboard.jsx` y `humo.spec.js` con la
  76, `humo.spec.js` con la 75. Los cambios son en zonas distintas (la 76
  agrega un KPI al Resumen; esto toca el `if` del vacio y la barra).
  **Implementar despues de que #76 se mergee** (prioriza, no bloquea).
- Sin migracion, sin parser, sin `recompute`: no va a `## Verificar en el PC`.

### Verificacion manual

`npm run dev` con una base real que tenga ranked y otra cosa: el selector
lista los tipos que hay, elegir uno cambia los numeros del Inicio y del
Coach, combinarlo con un mapa sin partidas de ese tipo muestra "Ninguna ronda
con estos filtros" con la barra visible, y "Limpiar" vuelve a todo.

Skills: no aplica (un `<select>` mas en una barra que ya existe; no hay
dominio nuevo que buscar afuera). Sin arena: una sola forma obvia. Sin plan
por consenso: chica, sin datos que se reescriban.
OMC: plan=— · revisión=— · verificación=—

## Implementacion

## Revision

## QA

## Para el humano
