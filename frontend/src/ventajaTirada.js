/**
 * Ventaja numerica tirada (panel de Duelos): etiquetas y enlaces del panel. Los
 * numeros salen de `/api/duels/thrown-advantage/`; aca solo se decide el texto.
 */

import { anclaDeRonda } from './navegacionRondas.js'

export const ETIQUETAS_VENTAJA = { one: 'Con uno más', two_plus: 'Con dos o más' }

export const ETIQUETAS_LADO = { Attack: 'Ataque', Defense: 'Defensa' }

export function hayVentajas(data) {
  return (data?.rounds || 0) > 0
}

// `orden` guarda el orden de la API: sin el, DataTable ordenaria por la etiqueta.

/** Ventaja de uno y de dos o mas, en el orden de la API, con su etiqueta. */
export function filasDeGrupos(data) {
  return (data?.groups || []).map((fila, orden) => ({
    ...fila,
    orden,
    label: ETIQUETAS_VENTAJA[fila.group] || fila.group,
  }))
}

/** Ataque y defensa con rondas, en el orden de la API. */
export function filasDeLados(data) {
  return (data?.sides || []).map((fila, orden) => ({
    ...fila,
    orden,
    label: ETIQUETAS_LADO[fila.side] || fila.side,
  }))
}

/** El detalle de la partida parado en esa ronda; `round` ya es la etiqueta R<n>. */
export function enlaceDeRonda(fila) {
  return `/partidas/${fila.match_id}${anclaDeRonda(fila.round - 1)}`
}
