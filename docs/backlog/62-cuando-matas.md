# 62. Cuando matas

estado: propuesto
candado: arquitecto 2026-10-24T16:05Z
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B11 ([tracker.gg](https://tracker.gg/r6siege/articles/r6-ow-v3-0), "number of kills in the first 30 seconds")
archivos: -
turnos: po 20261024T1204Z

## Que gana quien usa la app

En Tendencias ya esta "Cuando mueres"; falta el otro lado: en que momento de
la fase de accion sacas tus bajas. Dice si tu impacto esta en la apertura o
en el cierre de la ronda, y en defensa cuantas bajas tempranas consigues.

## Criterios de aceptacion

- [ ] `/api/trends/` trae una clave nueva `kills_by_time`: tramos de 30 s
  (`DEATH_BUCKET`) con el ultimo abierto en `DEATH_CAP` (150s+), igual
  que `deaths_by_time`, cada uno con `start`, `end`, `label`, `kills`,
  `attack`, `defense` y `pct`. Lee `Event.elapsed` de los eventos
  `Kill` cuyo autor es tu jugador en las rondas del `base_queryset`; el
  lado sale de tu fila `RoundPlayer` de esa ronda. Test con bajas en 10 s,
  45 s y 200 s que caen en 0-30s, 30-60s y 150s+.
- [ ] Los teamkills no cuentan (mismo criterio que `_solo_rivales`): test
  con una baja a un compañero que no aparece en ningun tramo.
- [ ] La suma de `kills` de todos los tramos es igual al total de bajas a
  rivales del feed con los mismos filtros; un filtro `side=Defense` deja
  `attack` en 0 en todos los tramos (test).
- [ ] Base vacia: 200 y `kills_by_time: []`.
- [ ] Tendencias: panel "Cuando matas" al lado de "Cuando mueres", mismo
  grafico apilado por lado y mismo texto sobre segundos de fase de accion;
  e2e sobre `seed_demo` que lo encuentra.
- [ ] Fila nueva en `docs/metricas.md` al lado de "Cuando mueres".

## Fuera de alcance

- Cruzar con el winrate de la ronda o con la primera baja: eso es la ficha 63.
- Columna nueva al importar: se calcula al consultar desde `Event`, como
  Duelos. Si el Arquitecto ve que `RoundPlayer` lo necesita, es otra ficha.
