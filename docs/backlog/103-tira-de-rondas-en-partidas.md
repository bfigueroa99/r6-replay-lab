# 103. Tira de rondas en el listado de partidas

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: ALCANCE.md F4 (el PR #14, que tocaba Matches.jsx, se cerro sin merge el 2026-11-05)
archivos: backend/replays/views.py (match_list), frontend/src/pages/Matches.jsx, frontend/e2e/
turnos: po 20261106T0530Z-ciXX3AM

## PR

## Que gana quien usa la app

En Partidas, cada fila muestra la secuencia de rondas ganadas y perdidas, con
el lado de cada una, y no solo el marcador final: las remontadas, los
derrumbes y la mitad que se cayo se ven sin abrir la partida.

## Criterios de aceptacion

- [ ] Cada fila de `/api/matches/` trae `strip`: la lista de rondas en orden
      (`number`) con `won` (`my_team_won`, puede ser `null`), `side`
      (`my_side`) y `overtime` (`overtime_number > 0`). Se arma con una sola
      consulta para toda la pagina, no una por partida (test con
      `assertNumQueries` o contando que no crece con el largo de la pagina).
- [ ] La tira es de la partida entera: el filtro de lado o de sitio elige que
      partidas salen, pero no recorta sus rondas (test: con `side=attack` la
      tira sigue trayendo las rondas de defensa).
- [ ] En `Matches.jsx` cada fila dibuja la tira: un cuadradito por ronda,
      ganada y perdida con colores distintos, ronda sin ganador claro
      (`won=null`, ficha 38) en gris, el lado marcado (borde o letra) y la
      prorroga separada; `title` con "R5 · ataque · ganada". Una partida sin
      rondas (ficha 82) muestra la fila sin tira y sin error.
- [ ] Los filtros de Partidas (ficha 78, resultado) y la paginacion siguen
      igual; el e2e de Partidas ve la tira en una partida de `seed_demo` y la
      consola limpia.

## Fuera de alcance

- Hacer clic en un cuadradito para ir a esa ronda (eso es F6, aparte).
- Mostrar la tira en el Inicio (R1) o en Sesiones.
- Bajas por ronda en la tira.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
