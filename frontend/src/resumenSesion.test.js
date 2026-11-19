import { describe, expect, it } from 'vitest'
import { celdaPartidaDeSesion, textoResumenSesion } from './resumenSesion.js'

const completa = {
  start: '2026-08-01T20:00:00',
  hours: 2.5,
  matches: 3,
  wins: 1,
  losses: 1,
  undecided: 1,
  winrate: 57.1,
  kd: 1.2,
  rating: 1.05,
  best_match: { id: 1, map: 'Bank', score: '4-3', won: true, rating: 1.4 },
  worst_match: { id: 2, map: 'Border', score: '2-4', won: false, rating: 0.8 },
}

describe('textoResumenSesion', () => {
  it('arma las cinco lineas de una sesion completa', () => {
    expect(textoResumenSesion(completa)).toBe(
      [
        'Sesión del 2026-08-01 20:00 · 2.5 h',
        '3 partidas: 1G 1P 1 sin resultado',
        'Rondas ganadas 57% · K/D 1.20 · rating 1.05',
        'Mejor partida: Bank · 4-3 · rating 1.40',
        'Peor partida: Border · 2-4 · rating 0.80',
      ].join('\n'),
    )
  })

  it('una sesion de una partida va en singular, sin duracion, sin extremos ni "sin resultado"', () => {
    const una = { ...completa, hours: 0, matches: 1, wins: 1, losses: 0, undecided: 0, best_match: null, worst_match: null }
    expect(textoResumenSesion(una)).toBe(
      ['Sesión del 2026-08-01 20:00', '1 partida: 1G 0P', 'Rondas ganadas 57% · K/D 1.20 · rating 1.05'].join('\n'),
    )
  })

  it('las metricas nulas salen como raya', () => {
    const nula = { ...completa, winrate: null, kd: null, rating: undefined, worst_match: null }
    const lineas = textoResumenSesion(nula).split('\n')
    expect(lineas[2]).toBe('Rondas ganadas — · K/D — · rating —')
    expect(lineas).toHaveLength(4)
    expect(lineas[3]).toBe('Mejor partida: Bank · 4-3 · rating 1.40')
  })
})

describe('celdaPartidaDeSesion', () => {
  it('celdaPartidaDeSesion da texto e id de la partida', () => {
    expect(celdaPartidaDeSesion(completa.best_match)).toEqual({ id: 1, texto: 'Bank · 4-3 · 1.40' })
  })

  it('celdaPartidaDeSesion sin partida da null', () => {
    expect(celdaPartidaDeSesion(null)).toBeNull()
    expect(celdaPartidaDeSesion(undefined)).toBeNull()
  })

  it('celdaPartidaDeSesion con rating nulo muestra guion', () => {
    expect(celdaPartidaDeSesion({ id: 7, map: 'Kafe', score: '3-3', rating: null })).toEqual({
      id: 7,
      texto: 'Kafe · 3-3 · —',
    })
  })
})
