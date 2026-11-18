/**
 * Rondas perdidas sobreviviendo (panel de Tendencias): filas y enlaces del
 * panel. Los numeros salen de `/api/rounds/lost-alive/`.
 */

import { MUESTRA_CORTE } from './muestra.js'
import { anclaDeRonda } from './navegacionRondas.js'

export const ETIQUETAS_LADO = { Attack: 'Ataque', Defense: 'Defensa' }

export function hayPerdidas(data) {
  return (data?.total?.lost || 0) > 0
}

/**
 * Ataque, Defensa y Total; `orden` lo fija para la tabla, que si no ordenaria
 * por la etiqueta. `poca` avisa debajo del corte comun de muestra; una fila
 * sin perdidas no avisa: sale con raya.
 */
export function filasPorLado(data, minimo = MUESTRA_CORTE) {
  if (!data?.total) return []
  const filas = [
    ...(data.sides || []).map((fila) => ({ ...fila, clave: fila.side, lado: ETIQUETAS_LADO[fila.side] || fila.side })),
    { ...data.total, clave: 'total', lado: 'Total' },
  ]
  return filas.map((fila, orden) => ({ ...fila, orden, poca: fila.lost > 0 && fila.lost < minimo }))
}

/** El detalle de la partida parado en esa ronda; `number` es el de la base (0 = R1). */
export function enlaceDeRonda(fila) {
  return `/partidas/${fila.match_id}${anclaDeRonda(fila.number)}`
}
