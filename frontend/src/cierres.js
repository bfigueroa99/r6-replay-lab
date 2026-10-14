/**
 * Filas del panel "Como se cierran tus rondas" de Tendencias. Separado de la
 * pagina para probar la logica sin montarla.
 */

const LADOS = { Attack: 'Ataque', Defense: 'Defensa' }

/** El complemento de un porcentaje; nulo si no hay dato, para no inventar un 100. */
function complemento(pct) {
  return pct === null || pct === undefined ? null : Math.round((100 - pct) * 10) / 10
}

/**
 * Una fila por lado, en el orden del backend, con los porcentajes de "sin
 * eliminacion" como complemento de los de eliminacion: el backend los manda
 * sobre las ganadas (o perdidas) con dato, asi que suman 100.
 */
export function filasDeCierre(filas) {
  return (filas || []).map((fila, orden) => ({
    ...fila,
    orden,
    lado: LADOS[fila.side] || fila.side,
    won_other_pct: complemento(fila.won_elimination_pct),
    lost_other_pct: complemento(fila.lost_elimination_pct),
  }))
}

/** El panel no tiene nada que decir si ningun lado tiene rondas. */
export function hayCierres(filas) {
  return (filas || []).some((fila) => (fila?.rounds || 0) > 0)
}
