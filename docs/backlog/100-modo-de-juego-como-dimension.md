# 100. Modo de juego como dimension

estado: propuesto
candado: arquitecto 2026-11-06T04:38Z
rama: -
tipo: funcionalidad
epica: temporada-y-modo
area: fullstack
prioridad: 3
fuente: A7 de ALCANCE.md; sigue a la ficha 77 (selector de tipo de partida) y a la 96 (filtros en la URL)
archivos: backend/replays/views.py (_filters, filters/, trends), backend/replays/analytics/aggregates.py (base_queryset, match_queryset), frontend/src/components/Filters.jsx, frontend/src/filtrosUrl.js, frontend/src/pages/Trends.jsx, backend/tests/, frontend/src/*.test.js, frontend/e2e/, docs/metricas.md
turnos: po 20261106T0319Z-cqz8j6p

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En partidas rapidas y no clasificatorias se juega Bomba, Rehen y Area
segura, y hoy todo se mezcla: los sitios, el winrate de ataque y la duracion
de las rondas de Bomba suman rondas de Rehen. Con un selector "Modo" en la
barra y una tabla "Por modo" en Tendencias se separa el modo que te va bien
del que no.

## Criterios de aceptacion

- [ ] `_filters` acepta `gamemode` (texto, como `match_type`) y
      `base_queryset` y `match_queryset` filtran por `Match.gamemode`; un
      modo que no existe da listas vacias y 200, no 500. Test con una partida
      `Bomb` y una `Hostage`: `/api/overview/?gamemode=Hostage` cuenta solo
      las rondas de la segunda.
- [ ] `GET /api/filters/` devuelve `gamemodes` (los valores presentes,
      ordenados, sin vacios) y la barra muestra el selector "Modo" con
      "Todos" y nombres en castellano para los conocidos (Bomba, Rehén, Área
      segura, Bomba rápida; un `Unknown(...)` sale tal cual). Con un solo
      modo en la base el selector no aparece. Vitest de la funcion que arma
      las opciones.
- [ ] `gamemode` entra a `CLAVES_DE_URL` de `filtrosUrl.js` (ficha 96), con
      la misma validacion de texto que `match_type`. Vitest: la query
      `?gamemode=Hostage` sobrevive ida y vuelta.
- [ ] `GET /api/trends/` agrega `by_gamemode`: por modo, partidas,
      winrate de partida (`won=None` fuera del %), winrate de ronda, K/D y
      rating con `derive`; Tendencias lo muestra en una tabla "Por modo"
      solo si hay mas de un modo. Test con los numeros a mano.
- [ ] El e2e cambia el selector de modo con `seed_demo` (si el seed tiene
      un solo modo, el Arquitecto decide si suma una partida de otro modo y
      ajusta los numeros que afirman las pruebas) y la consola queda limpia.

## Fuera de alcance

- Reglas propias por modo (sitios de Rehen, condicion de victoria de Area
  segura): el corte es solo de filtro y tabla.
- Temporada como dimension (A3): idea aparte.
- Cambiar el selector "Tipo" (ficha 77).
- Coordinar con la ficha 79 (PR #81, espera al humano), que tambien toca
  `base_queryset` y `match_queryset`: orden de merge, no decision.
