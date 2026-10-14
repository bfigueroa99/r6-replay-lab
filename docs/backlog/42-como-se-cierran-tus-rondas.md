# 42. Como se cierran tus rondas: por eliminacion o sin ella, por lado

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B6 (idea del PO 20261013T0511Z); epica lado-y-marcador en curso (B1, B4 y B2 tramo 1 en main por #25, 39 y 41)
archivos: -
turnos: po 20261014T0911Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver, por lado, cuantas de tus rondas ganadas y perdidas se cierran eliminando
al otro equipo y cuantas sin eliminacion (objetivo o tiempo): si en defensa
pierdes porque te quedas sin gente o porque no llegas a tiempo. Hoy la
condicion solo se ve ronda por ronda en el detalle de una partida.

## Criterios de aceptacion

- [ ] `GET /api/trends/` devuelve una lista nueva (nombre a eleccion del
  Arquitecto, p. ej. `round_endings`) con una fila por lado (`Attack`,
  `Defense`) y por cada fila: `won_elimination`, `won_other`,
  `lost_elimination`, `lost_other`, `unknown` y el total de rondas. Test con
  factories: una ronda ganada con `win_condition="KilledOpponents"` en ataque
  suma 1 a `won_elimination` de `Attack` y a nada mas.
- [ ] Cada fila suma todas tus rondas de ese lado: `won_* + lost_* + unknown
  == rounds`. Ronda con `win_condition=""` o `my_team_won` nulo va a
  `unknown`. Test con una ronda de cada caso.
- [ ] "Sin eliminacion" se lee de `win_condition="ObjectiveOrTime"`, que hoy
  siempre llega con `win_condition_certain=False`: la UI lo rotula como
  inferido ("objetivo o tiempo") y nunca lo parte en plant, defuse o tiempo
  (`docs/formato-rec.md`). Test que afirma que la respuesta no trae claves de
  plant ni de defuse.
- [ ] Respeta los filtros de siempre (`map`, `operator`, `side`, `since`,
  `match_type`, `session`): test con dos mapas y `map=` que deja uno.
- [ ] Tendencias muestra el panel "Cómo se cierran tus rondas" con porcentajes
  por lado y la banda de muestra chica que ya usan los paneles vecinos; base
  vacia: estado vacio, sin error en consola. El e2e (`humo.spec.js`) lo ve con
  `seed_demo`.
- [ ] Fila nueva en `docs/metricas.md` con la definicion de cada columna.

## Fuera de alcance

- Separar plant, defuse y tiempo: el `.rec` de temporadas nuevas no lo trae.
- Cruce por mapa o sitio: el filtro `map=` ya lo da; una tabla mapa x lado
  seria otra ficha.
- Cambiar como `metrics.py` calcula `win_condition`.

## Diseno

## Implementacion

## Para el humano
