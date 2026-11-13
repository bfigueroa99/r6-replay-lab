import { describe, expect, it } from 'vitest'

import { filasClutchCompaneros } from './clutchCompaneros.js'

const data = {
  min_attempts: 5,
  me: { attempts: 6, won: 3, pct: 50, low_sample: false },
  rows: [
    { player_id: 7, username: 'Seba', attempts: 8, won: 2, pct: 25, low_sample: false },
    { player_id: 9, username: 'Nico', attempts: 3, won: 3, pct: 100, low_sample: true },
  ],
}

describe('filasClutchCompaneros', () => {
  it('sin datos o sin compañeros no da filas', () => {
    expect(filasClutchCompaneros(undefined)).toEqual([])
    expect(filasClutchCompaneros({ ...data, rows: [] })).toEqual([])
  })

  it('pone tu fila primero y despues las de la API en su orden', () => {
    const filas = filasClutchCompaneros(data)
    expect(filas.map((f) => f.nombre)).toEqual(['Tú', 'Seba', 'Nico'])
    expect(filas.map((f) => f.orden)).toEqual([0, 1, 2])
    expect(filas[0]).toMatchObject({ clave: 'yo', esYo: true, attempts: 6, won: 3, pct: 50 })
    expect(filas[1]).toMatchObject({ clave: 7, playerId: 7, esYo: false, attempts: 8, won: 2, pct: 25 })
  })

  it('pasa la marca de muestra chica tal cual', () => {
    expect(filasClutchCompaneros(data).map((f) => f.low_sample)).toEqual([false, false, true])
  })
})
