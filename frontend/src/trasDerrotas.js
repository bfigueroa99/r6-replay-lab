/** Tabla "Después de perder seguido" de Tendencias. */

import { PARTIDAS_CORTE } from './prorrogaPorLado.js'

const TRAMOS = ['Sin derrotas antes', 'Tras 1 derrota', 'Tras 2 derrotas', 'Tras 3 o más']

/** Filas en orden de racha con su tramo; `[]` sin partidas, para mostrar una nota y no ceros. */
export function filasTrasDerrotas(rows) {
  if (!(rows || []).some((fila) => fila.matches > 0)) return []
  return [...rows]
    .sort((a, b) => a.streak - b.streak)
    .map((fila) => ({ ...fila, tramo: TRAMOS[fila.streak] ?? fila.label }))
}

/**
 * `true` si alguna fila tiene partidas decididas pero menos que el corte. El
 * winrate es sobre las decididas: una fila con 20 incompletas y 2 decididas
 * sigue siendo poca muestra.
 */
export function conPocasPartidas(filas) {
  return (filas || []).some((fila) => fila.decided > 0 && fila.decided < PARTIDAS_CORTE)
}
