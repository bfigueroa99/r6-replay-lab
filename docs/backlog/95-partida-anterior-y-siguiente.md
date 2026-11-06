# 95. Partida anterior y siguiente, y flechas para cambiar de ronda

estado: propuesto
candado: arquitecto 2026-11-06T01:09Z
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: fullstack
prioridad: 3
fuente: F17 de ALCANCE.md; idea del PR #14 (cerrado sin merge el 2026-11-05, rama `claude/dazzling-einstein-w3qcyq` como referencia, decision del humano en `## Para el equipo` del 2026-11-05)
archivos: -
turnos: po 20261106T0041Z-cSxDY1g

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Revisar una sesion de partidas hoy obliga a volver al listado entre una y
otra, y cambiar de ronda dentro del detalle es solo con el mouse. Con esto,
desde el detalle de una partida se pasa a la anterior o a la siguiente con
un enlace, y las rondas se recorren con las flechas del teclado.

## Criterios de aceptacion

- [ ] `GET /api/matches/<id>/` suma `prev_id` y `next_id`: la partida
      inmediatamente anterior y posterior por `Match.date` (desempate por
      `id`, el mismo orden que el listado de `/api/matches/`), o `null`
      en los extremos. Test de Django con tres partidas: la del medio trae
      las dos, la primera trae `prev_id: null`, la ultima `next_id: null`,
      y dos partidas con la misma fecha no se saltan ni se repiten.
- [ ] `MatchDetail.jsx` muestra enlaces "← Partida anterior" y "Partida
      siguiente →" (deshabilitados o ausentes en los extremos) que llevan a
      `/partidas/<id>`; al navegar, la ronda elegida vuelve a la primera y
      la pagina no queda con datos de la partida previa.
- [ ] En el detalle, las flechas izquierda y derecha del teclado cambian la
      ronda seleccionada (sin pasarse de la primera ni de la ultima) y no
      actuan mientras el foco esta en un campo de texto o un select. La
      logica de "ronda siguiente/anterior con tope" vive en una funcion pura
      con test de vitest.
- [ ] El e2e de `frontend/e2e/` abre una partida de `seed_demo`, sigue
      "Partida siguiente" y comprueba que cambia el titulo, y aprieta la
      flecha derecha y comprueba que cambia la ronda marcada, sin errores en
      la consola.

## Fuera de alcance

- Navegar respetando los filtros globales (tipo de partida, mapa, fechas):
  el orden es el del historial completo. Si se quiere, va despues de A10
  (ficha 96), cuando los filtros vivan en la URL.
- Atajos para cambiar de partida con el teclado (solo enlaces).
- Cualquier cambio a la timeline o a los paneles del detalle.

## Diseno

(Arquitecto)

## Implementacion

## Para el humano

(Nada por ahora.)
