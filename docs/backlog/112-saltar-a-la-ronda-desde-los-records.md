# 112. Saltar a la ronda desde los records

estado: propuesto
candado: arquitecto 2026-11-12T20:25Z
rama: -
tipo: funcionalidad
epica: revision-de-rondas
area: frontend
prioridad: 3
fuente: ALCANCE.md F6 (el PR #14 que lo frenaba se cerro sin merge el 2026-11-05)
archivos: -
turnos: po 20261112T1128Z-cKKCvKD

## PR

## Que gana quien usa la app

En el Inicio, un record de ronda ("Mejor ronda" y los demas que traen
`round_label`) abre el detalle de la partida ya parado en esa ronda, y no
arriba de todo con la ronda 1. Es el primer tramo de F6: deja el ancla
`#ronda-N` en el detalle, que despues pueden usar Remontadas, el Coach y las
listas.

## Criterios de aceptacion

- [ ] `_record_de_ronda` (`aggregates.py`) devuelve tambien el numero de
      ronda (`round_number`, el mismo que usa el detalle); test sobre
      `personal_records`.
- [ ] El detalle de partida acepta `/partidas/<id>#ronda-<n>`: selecciona o
      despliega esa ronda y la lleva a la vista; un `n` que no existe o no
      es numero deja el detalle como siempre, sin error. Logica de leer el
      hash en una funcion pura con vitest.
- [ ] Los records de ronda del Inicio enlazan a `#ronda-<n>`; los de
      partida siguen enlazando a la partida sola.
- [ ] e2e: desde el Inicio del seed, el enlace de "Mejor ronda" abre el
      detalle con esa ronda seleccionada (afirmar por el texto de la ronda
      seleccionada, no por scroll); y `#ronda-999` no ensucia la consola.

## Fuera de alcance

- Enlaces desde Remontadas, Clutches y el Coach (tramos siguientes de F6 y
  de F15).
- Flechas o atajos de teclado entre rondas.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
