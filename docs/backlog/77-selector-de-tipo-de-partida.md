# 77. Selector de tipo de partida en la barra de filtros

estado: entregado
candado: -
rama: claude/equipo-dev/77-selector-de-tipo-de-partida
tipo: funcionalidad
epica: temporada-y-modo
area: frontend
prioridad: 2
fuente: ALCANCE.md A1; replica/features.csv ("Soporte de ranked, unranked y custom", must, clone partial: falta el selector en Filters.jsx); PR #14 cerrado sin merge el 2026-11-05 ya no lo cubre
archivos: frontend/src/tipoPartida.js, frontend/src/tipoPartida.test.js, frontend/src/components/Filters.jsx, frontend/src/pages/Dashboard.jsx, backend/tests/test_tipo_de_partida.py, frontend/e2e/humo.spec.js
turnos: po 20261105T0230Z-c8Ahepa, arquitecto 20261105T0247Z-cSs57wh, dev 20261105T0320Z-cNojwdB, revisor 20261105T0350Z-c5JBREy, qa 20261105T0403Z-c23PART, release 20261105T0403Z-c23PART

## PR

Titulo: `[equipo-dev][frontend] Selector de tipo de partida en la barra de filtros`

### Que cambia

La barra de filtros cambia el checkbox "Solo ranked" por un selector "Tipo" (Todos y cada tipo que hay en la base: Ranked, Unranked, Custom...). Todo lo que usa la barra (Inicio, Coach, Operadores, Compañeros, Duelos, Tendencias) se filtra por ese tipo. Si los filtros dejan el Inicio en 0 rondas, la barra sigue a la vista con la nota "Ninguna ronda con estos filtros" y el boton Limpiar, en vez del cartel de base vacia que la escondia.

### Por que esto y no otra cosa

Ficha 77 (ALCANCE.md A1; `must` de la referencia en `partial`). El backend ya filtraba por `match_type`: es casi todo frontend. El selector reemplaza al checkbox (variante conservadora): la API sigue aceptando `ranked_only` y la UI nunca manda los dos juntos.

### Como se probo

- verificar.sh: VERDE dc51ecf (QA) y sobre el commit de entrega; 922 tests backend, 170 vitest, 57 e2e.
- Tests nuevos: `tipoPartida.test.js` (8: opciones, tipo elegido, `ranked_only` viejo, elegir apaga `ranked_only`, `qs` sin `match_type` vacio, `hayFiltros`); `test_tipo_de_partida.py` (5: Ranked = `ranked_only`, Unranked excluye Ranked, opciones sin vacio ni repetidos, tipo inexistente da 0 y no 500, `ranked_only` + otro tipo no da 500); e2e `el selector de tipo filtra el Inicio`.
- QA: runserver con base vacia y sembrada, curl con parametros borde (todo 200), chunk inicial +0,3 %, 5 mutaciones que caen.
- OMC: diseno plan=— · revisión=— · verificación=—
- OMC: implementacion plan=— · revisión=3 hallazgos LOW (1 arreglado, 1 comentario corregido, 1 sin cambio) · verificación=—
- OMC: revision plan=— · revisión=2 hallazgos LOW (1 arreglado con test, 1 a Para el humano) · verificación=—
- OMC: QA plan=— · revisión=— · verificación=PASS

### Riesgos y lo que no entra

Sin migracion, sin `recompute`, sin parser, sin metrica nueva. Afuera: filtro por modo (A7), filtros en la URL (A10), filtros en Partidas (ficha 78) y el mismo callejon de 0 rondas en Coach, Operadores, Compañeros, Duelos y Tendencias (idea para ALCANCE.md).

### Como probarlo en 2 minutos

```
cd backend; python manage.py runserver
```
Abrir http://localhost:8000: la barra muestra "Tipo" en vez de "Solo ranked". Elegir un tipo cambia los numeros; combinarlo con un mapa sin partidas de ese tipo muestra "Ninguna ronda con estos filtros" con la barra visible; "Limpiar" vuelve a "Todos".

### Para el humano

Aviso, no bloquea: con la base vacia y un filtro puesto, el Inicio muestra la nota en vez del boton de importar; se sale con Limpiar.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Hoy la barra de filtros solo deja elegir "Solo ranked": quien juega unranked,
rapidas o customs no puede ver sus numeros de ese tipo sin mezclarlos con el
resto. Con un selector "Tipo" (Todos, Ranked, Unranked, la que haya en la base)
todo lo que usa la barra (Inicio, Coach, Operadores, Compañeros, Tendencias...)
se filtra por tipo de partida, y la app cierra un `must` de la referencia que
estaba en `partial`.

## Criterios de aceptacion

- [x] La barra de filtros muestra un `<select>` "Tipo" con "Todos" y una opcion
      por cada valor de `match_types` de `/api/filters/` (sembrado: al menos
      Ranked y uno mas); elegir uno manda `match_type=<valor>` a la API (vitest
      sobre la funcion que arma los parametros, o e2e mirando la request).
- [x] Con `match_type=Ranked`, `/api/overview/` da los mismos numeros que con
      `ranked_only=1` sobre la base sembrada (test backend: los dos caminos ya
      existen en `base_queryset`; el test fija que coinciden).
- [x] "Solo ranked" y el selector no se contradicen: o el checkbox desaparece
      reemplazado por el selector, o marcarlo fija el selector en Ranked y
      elegir otro tipo lo desmarca (la eleccion es del Arquitecto; la variante
      conservadora es reemplazar el checkbox y aceptar `ranked_only` en la
      API como hasta ahora).
- [x] "Limpiar" vuelve el selector a "Todos".
- [x] e2e: en Chromium, elegir un tipo en el Inicio cambia el total de rondas
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

Arquitecto 20261105T0247Z-cSs57wh. El backend ya filtraba (`_filters`, `base_queryset`, `match_types` en `/api/filters/`). El selector reemplaza al checkbox; logica pura en `tipoPartida.js` (`opcionesDeTipo`, `tipoElegido`, `conTipo`, `hayFiltros`); el Inicio con 0 rondas y filtros puestos muestra la barra y una nota. El e2e suma Unranked interceptando `/api/filters/` porque `seed_demo` es todo Ranked. Detalle en `git log`.

## Implementacion

Dev 20261105T0320Z-cNojwdB. Todo el diseno. Desvio: el vacio filtrado comparte arbol con el Resumen, y el EmptyState mira tambien los filtros de la respuesta, para no volver a montar la barra al apretar Limpiar (el e2e cuenta un solo pedido a `/api/filters/`).

## Revision 2026-11-05 sobre 6aae353

Revisor 20261105T0350Z-c5JBREy. Veredicto: aprobar. Hallazgos LOW: el e2e no afirmaba el total al elegir Unranked (agregado en la revision); base vacia + filtro muestra la nota en vez del boton de importar (aviso en Para el humano).

## Para el humano`.

Ficha:

- Criterios 1 a 5: los cubren los tests que cita la Implementacion. Los confirme en el diff: el vitest `elegir un tipo apaga solo ranked` con `qs`, `test_filtrar_por_ranked_da_lo_mismo_que_solo_ranked` (compara overall, attack y defense) y el e2e (opciones, request con `match_type=Ranked`, 0 rondas sin `.empty-state`, Limpiar vuelve a `''`, consola limpia).
- El diff toca solo archivos de `archivos:`. No hay numero nuevo en la UI: el total de rondas ya existia, asi que `metricas.md` no cambia. No hay identificadores con tildes ni `print` o `console.log`. Respeta Fuera de alcance: no toca modo, URL, Partidas ni `seed_demo`, y Coach y las otras paginas siguen igual.
- verificar.sh: VERDE 01ffb79 (codigo del Dev) y VERDE 6aae353 (con el test nuevo). Cada corrida: 922 tests backend, 170 vitest y 57 e2e.

Veredicto: aprobar -> `revisado`.

OMC: plan=— · revisión=2 hallazgos LOW (1 arreglado con test, 1 a Para el humano) · verificación=—

## QA 2026-11-05 sobre dc51ecf

QA 20261105T0403Z-c23PART. Ejercite el sistema sin releer el diff.

- **check.sh completo:** `git show origin/dev:scripts/equipo-dev/verificar.sh | bash -s --` -> `VERDE dc51ecf43: 922 tests backend, 170 vitest, 57 e2e. Todo en verde.` (exit 0).
- **runserver, base vacia** (`SQLITE_PATH` y `R6_ENV_FILE` temporales en el scratchpad, `manage.py migrate`, `runserver 8777`):
  `curl localhost:8777/api/filters/` -> `match_types: []` 200. `/api/overview/` con `match_type=Ranked`, `match_type=`, `match_type=Nada&ranked_only=1`, `match_type=%27%3B--`, `match_type=Ranked&until=foo` y `page=-1&match_type=Unranked` -> todos 200, `overall.rounds` 0.
- **runserver, base sembrada** con `tests/factories.py` (`manage.py shell` con un script: Ranked 3 + 3 rondas, Unranked 2, `match_type=""` 1, Custom 1):
  - `/api/filters/` -> `['Custom', 'Ranked', 'Unranked']`: sin opcion vacia (criterio 1).
  - `/api/overview/`: sin filtro 10 rondas; `match_type=Ranked` 6 = `ranked_only=1` 6 (criterio 2); Unranked 2; Custom 1; `match_type=` 10; `Nada` 0; `ranked_only=1&match_type=Unranked` 0 (200); `ranked` en minuscula 0 (el filtro es exacto; el selector manda el valor de la API tal cual).
  - Vecinos con `match_type`: `/api/operators/`, `/api/teammates/?min_rounds=0`, `/api/trends/`, `/api/matches/` -> 200 con lo filtrado.
- **Chunk inicial** (`npx vite build`): dev 190,12 kB (gzip 62,42) -> rama 190,68 kB (gzip 62,57), +0,3 %.
- **Mutaciones** (cada una revertida con `git checkout`):
  - M1 `conTipo` sin `ranked_only: false` -> caen `elegir un tipo apaga solo ranked` y `elegir Todos deja match_type vacio y qs no lo manda`.
  - M2 `opcionesDeTipo` sin descartar repetidos -> cae `opciones de tipo sacan vacios y repetidos`.
  - M3 `hayFiltros` contando `false` -> cae `hay filtros ignora vacios y false`.
  - M4 `Dashboard.jsx` con `if (vacio)` (EmptyState siempre con 0 rondas) -> cae el e2e `el selector de tipo filtra el Inicio` (element not found).
  - M5 `Dashboard.jsx` sin mirar `overview.data?.filters` -> cae el mismo e2e (cuenta de pedidos a `/api/filters/`).
  - Para el e2e suelto en la nube: `E2E_CHROMIUM=/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell npx vite build && npx playwright test -g "selector de tipo"`; sin mutar, `1 passed`.
- Sin migracion, parser, `recompute`, Electron ni `.ps1`: nada para `## Verificar en el PC`.
- El hallazgo LOW del revisor (base vacia + filtro -> nota en vez del boton de importar) sigue como aviso; no lo alcanza el selector con la base vacia (solo ofrece "Todos").

Veredicto: los 5 criterios con evidencia -> `aprobado`.

OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, 5/5 criterios, sin bloqueantes)

## Para el humano

- (revisor 2026-11-05) No bloquea: con la base vacia y un filtro puesto, el Inicio muestra "0 rondas con estos filtros" en vez del boton de importar (detalle en Revision). Se arregla con Limpiar.
