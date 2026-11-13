/**
 * Panel "Puesto en el lobby" de Tendencias: `lobby_rank` de `/api/trends/`
 * pasado a las tres stats que muestra la pagina.
 */

import { MUESTRA_PARTIDAS } from './margen.js'

const FILAS = [
  { key: 'best_in_lobby', label: 'Mejor de la partida' },
  { key: 'best_in_team', label: 'Mejor de tu equipo' },
  { key: 'last_in_lobby', label: 'Último de la partida' },
]

/** Las tres stats, o `[]` si no hay partidas con otros jugadores. */
export function statsDePuesto(data) {
  if (!data?.best_in_lobby?.matches) return []
  return FILAS.map(({ key, label }) => {
    const caso = data[key] ?? { count: 0, matches: 0, pct: null }
    return {
      key,
      label,
      pct: caso.pct,
      sub: `${caso.count} de ${caso.matches} ${caso.matches === 1 ? 'partida' : 'partidas'}`,
    }
  })
}

/** Aviso de muestra chica: el porcentaje no se oculta, se avisa. */
export function avisoPuesto(data) {
  const n = data?.best_in_lobby?.matches ?? 0
  if (!n || n >= MUESTRA_PARTIDAS) return null
  return 'Pocas partidas: con menos de 10 el porcentaje se mueve mucho por azar.'
}
