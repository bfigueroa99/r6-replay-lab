# 86. Duelos dice "0 rondas con estos filtros" con un filtro que tiene rondas pero ningun duelo

estado: aprobado
candado: release 2026-11-05 15:36 UTC
rama: claude/equipo-dev/86-duelos-dice-0-rondas-con-rondas-sin-duelos
tipo: bug
epica: -
area: fullstack
prioridad: 3
fuente: hallazgo MEDIUM del Revisor de la 85 (`Duelos.jsx:43`), reproducido por la QA 20261105T1358Z-cxcyM5F en la app real
archivos: backend/replays/views.py, backend/tests/test_duels.py, frontend/src/tipoPartida.js, frontend/src/tipoPartida.test.js, frontend/src/components/ui.jsx, frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js
turnos: qa 20261105T1358Z-cxcyM5F, arquitecto 20261105T1429Z-c7UZ3T6, dev 20261105T1429Z-chSa5eY, revisor 20261105T1455Z-caYiimg, qa 20261105T1521Z-cEexMKJ

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Duelos decide si esta "vacia" por la cantidad de duelos (bajas y muertes
contra rivales), no por rondas. Con un filtro que deja rondas donde no
mataste ni moriste (un mapa o un lado), la pagina dice "0 rondas con estos
filtros" mientras el Resumen con el mismo filtro muestra esas rondas: el
numero es falso. Con el arreglo dice que no hay duelos, no que no hay rondas.

## Repro (dev a9f8a28)

1. Base de prueba con `backend/tests/factories.py`: una partida en Club
   House con una ronda en la que mataste a un rival (`make_event`) y otra en
   Bank con una ronda sin bajas ni muertes
   (`make_round_player(r, kills=0, died=False)`).
2. `runserver`, Duelos, Mapa = Bank: "0 rondas con estos filtros".
3. Resumen con el mismo filtro: la ronda esta. `/api/overview/?map=bank`
   da `rounds: 1`; `/api/duels/?map=bank` da `duels: 0`.

## Criterios de aceptacion

- [ ] Con un filtro que deja rondas y 0 duelos, Duelos mantiene titulo y
      barra y dice "0 duelos con estos filtros" (o equivalente), nunca
      "0 rondas" (e2e o vitest).
- [ ] Con un filtro que deja 0 rondas sigue diciendo "0 rondas con estos
      filtros" (el e2e de la 85 sigue verde).
- [ ] Base vacia sin filtros: EmptyState igual que hoy.

## Fuera de alcance

- Cambiar como se cuentan los duelos o los textos del resto de las paginas.
- Que `/api/duels/` devuelva rondas si no hace falta: el arreglo puede ser
  solo de texto (`SinRondasFiltradas` acepta el subtitulo).

## Diseno

Arquitecto 20261105T1429Z-c7UZ3T6 sobre dev 85009f6. Una sola forma obvia:
sin arena ni consenso.

**Causa.** `Duelos.jsx:43` pasa `vacio: !totals?.duels` a `vistaSinRondas`, y
`/api/duels/` no dice cuantas rondas quedan con el filtro. Hacen falta las
rondas para separar "0 rondas" (barra + texto de la 85) de "rondas sin
duelos" (texto nuevo).

**Archivos y por que esos**

1. `backend/replays/views.py` (`duels`, ~linea 376): agregar al payload, al
   nivel de `totals` y no adentro, `"rounds": agg.base_queryset(**filters).count()`.
   Afuera de `duel_totals` a proposito: `test_duels.py:96` compara ese dict
   entero y `coach.py:699/732` lo usa; no hace falta tocarlos. Es la misma
   cuenta que `rounds` del Resumen (filas `is_me` con los filtros).
2. `frontend/src/tipoPartida.js`: funcion pura nueva al lado de
   `vistaSinRondas`:
   ```js
   /** Duelos: sin rondas manda la 85; con rondas pero sin bajas ni muertes contra rivales, 'sin-duelos'. */
   export function vistaDuelos({ rondas, duelos, filtros, cargando }) {
     if (!rondas) return vistaSinRondas({ vacio: true, filtros, cargando })
     return duelos ? null : 'sin-duelos'
   }
   ```
3. `frontend/src/components/ui.jsx` (`SinRondasFiltradas`): dos props
   opcionales con el texto de hoy como default, `subtitulo = '0 rondas con
   estos filtros'` y `nota = 'Ninguna ronda con estos filtros. Cambia alguno o
   usa Limpiar.'`. Las demas paginas no cambian.
4. `frontend/src/pages/Duelos.jsx`: reemplazar el `vistaSinRondas(...)` por
   `vistaDuelos({ rondas: data?.rounds, duelos: totals?.duels, filtros: filters, cargando: loading })`;
   `'importar'` y `'filtrado'` igual que hoy; `'sin-duelos'` ->
   `<SinRondasFiltradas titulo="Duelos" subtitulo="0 duelos con estos filtros"
   nota="Hay rondas con estos filtros, pero en ninguna mataste a un rival ni te mató uno. Cambia algún filtro o usa Limpiar."
   filtros={<Filters .../>} />` (la misma barra, asi Limpiar sigue a mano y
   no se remonta: la 85 cuida eso).

**Tests nuevos**

- `backend/tests/test_duels.py`:
  `test_la_api_de_duelos_cuenta_las_rondas_aunque_no_haya_duelos` (dos
  rondas, una con baja a un rival en Club House y otra en Bank sin bajas ni
  muerte con `make_round_player(r, kills=0, died=False)`; `/api/duels/?map=bank`
  da `rounds == 1` y `totals.duels == 0`; sin filtro, `rounds == 2`).
- `frontend/src/tipoPartida.test.js`, `describe('vistaDuelos (ficha 86)')`:
  `con rondas y duelos no hay vista especial` (null), `con rondas y sin duelos
  es sin-duelos` (con y sin filtros), `sin rondas y con filtros es filtrado`,
  `sin rondas ni filtros es importar`, `sin rondas mientras carga es filtrado`.
- `frontend/e2e/humo.spec.js`: `Duelos con rondas pero sin duelos dice 0
  duelos y no 0 rondas`. seed_demo no tiene un filtro asi, entonces se
  intercepta como hace la 85 con `/api/filters/`: `page.route('**/api/duels/**')`
  con `route.fetch()` y `fulfill` del json con `totals: { kills: 0, deaths: 0,
  duels: 0, winrate: null }`, `nemesis: []`, `operators: []`, `rivals: []` y
  `rounds` tal cual. Afirma `.page-head p` = `0 duelos con estos filtros`,
  `.filters` visible, `.empty-state` con 0 y consola limpia. El test de la 85
  (`un filtro sin rondas deja la barra en todas las páginas`) ya cubre que
  Duelos con 0 rondas sigue diciendo `0 rondas con estos filtros`: no se toca.

**Orden:** views.py + test backend; `vistaDuelos` + vitest; ui.jsx;
Duelos.jsx; e2e; `npm run build`; `check.sh`.

**Que puede romperse:** nada de datos (sin migracion ni recompute). El
`if (error)`/`loading` de arriba de Duelos no cambia. Si alguien usa
`SinRondasFiltradas` sin las props nuevas, ve lo de hoy.

**Archivos ocupados:** la 81 (textos con tildes, `con hallazgos`) toca
`Duelos.jsx`, `ui.jsx` y `humo.spec.js` en lineas de texto distintas a
estas. Implementar despues de que #81 se mergee (prioriza, no bloquea; si se
implementa antes, el conflicto es de texto y lo resuelve P3).

**Verificacion manual:** base de prueba del Repro de la ficha (factories),
`runserver`, Duelos con Mapa = Bank: "0 duelos con estos filtros", barra
visible; Limpiar vuelve a los numeros. Con Tipo = un tipo sin partidas:
"0 rondas con estos filtros" como hoy.

**`docs/metricas.md`:** sin numero nuevo en la UI (el conteo de rondas solo
decide que texto mostrar), sin fila.

Skills: no aplica (sin dominio nuevo: un texto y un conteo que el repo ya resuelve en la 85)
OMC: plan=— (ficha chica, una forma obvia) · revisión=— · verificación=—

## Implementacion

(dev 20261105T1429Z-chSa5eY, sobre dev 85009f6.)

Quedo el diseno entero:

- `views.py` (`duels`): `"rounds": agg.base_queryset(**filters).count()` al nivel de `totals`, fuera de `duel_totals` (lo comparte el coach).
- `tipoPartida.js`: `vistaDuelos` como la pide el diseno, y ademas `textosSinDuelos(filtros)` (ver desvios).
- `ui.jsx`: `SinRondasFiltradas` con `subtitulo` y `nota` opcionales; el default es el texto de hoy, las demas paginas no cambian.
- `Duelos.jsx`: `vistaDuelos` en lugar de `vistaSinRondas`; `'sin-duelos'` pinta `SinRondasFiltradas` con la misma barra.

Test que falla primero (bug): `python manage.py test tests.test_duels.RondasSinDuelosTests` -> `KeyError: 'rounds'` antes del arreglo; `npx vitest run src/tipoPartida.test.js` -> 5 failed (`vistaDuelos` no existia). Despues, verdes los dos.

Tests por criterio:

- Criterio 1 (rondas y 0 duelos -> "0 duelos", nunca "0 rondas"): `test_la_api_de_duelos_cuenta_las_rondas_aunque_no_haya_duelos` (backend), `vistaDuelos (ficha 86)` (5 vitest), `textosSinDuelos (ficha 86)` (2 vitest) y el e2e `Duelos con rondas pero sin duelos dice 0 duelos y no 0 rondas` (`page.route` vacia los duelos de la respuesta real y deja `rounds`; sin filtros y con Lado = ataque, barra y Limpiar visibles, sin `.empty-state`, consola limpia). Sobre dev ese e2e cae: sin filtros, `vistaSinRondas` daba `'importar'` y se veia el EmptyState.
- Criterio 2 (0 rondas -> "0 rondas con estos filtros"): el e2e de la 85 (`un filtro sin rondas deja la barra en todas las páginas`) sin tocar, verde; vitest `sin rondas y con filtros es filtrado`.
- Criterio 3 (base vacia sin filtros -> EmptyState): vitest `sin rondas ni filtros es importar`.

Desvios del diseno:

- Sin filtros puestos, la vista `sin-duelos` dice "0 duelos" y "Hay rondas importadas, pero en ninguna mataste a un rival ni te mató uno." en vez de "con estos filtros ... usa Limpiar", porque sin filtros Limpiar no se dibuja (`Filters.jsx`). Lo marco la revision ciega (LOW). Con filtros, el texto es el del diseno. Los textos salen de `textosSinDuelos`, que es logica pura y lleva vitest.
- El e2e espera la respuesta filtrada (`waitForResponse`, `side=Attack`) antes de afirmar. Sin esa espera el test terminaba con la ruta interceptada todavia en vuelo y `route.fetch` fallaba (lo vio la primera corrida de `check.sh`).

Anotado sin arreglar (LOW de la revision, fuera de alcance):

- `rounds` repite `faced.base.rounds`; se deja la cuenta explicita, como pide el diseno.
- En la vista `sin-duelos` tampoco se ven `faced` ni `rivals`, que podrian traer datos. Ya pasaba antes; si vale la pena mostrarlos, va en otra ficha.

`docs/metricas.md`: sin fila, porque no hay numero nuevo en la UI.

`verificar.sh`: VERDE af11d395c (955 tests backend, 197 vitest, 62 e2e).

Skills: no aplica (un texto y un conteo que el repo ya resuelve en la 85).
OMC: plan=— · revisión=3 hallazgos (1 arreglado) · verificación=—

## Revision 2026-11-05 sobre 61625a8

(revisor 20261105T1455Z-caYiimg; rama al dia con dev 85009f6.)

Revision a ciegas (`omc-code-reviewer`, eje de estandares; vista GET, sin
POST ni red: sin eje de seguridad). Confirmado por el Revisor:

- `rounds` de `/api/duels/` (`agg.base_queryset(**filters).count()`) cuenta
  lo mismo que `rounds` del Resumen (`totals()` hace `Count("id")` sobre el
  mismo `base_queryset`, filas `is_me`).
- `vistaDuelos` mantiene los casos de la 85: error primero, `Loading` sin
  datos, 0 rondas -> `importar`/`filtrado`, `rounds` ausente cae en `!rondas`
  sin romper.
- Los tests fallan con el bug: backend `KeyError: 'rounds'`; vitest importa
  funciones que no existian; el e2e, sin filtros y 0 duelos, veia
  `EmptyState`. El e2e espera la respuesta `side=Attack` antes de afirmar
  (ninguna otra request lleva ese parametro), sin ruta en vuelo al terminar.
- Sin dependencia, POST ni numero nuevo en la UI (sin fila en
  `metricas.md`, correcto); comentarios sin tildes, textos de UI con tildes.

Criterios: 1 cubierto (e2e `Duelos con rondas pero sin duelos dice 0 duelos
y no 0 rondas`, vitest `vistaDuelos`/`textosSinDuelos`, test backend); 2
cubierto (e2e de la 85 sin tocar, verde); 3 cubierto (vitest `sin rondas ni
filtros es importar`). `verificar.sh`: VERDE d75692b61 (955 tests backend,
197 vitest, 62 e2e).

Hallazgos:

- [bug] LOW `frontend/src/pages/Duelos.jsx:43-54`
  Que pasa: mientras carga la respuesta de un filtro nuevo, la vista se
  calcula con los datos viejos y los textos con los filtros nuevos.
  Como reproducirlo: en la vista `sin-duelos` sin filtros, elegir un tipo
  sin partidas: hasta que llega la respuesta se lee "Hay rondas con estos
  filtros" y despues cambia a "0 rondas con estos filtros". Transitorio
  (el comentario del e2e lo reconoce).
  Arreglo sugerido: con `loading` y vista `sin-duelos`, usar el texto
  neutro de `filtrado`; o dejarlo. No bloquea.

Veredicto: aprobar -> `revisado`.

OMC: plan=— · revisión=1 hallazgo LOW (0 arreglados; el Revisor no arregla) · verificación=—

## QA 2026-11-05 sobre 27c46da

(qa 20261105T1521Z-cEexMKJ; rama al dia con dev 85009f6. Bases sinteticas en
el scratchpad, nunca `.rec` ni `.sqlite3` al repo.)

Base del Repro con `factories.py` (Club House con una baja a un rival, Bank
con una ronda sin bajas ni muerte), `runserver`; tambien base vacia y base de
`seed_demo`.

1. Rondas sin duelos -> "0 duelos": cubierto. `curl /api/duels/?map=bank`:
   `rounds=1 duels=0`. En Chromium, Duelos con Mapa = Bank: h1 "Duelos",
   subtitulo "0 duelos con estos filtros", nota "Hay rondas con estos filtros,
   pero en ninguna mataste a un rival ni te mató uno...", barra y Limpiar
   visibles, sin `.empty-state`; Limpiar vuelve a los numeros. Consola limpia.
2. 0 rondas -> "0 rondas con estos filtros": cubierto. Bank + Lado Defensa en
   Chromium: "0 rondas con estos filtros" con la barra; API `rounds=0`.
3. Base vacia sin filtros: cubierto. `.empty-state` "Todavía no hay replays
   importados", sin barra; API `rounds=0 duels=0`.

Bordes de `/api/duels/` (base factories), todos 200: sin filtro 2/1,
`?map=club-house` 1/1, `?map=noexiste` 0/0, `?map=` 2/1, `?until=foo` 2/1,
`?page=-1` 2/1, `?days=-1` 0/0, `?match_type=Ranked` 2/1. `rounds` de Duelos
igual a `overall.rounds` de `/api/overview/` en 8 combinaciones (factories y
seed_demo: 203, Bank 70, Attack 116, `days=-1` 0).

Mutacion: `rounds` fijo en 0 en `views.py` -> `RondasSinDuelosTests` FAIL
(`0 != 1`); `vistaDuelos` sin `'sin-duelos'` -> 1 vitest y el e2e `Duelos con
rondas pero sin duelos dice 0 duelos y no 0 rondas` fallan; subtitulo
cambiado a "0 rondas con estos filtros" -> 1 vitest falla. Restaurado: verde.

Chunk inicial de `vite build`: dev 191.14 kB -> rama 191.66 kB (+0.27 %).
`verificar.sh`: VERDE 27c46daef (955 tests backend, 197 vitest, 62 e2e).
`omc-verifier`: PASS (3 VERIFIED).

Veredicto: `aprobado`.

OMC: plan=— · revisión=— · verificación=PASS

## Para el humano

- 2026-11-05 (revisor 20261105T1455Z-caYiimg): LOW sin arreglar, no bloquea: mientras carga un filtro nuevo, la vista `sin-duelos` puede decir un instante "Hay rondas con estos filtros" antes de pasar a "0 rondas".
