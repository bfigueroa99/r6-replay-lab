# 142. Operadores con los que mueres solo

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O9 (`by_operator` ya devuelve `untraded_death_pct` por `derive`, pero la tabla de Operadores no lo muestra)
archivos: -
turnos: po 20261114T0040Z-chQsvnq

## PR

## Que gana quien usa la app

En Operadores, por operador, que parte de tus muertes con el nadie las vengo,
contra la misma tasa con tus otros operadores del mismo lado: un roamer o un
flanco que te deja morir aislado se ve aunque su K/D cuadre.

## Criterios de aceptacion

- [ ] `/api/operators/` (o el endpoint que ya usa la tabla) trae por
      operador `deaths`, `untraded_deaths` y `untraded_death_pct` (la misma
      regla de `untraded_death` que el Inicio) y `rest_untraded_death_pct`:
      la tasa de tus muertes con los demas operadores de ese lado, con los
      mismos filtros. Test con dos operadores del mismo lado.
- [ ] Un operador sin muertes queda con la tasa nula, no 0 %. Test.
- [ ] La tabla de Operadores suma la columna "Mueres solo" (`NN %` con el
      `n` de muertes en la ayuda o en la celda) y la diferencia contra el
      resto; ordenable y en el CSV. Logica de la celda en un helper con
      vitest si no es trivial.
- [ ] e2e: la columna aparece sobre `seed_demo` con el valor de la API y la
      consola limpia.
- [ ] Fila nueva en `docs/metricas.md` (o la de **Muertes sin trade**
      ampliada) que diga que ahora tambien va por operador.

## Fuera de alcance

- Señal del Coach con este dato.
- Partirlo por mapa.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
