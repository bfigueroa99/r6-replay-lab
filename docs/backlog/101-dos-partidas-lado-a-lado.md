# 101. Dos partidas lado a lado

estado: propuesto
candado: arquitecto 2026-11-06 05:55Z
rama: -
tipo: funcionalidad
epica: paridad-referencia
area: frontend
prioridad: 2
fuente: ALCANCE.md R6 (replica/features.csv: la referencia compara partidas)
archivos: frontend/src/pages/MatchDetail.jsx o pagina nueva, frontend/src/lib/ (funcion pura), frontend/e2e/
turnos: po 20261106T0530Z-ciXX3AM

## PR

## Que gana quien usa la app

Elegir dos partidas tuyas (la que ganaste y la que perdiste en el mismo mapa,
o la de hoy contra la de la semana pasada) y ver sus numeros uno al lado del
otro con la diferencia resaltada, sin abrir dos pestañas y comparar de
memoria. Es lo que la referencia hace y la app todavia no.

## Criterios de aceptacion

- [ ] Desde el detalle de una partida hay un control "Comparar con..." que
      lista tus otras partidas (mapa, fecha, marcador) y lleva a una vista
      con las dos; la URL lleva las dos (`/partidas/<a>?vs=<b>` o
      `/comparar/<a>/<b>`), asi se puede recargar y volver.
- [ ] La vista muestra, por partida: mapa (con version), fecha, tipo,
      marcador, rondas ganadas por lado (ataque y defensa), y de tus totales
      (`my_totals`): bajas, muertes, aperturas ganadas y perdidas, muertes
      sin trade, KST y rating. Una columna "Diferencia" con el signo y el
      color de quien sale mejor.
- [ ] El armado de las filas es una funcion pura (sin React) con tests de
      vitest: diferencia con signo, partida sin tu fila (sin `my_totals`) y
      partida sin rondas (ficha 82) devuelven filas con `—` y no rompen.
- [ ] Un id inexistente en la segunda partida muestra el mismo aviso de
      "partida no encontrada" que el detalle (ficha 84), no una pantalla en
      blanco.
- [ ] Entra al e2e (`frontend/e2e/`): abrir dos partidas de `seed_demo`
      comparadas, ver los dos marcadores y la columna de diferencia, consola
      limpia.

## Fuera de alcance

- Backend nuevo: `/api/matches/<id>/` dos veces ya trae todo.
- Comparar mas de dos partidas, o una partida contra tu promedio (eso es
  Tendencias y E16).
- Comparar jugadores (descartada en ALCANCE.md).
- Comparar ronda por ronda o las timelines.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada: la forma de la URL es reversible; el Arquitecto elige entre modo del
detalle y pagina nueva)
