/**
 * Filas del panel "Partidas cerradas y holgadas" de Tendencias. Separado de
 * la pagina para probar la logica sin montarla.
 */

/** Partidas minimas por tramo antes de avisar varianza: aca la muestra son partidas, no rondas. */
export const MUESTRA_PARTIDAS = 10

const TRAMOS = {
  overtime: 'Prórroga',
  1: '1 ronda',
  2: '2 rondas',
  '3+': '3 o más',
}

/** Etiqueta de un tramo de margen final; uno desconocido pasa tal cual. */
export function etiquetaMargen(margen) {
  return TRAMOS[margen] ?? String(margen)
}

/**
 * Una fila por tramo, en el orden del backend (de la mas cerrada a la mas
 * holgada). Los tramos vacios no se ocultan: no tener prorrogas tambien dice algo.
 */
export function filasDeMargen(byMargin) {
  return (byMargin?.rows || []).map((fila, orden) => ({
    ...fila,
    orden,
    tramo: etiquetaMargen(fila.margin),
  }))
}

/** Hay al menos una partida con margen legible. */
export function hayMargen(byMargin) {
  return (byMargin?.matches_known || 0) > 0
}
