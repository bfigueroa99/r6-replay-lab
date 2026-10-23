/** Tests del texto de las rachas de rondas del detalle de partida. */

import { describe, expect, it } from 'vitest'

import { textoDeRachas } from './rachas.js'

describe('textoDeRachas', () => {
  it('junta las dos rachas', () => {
    const rachas = {
      wins: { length: 4, from_round_label: 'R3' },
      losses: { length: 3, from_round_label: 'R8' },
    }
    expect(textoDeRachas(rachas)).toBe('Racha: 4 ganadas desde R3 · 3 perdidas desde R8')
  })

  it('usa singular para una racha de una ronda', () => {
    const rachas = {
      wins: { length: 1, from_round_label: 'R1' },
      losses: { length: 1, from_round_label: 'R2' },
    }
    expect(textoDeRachas(rachas)).toBe('Racha: 1 ganada desde R1 · 1 perdida desde R2')
  })

  it('omite la mitad nula', () => {
    expect(textoDeRachas({ wins: null, losses: { length: 2, from_round_label: 'R5' } }))
      .toBe('Racha: 2 perdidas desde R5')
  })

  it('sin rachas devuelve vacio', () => {
    expect(textoDeRachas({ wins: null, losses: null })).toBe('')
    expect(textoDeRachas(undefined)).toBe('')
  })
})
