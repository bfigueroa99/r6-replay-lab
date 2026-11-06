/**
 * Armado de la comparacion de dos partidas (ficha 101). Sin React: recibe los
 * payloads de /api/matches/<id>/ y devuelve filas ya como texto.
 */

const GUION = '—'

/** true: sale mejor quien tiene mas; false: quien tiene menos. */
const MAS_ES_MEJOR = {
  kills: true,
  deaths: false,
  opening_kills: true,
  opening_deaths: false,
  untraded_deaths: false,
  kst_pct: true,
  rating: true,
  Attack: true,
  Defense: true,
}

const NUMERICAS = [
  ['kills', 'Bajas'],
  ['deaths', 'Muertes'],
  ['opening_kills', 'Aperturas ganadas'],
  ['opening_deaths', 'Aperturas perdidas'],
  ['untraded_deaths', 'Muertes sin trade'],
  ['kst_pct', 'KST'],
  ['rating', 'Rating'],
]

const fecha = (iso) => (iso ? String(iso).slice(0, 16).replace('T', ' ') : GUION)

const esNumero = (v) => typeof v === 'number' && Number.isFinite(v)

/** Las opciones del selector: sin la partida actual y con el mismo mapa aparte. */
export function opcionesParaComparar(matches, actual) {
  const mismoMapa = []
  const otras = []
  for (const m of matches || []) {
    if (String(m.id) === String(actual?.id)) continue
    const opcion = { id: m.id, texto: `${fecha(m.played_at)} · ${m.map} · ${m.score} · ${m.result}` }
    // la etiqueta con version y no el slug: Consulate (Y10) no es el Consulate viejo
    if (actual && m.map === actual.map) mismoMapa.push(opcion)
    else otras.push(opcion)
  }
  return { mismoMapa, otras }
}

/** Rondas ganadas y jugadas por lado; una ronda sin ganador suma al total y no a las ganadas. */
export function rondasPorLado(rounds) {
  const lados = { Attack: { won: 0, total: 0 }, Defense: { won: 0, total: 0 } }
  for (const r of rounds || []) {
    const lado = lados[r.my_side]
    if (!lado) continue
    lado.total += 1
    if (r.my_team_won === true) lado.won += 1
  }
  return lados
}

function conSigno(n, decimales) {
  const texto = n.toFixed(decimales)
  // -0.00 tambien es cero
  if (Number(texto) === 0) return (0).toFixed(decimales)
  return n > 0 ? `+${texto}` : texto
}

function quienMejor(clave, a, b) {
  if (a === b) return null
  const mas = MAS_ES_MEJOR[clave]
  return (a > b) === mas ? 'a' : 'b'
}

function filaTexto(clave, etiqueta, a, b) {
  return { clave, etiqueta, a, b, diferencia: '', mejor: null }
}

function filaNumerica(clave, etiqueta, va, vb, formato, decimales) {
  if (!esNumero(va) || !esNumero(vb)) {
    return {
      clave,
      etiqueta,
      a: esNumero(va) ? formato(va) : GUION,
      b: esNumero(vb) ? formato(vb) : GUION,
      diferencia: '',
      mejor: null,
    }
  }
  // se compara lo que se muestra: un rating 1.234 contra 1.231 no es diferencia
  const ra = Number(va.toFixed(decimales))
  const rb = Number(vb.toFixed(decimales))
  return {
    clave,
    etiqueta,
    a: formato(va),
    b: formato(vb),
    diferencia: conSigno(ra - rb, decimales),
    mejor: quienMejor(clave, ra, rb),
  }
}

/** Tus totales, o null si la partida no tiene tu fila. */
function misTotales(payload) {
  const mine = payload?.my_totals
  if (!mine || !mine.rounds) return null
  return mine
}

function filaLado(clave, etiqueta, la, lb) {
  const texto = (l) => (l.total ? `${l.won} de ${l.total}` : GUION)
  // el winrate del lado y no el conteo: 4 de 6 no es mejor que 3 de 3
  const wr = (l) => (l.total ? (100 * l.won) / l.total : null)
  const fila = filaNumerica(clave, etiqueta, wr(la), wr(lb), () => '', 0)
  return { ...fila, a: texto(la), b: texto(lb) }
}

/** Filas de la tabla, en orden, con el texto de cada celda y quien sale mejor. */
export function filasDeComparacion(a, b) {
  const ma = a?.match || {}
  const mb = b?.match || {}
  const marcador = (m) => (m.score ? `${m.score}${m.result ? ` ${m.result}` : ''}` : GUION)
  const filas = [
    filaTexto('map', 'Mapa', ma.map || GUION, mb.map || GUION),
    filaTexto('played_at', 'Fecha', fecha(ma.played_at), fecha(mb.played_at)),
    filaTexto('match_type', 'Tipo', ma.match_type || GUION, mb.match_type || GUION),
    filaTexto('score', 'Marcador', marcador(ma), marcador(mb)),
  ]

  const la = rondasPorLado(a?.rounds)
  const lb = rondasPorLado(b?.rounds)
  filas.push(filaLado('Attack', 'Rondas en ataque', la.Attack, lb.Attack))
  filas.push(filaLado('Defense', 'Rondas en defensa', la.Defense, lb.Defense))

  const ta = misTotales(a)
  const tb = misTotales(b)
  for (const [clave, etiqueta] of NUMERICAS) {
    const va = ta ? ta[clave] : null
    const vb = tb ? tb[clave] : null
    if (clave === 'kst_pct') {
      filas.push(filaNumerica(clave, etiqueta, va, vb, (v) => `${Math.round(v)}%`, 0))
    } else if (clave === 'rating') {
      filas.push(filaNumerica(clave, etiqueta, va, vb, (v) => v.toFixed(2), 2))
    } else {
      filas.push(filaNumerica(clave, etiqueta, va, vb, (v) => String(v), 0))
    }
  }
  return filas
}
