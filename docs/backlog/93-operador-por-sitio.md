# 93. Operador por sitio contra el resto del sitio

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: paridad-referencia
area: fullstack
prioridad: 3
fuente: O1 de ALCANCE.md; `replica/features.csv` "Delta de win rate de un operador contra la base, por mapa y sitio" (must, partial: la ficha 65 da el delta contra tu lado, falta el corte por mapa y sitio); [aurelix](https://aurelix.app/blog/how-to-analyse-r6-siege-replays)
archivos: -
turnos: po 20261105T1945Z-cvqUYh1

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Operadores, una tabla por mapa y sitio que dice con que operador ganas mas
o menos rondas en ese sitio que con el resto de tus operadores ahi: que
operador te rinde en Cocina de Oregon y cual te hunde. Hoy el winrate por
operador (ficha 65) y por sitio van por separado, y la referencia los cruza.

## Criterios de aceptacion

- [ ] Endpoint (o clave nueva en `/api/operators/`, a eleccion del
      Arquitecto) con filas `mapa (version) / sitio / lado / operador`:
      rondas, winrate, winrate del resto del sitio (mismas mapa, sitio y lado,
      otros operadores), delta y margen de ruido. Respeta los filtros globales.
- [ ] Solo filas con al menos 10 rondas del operador en ese sitio y al menos
      10 rondas del resto; el minimo vive en una constante y en
      `docs/metricas.md`.
- [ ] La comparacion es contra el resto del sitio, no contra el total del
      sitio (el operador esta dentro del total: mismo motivo que
      `_contra_el_resto` de la ficha 80), con banda de ruido de proporcion
      combinada (`_ruido_combinado`): veredicto `rinde`, `hunde` o `ruido`.
      Test con numeros fijos de `factories.py` para los tres veredictos.
- [ ] Rondas sin ganador (`my_team_won` nulo) y rondas sin sitio u operador
      quedan fuera del numerador y del denominador; test.
- [ ] En Operadores se ve la tabla nueva, ordenada por |delta|, con texto
      cuando no hay filas con muestra suficiente; e2e con los numeros de
      `seed_demo` (o el texto vacio si el seed no llega a 10 rondas: el
      Arquitecto decide si baja el minimo por parametro en el e2e o ajusta el
      seed).
- [ ] Fila nueva en `docs/metricas.md` con la definicion y el minimo.

## Fuera de alcance

- Señal nueva del Coach sobre esto (si sirve, otra ficha).
- Operadores rivales por sitio (D2, otra idea).
- Corte por temporada (A3).

## Diseno

## Implementacion

## Revision

## QA

## Pendiente

## Para el humano
