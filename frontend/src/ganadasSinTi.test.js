import { describe, expect, it } from 'vitest'

import { filasPorLadoSinTi, filasSostienen } from './ganadasSinTi.js'

const data = {
  min_rounds: 5,
  sides: [
    { side: 'Attack', rounds: 4, won: 1, pct: 25 },
    { side: 'Defense', rounds: 2, won: 2, pct: 100 },
    { side: 'total', rounds: 6, won: 3, pct: 50 },
  ],
  mates: [
    { player_id: 7, username: 'Seba', rounds: 3, survived: 2, pct: 66.7, low_sample: true },
    { player_id: 9, username: 'Nico', rounds: 6, survived: 1, pct: 16.7, low_sample: false },
  ],
}

describe('filasPorLadoSinTi', () => {
  it('sin rondas no hay tabla', () => {
    expect(filasPorLadoSinTi(undefined)).toEqual([])
    expect(filasPorLadoSinTi({ sides: [{ side: 'total', rounds: 0, won: 0, pct: null }], mates: [] })).toEqual([])
  })

  it('deja las filas en el orden de la API con el total al final', () => {
    const filas = filasPorLadoSinTi(data)
    expect(filas.map((f) => f.side)).toEqual(['Attack', 'Defense', 'total'])
    expect(filas.map((f) => f.orden)).toEqual([0, 1, 2])
    expect(filas[2]).toMatchObject({ rounds: 6, won: 3, pct: 50 })
  })
})

describe('filasSostienen', () => {
  it('mapea los compañeros con su enlace y su muestra', () => {
    const filas = filasSostienen(data)
    expect(filas.map((f) => f.nombre)).toEqual(['Seba', 'Nico'])
    expect(filas[0]).toMatchObject({ clave: 7, playerId: 7, rounds: 3, survived: 2, pct: 66.7, low_sample: true, orden: 0 })
    expect(filas[1].low_sample).toBe(false)
  })

  it('sin compañeros da una lista vacia', () => {
    expect(filasSostienen({ ...data, mates: [] })).toEqual([])
    expect(filasSostienen(undefined)).toEqual([])
  })
})
