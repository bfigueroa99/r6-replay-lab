# 44. Records personales en el Resumen

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E4 (idea del PO 20261013T1915Z); epica progreso en curso (E3 en main por la ficha 40)
archivos: -
turnos: po 20261014T0911Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver de un vistazo tus mejores marcas (mejor partida, mas bajas en una
partida y en una ronda, el clutch mas grande, el mejor dia), cada una con un
enlace para volver a mirarla. Marca el techo a superar y saca provecho del
historial acumulado, que es lo que ningun tracker de API tiene ronda por
ronda.

## Criterios de aceptacion

- [ ] Un agregado nuevo en `analytics/aggregates.py` (expuesto en
  `/api/overview/` o en un endpoint GET propio, a eleccion del Arquitecto)
  devuelve, cada uno con `match_id`, fecha, mapa y el valor: mejor rating de
  partida (solo partidas con al menos 6 rondas tuyas), mas bajas en una
  partida, mas bajas en una ronda (con el numero de ronda), 1vX ganado mas
  grande (`one_vx`) y mejor dia por rondas ganadas (con minimo de rondas, el
  dia sin `match_id`). Test con factories que afirma cada record y su
  `match_id`.
- [ ] Empates: gana la partida mas reciente, para que el record cambie cuando
  lo igualas. Test con dos partidas de igual cantidad de bajas.
- [ ] Respeta los filtros de siempre (`map`, `operator`, `side`, `since`,
  `match_type`): test con `map=` que cambia el record de bajas.
- [ ] Base vacia o sin clutches: el record que no existe es `null` (no 500, no
  0 inventado). Test sobre base vacia.
- [ ] El Resumen (`Dashboard.jsx`) muestra el panel "Tus récords" con un
  enlace `/partidas/<id>` en cada uno; el e2e (`humo.spec.js`) lo ve con
  `seed_demo`, sigue un enlace y no ensucia la consola.
- [ ] Fila nueva en `docs/metricas.md` para cada record (que cuenta, minimos y
  desempate).

## Fuera de alcance

- La racha actual: es de PR #14, no se duplica.
- Historial de records (cuando se batio cada uno) o avisos de record nuevo.
- Records de otros jugadores o de compañeros.

## Diseno

## Implementacion

## Para el humano
