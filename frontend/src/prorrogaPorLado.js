/**
 * Tabla "Prórroga por lado" de Tendencias: la fila de prorroga del panel de
 * mitades, abierta segun el lado de cada ronda (`by_overtime_side`).
 */

const TRAMOS = { Attack: 'Prórroga en ataque', Defense: 'Prórroga en defensa' }

/** Filas de la tabla; `[]` sin prorrogas, para mostrar una nota y no ceros. */
export function filasProrrogaPorLado(rows) {
  const filas = rows || []
  if (!filas.some((fila) => fila.rounds > 0)) return []
  return filas.map((fila, orden) => ({ ...fila, orden, tramo: TRAMOS[fila.side] || fila.side }))
}
