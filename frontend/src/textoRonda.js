import { marcasDeApertura } from './aperturas.js'

/**
 * Una ronda del detalle de partida en texto plano, para pegarla en un chat al
 * revisarla con el equipo. Las etiquetas y las marcas son las de la timeline
 * de la pagina: lo copiado tiene que decir lo mismo que se ve.
 */

// Copiada de aperturas.js y no exportada de ahi: asi este modulo no toca ese archivo
const porOrden = (a, b) => (a.order ?? 0) - (b.order ?? 0)

const LADOS = { Attack: 'ataque', Defense: 'defensa' }

function resultado(gano) {
  if (gano === true) return 'ganada'
  if (gano === false) return 'perdida'
  return 'sin resultado'
}

function cabecera(ronda, mapa) {
  return [
    mapa,
    ronda.label,
    LADOS[ronda.my_side] || 'lado desconocido',
    `sitio ${ronda.site || 'desconocido'}`,
    resultado(ronda.my_team_won),
  ]
    .filter(Boolean)
    .join(' · ')
}

function lineaDeBaja(evento, marcas) {
  const reloj = evento.clock_raw || '—'
  // Un teamkill sale como "mató a" y una caida o la bomba como "murió": la
  // timeline tampoco los distingue
  const que =
    evento.kind === 'Kill' ? `${evento.actor} mató a ${evento.target}` : `${evento.actor} murió`
  const chips = [
    evento.order === marcas.apertura ? 'apertura' : null,
    evento.order === marcas.entry ? 'entry' : null,
    evento.headshot ? 'HS' : null,
    evento.traded ? 'tradeada' : null,
  ].filter(Boolean)
  const linea = `${reloj} ${que}${chips.length ? ` (${chips.join(', ')})` : ''}`
  return linea.trimEnd()
}

/** Texto de la ronda: cabecera y una linea por baja, o `null` sin ronda. */
export function textoRonda(ronda, mapa, miEquipo) {
  if (!ronda) return null
  const bajas = (ronda.events || [])
    .filter((e) => e.kind === 'Kill' || e.kind === 'Death')
    .slice()
    .sort(porOrden)
  const marcas = marcasDeApertura(ronda, miEquipo)
  const cuerpo = bajas.length ? bajas.map((e) => lineaDeBaja(e, marcas)) : ['Sin bajas']
  return [cabecera(ronda, mapa), ...cuerpo].join('\n')
}
