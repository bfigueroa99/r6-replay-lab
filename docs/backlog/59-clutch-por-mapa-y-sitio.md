# 59. Clutch por mapa y sitio

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 3
fuente: ALCANCE.md K5
archivos: -
turnos: po 20261019T0325Z

Implementar despues de #55: usa la columna `RoundPlayer.clutch_vs` que esa
ficha agrega con su migracion.

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

La ficha 55 da la conversion de clutch por X y lado; esta la parte por mapa
y por sitio de bomba. Se ve en que sitio cierras las rondas que quedan en tus
manos y en cual te quedas solo y pierdes siempre, que es donde conviene
revisar como se juega el final de ronda.

## Criterios de aceptacion

- [ ] Agregado nuevo `clutch_by_site` en `replays/analytics/aggregates.py`:
  una fila por mapa y sitio (`Match.map_slug`, `map_name`, `Round.site`) y
  otra de total por mapa, con intentos (`clutch_vs > 0`), ganados
  (`clutch_vs > 0` y `won`) y %. Respeta los filtros de la barra (lado,
  fechas, ranked, operador). Rondas sin sitio van a una fila "Sin sitio" del
  mapa, no se pierden. Test de Django con dos mapas y tres sitios armados.
- [ ] Muestra minima: un sitio con menos de 5 intentos sale igual pero con
  `low_sample: true`, para que la UI lo marque; el umbral es una constante
  con nombre. Test del borde (4 y 5 intentos).
- [ ] Se sirve en el mismo endpoint que la tabla de conversion de la ficha
  55, como `clutch_by_site`; con base vacia devuelve lista vacia sin 500.
- [ ] En la pagina donde la ficha 55 deja la tabla de conversion, una tabla
  "Clutch por mapa y sitio" debajo, ordenada por mapa y con el % de cada
  sitio, boton CSV y la marca de muestra chica. Sin intentos dice
  "Todavía no quedaste último en ninguna ronda". Entra al e2e con
  `seed_demo`.
- [ ] Fila nueva en `docs/metricas.md` ("Clutch por mapa y sitio") que remite
  a la definicion de intento y ganado de la ficha 55.

## Fuera de alcance

- Clutch por operador (idea O6): otra ficha, misma columna.
- La parte "cuantos se esperaban" de K3, que necesita la tabla de K1.
- Cambiar `one_vx`, el Rating o la tabla de la ficha 55.

## Diseno

## Implementacion
