# 43. Match point y ronda decisiva

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B5, segundo tramo de B2 (rondas bajo presion); el primer tramo (adelante/empatado/atras) entro con la ficha 41
archivos: -
turnos: po 20261014T0911Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Ver como rindes en las rondas que pueden cerrar la partida: cuando tu equipo
esta a una ronda de ganarla, cuando el rival esta a una de ganarla, y cuando
pasan las dos cosas a la vez. Completa el panel "Según el marcador" de la
ficha 41 con el momento de mas presion.

## Criterios de aceptacion

- [ ] Una tabla de reglas en `pydissect/constants.py` (o `replays/`, a
  eleccion del Arquitecto) dice, por tipo de partida y desde que
  `code_version` vale, a cuantas rondas se gana y como es la prorroga. Una
  partida cuyo tipo o temporada no tiene regla no cuenta como match point:
  cae en "sin regla". Test con un tipo inventado que afirma que va a "sin
  regla" y no a "normal".
- [ ] `GET /api/trends/` devuelve una lista nueva (p. ej. `match_point`) con
  las filas `mine` (tu equipo a una ronda de ganar), `theirs` (el rival a una
  de ganar), `both` (las dos a la vez), `normal` y `unknown` (sin marcador o
  sin regla), con las metricas de siempre. Las filas suman todas tus rondas.
  Test con factories y una partida de punta a punta.
- [ ] Reusa la lectura de `score_before` de `by_score_state` (mismo corte por
  `code_version >= Y9S4`; antes de eso el marcador es [0, 0] y va a
  `unknown`). Test con una partida Y9S3 que afirma `unknown`.
- [ ] Tendencias muestra el panel junto a "Según el marcador", con la banda de
  muestra chica; base vacia sin error en consola. El e2e lo ve con
  `seed_demo` (si hace falta, `seed_demo` usa un tipo con regla; los numeros
  que afirma el e2e se actualizan en la misma rama).
- [ ] Fila nueva en `docs/metricas.md` que explica las reglas por tipo y que
  una partida sin regla no cuenta.

## Fuera de alcance

- Inferir la regla desde las partidas importadas (el marcador final): sesga
  hacia las partidas que terminaron y no detecta un match point perdido.
- Probabilidad de ganar la partida segun el marcador.
- Modos sin rondas por equipos (si aparecen, "sin regla").

## Diseno

(Arquitecto) La regla de cada tipo sale de una fuente citada en el diseno
(nota de parche o pagina oficial de Ubisoft) con la temporada desde la que
vale; si no se puede citar, ese tipo queda fuera de la tabla. La tabla es
datos, asi que agregar una regla despues no toca codigo.

## Implementacion

## Para el humano

Aviso, sin pregunta abierta: la tabla de reglas (a cuantas rondas se gana
cada tipo y como es la prorroga) se arma desde fuentes publicas y se probo
solo con datos sinteticos. Conviene mirar en el PC que el panel marque
match point en una partida ranked y una rapida reales.
