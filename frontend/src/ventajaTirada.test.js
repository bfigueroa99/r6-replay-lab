import { describe, expect, it } from 'vitest'

import { indiceDeAncla } from './navegacionRondas.js'
import { enlaceDeRonda, filasDeGrupos, filasDeLados, hayVentajas } from './ventajaTirada.js'

describe('hayVentajas', () => {
  it('sin datos o sin rondas con ventaja no hay', () => {
    expect(hayVentajas(undefined)).toBe(false)
    expect(hayVentajas({ rounds: 0 })).toBe(false)
  })

  it('con alguna ronda con ventaja hay', () => {
    expect(hayVentajas({ rounds: 3 })).toBe(true)
  })
})

describe('filasDeGrupos', () => {
  it('etiqueta los grupos y guarda el orden de la API', () => {
    const filas = filasDeGrupos({ groups: [{ group: 'one', rounds: 4 }, { group: 'two_plus', rounds: 1 }] })
    expect(filas.map((f) => [f.label, f.orden])).toEqual([
      ['Con uno más', 0],
      ['Con dos o más', 1],
    ])
  })

  it('sin datos no hay filas', () => {
    expect(filasDeGrupos(null)).toEqual([])
  })
})

describe('filasDeLados', () => {
  it('pone el lado en castellano', () => {
    const filas = filasDeLados({ sides: [{ side: 'Attack' }, { side: 'Defense' }] })
    expect(filas.map((f) => f.label)).toEqual(['Ataque', 'Defensa'])
  })
})

describe('enlaceDeRonda', () => {
  it('abre la partida en la ronda que lee el ancla', () => {
    const href = enlaceDeRonda({ match_id: 7, round: 3 })
    expect(href).toBe('/partidas/7#ronda-3')
    const hash = href.slice(href.indexOf('#'))
    expect(indiceDeAncla(hash, [{ number: 0 }, { number: 1 }, { number: 2 }])).toBe(2)
  })
})
