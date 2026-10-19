# 58. Primera ronda de cada mitad

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 2
fuente: ALCANCE.md B8
archivos: -
turnos: po 20261019T0325Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Siege no hay ronda de pistola, pero la primera ronda de cada lado se
juega sin informacion y marca el tono de la mitad. Con esta tabla se ve si
arrancas frio: tu winrate y rating en la ronda 1 y en la primera ronda
despues del cambio de lado, contra el resto de tus rondas.

## Criterios de aceptacion

- [ ] Agregado nuevo `by_half_opener` en `replays/analytics/aggregates.py`,
  servido en `/api/trends/` como `by_half_opener`: tres filas en orden fijo
  (`match_start`, `side_switch`, `rest`) con las metricas de `totals()`
  (rondas, ganadas, winrate, rating, KPR, aperturas). `match_start` = la
  ronda sin prorroga de numero mas bajo de la partida (la misma que lee
  `_lado_inicial`); `side_switch` = la ronda sin prorroga de numero mas bajo
  cuyo `my_side` difiere del lado inicial; `rest` = todas tus demas rondas
  sin prorroga con lado. Las rondas de prorroga no entran en ninguna fila.
  Test de Django con una partida armada (6 rondas, cambio en la 4): la 1 cae
  en `match_start`, la 4 en `side_switch` y las otras 4 en `rest`.
- [ ] La ronda de apertura se lee de la partida entera, como en `by_half`:
  con `?side=defense` la fila `match_start` solo cuenta las partidas que
  arrancaste en defensa, pero cual es la primera ronda no cambia. Test con
  `?side=`.
- [ ] Una partida sin lado inicial (todas sus rondas con `my_side` vacio) no
  aporta a ninguna fila, ni da 500. Test con base vacia y con esa partida.
- [ ] En Tendencias, dentro del panel "Por mitad de la partida", una tabla
  "Primera ronda de cada lado" con las tres filas ("Ronda 1", "Primera tras
  el cambio", "Resto"), las mismas columnas que la tabla de mitades, boton
  CSV y el aviso de muestra chica que ya usa el panel. Entra al e2e con los
  datos de `seed_demo` (las tres filas visibles y consola limpia).
- [ ] Fila nueva en `docs/metricas.md` ("Primera ronda de cada lado") con la
  definicion exacta y la misma advertencia de `.rec` faltantes que tiene
  "Primera / segunda mitad".

## Fuera de alcance

- La primera ronda de la prorroga: es otra ronda de decision y ya la cubre
  la fila "Prorroga" de la tabla de mitades.
- Mirar el marcador (`score_before`) para corregir partidas con `.rec`
  faltantes: es la mejora anotada en la ficha 36 y vale para las dos tablas
  a la vez; ficha aparte.
- Una señal del Coach sobre la ronda 1.

## Diseno

## Implementacion
