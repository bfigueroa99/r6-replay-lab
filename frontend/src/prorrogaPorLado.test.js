/** Tests de la tabla "Prórroga por lado" de Tendencias. */

import { describe, expect, it } from 'vitest'

import { PARTIDAS_CORTE, conPocasPartidas, filasProrrogaPorLado } from './prorrogaPorLado.js'

const fila = (side, rounds) => ({ side, rounds, winrate: rounds ? 50 : null, rating: rounds ? 1 : null })

describe('filasProrrogaPorLado', () => {
  it('sin filas no hay tabla', () => {
    expect(filasProrrogaPorLado(undefined)).toEqual([])
    expect(filasProrrogaPorLado([])).toEqual([])
  })

  it('todo en cero no es una tabla de ceros', () => {
    expect(filasProrrogaPorLado([fila('Attack', 0), fila('Defense', 0)])).toEqual([])
  })

  it('pone el texto del lado y el orden, y deja el resto de la fila', () => {
    const filas = filasProrrogaPorLado([fila('Attack', 4), fila('Defense', 0)])
    expect(filas.map((f) => f.tramo)).toEqual(['Prórroga en ataque', 'Prórroga en defensa'])
    expect(filas.map((f) => f.orden)).toEqual([0, 1])
    expect(filas[0]).toMatchObject({ side: 'Attack', rounds: 4, winrate: 50 })
  })

  it('con el filtro de lado sale una sola fila', () => {
    const filas = filasProrrogaPorLado([fila('Defense', 3)])
    expect(filas).toHaveLength(1)
    expect(filas[0].tramo).toBe('Prórroga en defensa')
  })
})

const partidas = (side, matches, winrate) => ({ side, matches, decided: matches, wins: 0, winrate })

describe('filasProrrogaPorLado con partidas', () => {
  it('une las partidas por lado', () => {
    const filas = filasProrrogaPorLado(
      [fila('Attack', 4), fila('Defense', 2)],
      [partidas('Defense', 3, 33.3), partidas('Attack', 1, 100)],
    )
    expect(filas.map((f) => [f.side, f.matches, f.match_winrate])).toEqual([
      ['Attack', 1, 100],
      ['Defense', 3, 33.3],
    ])
  })

  it('un lado sin partidas queda en 0 y sin porcentaje', () => {
    const filas = filasProrrogaPorLado([fila('Attack', 4), fila('Defense', 2)], [partidas('Attack', 2, 50)])
    expect(filas[1]).toMatchObject({ side: 'Defense', matches: 0, match_winrate: null })
  })

  it('sin el segundo argumento las filas no cambian', () => {
    const filas = filasProrrogaPorLado([fila('Attack', 4)])
    expect(filas[0]).toEqual({ ...fila('Attack', 4), orden: 0, tramo: 'Prórroga en ataque' })
  })
})

describe('conPocasPartidas', () => {
  it('avisa entre 1 y 9 partidas y no con 0 ni con 10', () => {
    expect(PARTIDAS_CORTE).toBe(10)
    expect(conPocasPartidas([{ matches: 0 }, { matches: 10 }])).toBe(false)
    expect(conPocasPartidas([{ matches: 1 }, { matches: 10 }])).toBe(true)
    expect(conPocasPartidas([{ matches: 9 }])).toBe(true)
    expect(conPocasPartidas([])).toBe(false)
  })
})
