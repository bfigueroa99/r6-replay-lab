# 137. Cuantas de tus muertes son headshot

estado: propuesto
candado: arquitecto 2026-11-14T00:41Z
rama: -
tipo: funcionalidad
epica: rivales
area: fullstack
prioridad: 3
fuente: ALCANCE.md D8
archivos: -
turnos: po 20261113T2157Z-cG2vDSe

## PR

## Que gana quien usa la app

El HS% que muestra la app es el tuyo al matar; el reverso no existe. En Duelos,
de tus muertes a manos de rivales, cuantas fueron headshot, por lado, al lado
del mismo numero para tus compañeros en las mismas rondas: si te enganchan la
cabeza mas que al resto del equipo, te asomas expuesto.

## Criterios de aceptacion

- [ ] Agregado nuevo: de los `Event` de baja cuyo `target` eres tu y cuyo
      autor es rival (`_solo_rivales`, sin teamkills), `deaths`,
      `with_data` (`headshot` no nulo), `headshots` y `pct` =
      headshots / with_data, por lado de tu fila (`Attack`, `Defense`) y
      total. `headshot` nulo no entra en el porcentaje. Test con muertes con
      y sin dato y un teamkill que no cuenta.
- [ ] La referencia: el mismo calculo sobre las muertes de tus compañeros
      (tu `team_index`, `is_me=False`) en tus rondas filtradas. Test.
- [ ] Los filtros globales aplican sobre tu fila de la ronda; test con
      filtro de lado.
- [ ] Se ve en Duelos (clave nueva en el endpoint que ya usa la pagina o uno
      nuevo de lectura) como una tabla chica Tú / Tus compañeros por lado, con
      el `n` (muertes con dato) a la vista y aviso si es chico; sin dato,
      una nota. e2e sobre `seed_demo` con los numeros de la API y consola
      limpia.
- [ ] Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Partirlo por operador rival (otro tramo).
- Señal del Coach.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
