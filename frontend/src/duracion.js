/**
 * Filas del panel "Rondas cortas y largas" de Tendencias. Separado de la
 * pagina para probar la logica sin montarla.
 */

import { filasConPocaMuestra } from './muestra.js'

const TRAMOS = {
  '0-45': '0–45 s',
  '45-90': '45–90 s',
  '90-135': '90–135 s',
  '135+': '135 s o más',
  plant: 'Posible plant',
}

const LADOS = ['Attack', 'Defense', 'total']

/** Etiqueta de un tramo de duracion; uno desconocido pasa tal cual. */
export function etiquetaDuracion(length) {
  return TRAMOS[length] ?? String(length)
}

/**
 * "57% (203)". Sin rondas, guion: un 0 % diria que perdiste todo. La fila de
 * posible plant trae rondas pero no winrate, y muestra solo el conteo.
 */
export function textoCelda(celda) {
  const rondas = celda?.rounds || 0
  if (!rondas) return '—'
  if (celda.winrate === null || celda.winrate === undefined) return `— (${rondas})`
  return `${Math.round(celda.winrate)}% (${rondas})`
}

/** Una fila por tramo, en el orden del backend; los vacios no se ocultan. */
export function filasDeDuracion(byRoundLength) {
  return (byRoundLength?.rows || []).map((fila, orden) => ({
    ...fila,
    orden,
    tramo: etiquetaDuracion(fila.length),
    vista: Object.fromEntries(LADOS.map((lado) => [lado, textoCelda(fila[lado])])),
    rating: fila.total?.rating ?? null,
    kpr: fila.total?.kpr ?? null,
  }))
}

/** Ataque, defensa y total de los cuatro tramos: cuanto tardas en ganar y en perder. */
export function resumenDeDuracion(byRoundLength) {
  const resumen = byRoundLength?.summary
  if (!resumen) return []
  return [
    ['Attack', 'Ataque'],
    ['Defense', 'Defensa'],
    ['total', 'Total'],
  ].map(([clave, lado], orden) => ({
    clave,
    lado,
    orden,
    rounds: resumen[clave]?.rounds || 0,
    avg_duration_won: resumen[clave]?.avg_duration_won ?? null,
    avg_duration_lost: resumen[clave]?.avg_duration_lost ?? null,
  }))
}

/** Celdas de los cuatro tramos con poca muestra; la fila de plant no cuenta. */
export function celdasConPocaMuestra(byRoundLength, minimo) {
  const celdas = (byRoundLength?.rows || [])
    .filter((fila) => fila.length !== 'plant')
    .flatMap((fila) => LADOS.map((lado) => fila[lado]))
  return filasConPocaMuestra(celdas, minimo)
}

/** Hay al menos una ronda con reloj legible. */
export function hayDuracion(byRoundLength) {
  if ((byRoundLength?.summary?.total?.rounds || 0) > 0) return true
  return (byRoundLength?.rows || []).some((fila) => (fila.total?.rounds || 0) > 0)
}
