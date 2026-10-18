/** Tests de las filas del panel "Solo, en dúo o en stack". */

import { describe, expect, it } from 'vitest'

import { etiquetaGrupo, filasDeGrupo, textoHabituales } from './grupo.js'

const fila = (group, regulars, matches = 0) => ({ group, regulars, matches, match_winrate: null })

describe('etiquetaGrupo', () => {
  it('nombra los cuatro grupos y deja pasar uno desconocido', () => {
    expect(['solo', 'duo', 'trio', 'stack'].map(etiquetaGrupo)).toEqual(['Solo', 'Dúo', 'Trío', 'Stack'])
    expect(etiquetaGrupo('quinteto')).toBe('quinteto')
  })
})

describe('filasDeGrupo', () => {
  it('conserva las cuatro filas en el orden del backend aunque esten en cero', () => {
    const filas = filasDeGrupo({
      rows: [fila('solo', 0), fila('duo', 1), fila('trio', 2), fila('stack', 3, 29)],
    })
    expect(filas.map((f) => f.etiqueta)).toEqual(['Solo', 'Dúo', 'Trío', 'Stack'])
    expect(filas.map((f) => f.orden)).toEqual([0, 1, 2, 3])
    expect(filas.map((f) => f.habituales)).toEqual([0, 1, 2, '3 o más'])
    expect(filas[3].matches).toBe(29)
  })

  it('una respuesta ausente devuelve una lista vacia', () => {
    expect(filasDeGrupo(undefined)).toEqual([])
    expect(filasDeGrupo({})).toEqual([])
  })
})

describe('textoHabituales', () => {
  it('lista los habituales o avisa que no hay ninguno', () => {
    expect(textoHabituales({ regulars: [{ username: 'Chamo' }, { username: 'Seba' }] }))
      .toBe('Habituales: Chamo, Seba.')
    expect(textoHabituales({ regulars: [], min_matches: 7 }))
      .toBe('Ningún compañero llega a 7 partidas contigo: todo cae en Solo.')
    expect(textoHabituales(undefined)).toContain('5 partidas')
  })
})
