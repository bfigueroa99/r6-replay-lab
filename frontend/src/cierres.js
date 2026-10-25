/**
 * Filas del panel "Como se cierran tus rondas" de Tendencias. Separado de la
 * pagina para probar la logica sin montarla.
 */

const LADOS = { Attack: 'Ataque', Defense: 'Defensa' }

const sinDato = (pct) => pct === null || pct === undefined

/** El complemento de un porcentaje; nulo si no hay dato, para no inventar un 100. */
function complemento(pct) {
  return sinDato(pct) ? null : Math.round((100 - pct) * 10) / 10
}

/**
 * Los dos porcentajes enteros que muestra la tabla. El complemento se saca del
 * ya redondeado: redondear 87,5 y 12,5 por separado da 88 + 13 = 101.
 */
function enteros(pct) {
  if (sinDato(pct)) return [null, null]
  const entero = Math.round(pct)
  return [entero, 100 - entero]
}

/**
 * Una fila por lado, en el orden del backend, con los porcentajes de "sin
 * eliminacion" como complemento de los de eliminacion: el backend los manda
 * sobre las ganadas (o perdidas) con dato, asi que suman 100.
 */
export function filasDeCierre(filas) {
  return (filas || []).map((fila, orden) => {
    const [ganadasElim, ganadasOtra] = enteros(fila.won_elimination_pct)
    const [perdidasElim, perdidasOtra] = enteros(fila.lost_elimination_pct)
    return {
      ...fila,
      orden,
      lado: LADOS[fila.side] || fila.side,
      won_other_pct: complemento(fila.won_elimination_pct),
      lost_other_pct: complemento(fila.lost_elimination_pct),
      vista: {
        won_elimination_pct: ganadasElim,
        won_other_pct: ganadasOtra,
        lost_elimination_pct: perdidasElim,
        lost_other_pct: perdidasOtra,
      },
    }
  })
}

/** El panel no tiene nada que decir si ningun lado tiene rondas. */
export function hayCierres(filas) {
  return (filas || []).some((fila) => (fila?.rounds || 0) > 0)
}
