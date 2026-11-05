/** Tests de las filas del panel "Aperturas que pesan". */

import { describe, expect, it } from 'vitest'

import { filasDeAperturasConTrade } from './aperturasTrade.js'

const overall = {
  opening_kills_clean: 7,
  opening_kills_traded: 2,
  opening_deaths_traded: 1,
  opening_deaths_untraded: 4,
  winrate_opening_kill_clean: 71.4,
  winrate_opening_kill_traded: 50,
  winrate_opening_death_traded: null,
  winrate_opening_death_untraded: 25,
}

describe('filasDeAperturasConTrade', () => {
  it('da cuatro filas en orden', () => {
    const filas = filasDeAperturasConTrade(overall)
    expect(filas.map((f) => f.label)).toEqual([
      'Ganada limpia', 'Ganada devuelta', 'Perdida vengada', 'Perdida sin vengar',
    ])
    expect(filas.map((f) => f.orden)).toEqual([0, 1, 2, 3])
    expect(filas.map((f) => f.rondas)).toEqual([7, 2, 1, 4])
    expect(filas[0].winrate).toBe(71.4)
  })

  it('sin muestra el winrate queda en null', () => {
    const filas = filasDeAperturasConTrade({ ...overall, opening_deaths_traded: 0 })
    expect(filas[2].rondas).toBe(0)
    expect(filas[2].winrate).toBeNull()
  })

  it('sin claves nuevas no rompe', () => {
    expect(filasDeAperturasConTrade({ rounds: 10 }).map((f) => [f.rondas, f.winrate])).toEqual([
      [null, null], [null, null], [null, null], [null, null],
    ])
    expect(filasDeAperturasConTrade(undefined)).toHaveLength(4)
  })
})
