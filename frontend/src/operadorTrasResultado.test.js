import { describe, expect, it } from 'vitest'

import {
  filasCambioTrasPerder,
  filasTrasResultado,
  hayPares,
  textoWinrate,
  winrateCsv,
} from './operadorTrasResultado.js'

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

describe('filasCambioTrasPerder', () => {
  const cambio = (side, desde, hacia, rounds, winrate) => ({
    side,
    from_operator: desde,
    to_operator: hacia,
    rounds,
    decided: rounds,
    won: 0,
    winrate,
  })
  const data = {
    switch_min_rounds: 5,
    switches: [
      cambio('Attack', 'Ash', 'Thermite', 5, 60),
      cambio('Attack', 'Ash', 'Sledge', 4, 25),
      cambio('Defense', 'Mute', 'Jäger', 2, null),
    ],
  }

  it('sin switches no hay filas', () => {
    expect(filasCambioTrasPerder(undefined)).toEqual([])
    expect(filasCambioTrasPerder({ pairs: 3 })).toEqual([])
    expect(filasCambioTrasPerder({ switches: [] })).toEqual([])
  })

  it('sin lado salen los dos, con el lado en español', () => {
    const filas = filasCambioTrasPerder(data)
    expect(filas.map((f) => [f.lado, f.desde, f.hacia, f.rondas, f.winrate])).toEqual([
      ['Ataque', 'Ash', 'Thermite', 5, 60],
      ['Ataque', 'Ash', 'Sledge', 4, 25],
      ['Defensa', 'Mute', 'Jäger', 2, null],
    ])
    expect(new Set(filas.map((f) => f.clave)).size).toBe(3)
  })

  it('con lado sale solo ese', () => {
    expect(filasCambioTrasPerder(data, 'Defense').map((f) => f.desde)).toEqual(['Mute'])
    expect(filasCambioTrasPerder(data, 'Attack')).toHaveLength(2)
  })

  it('marca pocas rondas debajo del minimo por par y no en el minimo', () => {
    const [cinco, cuatro] = filasCambioTrasPerder(data, 'Attack')
    expect(cinco.poca).toBe(false)
    expect(cuatro.poca).toBe(true)
  })
})
