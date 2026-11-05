# 86. Duelos dice "0 rondas con estos filtros" con un filtro que tiene rondas pero ningun duelo

estado: en curso 2026-11-05
candado: -
rama: claude/equipo-dev/86-duelos-dice-0-rondas-con-rondas-sin-duelos
tipo: bug
epica: -
area: fullstack
prioridad: 3
fuente: hallazgo MEDIUM del Revisor de la 85 (`Duelos.jsx:43`), reproducido por la QA 20261105T1358Z-cxcyM5F en la app real
archivos: backend/replays/views.py, backend/tests/test_duels.py, frontend/src/tipoPartida.js, frontend/src/tipoPartida.test.js, frontend/src/components/ui.jsx, frontend/src/pages/Duelos.jsx, frontend/e2e/humo.spec.js
turnos: qa 20261105T1358Z-cxcyM5F, arquitecto 20261105T1429Z-c7UZ3T6

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

## QA

## Para el humano
