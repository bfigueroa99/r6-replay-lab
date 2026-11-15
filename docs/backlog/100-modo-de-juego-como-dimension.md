# 100. Modo de juego como dimension

estado: entregado
candado: -
rama: claude/equipo-dev/100-modo-de-juego-como-dimension
tipo: funcionalidad
epica: temporada-y-modo
area: fullstack
prioridad: 3
fuente: A7 de ALCANCE.md; sigue a la ficha 77 (selector de tipo de partida) y a la 96 (filtros en la URL)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/modoDeJuego.js, frontend/src/modoDeJuego.test.js, frontend/src/components/Filters.jsx, frontend/src/filtrosUrl.js, frontend/src/filtrosUrl.test.js, frontend/src/pages/Trends.jsx, backend/tests/test_modo_de_juego.py, frontend/e2e/modo-de-juego.spec.js, docs/metricas.md, frontend/src/partidas.js, frontend/src/partidas.test.js
turnos: po 20261106T0319Z-cqz8j6p, arquitecto 20261106T0438Z-c2U4Qx9, dev 20261106T0503Z-cNnHCRB, revisor 20261106T0530Z-cjYLw9e, qa 20261106T0554Z-c7uH5QP, release 20261106T0554Z-c7uH5QP

## PR

Titulo: `[equipo-dev][frontend] Modo de juego como filtro y tabla Por modo en Tendencias`

### Que cambia

La barra de filtros tiene un selector "Modo" (Bomba, Rehén, Área segura, Bomba rápida), que aparece cuando la base tiene más de un modo o cuando llega un enlace con `?gamemode=`. Filtra todas las páginas, Partidas incluida, y viaja en la URL. Tendencias suma una tabla "Por modo" con partidas, % de partidas ganadas, % de rondas ganadas, K/D y rating por modo. Así las rondas de Rehén ya no se mezclan con las de Bomba.

### Por que esto y no otra cosa

Ficha 100 (A7 de `ALCANCE.md`). Copia el camino del selector "Tipo" (ficha 77) y la fila por grupo de `by_stack`. `Match.gamemode` ya existía, así que no hay migración, `recompute` ni cambios en el parser. Se descartó sumar una partida de otro modo a `seed_demo`: habría movido los números que afirma el e2e. El e2e intercepta la API.

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE c77651c, 1092 tests backend, 276 vitest, 82 e2e. Se repite sobre el commit de entrega.
- `backend/tests/test_modo_de_juego.py`, 9 tests:
  - filtro por Hostage;
  - un modo inexistente da 200 y 0;
  - el listado de partidas respeta el modo;
  - las opciones salen sin vacíos;
  - `by_gamemode` con los números a mano;
  - `won=None` queda fuera del %;
  - el filtro de lado mantiene el resultado de la partida (dos tests);
  - la fila "Sin modo".
- Vitest:
  - `modoDeJuego.test.js`: opciones, cuándo se muestra el selector, nombres.
  - `filtrosUrl.test.js`: `gamemode` hace ida y vuelta por la URL; uno de 65 caracteres se descarta.
  - `partidas.test.js`: Partidas manda el modo.
- e2e `modo-de-juego.spec.js`, con la consola limpia:
  - el selector no aparece con un solo modo y aparece con la API interceptada;
  - el enlace `?gamemode=`;
  - Partidas;
  - "Por modo" en Tendencias, con y sin la tabla.
- QA con `runserver` sobre una base vacía y otra sembrada (5 modos, `Unknown(7)`, modo vacío, `won=None`, una partida sin rondas):
  - todos los bordes y los endpoints vecinos dan 200;
  - Chromium sin errores en la consola;
  - las 8 mutaciones caen;
  - el chunk inicial crece 0.4 %.
- OMC: plan=— · revisión=— · verificación=— (diseño)
- OMC: plan=— · revisión=4 hallazgos (3 arreglados) · verificación=— (implementación)
- OMC: plan=— · revisión=4 hallazgos (1 arreglado) · verificación=— (revisión)
- OMC: plan=— · revisión=— · verificación=PASS (QA)

### Riesgos y lo que no entra

Sin migración, `recompute`, parser ni Electron. Sin `?gamemode`, los querysets son los de antes y ningún número existente cambia. No entran reglas propias por modo, la temporada como dimensión (A3) ni cambios al selector "Tipo". Quedan dos LOW abiertos, sin ficha:
- `hayVariosModos` cuenta filas: con Bomb más partidas sin modo aparece la tabla pero no el selector.
- El texto "cabeceras viejas" para "Sin modo" no es exacto.

### Como probarlo en 2 minutos

```
cd backend; python manage.py seed_demo; python manage.py runserver
curl -s localhost:8000/api/filters/            # "gamemodes": ["Bomb"]
curl -s "localhost:8000/api/overview/?gamemode=Hostage"   # overall.rounds 0, 200
```
En la UI, con el seed (todo Bomb), no aparece "Modo" ni "Por modo". Con `http://localhost:8000/?gamemode=Hostage`, el selector aparece con "Rehén" elegido y 0 rondas. "Limpiar" lo saca.

### Para el humano

Nada.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

En partidas rápidas y no clasificatorias se juega Bomba, Rehén y Área segura, y hasta ahora todo salía mezclado. Con el selector "Modo" y la tabla "Por modo" se ve qué modo te va bien y cuál no.

## Criterios de aceptacion

- [x] `gamemode` en `_filters`, `base_queryset` y `match_queryset`; un modo inexistente da 200 y listas vacías.
- [x] `/api/filters/` devuelve `gamemodes`; selector "Modo" en castellano, oculto con un solo modo.
- [x] `gamemode` en `CLAVES_DE_URL`.
- [x] `/api/trends/` con `by_gamemode`; tabla "Por modo" solo con más de un modo.
- [x] e2e con el selector de modo y la consola limpia.

## Resumen de etapas

- Diseño: copia la ficha 77 y `by_stack`, sin cambio de `seed_demo`.
- Implementación: desvíos de `partidas.js` (`gamemode` en `CLAVES_DE_PARTIDA`) y de `opcionesDeModo(gamemodes, elegido)`. VERDE 8827e49.
- Revisión: aprobar, 4 LOW. Uno lo arregló el Revisor: un test que distingue el resultado de la partida del de sus rondas filtradas. VERDE e6fb3b3.
- QA (c77651c): aprobado. Los comandos completos están en `git log` de la rama (commit "Prueba: 100").
