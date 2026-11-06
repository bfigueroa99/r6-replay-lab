/** Tests de la tabla "Lado inicial por mapa" de Tendencias. */

import { describe, expect, it } from 'vitest'

import { MIN_PARTIDAS_LADO, filasLadoInicialMapa, textoVeredicto } from './ladoInicialMapa.js'

const celda = (matches, winrate) => ({ matches, decided: matches, wins: 0, winrate })

describe('filasLadoInicialMapa', () => {
  it('aplana una fila completa con los dos lados', () => {
    const [fila] = filasLadoInicialMapa([
      {
        slug: 'bank', map_id: 3, map: 'Bank', matches: 9,
        attack: celda(4, 75), defense: celda(5, 20),
        delta: 55, margin: 60.2, verdict: 'ruido',
      },
    ])
    expect(fila).toEqual({
      slug: 'bank', map_id: 3, map: 'Bank', matches: 9,
      attack_matches: 4, attack_winrate: 75,
      defense_matches: 5, defense_winrate: 20,
      delta: 55, margin: 60.2, verdict: 'ruido', veredicto: 'Dentro del ruido',
    })
  })

  it('deja en null el lado que no llego al minimo y dice poca muestra', () => {
    const [fila] = filasLadoInicialMapa([
      {
        slug: 'oregon', map_id: 0, map: 'Oregon', matches: 4,
        attack: celda(4, 50), defense: celda(0, null),
        delta: null, margin: null, verdict: null,
      },
    ])
    expect(fila.defense_matches).toBe(0)
    expect(fila.defense_winrate).toBeNull()
    expect(fila.delta).toBeNull()
    expect(fila.veredicto).toBe('Poca muestra')
  })

  it('sin filas devuelve una lista vacia', () => {
    expect(filasLadoInicialMapa(undefined)).toEqual([])
    expect(filasLadoInicialMapa([])).toEqual([])
  })
})

describe('textoVeredicto', () => {
  it('nombra los cuatro veredictos', () => {
    expect(['ataque', 'defensa', 'ruido', null].map((verdict) => textoVeredicto({ verdict }))).toEqual([
      'Mejor arrancando en ataque',
      'Mejor arrancando en defensa',
      'Dentro del ruido',
      'Poca muestra',
    ])
  })

  it('un lado necesita tres partidas con resultado', () => {
    expect(MIN_PARTIDAS_LADO).toBe(3)
  })
})
