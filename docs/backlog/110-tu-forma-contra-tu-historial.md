# 110. Tu forma contra tu historial

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: progreso
area: fullstack
prioridad: 3
fuente: ALCANCE.md E16
archivos: -
turnos: po 20261112T1128Z-cKKCvKD

## PR

## Que gana quien usa la app

En el Inicio, un panel junta tus ultimas 10 partidas y las compara con el
resto de tu historial: rating, winrate de rondas, KST y muertes sin trade,
cada uno con la diferencia y si sale del ruido. Hoy "Forma reciente" lista
las 10 partidas una por una; esto dice si estas en racha o en bajon por algo
mas que el resultado.

## Criterios de aceptacion

- [ ] `/api/overview/` (o la clave que elija el diseno) devuelve un bloque
      `form` con `recent` (las mismas partidas que `recent_form()`, mismo
      orden por `played_at`) y `rest` (todas tus otras rondas con los
      mismos filtros), cada uno con `rounds`, `rating`, `winrate`, `kst`
      y el % de muertes sin trade, mas `delta` y `margin` por metrica
      (banda de `_ruido_combinado` donde la metrica es una proporcion).
      Test con historial armado: 10 partidas recientes ganadas contra 10
      viejas perdidas dan `delta` de winrate positivo y fuera del margen.
- [ ] Con 10 partidas o menos no hay `rest`: el bloque dice por que
      (`rest: null`) y el panel muestra una nota, no ceros. Test.
- [ ] Los filtros de la barra aplican a los dos lados de la comparacion
      (test con `?map=`).
- [ ] El panel se ve en el Inicio; el e2e de humo lo afirma con los numeros
      del `seed_demo` y la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Forma contra tu historial").

## Fuera de alcance

- Ventana configurable (10 queda como constante en `aggregates.py`).
- Un grafico: solo numeros con signo, como "vs. tu lado" de Operadores.
- Señal del Coach sobre la racha (seria otra ficha).

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
