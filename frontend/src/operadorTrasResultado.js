// Logica del panel "Repetir o cambiar tras perder" de Operadores. El backend
// devuelve siempre los dos lados y el total (sin las rondas del otro lado no
// distingue un hueco de un cambio de lado), asi que el filtro de lado se
// aplica aca: decide que filas se muestran.

const BLOQUES = [
  ['total', 'Total'],
  ['Attack', 'Ataque'],
  ['Defense', 'Defensa'],
]

const TRAS = [
  ['after_loss', 'Tras perder'],
  ['after_win', 'Tras ganar'],
]

export const hayPares = (data) => !!data?.pairs

export function filasTrasResultado(data, lado) {
  if (!hayPares(data)) return []
  const conLado = lado === 'Attack' || lado === 'Defense'
  const bloques = BLOQUES.filter(([clave]) => (conLado ? clave === lado : true))
  const minimo = data.min_rounds || 0
  const filas = []
  for (const [clave, nombre] of bloques) {
    const bloque = clave === 'total' ? data.total : data.sides?.[clave]
    for (const [tras, textoTras] of TRAS) {
      const repeat = bloque?.[tras]?.repeat || {}
      const cambio = bloque?.[tras]?.switch || {}
      const repite = repeat.rounds || 0
      const cambia = cambio.rounds || 0
      if (!repite && !cambia) continue
      filas.push({
        clave: `${clave}-${tras}`,
        orden: filas.length,
        lado: nombre,
        tras: textoTras,
        repeat_rounds: repite,
        repeat_winrate: repeat.winrate ?? null,
        repeat_poca: repite < minimo,
        switch_rounds: cambia,
        switch_winrate: cambio.winrate ?? null,
        switch_poca: cambia < minimo,
      })
    }
  }
  return filas
}

export function textoWinrate(winrate, poca) {
  if (winrate === null || winrate === undefined) return '—'
  const texto = `${Math.round(winrate)}%`
  return poca ? `${texto} · pocas rondas` : texto
}

// Con coma decimal, como el resto de las columnas numericas del CSV: el
// archivo es para un Excel en español.
export const winrateCsv = (winrate) =>
  winrate === null || winrate === undefined ? '' : String(winrate).replace('.', ',')
