# 60. Racha de rondas dentro de la partida

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B13
archivos: -
turnos: po 20261019T0325Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Un 0-4 seguido dice mas que el 3-4 final: en el detalle de cada partida se
ve la racha mas larga de rondas ganadas y la de perdidas seguidas, y en
Records queda tu mejor racha de rondas de todo el historial con enlace a la
partida.

## Criterios de aceptacion

- [ ] Funcion pura en `replays/analytics/aggregates.py` que recibe las
  rondas de una partida (`number`, `my_team_won`) y devuelve la racha mas
  larga de ganadas y la de perdidas, cada una con la ronda en que empieza.
  Cortan la racha: una ronda con `my_team_won` nulo y un hueco en la
  numeracion (falta un `.rec`). Tests: `G G P G G G` da 3 ganadas desde la
  4 y 1 perdida; `G G (hueco) G` da 2; `G nulo G` da 1.
- [ ] `/api/matches/<id>/` agrega `round_streaks` con `wins` y `losses`
  (`{length, from_round_label}` o `null` si no hay ninguna). Test de Django
  sobre una partida de `seed_demo` o armada.
- [ ] `personal_records` agrega `longest_round_streak`: la racha de rondas
  ganadas mas larga entre tus partidas filtradas, con `match_id`, mapa,
  fecha, `value` y `round_label` de la primera ronda; a igual largo gana la
  partida mas reciente, como los demas records. Test con dos partidas.
- [ ] La UI muestra las dos rachas en el encabezado del detalle de partida
  ("Racha: 4 ganadas desde R3 · 3 perdidas desde R8") y el record nuevo en
  Records ("Racha de rondas", `records.js`) con el enlace de siempre. Entra
  al e2e con `seed_demo` (detalle de una partida y Resumen).
- [ ] Fila nueva en `docs/metricas.md` ("Racha de rondas") con lo que corta
  una racha.

## Fuera de alcance

- La racha de partidas (ganadas o perdidas seguidas): la tiene PR #14.
- Rachas de compañeros o rivales y rachas de prorroga aparte.
- Calcularla al importar: se arma al consultar, sin migracion.

## Diseno

## Implementacion
