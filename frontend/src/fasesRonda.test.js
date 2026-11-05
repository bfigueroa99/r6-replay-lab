/** Tests de las fases de la ronda del detalle de partida. */

import { describe, expect, it } from 'vitest'

import { filasDeFases, hayBajas, notaDeFases } from './fasesRonda.js'

const fila = (key, mine, rival, ahead = 0, aheadWon = 0, behind = 0, behindWon = 0) => ({
  key,
  label: key,
  mine,
  rival,
  rounds_ahead: ahead,
  rounds_ahead_won: aheadWon,
  rounds_behind: behind,
  rounds_behind_won: behindWon,
})

const fases = (rows, extra = {}) => ({
  rows,
  untimed_kills: 0,
  unknown_team_kills: 0,
  teamkills: 0,
  ...extra,
})

describe('filasDeFases', () => {
  it('sin phases devuelve una lista vacia', () => {
    expect(filasDeFases(undefined)).toEqual([])
    expect(filasDeFases({})).toEqual([])
  })

  it('arma el texto de rondas dominadas y ganadas', () => {
    const [temprano] = filasDeFases(fases([fila('temprano', 5, 2, 3, 2, 1, 0)]))
    expect(temprano.ganadasAdelante).toBe('2 de 3')
    expect(temprano.ganadasAtras).toBe('0 de 1')
    expect(temprano.mejor).toBe('mine')
  })

  it('con cero rondas dominadas muestra un guion', () => {
    const [medio] = filasDeFases(fases([fila('medio', 0, 1)]))
    expect(medio.ganadasAdelante).toBe('—')
    expect(medio.mejor).toBe('rival')
  })

  it('en empate no marca a nadie', () => {
    const [tarde] = filasDeFases(fases([fila('tarde', 2, 2)]))
    expect(tarde.mejor).toBeNull()
  })
})

describe('hayBajas', () => {
  it('es falso con todas las fases en cero', () => {
    expect(hayBajas(fases([fila('temprano', 0, 0), fila('medio', 0, 0)]))).toBe(false)
    expect(hayBajas(fases([fila('temprano', 0, 0), fila('medio', 0, 1)]))).toBe(true)
  })
})

describe('notaDeFases', () => {
  it('no hay nota si todas las bajas entran en una fase', () => {
    expect(notaDeFases(fases([], { teamkills: 2 }))).toBeNull()
  })

  it('cuenta las bajas sin reloj y sin fila', () => {
    expect(notaDeFases(fases([], { untimed_kills: 2, unknown_team_kills: 1 }))).toBe(
      '3 bajas sin reloj o de un jugador sin fila quedan fuera de las fases.',
    )
    expect(notaDeFases(fases([], { untimed_kills: 1 }))).toBe(
      '1 baja sin reloj o de un jugador sin fila queda fuera de las fases.',
    )
  })
})
