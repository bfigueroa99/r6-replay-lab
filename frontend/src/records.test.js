/** Tests de las filas del panel "Tus records" del Resumen. */

import { describe, expect, it } from 'vitest'

import { filasDeRecords } from './records.js'

const partida = (extra) => ({
  match_id: 7,
  played_at: '2026-09-02T21:10:00',
  map: 'Oregon',
  rounds: 9,
  ...extra,
})

const RECORDS = {
  best_day: { day: '2026-09-02', value: 75, rounds: 20, rounds_won: 15 },
  biggest_clutch: { ...partida({ value: 3, round_label: 'R4' }), rounds: undefined },
  most_kills_round: { ...partida({ value: 4, round_label: 'R2' }), rounds: undefined },
  most_kills_match: partida({ value: 1 }),
  best_match_rating: partida({ value: 1.625 }),
}

describe('filasDeRecords', () => {
  it('sale en orden fijo aunque el backend mande otro', () => {
    expect(filasDeRecords(RECORDS).map((f) => f.clave)).toEqual([
      'best_match_rating',
      'most_kills_match',
      'most_kills_round',
      'biggest_clutch',
      'best_day',
    ])
  })

  it('deja afuera los records nulos y aguanta una respuesta sin records', () => {
    const filas = filasDeRecords({ ...RECORDS, biggest_clutch: null, best_day: null })
    expect(filas.map((f) => f.clave)).not.toContain('biggest_clutch')
    expect(filas).toHaveLength(3)
    expect(filasDeRecords(undefined)).toEqual([])
  })

  it('el mejor dia no enlaza a ninguna partida y el resto si', () => {
    const filas = filasDeRecords(RECORDS)
    expect(filas.find((f) => f.clave === 'best_day').href).toBeNull()
    expect(filas.find((f) => f.clave === 'most_kills_round').href).toBe('/partidas/7')
  })

  it('formatea cada valor', () => {
    const valores = Object.fromEntries(filasDeRecords(RECORDS).map((f) => [f.clave, f.valor]))
    expect(valores).toEqual({
      best_match_rating: '1.63 de rating',
      most_kills_match: '1 baja',
      most_kills_round: '4 bajas',
      biggest_clutch: '1v3',
      best_day: '75 % de rondas ganadas',
    })
  })

  it('el detalle dice la ronda, el mapa y la fecha', () => {
    const filas = Object.fromEntries(filasDeRecords(RECORDS).map((f) => [f.clave, f.detalle]))
    expect(filas.most_kills_round).toBe('ronda R2 · Oregon · 2026-09-02')
    expect(filas.most_kills_match).toBe('Oregon · 2026-09-02 · 9 rondas')
    expect(filas.best_day).toBe('2026-09-02 · 15 de 20 rondas')
  })
})
