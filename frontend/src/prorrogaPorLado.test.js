/** Tests de la tabla "Prórroga por lado" de Tendencias. */

import { describe, expect, it } from 'vitest'

import { filasProrrogaPorLado } from './prorrogaPorLado.js'

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
