# 61. Clutch por operador

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O6 (siguiente tramo tras las fichas 55 y 59, ya en main)
archivos: -
turnos: po 20261024T1204Z

## Que gana quien usa la app

Hoy el panel "Clutches" de Compañeros dice cuantos clutches intentas y
conviertes por 1vX y por mapa y sitio, pero no con que operador. Esta tabla
dice con que operador cierras las rondas que quedan en tus manos y con cual
las sueltas, separado por lado.

## Criterios de aceptacion

- [ ] `/api/teammates/` trae una clave nueva `clutch_by_operator`: una fila
  por operador y lado con `operator`, `side`, `attempts`, `won`, `pct` y
  `low_sample`; intento y ganado con la misma definicion que
  `clutch_conversion` (`clutch_vs > 0`, rondas con `my_team_won` nulo
  afuera), asi que la suma de `attempts` de todas las filas es igual a la
  suma de `attempts` de `clutch_conversion` con los mismos filtros (menos
  las rondas sin operador, que no salen en ninguna fila: test).
- [ ] Las filas con menos intentos que el minimo (constante en
  `aggregates.py`, como `CLUTCH_SITIO_MIN`) salen igual con
  `low_sample: true`; borde N-1 / N con test.
- [ ] Respeta los filtros de la barra (`side`, `map`, `ranked_only`,
  `since`, `until`): test con `side=Attack` que deja solo filas de ataque.
- [ ] Base vacia: 200 y `clutch_by_operator: []`.
- [ ] Compañeros, panel "Clutches": tabla "Clutch por operador" (Operador,
  Lado, Intentos, Ganados, Conversión) con `*` en muestra chica, orden por
  intentos y boton CSV `clutch-por-operador`; e2e sobre `seed_demo` que la
  encuentra con al menos una fila.
- [ ] Fila nueva en `docs/metricas.md` junto a las de clutch.

## Fuera de alcance

- "Cuantos se esperaban" (parte de K3 que depende de la tabla K1).
- Clutch por operador y mapa a la vez: la muestra no da.
- Migracion o columna nueva: `clutch_vs` ya existe (ficha 55).
