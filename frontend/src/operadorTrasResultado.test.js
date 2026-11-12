import { describe, expect, it } from 'vitest'

import { filasTrasResultado, hayPares, textoWinrate, winrateCsv } from './operadorTrasResultado.js'

const celda = (rounds, winrate = null) => ({ rounds, decided: rounds, won: 0, winrate })
const bloque = (perderRep, perderCam, ganarRep, ganarCam) => ({
  after_loss: { repeat: perderRep, switch: perderCam },
  after_win: { repeat: ganarRep, switch: ganarCam },
})

const DATA = {
  min_rounds: 12,
  pairs: 40,
  total: bloque(celda(12, 50), celda(8, 25), celda(0), celda(20, 60)),
  sides: {
    Attack: bloque(celda(12, 50), celda(8, 25), celda(0), celda(0)),
    Defense: bloque(celda(0), celda(0), celda(0), celda(20, 60)),
  },
}

describe('hayPares', () => {
  it('sin datos o sin pares es false', () => {
    expect(hayPares(null)).toBe(false)
    expect(hayPares({ pairs: 0 })).toBe(false)
    expect(hayPares(DATA)).toBe(true)
  })
})

describe('filasTrasResultado', () => {
  it('sin pares no hay filas', () => {
    expect(filasTrasResultado(undefined, '')).toEqual([])
    expect(filasTrasResultado({ ...DATA, pairs: 0 }, '')).toEqual([])
  })

  it('sin lado salen Total, Ataque y Defensa en ese orden y se omiten las filas vacias', () => {
    const filas = filasTrasResultado(DATA, '')
    expect(filas.map((f) => `${f.lado} ${f.tras}`)).toEqual([
      'Total Tras perder',
      'Total Tras ganar',
      'Ataque Tras perder',
      'Defensa Tras ganar',
    ])
    expect(filas.map((f) => f.orden)).toEqual([0, 1, 2, 3])
  })

  it('con lado sale solo ese', () => {
    const filas = filasTrasResultado(DATA, 'Defense')
    expect(filas).toHaveLength(1)
    expect(filas[0]).toMatchObject({ lado: 'Defensa', tras: 'Tras ganar', switch_rounds: 20, switch_winrate: 60 })
  })

  it('marca pocas rondas debajo del minimo y no en el minimo', () => {
    const [fila] = filasTrasResultado(DATA, 'Attack')
    expect(fila.repeat_poca).toBe(false)
    expect(fila.switch_poca).toBe(true)
  })
})

describe('textoWinrate y winrateCsv', () => {
  it('redondea, avisa la muestra chica y deja guion sin dato', () => {
    expect(textoWinrate(66.7, false)).toBe('67%')
    expect(textoWinrate(25, true)).toBe('25% · pocas rondas')
    expect(textoWinrate(null, true)).toBe('—')
  })

  it('el CSV usa coma decimal y vacio sin dato', () => {
    expect(winrateCsv(33.3)).toBe('33,3')
    expect(winrateCsv(null)).toBe('')
  })
})
