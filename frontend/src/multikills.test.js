/** Tests del texto de multikills por tamano. */

import { describe, expect, it } from 'vitest'

import { detalleMultikills, partesMultikills, rondasConMultikill, textoMultikills } from './multikills.js'

describe('textoMultikills', () => {
  it('arma el texto solo con los tamanos mayores que cero, de menor a mayor', () => {
    expect(textoMultikills({ k2: 2, k3: 1, k4: 0, aces: 1 })).toBe('2×2K · 1×3K · 1×ACE')
    expect(textoMultikills({ aces: 3, k4: 1 })).toBe('1×4K · 3×ACE')
  })

  it('sin multikills devuelve texto vacio', () => {
    expect(textoMultikills({ k2: 0, k3: 0, k4: 0, aces: 0 })).toBe('')
  })

  it('una fila ausente o sin las claves no rompe', () => {
    expect(textoMultikills(undefined)).toBe('')
    expect(textoMultikills({})).toBe('')
    expect(partesMultikills(null)).toEqual([])
    expect(detalleMultikills(undefined)).toBe('')
  })
})

describe('detalleMultikills', () => {
  it('el detalle usa singular y plural', () => {
    expect(detalleMultikills({ k2: 2, aces: 1 })).toBe('2 rondas de 2 bajas · 1 de 5 o más')
    expect(detalleMultikills({ k3: 1 })).toBe('1 ronda de 3 bajas')
  })
})

describe('rondasConMultikill', () => {
  it('rondasConMultikill usa multikill_rounds y si falta suma los cuatro', () => {
    expect(rondasConMultikill({ multikill_rounds: 7, k2: 1 })).toBe(7)
    expect(rondasConMultikill({ k2: 2, k3: 1, aces: 1 })).toBe(4)
    expect(rondasConMultikill(undefined)).toBe(0)
  })
})
