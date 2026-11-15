import { describe, expect, it } from 'vitest'

import { ETIQUETAS_GRUPO, avisoPocaMuestra, filasDeEstados, filasDeGrupos, hayMuertes, notaSinFeed } from './estadoAlMorir.js'

describe('estadoAlMorir', () => {
  it('etiqueta los tres grupos en orden', () => {
    const data = {
      groups: [
        { group: 'ahead', rounds: 3 },
        { group: 'even', rounds: 0 },
        { group: 'behind', rounds: 1 },
      ],
    }
    expect(filasDeGrupos(data).map((f) => f.label)).toEqual(['Con ventaja', 'En paridad', 'En desventaja'])
    expect(ETIQUETAS_GRUPO.behind).toBe('En desventaja')
    expect(filasDeGrupos(data).map((f) => f.orden)).toEqual([0, 1, 2])
    expect(filasDeGrupos(null)).toEqual([])
  })

  it('los estados conservan el orden de la API', () => {
    const data = { states: [{ state: '5v4' }, { state: '5v5' }, { state: '4v5' }] }
    expect(filasDeEstados(data).map((f) => [f.state, f.orden])).toEqual([['5v4', 0], ['5v5', 1], ['4v5', 2]])
    expect(filasDeEstados({})).toEqual([])
  })

  it('la nota de muertes sin feed solo sale si hay alguna', () => {
    expect(notaSinFeed(0)).toBeNull()
    expect(notaSinFeed(undefined)).toBeNull()
    expect(notaSinFeed(1)).toBe('1 muerte no se puede ubicar en el feed (sin evento o después de irte) y no entra.')
    expect(notaSinFeed(4)).toBe('4 muertes no se pueden ubicar en el feed (sin evento o después de irte) y no entran.')
  })

  it('avisa con 29 muertes en una fila y no con 30', () => {
    expect(avisoPocaMuestra([{ rounds: 29 }, { rounds: 40 }])).toBe(true)
    expect(avisoPocaMuestra([{ rounds: 30 }, { rounds: 0 }])).toBe(false)
  })

  it('sin muertes con estado no hay tabla', () => {
    expect(hayMuertes(null)).toBe(false)
    expect(hayMuertes({ deaths: 0 })).toBe(false)
    expect(hayMuertes({ deaths: 2 })).toBe(true)
  })
})
