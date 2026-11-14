import { describe, expect, it } from 'vitest'
import { pestanasDeRondas } from './prorrogaDetalle.js'

const ronda = (number, overtime = false) => ({ number, overtime })

describe('pestanasDeRondas', () => {
  it('sin prorroga no hay corte', () => {
    const p = pestanasDeRondas([ronda(0), ronda(1), ronda(2)])
    expect(p.map((x) => x.corteAntes)).toEqual([false, false, false])
    expect(p.map((x) => x.prorroga)).toEqual([false, false, false])
  })

  it('el corte va una sola vez, antes de la primera de prorroga', () => {
    const p = pestanasDeRondas([ronda(0), ronda(1), ronda(2, true), ronda(3, true)])
    expect(p.map((x) => x.corteAntes)).toEqual([false, false, true, false])
  })

  it('cada ronda de prorroga queda marcada y las normales no', () => {
    const p = pestanasDeRondas([ronda(0), ronda(1, true), ronda(2, true)])
    expect(p.map((x) => x.prorroga)).toEqual([false, true, true])
  })

  it('sin rondas devuelve lista vacia', () => {
    expect(pestanasDeRondas([])).toEqual([])
    expect(pestanasDeRondas(null)).toEqual([])
    expect(pestanasDeRondas(undefined)).toEqual([])
  })

  it('un overtime ausente cuenta como ronda normal', () => {
    expect(pestanasDeRondas([{ number: 0 }])).toEqual([{ prorroga: false, corteAntes: false }])
  })
})
