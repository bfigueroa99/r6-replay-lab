import { describe, expect, it } from 'vitest'

import { avisoPuesto, statsDePuesto } from './puestoLobby.js'

const caso = (count, matches) => ({ count, matches, pct: matches ? (count / matches) * 100 : null })

const datos = (n = 12) => ({
  best_in_lobby: caso(3, n),
  best_in_team: caso(6, n - 1),
  last_in_lobby: caso(1, n),
})

describe('statsDePuesto', () => {
  it('da las tres filas en orden con su etiqueta y su muestra', () => {
    const filas = statsDePuesto(datos())
    expect(filas.map((f) => f.label)).toEqual([
      'Mejor de la partida',
      'Mejor de tu equipo',
      'Último de la partida',
    ])
    expect(filas.map((f) => f.sub)).toEqual(['3 de 12 partidas', '6 de 11 partidas', '1 de 12 partidas'])
    expect(filas[0].pct).toBe(25)
  })

  it('sin datos no da filas', () => {
    expect(statsDePuesto(undefined)).toEqual([])
    expect(statsDePuesto(null)).toEqual([])
  })

  it('sin partidas con otros jugadores no da filas', () => {
    expect(statsDePuesto({ best_in_lobby: caso(0, 0), best_in_team: caso(0, 0), last_in_lobby: caso(0, 0) })).toEqual([])
  })

  it('una sola partida dice partida en singular', () => {
    const una = { best_in_lobby: caso(1, 1), best_in_team: caso(0, 1), last_in_lobby: caso(0, 1) }
    expect(statsDePuesto(una)[0].sub).toBe('1 de 1 partida')
  })
})

describe('avisoPuesto', () => {
  it('avisa con menos de 10 partidas', () => {
    expect(avisoPuesto(datos(9))).toMatch(/Pocas partidas/)
  })

  it('no avisa con 10 o mas', () => {
    expect(avisoPuesto(datos(10))).toBeNull()
  })

  it('no avisa sin datos', () => {
    expect(avisoPuesto(undefined)).toBeNull()
  })
})
