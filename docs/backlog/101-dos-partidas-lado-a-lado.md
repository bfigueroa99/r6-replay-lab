# 101. Dos partidas lado a lado

estado: entregado
candado: -
rama: claude/equipo-dev/101-dos-partidas-lado-a-lado
tipo: funcionalidad
epica: paridad-referencia
area: frontend
prioridad: 2
fuente: ALCANCE.md R6 (replica/features.csv: la referencia compara partidas)
archivos: docs/metricas.md, frontend/src/compararPartidas.js, frontend/src/compararPartidas.test.js, frontend/src/pages/Comparar.jsx, frontend/src/App.jsx, frontend/src/pages/MatchDetail.jsx, frontend/src/styles.css, frontend/e2e/comparar-partidas.spec.js
turnos: po 20261106T0530Z-ciXX3AM, arquitecto 20261106T0554Z-cFqJHEh, dev 20261106T0621Z-c14zTHs, revisor 20261109T0330Z-c8x1kCc, qa 20261109T0805Z-cTPuCNz, release 20261109T0805Z-cTPuCNz

## PR

Titulo: `[equipo-dev][frontend] Dos partidas lado a lado`

### Que cambia

Desde el detalle de una partida, "Comparar con…" lleva a `/comparar/<a>`,
donde se elige la otra (primero las del mismo mapa) y se ve
`/comparar/<a>/<b>`: mapa, fecha, tipo, marcador, rondas por lado y tus
totales (bajas, muertes, aperturas, muertes sin trade, KST, rating) de las dos,
con una columna Diferencia en verde si A sale mejor y en rojo si sale mejor B.
La URL se puede recargar y compartir con el boton atras.

### Por que esto y no otra cosa

Ficha 101 (ALCANCE R6: la referencia compara partidas). Pagina nueva y no modo
del detalle: `MatchDetail.jsx` queda con un enlace y la URL sale de la ruta.
Sin backend: `/api/matches/<id>/` dos veces ya trae todo.

### Como se probo

- `verificar.sh`: VERDE c2c165698, 1092 tests backend, 288 vitest, 83 e2e
  (se repite sobre el commit de entrega antes del merge).
- 12 vitest en `compararPartidas.test.js`: signo y sentido de "mejor" (bajas,
  muertes, aperturas perdidas, muertes sin trade), diferencia cero, KST en
  puntos y rating con 2 decimales, lados por winrate y no por conteo, ronda
  sin ganador, partida sin tu fila, sin rondas, rating nulo, orden de filas,
  opciones sin la actual y mismo mapa por etiqueta con version.
- e2e `comparar-partidas.spec.js`: del detalle al select, dos marcadores,
  "Diferencia", recarga, `/comparar/<a>/999999`, consola limpia.
- QA en Chromium sobre base sembrada y vacia: casos borde, mutacion (4 de 4
  mutantes mueren), chunk inicial +0.09 %. Detalle en `## QA`.
- OMC: plan=— · revisión=— · verificación=— (Diseno)
- OMC: plan=— · revisión=5 hallazgos (4 arreglados) · verificación=— (Implementacion)
- OMC: plan=— · revisión=2 hallazgos (1 arreglado) · verificación=— (Revision)
- OMC: plan=— · revisión=— · verificación=PASS (QA)

### Riesgos y lo que no entra

Sin migraciones ni `recompute`. Fuera: comparar mas de dos, partida contra
promedio, jugadores, ronda por ronda. LOW abierto: si `/api/matches/`
falla, el select queda en "Cargando partidas…" (el error se ve abajo).

### Como probarlo en 2 minutos

```
cd frontend; npm run build; cd ../backend; python manage.py runserver
```
Abrir una partida, "Comparar con…", elegir otra del grupo "Mismo mapa": se ven
las dos columnas y la Diferencia coloreada; recargar y volver con atras.
`/comparar/<id>/999999` dice "Esa partida no existe".

Verificar en el PC: comparar una victoria y una derrota del mismo mapa con la
base real, y una partida de un `.rec` cortado como B.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Elegir dos partidas tuyas y ver sus numeros lado a lado con la diferencia
resaltada, sin comparar de memoria entre dos pestañas.

## Criterios de aceptacion

- [x] "Comparar con…" desde el detalle; URL `/comparar/<a>/<b>` recargable.
- [x] Mapa, fecha, tipo, marcador, rondas por lado y `my_totals` con columna
      Diferencia con signo y color de quien sale mejor.
- [x] Funcion pura con vitest; sin `my_totals` y sin rondas dan `—`.
- [x] Id inexistente en B: "Esa partida no existe".
- [x] Entra al e2e con consola limpia.

## Diseno, Implementacion y Revision

Diseno (arquitecto 20261106T0554Z-cFqJHEh): pagina `Comparar.jsx`, funcion
pura `compararPartidas.js`, sin backend. Implementacion (dev
20261106T0621Z-c14zTHs): key del componente en A y B en un hijo con `key={b}`
(cambiar B no vuelve a pedir A ni el listado; si B no existe el aviso sale
debajo del selector); diferencias de lados y KST en `pts`. Revision
(revisor 20261109T0330Z-c8x1kCc): aprobar; test de `MAS_ES_MEJOR` para
aperturas perdidas y muertes sin trade agregado (af6eeab); LOW del select con
el listado caido, sin arreglar. Detalle completo en `git log` de la rama.

## QA 2026-11-09 sobre c2c1656

(qa 20261109T0805Z-cTPuCNz) **aprobado**. `verificar.sh` VERDE c2c165698. Base
sembrada (`seed_demo` + `factories.make_match(map_name="Bank", index=900,
my_score=0, opponent_score=0)`, sin rondas ni fila) y vacia, `runserver` en
el scratchpad. curl a `/api/matches/<1|30|abc|999999|-1>/` y `?limit=200|-1|foo`:
200/404 como corresponde. Chromium: `/comparar/1/2` cotejado con la API;
`/comparar/1/30` y `/30/30` todo `—`; ids inexistentes y base vacia dan
"Esa partida no existe"; select, atras y recarga mantienen B; 375 px sin
scroll horizontal. Chunk inicial 195.34 -> 195.52 kB. Mutacion: 4 de 4 mueren.
OMC: plan=— · revisión=— · verificación=PASS (omc-verifier, 0 bloqueantes)

## Para el humano

Verificar en el PC: lo de `## PR`.
