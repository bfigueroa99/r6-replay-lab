# 63. Cuando llega la apertura

estado: propuesto
candado: arquitecto 2026-10-24T16:05Z
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B14
archivos: -
turnos: po 20261024T1204Z

## Que gana quien usa la app

El segundo de la fase de accion en que cae la primera baja de la ronda (sea
de quien sea) y tu winrate segun si llego temprano, al medio o tarde: si en
defensa te abren de entrada o si en ataque tardas en forzar el primer duelo.
Las aperturas de hoy dicen quien gana el primer duelo, no cuando llega.

## Criterios de aceptacion

- [ ] `/api/trends/` trae una clave nueva `opening_timing`: por lado
  (`attack`, `defense`), tres tramos fijos (temprano: menos de 30 s; medio:
  30 a 90 s; tarde: 90 s o mas; constantes en `aggregates.py`) mas una fila
  "Sin bajas", cada uno con `rounds`, `won`, `winrate` y
  `opening_won` (rondas en que la primera baja fue de tu equipo). La
  primera baja es el primer evento `Kill` o `Death` de la ronda por
  `order`, el mismo que define `opening_kill`/`opening_death` en
  `metrics.py`; su segundo es `Event.elapsed`. Test con rondas en 10 s,
  60 s y 120 s.
- [ ] Bordes: 29.9 s es temprano y 30 s es medio; 90 s es tarde (test).
- [ ] Rondas con `my_team_won` nulo no entran en `won` ni en `rounds`;
  rondas sin ningun evento de baja van a "Sin bajas" (test).
- [ ] Respeta los filtros de la barra; con `side=Attack` la parte de
  `defense` queda en cero; base vacia: 200 con los tramos en cero.
- [ ] Tendencias: tabla "Cuándo llega la apertura" (Lado, Tramo, Rondas,
  Winrate, Primera baja tuya %) con boton CSV `apertura-por-tiempo`; e2e
  sobre `seed_demo` que la encuentra.
- [ ] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Por mapa: la ficha queda por lado; el corte por mapa es un tramo siguiente
  si la muestra da (anotarlo en ALCANCE si el Arquitecto lo ve).
- Cualquier cosa anclada al plant (`docs/formato-rec.md`).
