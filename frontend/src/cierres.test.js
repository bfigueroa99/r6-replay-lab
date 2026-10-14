/** Tests de las filas del panel "Como se cierran tus rondas". */

import { describe, expect, it } from 'vitest'

import { filasDeCierre, hayCierres } from './cierres.js'

const fila = (side, extra = {}) => ({
  side,
  rounds: 10,
  won_elimination: 3,
  won_other: 1,
  lost_elimination: 2,
  lost_other: 2,
  unknown: 2,
  won_elimination_pct: 75,
  lost_elimination_pct: 50,
  ...extra,
})

describe('filasDeCierre', () => {
  it('etiqueta los lados en castellano y conserva el orden del backend', () => {
    const filas = filasDeCierre([fila('Attack'), fila('Defense')])
    expect(filas.map((f) => f.lado)).toEqual(['Ataque', 'Defensa'])
    expect(filas.map((f) => f.orden)).toEqual([0, 1])
  })

  it('el complemento sin eliminacion suma 100 con el de eliminacion', () => {
    const [ataque] = filasDeCierre([fila('Attack', { won_elimination_pct: 66.7 })])
    expect(ataque.won_other_pct).toBe(33.3)
    expect(ataque.won_elimination_pct + ataque.won_other_pct).toBeCloseTo(100)
    expect(ataque.lost_other_pct).toBe(50)
  })

  it('sin dato deja los porcentajes nulos y no inventa un 100', () => {
    const [vacia] = filasDeCierre([
      fila('Defense', { rounds: 0, won_elimination_pct: null, lost_elimination_pct: null }),
    ])
    expect(vacia.won_other_pct).toBeNull()
    expect(vacia.lost_other_pct).toBeNull()
  })

  it('un lado desconocido queda con su clave y una lista nula no rompe', () => {
    expect(filasDeCierre([fila('Spectator')])[0].lado).toBe('Spectator')
    expect(filasDeCierre(undefined)).toEqual([])
  })
})

describe('hayCierres', () => {
  it('es falso si los dos lados tienen 0 rondas o no hay filas', () => {
    expect(hayCierres([fila('Attack', { rounds: 0 }), fila('Defense', { rounds: 0 })])).toBe(false)
    expect(hayCierres(undefined)).toBe(false)
    expect(hayCierres([fila('Attack', { rounds: 0 }), fila('Defense', { rounds: 1 })])).toBe(true)
  })
})
