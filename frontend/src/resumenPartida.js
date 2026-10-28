/**
 * Resumen en texto plano de una partida, para copiarlo al portapapeles y
 * pegarlo en un chat. Sale del payload de /api/matches/<id>/ que la pagina ya
 * tiene: ninguna request nueva. Sin React para probarlo con vitest.
 */

// Mismo criterio que `fmt` de ui.jsx; no se importa porque ui.jsx trae React.
function numero(valor, digitos = 0, sufijo = '') {
  return valor === null || valor === undefined ? '—' : `${Number(valor).toFixed(digitos)}${sufijo}`
}

function miFila(ronda) {
  return (ronda.players || []).find((p) => p.is_me) || null
}

function lineaStats(rondas, mine) {
  // El nick con el que terminaste la partida: la ultima ronda con tu fila
  let nick = 'Tú'
  for (const ronda of rondas) {
    const fila = miFila(ronda)
    if (fila && fila.username) nick = fila.username
  }
  return (
    `${nick}: ${numero(mine.kills)} bajas / ${numero(mine.deaths)} muertes` +
    ` · K/D ${numero(mine.kd, 2)}` +
    ` · HS ${numero(mine.hs_pct, 0, '%')}` +
    ` · aperturas ${numero(mine.opening_kills)}-${numero(mine.opening_deaths)}` +
    ` · KST ${numero(mine.kst_pct, 0, '%')}`
  )
}

function lineaRondasGanadas(rondas) {
  const partes = []
  for (const [lado, nombre] of [
    ['Attack', 'ataque'],
    ['Defense', 'defensa'],
  ]) {
    // Una ronda sin ganador conocido (.rec cortado) no es ni ganada ni perdida
    const delLado = rondas.filter((r) => r.my_side === lado && r.my_team_won !== null && r.my_team_won !== undefined)
    if (!delLado.length) continue
    const ganadas = delLado.filter((r) => r.my_team_won === true).length
    partes.push(`${nombre} ${ganadas} de ${delLado.length}`)
  }
  return partes.length ? `Rondas ganadas: ${partes.join(' · ')}` : null
}

function lineaMejorRonda(rondas) {
  let mejor = null
  let maximo = 0
  for (const ronda of rondas) {
    const bajas = miFila(ronda)?.kills || 0
    // Estricto: en empate queda la primera
    if (bajas > maximo) {
      maximo = bajas
      mejor = ronda
    }
  }
  if (!mejor) return null
  return `Mejor ronda: ${mejor.label}, ${maximo} ${maximo === 1 ? 'baja' : 'bajas'}`
}

/** Las lineas del resumen unidas con '\n'; las que no tienen datos no salen. */
export function textoResumenPartida(data) {
  const match = data?.match || {}
  const rondas = data?.rounds || []
  const mine = data?.my_totals || {}
  const fecha = match.played_at ? match.played_at.slice(0, 16).replace('T', ' ') : null
  return [
    `${match.map} · ${match.score} · ${match.result}`,
    [fecha, match.match_type].filter(Boolean).join(' · ') || null,
    lineaStats(rondas, mine),
    lineaRondasGanadas(rondas),
    lineaMejorRonda(rondas),
  ]
    .filter(Boolean)
    .join('\n')
}
