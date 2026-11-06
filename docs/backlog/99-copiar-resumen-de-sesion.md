# 99. Copiar el resumen de una sesion

estado: propuesto
candado: arquitecto 2026-11-06 03:46 UTC
rama: -
tipo: funcionalidad
epica: exportar
area: fullstack
prioridad: 3
fuente: H7 de ALCANCE.md; reusa la idea de la ficha 66 (copiar resumen de partida, `frontend/src/resumenPartida.js`)
archivos: backend/replays/analytics/aggregates.py (sessions), frontend/src/resumenSesion.js, frontend/src/resumenSesion.test.js, frontend/src/pages/Trends.jsx, backend/tests/, frontend/e2e/, docs/metricas.md
turnos: po 20261106T0319Z-cqz8j6p

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Al terminar la noche, un boton en la tabla de Sesiones de Tendencias copia
al portapapeles el resumen de esa sesion en texto plano (partidas ganadas y
perdidas, winrate de rondas, K/D y rating, mejor y peor partida) para
pegarlo en el chat del grupo. Hoy hay que mirarlo y tipearlo, o copiar
partida por partida con el boton de la ficha 66.

## Criterios de aceptacion

- [ ] Cada fila de `GET /api/sessions/` agrega `wins`, `losses` y
      `decided` (partidas con `Match.won` conocido; `won=None` no cuenta
      como perdida, ficha 68) y `best_match` / `worst_match` (id, mapa con
      la etiqueta de version, marcador y rating de la partida, por rating de
      tus rondas en esa partida; `null` con una sola partida). Test de
      `aggregates.sessions` con una sesion de 3 partidas (G, P, sin
      resultado) que da 1-1 y las dos partidas extremas correctas.
- [ ] `frontend/src/resumenSesion.js`, funcion pura sin React, arma el texto
      desde una fila de `/api/sessions/`: fecha y duracion, "3 partidas: 1G
      1P 1 sin resultado", winrate de rondas, K/D, rating, mejor y peor
      partida; los nulos salen como `—` (mismo criterio que
      `resumenPartida.js`). Vitest con una sesion completa, una de una
      partida y una con metricas nulas.
- [ ] En la tabla Sesiones de Tendencias, cada fila tiene un boton "Copiar"
      que usa `navigator.clipboard.writeText` con el mismo manejo de error
      que el detalle de partida (sin portapapeles: mensaje, no excepcion).
      Ninguna request nueva: sale del payload que la pagina ya tiene.
- [ ] El e2e abre Tendencias con `seed_demo`, aprieta "Copiar" en la
      primera sesion y lee el portapapeles (permiso de Chromium) con el
      texto esperado; consola limpia.
- [ ] Las columnas nuevas (ganadas y perdidas de la sesion) entran a
      `docs/metricas.md` si la tabla las muestra.

## Fuera de alcance

- Copiar varias sesiones juntas, imagen o archivo: solo texto plano.
- Cambiar como se corta una sesion (`SESSION_GAP_MINUTES`).
- Mandar el texto a ningun lado: lo pega el usuario.
