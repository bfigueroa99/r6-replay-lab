/** Tests del selector y la tabla de modo de juego (ficha 100). */

import { describe, expect, it } from 'vitest'

import {
  filasPorModo,
  hayVariosModos,
  mostrarSelectorDeModo,
  nombreDeModo,
  opcionesDeModo,
} from './modoDeJuego.js'

describe('opcionesDeModo', () => {
  it('pone Todos primero y traduce los modos conocidos', () => {
    expect(opcionesDeModo(['Bomb', 'Hostage', 'SecureArea', 'QuickMatchBomb'])).toEqual([
      { value: '', label: 'Todos' },
      { value: 'Bomb', label: 'Bomba' },
      { value: 'Hostage', label: 'Rehén' },
      { value: 'SecureArea', label: 'Área segura' },
      { value: 'QuickMatchBomb', label: 'Bomba rápida' },
    ])
  })

  it('un modo desconocido sale tal cual', () => {
    expect(opcionesDeModo(['Unknown(9)'])[1]).toEqual({ value: 'Unknown(9)', label: 'Unknown(9)' })
  })

  it('saca vacios y repetidos', () => {
    expect(opcionesDeModo(['Bomb', '', null, 'Bomb'])).toEqual([
      { value: '', label: 'Todos' },
      { value: 'Bomb', label: 'Bomba' },
    ])
    expect(opcionesDeModo(undefined)).toEqual([{ value: '', label: 'Todos' }])
  })
})

describe('mostrarSelectorDeModo', () => {
  it('con un solo modo no aparece', () => {
    expect(mostrarSelectorDeModo(['Bomb'], '')).toBe(false)
    expect(mostrarSelectorDeModo(undefined, undefined)).toBe(false)
  })

  it('con dos modos aparece', () => {
    expect(mostrarSelectorDeModo(['Bomb', 'Hostage'], '')).toBe(true)
  })

  it('con un solo modo pero uno elegido aparece, para que se vea el filtro', () => {
    expect(mostrarSelectorDeModo(['Bomb'], 'Hostage')).toBe(true)
  })
})

describe('nombreDeModo y filas', () => {
  it('una partida sin modo se llama Sin modo', () => {
    expect(nombreDeModo('')).toBe('Sin modo')
    expect(nombreDeModo(null)).toBe('Sin modo')
  })

  it('filasPorModo agrega el nombre y hayVariosModos pide mas de una fila', () => {
    const filas = filasPorModo([{ gamemode: 'Bomb', matches: 3 }, { gamemode: '', matches: 1 }])
    expect(filas.map((f) => f.modo)).toEqual(['Bomba', 'Sin modo'])
    expect(filas[0].matches).toBe(3)
    expect(hayVariosModos(filas)).toBe(true)
    expect(hayVariosModos([{ gamemode: 'Bomb' }])).toBe(false)
    expect(hayVariosModos(undefined)).toBe(false)
  })
})
