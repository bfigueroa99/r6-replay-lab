# 113. Repetir o cambiar de operador después de perder

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O10
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/Operators.jsx, docs/metricas.md
turnos: po 20261112T1204Z-chGLrtC

## PR

## Que gana quien usa la app

En Operadores, despues de perder una ronda con un operador, la app dice
cuantas veces lo repetiste en la siguiente ronda del mismo lado de la partida
y cuantas cambiaste, con el winrate de esa ronda siguiente en cada caso (y lo
mismo despues de ganar, como base). Responde si cambiar de operador tras una
ronda mala te ayuda o es tilt, cosa que la tabla por operador no puede decir.

## Criterios de aceptacion

- [ ] Un agregado devuelve, por lado y en total, para pares de rondas tuyas
      consecutivas del mismo lado en la misma partida (por `Round.number`,
      saltando las del otro lado), separados por el resultado de la primera
      (`after_loss`, `after_win`): `repeat` y `switch` con `rounds` y
      `winrate` de la segunda. Test con una partida armada: perder con Ash y
      volver a Ash cuenta `repeat`; pasar a Thermite cuenta `switch`.
- [ ] Una ronda sin `.rec` entre medio (hueco en `number`), un operador
      vacio o `Unknown(...)` cortan el par, y los pares no cruzan partidas
      ni lados. Test.
- [ ] Una primera ronda sin ganador no entra ni en `after_loss` ni en
      `after_win`; una segunda sin ganador cuenta en `rounds` y no en el
      winrate. Test.
- [ ] Los filtros de mapa, tipo, modo, fechas y sesion aplican; el de lado
      elige que bloque se muestra; el de operador filtra el operador de la
      ronda perdida o ganada (la primera del par). Test del de operador.
- [ ] Se ve en Operadores con la muestra minima de operador (12 rondas) como
      aviso, no como recorte; sin pares, un texto y no un error. El e2e de
      humo pasa por Operadores con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Repetir o cambiar de operador").

## Fuera de alcance

- El mismo corte para el spawn (S3) o el sitio de defensa (ficha 107).
- Separar por operador de destino o recomendar a cual cambiar.
- Operadores de tus compañeros.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
