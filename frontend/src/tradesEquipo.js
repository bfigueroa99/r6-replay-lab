/**
 * Trades por equipo del detalle de partida: las dos filas del panel y que
 * equipo sale mejor en cada columna comparable. Logica pura, aparte del
 * componente, para probarla sin montarlo.
 */

const EQUIPOS = [
  { key: 'mine', label: 'Tu equipo' },
  { key: 'rival', label: 'Rival' },
]

// Solo se comparan columnas donde "mejor" no depende de cuantas rondas o
// muertes hubo: muertes y tradeadas a secas no dicen nada por si solas.
const COMPARABLES = {
  untraded_deaths: 'menos',
  untraded_pct: 'menos',
  trade_kills: 'mas',
}

function quienSaleMejor(mio, rival, sentido) {
  if (mio === null || mio === undefined || rival === null || rival === undefined) return null
  if (mio === rival) return null
  const mineGana = sentido === 'menos' ? mio < rival : mio > rival
  return mineGana ? 'mine' : 'rival'
}

/**
 * Dos filas (`Tu equipo`, `Rival`) con los numeros de `team_trades` y, en
 * `mejor`, las columnas donde esa fila gana. Sin `team_trades` (respuesta
 * vieja en cache) devuelve una lista vacia para que la pagina no rompa.
 */
export function filasTradesEquipo(teamTrades) {
  if (!teamTrades || !teamTrades.mine || !teamTrades.rival) return []
  const mejorPorColumna = Object.fromEntries(
    Object.entries(COMPARABLES).map(([col, sentido]) => [
      col,
      quienSaleMejor(teamTrades.mine[col], teamTrades.rival[col], sentido),
    ]),
  )
  return EQUIPOS.map(({ key, label }, orden) => {
    const datos = teamTrades[key]
    return {
      key,
      label,
      orden,
      deaths: datos.deaths ?? 0,
      traded_deaths: datos.traded_deaths ?? 0,
      untraded_deaths: datos.untraded_deaths ?? 0,
      untraded_pct: datos.untraded_pct ?? null,
      trade_kills: datos.trade_kills ?? 0,
      mejor: Object.fromEntries(
        Object.keys(COMPARABLES).map((col) => [col, mejorPorColumna[col] === key]),
      ),
    }
  })
}

/** La nota de una linea debajo de la tabla; null si no hay datos. */
export function textoTradesEquipo(teamTrades) {
  if (!teamTrades || !teamTrades.mine || !teamTrades.rival) return null
  const n = teamTrades.mine.untraded_deaths ?? 0
  const m = teamTrades.rival.untraded_deaths ?? 0
  return `Tu equipo dejó ${n} ${n === 1 ? 'muerte' : 'muertes'} sin trade; el rival, ${m}.`
}
