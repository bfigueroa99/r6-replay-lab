/**
 * Fases de la ronda del detalle de partida: las filas del panel y sus textos.
 * Logica pura, aparte del componente, para probarla sin montarlo.
 */

function ganadas(won, n) {
  return n ? `${won} de ${n}` : '—'
}

/**
 * Una fila por fase con las bajas de cada equipo, quien saco mas (`mejor`,
 * null en empate) y el texto de rondas dominadas. Sin `phases` (respuesta
 * vieja en cache) devuelve una lista vacia para que la pagina no rompa.
 */
export function filasDeFases(phases) {
  if (!phases || !Array.isArray(phases.rows)) return []
  return phases.rows.map((fila, orden) => {
    const mine = fila.mine ?? 0
    const rival = fila.rival ?? 0
    return {
      key: fila.key,
      label: fila.label,
      orden,
      mine,
      rival,
      mejor: mine === rival ? null : mine > rival ? 'mine' : 'rival',
      ganadasAdelante: ganadas(fila.rounds_ahead_won ?? 0, fila.rounds_ahead ?? 0),
      ganadasAtras: ganadas(fila.rounds_behind_won ?? 0, fila.rounds_behind ?? 0),
    }
  })
}

/** Alguna fase con bajas entre equipos. */
export function hayBajas(phases) {
  return filasDeFases(phases).some((f) => f.mine + f.rival > 0)
}

/**
 * La nota de las bajas que no entran en ninguna fase (sin reloj o de un
 * jugador sin fila en la ronda); null si no hay. Los teamkills no van: ya
 * tienen su propia metrica y no son bajas de ningun equipo.
 */
export function notaDeFases(phases) {
  if (!phases) return null
  const n = (phases.untimed_kills ?? 0) + (phases.unknown_team_kills ?? 0)
  if (!n) return null
  return n === 1
    ? '1 baja sin reloj o de un jugador sin fila queda fuera de las fases.'
    : `${n} bajas sin reloj o de un jugador sin fila quedan fuera de las fases.`
}
