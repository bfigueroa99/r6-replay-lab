/** Tests de los trades por equipo del detalle de partida. */

import { describe, expect, it } from 'vitest'

import { filasTradesEquipo, textoTradesEquipo } from './tradesEquipo.js'

const equipo = (deaths, traded, untraded, tradeKills, pctSinTrade) => ({
  deaths,
  traded_deaths: traded,
  untraded_deaths: untraded,
  trade_kills: tradeKills,
  untraded_pct: pctSinTrade,
})

describe('filasTradesEquipo', () => {
  it('marca al rival cuando dejo mas muertes sin trade', () => {
    const filas = filasTradesEquipo({ mine: equipo(6, 2, 4, 1, 66.7), rival: equipo(5, 4, 1, 3, 20) })
    expect(filas.map((f) => f.label)).toEqual(['Tu equipo', 'Rival'])
    const [mia, rival] = filas
    expect(rival.mejor).toEqual({ untraded_deaths: true, untraded_pct: true, trade_kills: true })
    expect(mia.mejor).toEqual({ untraded_deaths: false, untraded_pct: false, trade_kills: false })
    expect(mia.untraded_deaths).toBe(4)
  })

  it('empate no marca a nadie', () => {
    const filas = filasTradesEquipo({ mine: equipo(4, 2, 2, 1, 50), rival: equipo(4, 2, 2, 1, 50) })
    for (const fila of filas) {
      expect(Object.values(fila.mejor)).toEqual([false, false, false])
    }
  })

  it('sin muertes el porcentaje queda en null y no marca', () => {
    const [mia, rival] = filasTradesEquipo({ mine: equipo(0, 0, 0, 2, null), rival: equipo(3, 1, 2, 0, 66.7) })
    expect(mia.untraded_pct).toBeNull()
    expect(mia.mejor.untraded_pct).toBe(false)
    expect(rival.mejor.untraded_pct).toBe(false)
    // las otras columnas si se comparan
    expect(mia.mejor.untraded_deaths).toBe(true)
    expect(mia.mejor.trade_kills).toBe(true)
  })

  it('sin team_trades devuelve lista vacia', () => {
    expect(filasTradesEquipo(undefined)).toEqual([])
    expect(filasTradesEquipo({ mine: equipo(1, 0, 1, 0, 100) })).toEqual([])
  })
})

describe('textoTradesEquipo', () => {
  it('cuenta las muertes sin trade de cada equipo', () => {
    expect(textoTradesEquipo({ mine: equipo(3, 2, 1, 0, 33.3), rival: equipo(4, 0, 4, 2, 100) })).toBe(
      'Tu equipo dejó 1 muerte sin trade; el rival, 4.',
    )
  })

  it('sin datos no hay nota', () => {
    expect(textoTradesEquipo(null)).toBeNull()
  })
})
