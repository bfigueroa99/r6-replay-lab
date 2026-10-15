# 50. Partidas cerradas y partidas holgadas

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B10 ([aurelix](https://aurelix.app), tarjeta "Close games")
archivos: -
turnos: po 20261015T1711Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Tendencias, tu winrate y rating en las partidas que se definieron por una
ronda o fueron a prorroga, contra las que se definieron por 3 o mas: si
cierras las parejas o solo ganas las que vas sobrado. Remontadas (ficha 45)
mira la trayectoria; esto mira el margen final.

## Criterios de aceptacion

- [ ] `/api/trends/` trae una clave nueva (p. ej. `by_margin`) con tramos
      fijos: `prorroga`, `1 ronda`, `2 rondas`, `3 o mas`; cada uno con
      partidas, partidas ganadas, winrate de partida y rating (test).
- [ ] El margen sale del marcador final (`Round.score_after` de la ultima
      ronda) con el mismo corte `code_version >= Y9S4` que `by_score_state`;
      las partidas anteriores o sin marcador no cuentan y la respuesta dice
      cuantas quedaron fuera (test con una partida Y9S3).
- [ ] Una partida con `overtime_number` en alguna ronda cae en `prorroga`
      aunque el margen final sea 2 (test).
- [ ] Los filtros de partida de siempre (mapa, `since`/`until`, ranked,
      sesion) recortan las partidas; `side` no parte una partida y se ignora.
      Base vacia devuelve 200 con los tramos en 0 (test).
- [ ] Panel en `Trends.jsx` con la tabla y la banda de ruido como las demas
      tablas de partida; e2e en `frontend/e2e/` que lo ve con `seed_demo`.
- [ ] Fila en `docs/metricas.md`.

## Fuera de alcance

- Margen por mapa o por lado.
- Exportarlo a CSV (H3 lo junta con las demas tablas nuevas).
- Umbrales configurables desde la UI.

## Diseno

(Arquitecto)

## Implementacion
