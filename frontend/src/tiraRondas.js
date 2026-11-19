/**
 * Tira de rondas de cada fila de Partidas (ficha 103). Sin React: recibe el
 * `strip` de /api/matches/ y devuelve las celdas ya listas para dibujar.
 */

const LETRA = { Attack: 'A', Defense: 'D' }
const LADO = { Attack: 'ataque', Defense: 'defensa' }

function claseDe(won) {
  if (won === true) return 'win'
  if (won === false) return 'loss'
  // won=null es una ronda sin ganador claro (ficha 38), no una perdida
  return 'nula'
}

function resultadoDe(won) {
  if (won === true) return 'ganada'
  if (won === false) return 'perdida'
  return 'sin ganador claro'
}

/** Una celda por ronda, en el orden del backend; la primera de prorroga lleva el corte antes. */
export function celdasDeTira(strip) {
  let enProrroga = false
  return (strip || []).map((ronda) => {
    const corteAntes = Boolean(ronda.overtime) && !enProrroga
    if (ronda.overtime) enProrroga = true
    const partes = [`R${ronda.number + 1}`, LADO[ronda.side] || 'lado desconocido', resultadoDe(ronda.won)]
    if (ronda.overtime) partes.push('prórroga')
    return {
      clave: ronda.number,
      clase: claseDe(ronda.won),
      letra: LETRA[ronda.side] || '?',
      titulo: partes.join(' · '),
      corteAntes,
    }
  })
}

/** La tira como texto para el CSV: `G G P | P G`, con `|` antes de la prorroga y `-` sin ganador. */
export function textoDeTira(strip) {
  const letra = { win: 'G', loss: 'P', nula: '-' }
  return celdasDeTira(strip)
    .map((celda) => `${celda.corteAntes ? '| ' : ''}${letra[celda.clase]}`)
    .join(' ')
}
