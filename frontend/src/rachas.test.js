/** Tests del texto de las rachas: rondas del detalle de partida y partidas del Inicio. */

import { describe, expect, it } from 'vitest'

import { textoDeRachas, textoRachaActual } from './rachas.js'

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

describe('textoRachaActual', () => {
  it('la racha actual nula no da texto', () => {
    expect(textoRachaActual(null)).toBe('')
    expect(textoRachaActual(undefined)).toBe('')
  })

  it('una victoria va en singular sin seguidas', () => {
    const racha = { result: 'win', length: 1, since: '2026-11-05T20:00:00' }
    expect(textoRachaActual(racha)).toBe('Racha actual: 1 victoria (2026-11-05)')
  })

  it('una derrota va en singular sin seguidas', () => {
    const racha = { result: 'loss', length: 1, since: '2026-11-05T20:00:00' }
    expect(textoRachaActual(racha)).toBe('Racha actual: 1 derrota (2026-11-05)')
  })

  it('varias derrotas van en plural con desde', () => {
    const racha = { result: 'loss', length: 2, since: '2026-11-04T21:30:00' }
    expect(textoRachaActual(racha)).toBe('Racha actual: 2 derrotas seguidas desde 2026-11-04')
  })

  it('varias victorias van en plural con desde', () => {
    const racha = { result: 'win', length: 29, since: '2026-08-01T20:00:00' }
    expect(textoRachaActual(racha)).toBe('Racha actual: 29 victorias seguidas desde 2026-08-01')
  })
})
