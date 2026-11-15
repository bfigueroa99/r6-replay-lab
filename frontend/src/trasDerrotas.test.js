/** Tests de la tabla "Después de perder seguido" de Tendencias. */

import { describe, expect, it } from 'vitest'

import { PARTIDAS_CORTE } from './prorrogaPorLado.js'
import { conPocasPartidas, filasTrasDerrotas } from './trasDerrotas.js'

const fila = (streak, matches, decided = matches) => ({
  streak,
  label: streak === 3 ? '3+' : String(streak),
  matches,
  decided,
  wins: 0,
  losses: decided,
  winrate: decided ? 0 : null,
})

const cuatro = (...partidas) => partidas.map((n, i) => fila(i, n))

describe('filasTrasDerrotas', () => {
  it('sin datos no hay tabla', () => {
    expect(filasTrasDerrotas(undefined)).toEqual([])
    expect(filasTrasDerrotas([])).toEqual([])
  })

  it('cuatro filas en cero no son una tabla de ceros', () => {
    expect(filasTrasDerrotas(cuatro(0, 0, 0, 0))).toEqual([])
  })

  it('pone el tramo de cada fila, en orden de racha, y deja el resto', () => {
    const filas = filasTrasDerrotas([fila(3, 1), fila(0, 5), fila(2, 0), fila(1, 2)])
    expect(filas.map((f) => f.tramo)).toEqual([
      'Sin derrotas antes',
      'Tras 1 derrota',
      'Tras 2 derrotas',
      'Tras 3 o más',
    ])
    expect(filas[0]).toMatchObject({ streak: 0, matches: 5, decided: 5 })
  })
})

describe('conPocasPartidas', () => {
  it('avisa con una fila de 1 a 9 partidas decididas', () => {
    expect(conPocasPartidas(cuatro(20, 20, 20, 1))).toBe(true)
    expect(conPocasPartidas(cuatro(20, PARTIDAS_CORTE - 1, 20, 20))).toBe(true)
  })

  it('no avisa por una fila sin partidas ni con todas sobre el corte', () => {
    expect(conPocasPartidas(cuatro(20, 20, PARTIDAS_CORTE, 0))).toBe(false)
    expect(conPocasPartidas(undefined)).toBe(false)
  })

  it('mira las decididas y no las jugadas', () => {
    expect(conPocasPartidas([fila(0, 20, 5)])).toBe(true)
  })
})
