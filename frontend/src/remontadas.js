/**
 * Filas del panel "Remontadas y derrumbes" de Tendencias. Separado de la
 * pagina para probar la logica sin montarla.
 */

const TRAMOS = {
  '+2': '+2 o más',
  '+1': '+1',
  0: 'Empatado',
  '-1': '-1',
  '-2': '-2 o menos',
}

/** Etiqueta de un tramo de diferencia al cambio de lado; uno desconocido pasa tal cual. */
export function etiquetaTramo(diff) {
  return TRAMOS[diff] ?? String(diff)
}

/**
 * Una fila por tramo, en el orden del backend (de ir arriba a ir abajo). No
 * se ocultan los tramos vacios: que no haya partidas yendo -2 tambien dice algo.
 */
export function filasDeCambio(filas) {
  return (filas || []).map((fila, orden) => ({
    ...fila,
    orden,
    tramo: etiquetaTramo(fila.diff),
  }))
}

/**
 * Partidas de una lista con la diferencia escrita desde tu lado: "Ibas -2" en
 * una remontada, "Ibas +2" en un derrumbe.
 */
export function filasDePartidas(partidas, clave) {
  const signo = clave === 'max_lead' ? '+' : '-'
  return (partidas || []).map((partida, orden) => ({
    ...partida,
    orden,
    fecha: (partida.played_at || '').slice(0, 16).replace('T', ' '),
    diferencia: `Ibas ${signo}${partida[clave]}`,
  }))
}
