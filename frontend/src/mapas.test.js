/** Tests de las opciones del selector de mapa con sus versiones. */

import { describe, expect, it } from 'vitest'

import { opcionesDeMapa } from './mapas.js'

describe('opcionesDeMapa', () => {
  it('sin versiones solo sale el mapa', () => {
    expect(opcionesDeMapa([{ map_slug: 'kanal', map_name: 'Kanal', versions: [] }])).toEqual([
      { value: 'kanal', label: 'Kanal' },
    ])
  })

  it('con dos versiones salen debajo del mapa con su map_id como valor', () => {
    const opciones = opcionesDeMapa([
      {
        map_slug: 'consulate',
        map_name: 'Consulate',
        versions: [
          { map_id: 418126004176, label: 'Consulate (Y10)' },
          { map_id: 2609221242, label: 'Consulate (Y7)' },
        ],
      },
    ])
    expect(opciones.map((o) => o.value)).toEqual(['consulate', '418126004176', '2609221242'])
    expect(opciones[1].label.endsWith('Consulate (Y10)')).toBe(true)
    expect(opciones[1].label).not.toBe('Consulate (Y10)')
  })

  it('sin datos no revienta', () => {
    expect(opcionesDeMapa(undefined)).toEqual([])
  })
})
