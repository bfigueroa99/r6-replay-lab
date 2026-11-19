/**
 * Tabla "Prórroga por lado" de Tendencias: la fila de prorroga del panel de
 * mitades, abierta segun el lado de cada ronda (`by_overtime_side`), con las
 * partidas a prorroga por el lado con que la arrancaste
 * (`by_overtime_start_side`) a la derecha.
 */

const TRAMOS = { Attack: 'Prórroga en ataque', Defense: 'Prórroga en defensa' }

/** El mismo corte de "Margen final": con menos partidas el porcentaje es varianza. */
export const PARTIDAS_CORTE = 10

/** Filas de la tabla; `[]` sin prorrogas, para mostrar una nota y no ceros. */
export function filasProrrogaPorLado(rows, partidas) {
  const filas = rows || []
  if (!filas.some((fila) => fila.rounds > 0)) return []
  return filas.map((fila, orden) => {
    const base = { ...fila, orden, tramo: TRAMOS[fila.side] || fila.side }
    if (!partidas) return base
    const suya = partidas.find((p) => p.side === fila.side)
    return { ...base, matches: suya ? suya.matches : 0, match_winrate: suya ? suya.winrate : null }
  })
}

/** `true` si algun lado tiene partidas a prorroga pero menos que el corte. */
export function conPocasPartidas(filas) {
  return (filas || []).some((fila) => fila.matches > 0 && fila.matches < PARTIDAS_CORTE)
}
