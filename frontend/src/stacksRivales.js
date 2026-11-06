// Textos del aviso de stack rival del detalle de la partida. El record va
// desde tu lado, igual que la fila de Duelos, para que los dos digan lo mismo.

export function nombresDelGrupo(players) {
  const nombres = (players ?? []).map((j) => j.username)
  if (nombres.length <= 1) return nombres.join('')
  return `${nombres.slice(0, -1).join(', ')} y ${nombres[nombres.length - 1]}`
}

// Separador que va antes del jugador i: lo usa la vista para renderizar los
// nicks como enlaces con la misma puntuacion que nombresDelGrupo.
export function separadorAntes(i, total) {
  if (i === 0) return ''
  return i === total - 1 ? ' y ' : ', '
}

export function textoStackRival(grupo) {
  const { matches, wins, losses } = grupo
  const partidas = matches === 1 ? '1 partida' : `${matches} partidas`
  const sinResultado = matches - wins - losses
  const extra = sinResultado > 0 ? ` (${sinResultado} sin resultado)` : ''
  return `ya te tocaron juntos en ${partidas}, récord ${wins}-${losses}${extra}`
}
