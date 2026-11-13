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

// `orden` guarda el orden de la API (ventaja a desventaja; 5v5, 5v4... 4v5):
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

/** Las muertes que el feed no deja ubicar se cuentan aparte para que el total cierre. */
export function notaSinFeed(n) {
  if (!n) return null
  return n === 1 ? '1 muerte sin evento en el feed no entra.' : `${n} muertes sin evento en el feed no entran.`
}

/** Cada muerte es una ronda: el corte de muestra va sobre `rounds`, como en Tendencias. */
export function avisoPocaMuestra(filas) {
  return filasConPocaMuestra(filas).length > 0
}
