/**
 * Estado al matar (panel de Duelos), el reverso de Estado al morir: etiquetas y
 * avisos del panel. Los numeros salen de `/api/duels/kill-state/`.
 */

import { ETIQUETAS_GRUPO } from './estadoAlMorir.js'
import { filasConPocaMuestra } from './muestra.js'

// `orden` guarda el orden de la API (ventaja a desventaja): sin el, DataTable
// ordenaria por la etiqueta.

/** Los tres grupos, en el orden que manda la API, con su etiqueta. */
export function filasDeGrupos(data) {
  return (data?.groups || []).map((fila, orden) => ({
    ...fila,
    orden,
    label: ETIQUETAS_GRUPO[fila.group] || fila.group,
  }))
}

/** Los estados exactos con bajas, en el orden de la API. */
export function filasDeEstados(data) {
  return (data?.states || []).map((fila, orden) => ({ ...fila, orden }))
}

export function hayBajas(data) {
  return (data?.kills || 0) > 0
}

/** Las bajas que el feed no ubica se cuentan aparte para que el total cierre con el Resumen. */
export function notaSinFeed(n) {
  if (!n) return null
  return n === 1
    ? '1 baja no se puede ubicar en el feed y no entra.'
    : `${n} bajas no se pueden ubicar en el feed y no entran.`
}

/** Bajas que el feed pone tras tu caida: el evento esta, pero no hay estado tuyo que contar. */
export function notaPostMortem(n) {
  if (!n) return null
  return n === 1
    ? '1 baja llegó al feed después de tu caída (trampa, gadget o intercambio del mismo instante): no tiene estado tuyo y no entra.'
    : `${n} bajas llegaron al feed después de tu caída (trampas, gadgets o intercambios del mismo instante): no tienen estado tuyo y no entran.`
}

/** El winrate es de la ronda: el corte de muestra va sobre `rounds`, no sobre bajas. */
export function avisoPocaMuestra(filas) {
  return filasConPocaMuestra(filas).length > 0
}
