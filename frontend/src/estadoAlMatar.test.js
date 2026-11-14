import { describe, expect, it } from 'vitest'

import {
  avisoPocaMuestra,
  filasDeEstados,
  filasDeGrupos,
  hayBajas,
  notaPostMortem,
  notaSinFeed,
} from './estadoAlMatar.js'

describe('estadoAlMatar', () => {
  it('etiqueta los tres grupos con las etiquetas de Estado al morir y en orden', () => {
    const data = {
      groups: [
        { group: 'ahead', kills: 3, rounds: 2 },
        { group: 'even', kills: 0, rounds: 0 },
        { group: 'behind', kills: 1, rounds: 1 },
      ],
    }
    expect(filasDeGrupos(data).map((f) => f.label)).toEqual(['Con ventaja', 'En paridad', 'En desventaja'])
    expect(filasDeGrupos(data).map((f) => f.orden)).toEqual([0, 1, 2])
    expect(filasDeGrupos(null)).toEqual([])
  })

  it('los estados conservan el orden de la API', () => {
    const data = { states: [{ state: '5v3' }, { state: '5v5' }, { state: '4v5' }] }
    expect(filasDeEstados(data).map((f) => [f.state, f.orden])).toEqual([['5v3', 0], ['5v5', 1], ['4v5', 2]])
    expect(filasDeEstados({})).toEqual([])
  })

  it('sin bajas con estado no hay tabla', () => {
    expect(hayBajas(null)).toBe(false)
    expect(hayBajas({ kills: 0 })).toBe(false)
    expect(hayBajas({ kills: 2 })).toBe(true)
  })

  it('la nota de bajas sin feed solo sale si hay alguna, en singular y plural', () => {
    expect(notaSinFeed(0)).toBeNull()
    expect(notaSinFeed(undefined)).toBeNull()
    expect(notaSinFeed(1)).toBe('1 baja no se puede ubicar en el feed y no entra.')
    expect(notaSinFeed(3)).toBe('3 bajas no se pueden ubicar en el feed y no entran.')
  })

  it('la nota de bajas despues de caer solo sale si hay alguna, en singular y plural', () => {
    expect(notaPostMortem(0)).toBeNull()
    expect(notaPostMortem(undefined)).toBeNull()
    expect(notaPostMortem(1)).toBe(
      '1 baja llegó al feed después de tu caída (trampa, gadget o intercambio del mismo instante): no tiene estado tuyo y no entra.',
    )
    expect(notaPostMortem(2)).toBe(
      '2 bajas llegaron al feed después de tu caída (trampas, gadgets o intercambios del mismo instante): no tienen estado tuyo y no entran.',
    )
  })

  it('el aviso de muestra va sobre rondas: avisa con 29 y no con 0 ni con 30', () => {
    expect(avisoPocaMuestra([{ kills: 80, rounds: 29 }])).toBe(true)
    expect(avisoPocaMuestra([{ kills: 5, rounds: 30 }, { kills: 0, rounds: 0 }])).toBe(false)
  })
})
