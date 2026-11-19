/**
 * Estado al morir (panel de Duelos): etiquetas y avisos del panel. Los numeros
 * salen de `/api/duels/death-state/`; aca solo se decide que texto acompana.
 */

import { filasConPocaMuestra } from './muestra.js'

export const ETIQUETAS_GRUPO = {
  ahead: 'Con ventaja',
  even: 'En paridad',
  behind: 'En desventaja',
}

// `orden` guarda el orden de la API (ventaja a desventaja; mas tuyos vivos primero y,
// a igualdad, menos rivales: 5v3, 5v4, 5v5, 4v5):
// sin el, DataTable ordenaria por la etiqueta.

/** Los tres grupos, en el orden que manda la API, con su etiqueta. */
export function filasDeGrupos(data) {
  return (data?.groups || []).map((fila, orden) => ({
    ...fila,
    orden,
    label: ETIQUETAS_GRUPO[fila.group] || fila.group,
  }))
}

/** Los estados exactos con muertes, en el orden de la API. */
export function filasDeEstados(data) {
  return (data?.states || []).map((fila, orden) => ({ ...fila, orden }))
}

export function hayMuertes(data) {
  return (data?.deaths || 0) > 0
}

/**
 * Las muertes que el feed no deja ubicar se cuentan aparte para que el total
 * cierre: las que no tienen evento y las que llegan despues de irte.
 */
export function notaSinFeed(n) {
  if (!n) return null
  const sujeto = n === 1 ? '1 muerte no se puede ubicar' : `${n} muertes no se pueden ubicar`
  return `${sujeto} en el feed (sin evento o después de irte) y no ${n === 1 ? 'entra' : 'entran'}.`
}

/** Cada muerte es una ronda: el corte de muestra va sobre `rounds`, como en Tendencias. */
export function avisoPocaMuestra(filas) {
  return filasConPocaMuestra(filas).length > 0
}
