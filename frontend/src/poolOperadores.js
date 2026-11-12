// Logica del panel "Tu pool" de Operadores. El backend devuelve siempre los
// dos lados (filtrar por lado dejaria el otro entero en "nunca jugados"), asi
// que el filtro de lado se aplica aca: decide que bloque se muestra.

const LADOS = [
  ['Attack', 'Ataque'],
  ['Defense', 'Defensa'],
]

export function bloquesDelPool(data, lado) {
  if (!data || !data.matches) return []
  const lados = LADOS.filter(([clave]) => !(lado === 'Attack' || lado === 'Defense') || clave === lado)
  return lados.map(([clave, titulo]) => {
    const bloque = data.sides?.[clave] || {}
    return {
      lado: clave,
      titulo,
      resumen: textoResumen(bloque, data.recent_matches),
      stale: bloque.stale || [],
      never: bloque.never || [],
    }
  })
}

function operadores(n) {
  return `${n} ${n === 1 ? 'operador distinto' : 'operadores distintos'}`
}

export function textoResumen(bloque, recentMatches) {
  const recientes = bloque?.distinct_recent || 0
  const total = bloque?.distinct_all || 0
  const ventana = recentMatches === 1 ? 'tu última partida' : `tus últimas ${recentMatches || 0} partidas`
  return `${operadores(recientes)} en ${ventana} · ${total} en todo el historial`
}

// "2026-08-03T20:00:00" -> "2026-08-03": el panel habla de dias, no de horas.
export function fechaCorta(iso) {
  return iso ? String(iso).slice(0, 10) : ''
}
