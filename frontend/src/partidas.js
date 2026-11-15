/**
 * Filtros de la pagina Partidas (ficha 78), sin React para poder probarlos.
 *
 * Partidas reusa la barra compartida de App, pero solo manda los filtros que
 * son de partida: lado, operador y sitio son de ronda (una partida tiene los
 * dos lados y diez operadores), asi que no se mandan aunque vengan puestos
 * desde otra pagina.
 */

import { qs } from './api.js'

export const CLAVES_DE_PARTIDA = ['map', 'days', 'since', 'until', 'session', 'match_type', 'gamemode', 'ranked_only']

export const OPCIONES_DE_RESULTADO = [
  { value: '', label: 'Todos' },
  { value: 'victoria', label: 'Victoria' },
  { value: 'derrota', label: 'Derrota' },
  { value: 'empate', label: 'Empate' },
  { value: 'incompleta', label: 'Incompleta' },
]

/** Solo las claves de la barra que filtran partidas. */
export function filtrosDePartida(filtros) {
  const out = {}
  for (const clave of CLAVES_DE_PARTIDA) {
    if (filtros && clave in filtros) out[clave] = filtros[clave]
  }
  return out
}

/** Query de `/matches/`; `qs()` ya saca el resultado vacio ("Todos"). */
export function paramsDePartidas(filtros, resultado, offset, limite) {
  return { ...filtrosDePartida(filtros), result: resultado, limit: limite, offset }
}

/** Identifica la combinacion de filtros que usa Partidas, para saber cuando cambio. */
export function claveDeFiltros(filtros, resultado) {
  return `${qs(filtrosDePartida(filtros))}|${resultado}`
}

/**
 * Offset a pedir: el guardado solo vale para la combinacion de filtros con la
 * que se pagino. Derivarlo asi vuelve a la primera pagina en el mismo render
 * en que cambia un filtro; un useEffect que resetea el offset pediria antes
 * una pagina de mas con el offset viejo.
 */
export function offsetVigente(pagina, clave) {
  return pagina.clave === clave ? pagina.offset : 0
}

export function subtituloDePartidas(total, filtrado) {
  const n = `${total} partida${total === 1 ? '' : 's'}`
  return filtrado ? `${n} con estos filtros.` : `${n} importada${total === 1 ? '' : 's'}.`
}
