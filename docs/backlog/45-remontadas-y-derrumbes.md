# 45. Remontadas y derrumbes

estado: propuesto
candado: arquitecto 2026-10-14T23:11Z
rama: -
tipo: funcionalidad
epica: lado-y-marcador
area: fullstack
prioridad: 3
fuente: ALCANCE.md B7 (idea del PO); cierra la epica lado-y-marcador despues de las fichas 36, 41 y 43
archivos: -
turnos: po 20261014T1911Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Tendencias aparece un panel que lista las partidas que ganaste yendo
abajo por 2 o mas rondas (remontadas) y las que perdiste yendo arriba por 2
o mas (derrumbes), cada una con enlace a su detalle. Debajo, tu winrate de
partida segun la diferencia de rondas que llevabas al cambio de lado: si
sueltas las partidas que tienes ganadas o si das vuelta las perdidas.

## Criterios de aceptacion

- [ ] `/api/trends/` devuelve una clave nueva (p. ej. `comebacks`) con dos
      listas, `remontadas` y `derrumbes`, cada item con `match_id`, mapa,
      fecha, marcador final y la maxima desventaja (o ventaja) en rondas
      que hubo antes de la ultima ronda. Una partida ganada que estuvo 1-3
      entra en `remontadas` con desventaja 2; una ganada que nunca estuvo
      abajo por 2 no entra.
- [ ] Una partida perdida que estuvo 3-1 a favor entra en `derrumbes`; una
      perdida que nunca estuvo arriba por 2 no entra.
- [ ] Solo cuentan partidas con marcador conocido: mismo corte que
      `by_score_state` (`code_version >= Y9S4`, marcador de dos equipos,
      `_marcador_conocido` en `aggregates.py`). Una partida anterior a Y9S4
      no aparece en ninguna lista ni en la tabla de diferencia. Test con
      una partida de cada lado del corte.
- [ ] Tabla de winrate de partida por diferencia de rondas al cambio de
      lado (primera ronda de la segunda mitad, la misma frontera que usa
      `by_half`): tramos `+2 o mas`, `+1`, `0`, `-1`, `-2 o menos`, con
      partidas y winrate por tramo. Respeta los filtros de la barra (mapa,
      fechas, sesion) como el resto de `/api/trends/`.
- [ ] Tendencias muestra el panel "Remontadas y derrumbes" con las dos
      listas (enlace al detalle de cada partida) y la tabla; con base vacia
      o sin partidas con marcador conocido muestra un texto de vacio, no un
      error. El e2e (`frontend/e2e/`) lo afirma sobre `seed_demo`.
- [ ] Fila en `docs/metricas.md` para la desventaja maxima y el winrate por
      diferencia al cambio de lado.

## Fuera de alcance

- Grafico del marcador ronda a ronda de cada partida (eso es F4, tira de
  rondas en el listado de Partidas).
- Umbral configurable desde la UI: el 2 queda fijo en el diseno.
- Probabilidad de ganar segun el marcador (modelo estadistico): solo
  conteos.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano
