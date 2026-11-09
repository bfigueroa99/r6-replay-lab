/** Tests de la tira de rondas de Partidas (ficha 103). */

import { describe, expect, it } from 'vitest'

import { celdasDeTira, textoDeTira } from './tiraRondas.js'

const ronda = (number, won, side = 'Attack', overtime = false) => ({ number, won, side, overtime })

describe('celdasDeTira', () => {
  it('ganada perdida y sin ganador tienen clases distintas', () => {
    const celdas = celdasDeTira([ronda(0, true), ronda(1, false), ronda(2, null)])
    expect(celdas.map((c) => c.clase)).toEqual(['win', 'loss', 'nula'])
  })

  it('el titulo dice ronda lado y resultado', () => {
    const celdas = celdasDeTira([ronda(4, true, 'Attack'), ronda(5, false, 'Defense'), ronda(6, null, 'Defense')])
    expect(celdas.map((c) => c.titulo)).toEqual([
      'R5 · ataque · ganada',
      'R6 · defensa · perdida',
      'R7 · defensa · sin ganador claro',
    ])
    expect(celdas.map((c) => c.letra)).toEqual(['A', 'D', 'D'])
  })

  it('la prorroga se separa una sola vez', () => {
    const celdas = celdasDeTira([
      ronda(5, true),
      ronda(6, false),
      ronda(7, true, 'Defense', true),
      ronda(8, true, 'Attack', true),
    ])
    expect(celdas.map((c) => c.corteAntes)).toEqual([false, false, true, false])
    expect(celdas[2].titulo).toBe('R8 · defensa · ganada · prórroga')
    expect(celdas[1].titulo).toBe('R7 · ataque · perdida')
  })

  it('tira vacia o ausente no rompe', () => {
    expect(celdasDeTira([])).toEqual([])
    expect(celdasDeTira(undefined)).toEqual([])
    expect(celdasDeTira(null)).toEqual([])
    expect(textoDeTira(undefined)).toBe('')
  })

  it('lado desconocido se marca con signo de pregunta', () => {
    const [celda] = celdasDeTira([ronda(0, true, '')])
    expect(celda.letra).toBe('?')
    expect(celda.titulo).toBe('R1 · lado desconocido · ganada')
  })

  it('cada celda tiene una clave distinta aunque haya prorroga', () => {
    const celdas = celdasDeTira([ronda(0, true), ronda(1, false), ronda(2, true, 'Attack', true)])
    expect(new Set(celdas.map((c) => c.clave)).size).toBe(3)
  })
})

describe('textoDeTira', () => {
  it('exporta la secuencia legible con la prorroga y la ronda sin ganador', () => {
    const strip = [ronda(0, true), ronda(1, true), ronda(2, false), ronda(3, null), ronda(4, false, 'Defense', true), ronda(5, true, 'Attack', true)]
    expect(textoDeTira(strip)).toBe('G G P - | P G')
  })
})
