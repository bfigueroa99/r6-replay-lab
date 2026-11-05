# 85. Un filtro sin rondas esconde la barra en Coach, Operadores, Compañeros, Duelos y Tendencias

estado: aprobado
candado: release 2026-11-05T14:05Z
rama: claude/equipo-dev/85-filtro-sin-rondas-esconde-la-barra
tipo: bug
epica: -
area: frontend
prioridad: 3
fuente: idea anotada en ESTADO.md por la sesion de la 77 ("Coach, Operadores, Compañeros, Duelos y Tendencias con 0 rondas filtradas muestran 'Todavía no hay replays importados' y esconden la barra de filtros"); el Inicio ya se arreglo en la 77
archivos: frontend/src/tipoPartida.js, frontend/src/tipoPartida.test.js, frontend/src/components/ui.jsx, frontend/src/pages/Coach.jsx, frontend/src/pages/Operators.jsx, frontend/src/pages/Teammates.jsx, frontend/src/pages/Duelos.jsx, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js
turnos: dev 20261105T1303Z-c1PA8YY, revisor 20261105T1330Z-cTQKqvr, qa 20261105T1358Z-cxcyM5F

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Los filtros son compartidos entre paginas. Si en el Inicio elegis un tipo,
un mapa o un rango sin rondas y despues abris el Coach, Operadores,
Compañeros, Duelos o Tendencias, hoy esas paginas dicen "Todavía no hay
replays importados", ofrecen importar y esconden la barra de filtros: no hay
como apretar Limpiar sin volver al Inicio, y el mensaje es falso. Con el
arreglo se ve la pagina con su barra y "0 rondas con estos filtros", como ya
hace el Inicio desde la 77.

## Repro (dev 696c79d)

1. `manage.py seed_demo` (todo Ranked) y la app abierta.
2. En el Inicio, Tipo = un tipo sin partidas (el e2e lo agrega con
   `page.route` sobre `/api/filters/`, como el test del selector de tipo).
   El Inicio dice "0 rondas con estos filtros" y mantiene la barra.
3. Menu -> Coach: "Todavía no hay replays importados", sin barra de filtros.
   Lo mismo en Operadores, Compañeros, Duelos y Tendencias.

## Criterios de aceptacion

- [ ] Con filtros puestos y 0 rondas, Coach, Operadores, Compañeros, Duelos y
      Tendencias muestran su titulo, la barra de filtros y "0 rondas con
      estos filtros", sin `.empty-state` (e2e).
- [ ] Limpiar desde esa vista vuelve a los numeros sin filtros (e2e).
- [ ] Sin filtros y con la base vacia, el EmptyState sigue igual (logica pura
      con vitest: `vistaSinRondas`).
- [ ] Mientras llega la respuesta nueva despues de limpiar, la vista no pasa
      por el EmptyState (vitest: `loading` con filtros vacios no da
      `importar`).

## Fuera de alcance

- Partidas, Datos, Jugador y el detalle: no usan el EmptyState por filtros.
- Cambiar el texto del EmptyState o el de "0 rondas" del Inicio.

## Diseno

(dev, ficha escrita en el momento por "Sin trabajo": bug real reproducible.)

- `tipoPartida.js`: `vistaSinRondas({ vacio, filtros, cargando })` devuelve
  `null` (hay rondas), `'filtrado'` (0 rondas con filtros, o cargando la
  respuesta nueva: asi la barra no se desmonta y no pierde lo abierto) o
  `'importar'` (base vacia de verdad).
- `ui.jsx`: `SinRondasFiltradas({ titulo, filtros })`, cabecera con el
  titulo, la barra que le pasa la pagina y la nota "0 rondas con estos
  filtros". Recibe la barra como elemento para no importar `Filters` desde
  `ui.jsx`.
- Cada pagina reemplaza su `return <EmptyState ...>` por la decision de
  `vistaSinRondas`.
- e2e en `humo.spec.js`: un tipo sin partidas en el Inicio y recorrer las
  cinco paginas por el menu (los filtros viven en el estado de `App`).

## Implementacion

(dev 20261105T1303Z-c1PA8YY, sobre dev 696c79d; turno "Sin trabajo": la 79
la reclamo otra sesion segundos antes.)

- `tipoPartida.js`: `vistaSinRondas({ vacio, filtros, cargando })` junto a
  `hayFiltros`, con 4 vitest (`vistaSinRondas (ficha 85)`).
- `ui.jsx`: `SinRondasFiltradas({ titulo, filtros })`, con los mismos textos
  que el Inicio ("0 rondas con estos filtros" y "Ninguna ronda con estos
  filtros. Cambia alguno o usa Limpiar.").
- Coach, Operadores, Compañeros (`loading || overview.loading`), Duelos y
  Tendencias deciden con `vistaSinRondas`; cada una pasa su barra con sus
  props (`showOperator={false}`, `showSession`).
- e2e `un filtro sin rondas deja la barra en todas las páginas`
  (`humo.spec.js`): Unranked en el Inicio (agregado con `page.route`), las
  cinco paginas por el menu, Limpiar desde Tendencias. **Falla sin el
  arreglo** (paginas revertidas con `git stash`, build): `expect(h1)
  toHaveText "Coach"`, element not found, `humo.spec.js:846`. Pasa con el
  arreglo.
- Desvio: ninguno. El Inicio queda con su criterio propio
  (`hayFiltros(overview.data?.filters)`); las cinco usan `cargando`, que no
  necesita que la API devuelva los filtros.
- Revision ciega (`omc-code-reviewer`, eje estandares): aprobar, 3 LOW sin
  arreglar, anotados para el Revisor: (1) Duelos decide por `!totals?.duels`,
  asi que un filtro con rondas y sin duelos dice "0 rondas"; (2) con la base
  vacia de verdad y una recarga en curso se ve un instante "0 rondas con
  estos filtros"; (3) dos criterios para lo mismo (Inicio y las cinco).
- `verificar.sh`: VERDE 951aeab5d (953 tests backend, 190 vitest, 60 e2e).

Skills: no aplica (patron ya resuelto en el Inicio por la 77).
OMC: plan=— · revisión=3 hallazgos (0 arreglados, todos LOW) · verificación=—

## Revision 2026-11-05 sobre 6658a30

Revisor 20261105T1330Z-cTQKqvr. Revision a ciegas (eje de estandares; diff de
un solo tema y 125 lineas, sin superficie de seguridad), confirmada por el
lider. Partida de verde: verificar.sh VERDE 6658a30 (953 tests backend,
190 vitest, 60 e2e).

Criterios de aceptacion:

- Titulo, barra y "0 rondas con estos filtros" sin `.empty-state` en las cinco
  paginas: e2e de `humo.spec.js` (navega por el menu, asi no pierde los
  filtros; con el codigo anterior falla porque el EmptyState no tiene el `h1`).
  Cumple.
- Limpiar vuelve a los numeros: mismo e2e. Cumple.
- Base vacia sin filtros sigue en el EmptyState: `vistaSinRondas` en
  `tipoPartida.test.js`. Cumple.
- Sin parpadeo al limpiar: rama `cargando` cubierta en vitest (el e2e solo
  mira el estado final; alcanza con el unitario). Cumple.

`hayFiltros` mira el objeto entero de App, asi que cuentan tambien `session`,
`since/until` y `operator` aunque la barra de la pagina no los muestre;
`ranked_only: false` y `match_type: ''` no cuentan. El diff toca solo
archivos de `archivos:`; sin `console.log`, identificadores sin tildes, UI con
tildes, sin numeros nuevos.

Hallazgos (ninguno bloquea):

- [bug] MEDIUM frontend/src/pages/Duelos.jsx:43
  Que pasa: Duelos decide "vacio" por `totals.duels` (bajas + muertes contra
  rivales), no por rondas, y muestra "0 rondas con estos filtros".
  Por que es cierto: un filtro de mapa/lado con rondas pero sin ningun duelo
  (sobreviviste sin matar) deja 1 ronda y 0 duelos, y la pagina dice
  "0 rondas". Antes decia "Todavía no hay replays importados", que era peor.
  Arreglo sugerido: que `SinRondasFiltradas` acepte el texto y Duelos pase
  "0 duelos con estos filtros".
- [estilo] LOW frontend/src/components/ui.jsx:260: durante la carga despues de
  Limpiar la nota dice "usa Limpiar" y el boton ya no esta (dura lo que tarda
  la respuesta). Sin arreglo obligatorio.
- [bug] LOW Coach/Operadores/Compañeros/Duelos: si el filtro que deja 0 rondas
  es `session` (puesto en Tendencias), la barra no lo muestra; Limpiar lo
  resuelve. Ya pasaba en la vista normal. Sin arreglo obligatorio.

Veredicto: aprobar -> `revisado`.

OMC: plan=— · revisión=3 hallazgos (0 arreglados; 1 MEDIUM, 2 LOW) · verificación=—

## QA 2026-11-05 sobre bd0ed81

QA 20261105T1358Z-cxcyM5F. Scripts en el scratchpad (no van al repo); base
SQLite aparte con `SQLITE_PATH`, nunca la del usuario.

- `verificar.sh` (check.sh completo): VERDE bd0ed8118 en 114 s, 953 tests
  backend, 190 vitest, 60 e2e.
- Criterio 1, app real por el camino de la UI (sin `page.route`):
  `SQLITE_PATH=<tmp> manage.py migrate && manage.py seed_demo` (29 partidas,
  203 rondas), `runserver 127.0.0.1:8785`; Playwright: en el Resumen,
  Periodo = "Entre dos fechas", 2000-01-01 a 2000-01-02, y por el menu a las
  cinco paginas. Coach, Operadores, Compañeros, Duelos y Tendencias: `h1`
  correcto, `.filters`=1, `.empty-state`=0, "0 rondas con estos filtros"=1,
  el rango sigue puesto. Cumple.
- Criterio 2: Limpiar en cada una de las cinco con el rango puesto: la nota
  se va, `.empty-state`=0, paneles/tablas 6/4/12/8/38. Consola sin errores
  ni warnings. Cumple.
- Criterio 3: base recien migrada, sin datos ni filtros, `/coach`,
  `/operadores`, `/companeros`, `/duelos`, `/tendencias`: `.empty-state`=1,
  sin barra ni nota; consola limpia. Vitest `sin filtros y base vacia
  ofrece importar` en verde. Cumple.
- Criterio 4: vitest `recien limpiado y cargando no pasa por el EmptyState`
  en verde. Cumple.
- Mutaciones (codigo restaurado despues, `git status` limpio):
  (1) sin `|| cargando` en `vistaSinRondas` -> cae el vitest del criterio 4;
  (2) `vistaSinRondas` siempre `'filtrado'` -> cae `sin filtros y base vacia
  ofrece importar`; (3) `Duelos.jsx` de `origin/dev` + `vite build` ->
  `E2E_CHROMIUM=/opt/pw-browsers/chromium npx playwright test
  e2e/humo.spec.js -g "un filtro sin rondas deja la barra"` falla en
  `humo.spec.js:846`; restaurado, 1 passed.
- Chunk inicial: `index-*.js` 191,2 kB en la rama contra 190,7 kB en dev
  (+0,3 %).
- Hallazgo MEDIUM del revisor, reproducido (no cae ningun criterio: la
  ficha habla de 0 rondas): base con una partida en Club House con un duelo
  y otra en Bank con 1 ronda sin bajas ni muertes (`factories.py`), Duelos
  con Mapa = Bank dice "0 rondas con estos filtros" y el Resumen con el
  mismo filtro muestra la ronda (`/api/overview/?map=bank` rounds=1,
  `/api/duels/?map=bank` duels=0). Antes decia "Todavía no hay replays
  importados". Va como ficha 86 (bug, `propuesto`) en `backlog`.

Veredicto: `aprobado`.

Skills: no aplica.
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier: 4 criterios VERIFIED, 0 bloqueantes)

## Para el humano
