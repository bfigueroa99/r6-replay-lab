/**
 * Panel "Rondas que tu equipo ganó sin ti" de Compañeros: `won_without_me` de
 * `/api/teammates/`.
 */

/** Filas por lado con el total al final, o `[]` si no caíste en ninguna ronda con ganador. */
export function filasPorLadoSinTi(data) {
  const sides = data?.sides || []
  const total = sides.find((f) => f.side === 'total')
  if (!total || !total.rounds) return []
  // `orden` fija el de la API (lados y despues Total) hasta que se ordene a mano
  return sides.map((fila, orden) => ({ ...fila, orden }))
}

/** Compañeros habituales de esas rondas ganadas, con su enlace y su marca de muestra. */
export function filasSostienen(data) {
  return (data?.mates || []).map((f, orden) => ({
    clave: f.player_id,
    playerId: f.player_id,
    nombre: f.username,
    rounds: f.rounds,
    survived: f.survived,
    pct: f.pct,
    low_sample: f.low_sample,
    orden,
  }))
}
