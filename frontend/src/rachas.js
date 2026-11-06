/**
 * Texto de las rachas de rondas del encabezado del detalle de partida.
 * Separado de la pagina para probar el formato sin montarla.
 */

function mitad(racha, singular, plural) {
  if (!racha) return null
  return `${racha.length} ${racha.length === 1 ? singular : plural} desde ${racha.from_round_label}`
}

/** "Racha: 4 ganadas desde R3 · 3 perdidas desde R8"; '' si no hay ninguna. */
export function textoDeRachas(rachas) {
  const partes = [
    mitad(rachas?.wins, 'ganada', 'ganadas'),
    mitad(rachas?.losses, 'perdida', 'perdidas'),
  ].filter(Boolean)
  return partes.length ? `Racha: ${partes.join(' · ')}` : ''
}

/**
 * "Racha actual: 3 victorias seguidas desde 2026-11-05" para el Inicio; ''
 * sin racha. Con una sola partida no hay "seguidas" que decir.
 */
export function textoRachaActual(racha) {
  if (!racha) return ''
  const ganada = racha.result === 'win'
  const fecha = racha.since.slice(0, 10)
  if (racha.length === 1) return `Racha actual: 1 ${ganada ? 'victoria' : 'derrota'} (${fecha})`
  return `Racha actual: ${racha.length} ${ganada ? 'victorias' : 'derrotas'} seguidas desde ${fecha}`
}
