# 55. Clutch: intentos y conversion por X

estado: propuesto
candado: arquitecto 2026-10-19T04:04Z
rama: -
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 2
fuente: ALCANCE.md K3 ([Siege.GG](https://siege.gg/blog/946-player-rating-rebalance), [vlr.gg](https://www.vlr.gg/713548/vlr-cl-knowers-come))
archivos: -
turnos: po 20261019T0004Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy la app solo cuenta los clutches que ganaste (`one_vx`): no sabes cuantas
veces quedaste ultimo y la perdiste. Con los intentos se ve el % real de
conversion en 1v1, 1v2, 1v3... por lado, que es lo que dice si cierras bien
las rondas o solo te acuerdas de las buenas.

## Criterios de aceptacion

- [ ] Columna nueva `clutch_vs` en `RoundPlayer`, calculada al importar en
  `replays/analytics/metrics.py`: si en algun momento de la ronda quedaste
  como unico vivo de tu equipo, vale la cantidad de rivales vivos en ese
  instante (bajas `Kill`, `Death` y `PLAYER_LEAVE` cuentan como muerte, igual
  que el resto de `metrics.py`); si no, 0. Gane o pierda la ronda. Test con
  feed sintetico: quedar solo frente a 3 y perder da `clutch_vs = 3`; quedar
  solo frente a 2 y ganar da `clutch_vs = 2` y el `one_vx` de siempre.
- [ ] Migracion nueva y `manage.py recompute` llenan la columna en partidas ya
  importadas (test: una partida importada antes de la columna, `recompute`,
  la columna queda con el valor esperado).
- [ ] Endpoint (en el agregado que ya devuelve los clutches, o uno nuevo de
  lectura) con una fila por X (1 a 5; `5+` agrupado si aparece mas) y por
  lado: intentos, ganados y %. Ganado = `clutch_vs > 0` y `won`. Con filtros
  de la barra (mapa, fechas, ranked). Test por `curl` o test de Django con
  `?side=attack`.
- [ ] La pagina donde hoy esta la tabla "Clutches" muestra la tabla de
  conversion por X arriba de la lista; sin intentos dice "Todavía no quedaste
  último en ninguna ronda". Entra al e2e con los datos de `seed_demo`.
- [ ] Fila nueva en `docs/metricas.md` ("Clutch: intentos y conversión") con
  la definicion exacta y la diferencia contra `one_vx`.

## Fuera de alcance

- La parte "cuantos se esperaban" de K3: necesita la tabla de K1 primero.
- Cambiar `one_vx`, el Rating, el record "Clutch mas grande" o la regla
  `sin-clutches` del Coach: siguen leyendo `one_vx`.
- Clutches de compañeros o rivales en una pantalla nueva.

## Diseno

## Implementacion

## Para el humano

Si `clutch_vs` y `one_vx` difieren en el X de una misma ronda ganada (la
logica de r6-dissect cuenta los rivales de otra forma), la tabla usa
`clutch_vs` para agrupar y `one_vx` queda como estaba. Es reversible; avisar
si se prefiere unificarlas.
