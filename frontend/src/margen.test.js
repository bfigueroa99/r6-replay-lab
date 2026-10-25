/** Tests de las filas del panel "Partidas cerradas y holgadas". */

import { describe, expect, it } from 'vitest'

import { etiquetaMargen, filasDeMargen, hayMargen } from './margen.js'

const tramo = (margin, matches = 0, wins = 0, winrate = null) => ({ margin, matches, wins, winrate })

describe('etiquetaMargen', () => {
  it('nombra los cuatro tramos y deja pasar uno desconocido', () => {
    expect(['overtime', '1', '2', '3+'].map(etiquetaMargen)).toEqual([
      'Prórroga', '1 ronda', '2 rondas', '3 o más',
    ])
    expect(etiquetaMargen('9')).toBe('9')
  })
})

describe('filasDeMargen', () => {
  it('conserva las cuatro filas en el orden del backend aunque esten en cero', () => {
    const filas = filasDeMargen({
      rows: [tramo('overtime'), tramo('1', 4, 3, 75), tramo('2'), tramo('3+')],
      matches_known: 4,
    })
    expect(filas.map((f) => f.tramo)).toEqual(['Prórroga', '1 ronda', '2 rondas', '3 o más'])
    expect(filas.map((f) => f.orden)).toEqual([0, 1, 2, 3])
    expect(filas[1].winrate).toBe(75)
    expect(filas[0].winrate).toBeNull()
  })

  it('sin respuesta devuelve una lista vacia sin romper', () => {
    expect(filasDeMargen(undefined)).toEqual([])
    expect(filasDeMargen({})).toEqual([])
  })
})

describe('hayMargen', () => {
  it('dice si hay partidas con margen legible', () => {
    expect(hayMargen({ matches_known: 2 })).toBe(true)
    expect(hayMargen({ matches_known: 0 })).toBe(false)
    expect(hayMargen(undefined)).toBe(false)
  })
})
