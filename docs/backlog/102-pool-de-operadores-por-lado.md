# 102. Tu pool de operadores por lado

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O7
archivos: backend/replays/views.py (_catalogo_operadores, operators), backend/replays/analytics/aggregates.py, frontend/src/pages/Operators.jsx, docs/metricas.md
turnos: po 20261106T0530Z-ciXX3AM

## PR

## Que gana quien usa la app

En Operadores, un panel "Tu pool" dice cuantos operadores distintos jugaste
por lado en tus ultimas 20 partidas y en todo el historial, y cuales del
catalogo nunca jugaste o no jugas hace 30 dias. Responde si dependes de dos
operadores por lado y que practicar para cuando te los banean o te los
quitan, cosa que la tabla por operador (ordenada por rondas) no dice.

## Criterios de aceptacion

- [ ] La API de Operadores (o una clave nueva en `/api/operators/`) devuelve
      por lado (`Attack`, `Defense`): `distinct_recent` (operadores
      distintos en tus ultimas 20 partidas), `distinct_all`, `never` (lista
      del catalogo `_catalogo_operadores` de ese lado sin ninguna ronda tuya)
      y `stale` (jugados alguna vez pero no en los ultimos 30 dias, con la
      fecha de la ultima vez). Test con historial armado: un operador jugado
      hace 40 dias cae en `stale`, uno nunca jugado en `never`.
- [ ] Los filtros de mapa y tipo de partida aplican; el de lado decide que
      bloque se muestra; el de operador se ignora para este panel (no tiene
      sentido "tu pool de Ash") y el test lo afirma.
- [ ] Las filas `Unknown(...)` y los operadores con `operator=""` no entran
      ni al conteo ni a `never`.
- [ ] El panel se ve en Operadores con los dos lados; sin partidas, un texto
      vacio y no un error. El e2e de humo pasa por Operadores con la consola
      limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Pool de operadores") con las
      ventanas de 20 partidas y 30 dias.

## Fuera de alcance

- Curva de aprendizaje por operador (E1) y presencia sobre lo jugado (O5).
- Recomendar que operador practicar: solo se lista.
- Hacer configurables las ventanas de 20 partidas y 30 dias (constantes en
  `aggregates.py`, como las demas muestras minimas).

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
