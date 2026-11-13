import { describe, expect, it } from 'vitest'

import { filasRepetirSpawn, hayParesSpawn, textoParesSpawn } from './repetirSpawn.js'

describe('repetirSpawn', () => {
  it('sin pares no hay panel', () => {
    expect(hayParesSpawn(null)).toBe(false)
    expect(hayParesSpawn({ pairs: 0 })).toBe(false)
    expect(hayParesSpawn({ pairs: 2 })).toBe(true)
  })

  it('dos filas en orden fijo aunque falte un bloque', () => {
    const filas = filasRepetirSpawn({
      min_rounds: 8,
      after_win: { repeat: { rounds: 9, winrate: 60 }, switch: { rounds: 3, winrate: 0 } },
    })
    expect(filas.map((f) => f.tras)).toEqual(['after_loss', 'after_win'])
    expect(filas[0]).toMatchObject({
      tramo: 'Tras perder', orden: 0, repeat_rounds: 0, repeat_winrate: null,
      switch_rounds: 0, switch_winrate: null,
    })
    expect(filas[1]).toMatchObject({
      tramo: 'Tras ganar', orden: 1, repeat_rounds: 9, repeat_winrate: 60,
      switch_rounds: 3, switch_winrate: 0,
    })
  })

  it('marca pocas rondas debajo del minimo y no en el minimo', () => {
    const [tras] = filasRepetirSpawn({
      min_rounds: 8,
      after_loss: { repeat: { rounds: 8, winrate: 50 }, switch: { rounds: 7, winrate: 100 } },
    })
    expect(tras.repeat_poca).toBe(false)
    expect(tras.switch_poca).toBe(true)
  })

  it('texto de pares en singular y plural', () => {
    expect(textoParesSpawn(1)).toBe('1 par de rondas de ataque seguidas')
    expect(textoParesSpawn(12)).toBe('12 pares de rondas de ataque seguidas')
  })
})
