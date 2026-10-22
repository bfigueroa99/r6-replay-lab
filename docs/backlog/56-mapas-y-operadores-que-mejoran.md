# 56. Mapas y operadores que mejoran y empeoran

estado: propuesto
candado: arquitecto 2026-10-22T08:05Z
rama: -
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E5 y E10
archivos: -
turnos: po 20261019T0004Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Tendencias compara hoy el total de tus ultimas N partidas contra las N
anteriores, pero no dice donde cambio. Con el mismo corte por mapa y por
operador ves en que mapa estas mejorando, cual se te cae y si el operador que
practicas rinde, con la banda de ruido que ya separa lo real de lo casual.

## Criterios de aceptacion

- [ ] `compare_periods` (o una funcion hermana en `aggregates.py`) devuelve,
  ademas del total, `by_map` y `by_operator`: por cada mapa (`map_slug`) y por
  cada par operador + lado con al menos `min_rounds` rondas en **los dos**
  periodos, rondas de cada periodo, winrate de ronda y rating actual y previo,
  delta, `noise` (el mismo `_ruido` del total) y `verdict`
  (`mejor`/`peor`/`ruido`). Lo que no llega a la muestra en un periodo no
  aparece. Test de Django con dos periodos sinteticos: un mapa que sube 30
  puntos con muestra sale `mejor`, uno sin muestra en el periodo previo no
  sale.
- [ ] Las filas vienen ordenadas por `delta` de winrate, de mayor a menor.
  Test.
- [ ] Respeta `by=matches|days` y `n` como el total, y los filtros de la barra
  que no son de tiempo. Test con `?by=days&n=30` y con `?side=defense`.
- [ ] `Trends.jsx` muestra dos tablas debajo de la comparacion actual ("Mapas"
  y "Operadores"), con el delta coloreado solo si el veredicto no es
  `ruido`; sin filas, "Sin muestra en los dos periodos". Entra al e2e sobre
  `seed_demo` (la pagina renderiza las dos tablas sin errores de consola).
- [ ] Fila en `docs/metricas.md` (seccion de comparacion de periodos) con la
  muestra minima y que significa el veredicto por fila.

## Fuera de alcance

- Sitios, compañeros u otras dimensiones: solo mapa y operador.
- Graficos de evolucion por mapa en el tiempo.
- Cambiar la muestra minima o la formula del ruido del total.

## Diseno

## Implementacion
