/** Tests de las filas del panel "Remontadas y derrumbes". */

import { describe, expect, it } from 'vitest'

import { etiquetaTramo, filasDeCambio, filasDePartidas } from './remontadas.js'

const tramo = (diff, matches = 0, wins = 0, winrate = null) => ({ diff, matches, wins, winrate })

describe('etiquetaTramo', () => {
  it('nombra los cinco tramos y deja pasar uno desconocido', () => {
    expect(['+2', '+1', '0', '-1', '-2'].map(etiquetaTramo)).toEqual([
      '+2 o más', '+1', 'Empatado', '-1', '-2 o menos',
    ])
    expect(etiquetaTramo('+7')).toBe('+7')
  })
})

describe('filasDeCambio', () => {
  it('conserva las cinco filas en el orden del backend aunque esten en cero', () => {
    const filas = filasDeCambio([tramo('+2'), tramo('+1'), tramo('0', 3, 2, 66.7), tramo('-1'), tramo('-2')])
    expect(filas.map((f) => f.tramo)).toEqual(['+2 o más', '+1', 'Empatado', '-1', '-2 o menos'])
    expect(filas.map((f) => f.orden)).toEqual([0, 1, 2, 3, 4])
    expect(filas[2].winrate).toBe(66.7)
    expect(filas[0].winrate).toBeNull()
  })

  it('sin datos devuelve una lista vacia', () => {
    expect(filasDeCambio(undefined)).toEqual([])
  })
})

describe('filasDePartidas', () => {
  const partida = { match_id: 7, map: 'Oregon', played_at: '2026-09-01T20:15:00+00:00', score: '4-3' }

  it('una remontada dice cuanto ibas abajo', () => {
    const [fila] = filasDePartidas([{ ...partida, max_deficit: 3 }], 'max_deficit')
    expect(fila.diferencia).toBe('Ibas -3')
    expect(fila.fecha).toBe('2026-09-01 20:15')
  })

  it('un derrumbe dice cuanto ibas arriba', () => {
    const [fila] = filasDePartidas([{ ...partida, max_lead: 2 }], 'max_lead')
    expect(fila.diferencia).toBe('Ibas +2')
  })

  it('sin lista devuelve una lista vacia', () => {
    expect(filasDePartidas(null, 'max_lead')).toEqual([])
  })
})
