# 85. Un filtro sin rondas esconde la barra en Coach, Operadores, Compañeros, Duelos y Tendencias

estado: implementado
candado: -
rama: claude/equipo-dev/85-filtro-sin-rondas-esconde-la-barra
tipo: bug
epica: -
area: frontend
prioridad: 3
fuente: idea anotada en ESTADO.md por la sesion de la 77 ("Coach, Operadores, Compañeros, Duelos y Tendencias con 0 rondas filtradas muestran 'Todavía no hay replays importados' y esconden la barra de filtros"); el Inicio ya se arreglo en la 77
archivos: frontend/src/tipoPartida.js, frontend/src/tipoPartida.test.js, frontend/src/components/ui.jsx, frontend/src/pages/Coach.jsx, frontend/src/pages/Operators.jsx, frontend/src/pages/Teammates.jsx, frontend/src/pages/Duelos.jsx, frontend/src/pages/Trends.jsx, frontend/e2e/humo.spec.js
turnos: dev 20261105T1303Z-c1PA8YY

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

## Revision

## QA

## Para el humano
