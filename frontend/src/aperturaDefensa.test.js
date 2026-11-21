import { describe, expect, it } from 'vitest'

import {
  filasAperturaDefensa,
  hayAperturas,
  textoAperturas,
  textoSinApertura,
  textoWinrateApertura,
} from './aperturaDefensa.js'

const sitio = (site, opens, extra = {}) => ({
  site,
  opens,
  opens_decided: opens,
  opens_won: 0,
  opens_winrate: opens ? 0 : null,
  opens_share: null,
  rest_rounds: 2,
  rest_decided: 2,
  rest_won: 1,
  rest_winrate: 50,
  ...extra,
})

const datos = {
  min_matches: 5,
  matches: 9,
  skipped: 1,
  maps: [
    { map: 'Bank', slug: 'bank', map_id: 0, opens_total: 6, sites: [sitio('B Lockers', 5, { opens_share: 83.3 }), sitio('A Vault', 1, { opens_share: 16.7 })] },
    { map: 'Border', slug: 'border', map_id: 0, opens_total: 3, sites: [sitio('B Armory', 3, { opens_share: 100 }), sitio('A Workshop', 0, { opens_share: 0 })] },
  ],
}

describe('aperturaDefensa', () => {
  it('sin partidas con apertura no hay nada que mostrar', () => {
    expect(hayAperturas(undefined)).toBe(false)
    expect(hayAperturas({ matches: 0, maps: [] })).toBe(false)
    expect(hayAperturas(datos)).toBe(true)
    expect(filasAperturaDefensa(undefined)).toEqual([])
  })

  it('una fila por mapa y sitio, en el orden de la API', () => {
    const filas = filasAperturaDefensa(datos)
    expect(filas.map((f) => [f.map, f.site, f.orden])).toEqual([
      ['Bank', 'B Lockers', 0],
      ['Bank', 'A Vault', 1],
      ['Border', 'B Armory', 2],
      ['Border', 'A Workshop', 3],
    ])
    expect(new Set(filas.map((f) => f.clave)).size).toBe(4)
    expect(filas[0]).toMatchObject({ opens: 5, opens_share: 83.3, rest_rounds: 2, rest_winrate: 50 })
  })

  it('marca pocas partidas por debajo del corte, sin ocultar el winrate', () => {
    const filas = filasAperturaDefensa(datos)
    expect(filas.map((f) => f.poca)).toEqual([false, true, true, true])
    expect(textoWinrateApertura(0, false)).toBe('0%')
    expect(textoWinrateApertura(66.7, true)).toBe('67% · pocas partidas')
    expect(textoWinrateApertura(null, true)).toBe('—')
  })

  it('cuenta las partidas en singular y plural', () => {
    expect(textoAperturas(1)).toBe('1 partida con apertura de defensa')
    expect(textoAperturas(29)).toBe('29 partidas con apertura de defensa')
    expect(textoSinApertura(0)).toBeNull()
    expect(textoSinApertura(1)).toBe(
      '1 partida con defensa no entra: falta una ronda antes de su primera defensa, o le falta lado o sitio.',
    )
    expect(textoSinApertura(3)).toBe(
      '3 partidas con defensa no entran: falta una ronda antes de su primera defensa, o les falta lado o sitio.',
    )
  })
})
