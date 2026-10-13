/** Tests del aviso de muestra chica en los cortes de Tendencias. */

import { describe, expect, it } from 'vitest'

import { MUESTRA_CORTE, filasConPocaMuestra } from './muestra.js'

describe('filasConPocaMuestra', () => {
  it('avisa las filas con rondas pero por debajo del minimo', () => {
    const filas = [{ rounds: 29 }, { rounds: 30 }, { rounds: 120 }, { rounds: 1 }]
    expect(filasConPocaMuestra(filas)).toEqual([{ rounds: 29 }, { rounds: 1 }])
  })

  it('las filas en cero no avisan', () => {
    expect(filasConPocaMuestra([{ rounds: 0 }, { rounds: 40 }])).toEqual([])
  })

  it('el minimo por defecto es 30 y se puede cambiar', () => {
    expect(MUESTRA_CORTE).toBe(30)
    expect(filasConPocaMuestra([{ rounds: 15 }], 10)).toEqual([])
    expect(filasConPocaMuestra([{ rounds: 15 }], 20)).toEqual([{ rounds: 15 }])
  })

  it('tolera lista vacia, nula y filas sin rondas', () => {
    expect(filasConPocaMuestra([])).toEqual([])
    expect(filasConPocaMuestra(null)).toEqual([])
    expect(filasConPocaMuestra([{}, null])).toEqual([])
  })
})
