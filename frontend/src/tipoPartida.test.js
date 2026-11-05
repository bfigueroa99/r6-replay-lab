/** Tests del selector de tipo de partida (ficha 77). */

import { describe, expect, it } from 'vitest'

import { qs } from './api.js'
import { conTipo, hayFiltros, opcionesDeTipo, tipoElegido } from './tipoPartida.js'

describe('opcionesDeTipo', () => {
  it('opciones de tipo arrancan con Todos y siguen el orden de la API', () => {
    expect(opcionesDeTipo(['Ranked', 'Unranked'])).toEqual([
      { value: '', label: 'Todos' },
      { value: 'Ranked', label: 'Ranked' },
      { value: 'Unranked', label: 'Unranked' },
    ])
  })

  it('opciones de tipo sin datos dejan solo Todos', () => {
    expect(opcionesDeTipo(undefined)).toEqual([{ value: '', label: 'Todos' }])
    expect(opcionesDeTipo(null)).toEqual([{ value: '', label: 'Todos' }])
    expect(opcionesDeTipo([])).toEqual([{ value: '', label: 'Todos' }])
  })

  it('opciones de tipo sacan vacios y repetidos', () => {
    expect(opcionesDeTipo(['Ranked', '', null, 'Ranked', 'Casual']).map((o) => o.value)).toEqual([
      '',
      'Ranked',
      'Casual',
    ])
  })
})

describe('tipoElegido y conTipo', () => {
  it('el tipo elegido sale de match_type', () => {
    expect(tipoElegido({ match_type: 'Unranked' })).toBe('Unranked')
    expect(tipoElegido({})).toBe('')
    expect(tipoElegido(undefined)).toBe('')
  })

  it('solo ranked viejo se lee como Ranked', () => {
    expect(tipoElegido({ ranked_only: true })).toBe('Ranked')
  })

  it('elegir un tipo apaga solo ranked', () => {
    const filtros = conTipo({ ranked_only: true, map: 'kanal' }, 'Unranked')
    expect(filtros).toEqual({ ranked_only: false, map: 'kanal', match_type: 'Unranked' })
    expect(qs(filtros)).toBe('?map=kanal&match_type=Unranked')
  })

  it('elegir Todos deja match_type vacio y qs no lo manda', () => {
    const filtros = conTipo({ ranked_only: true }, '')
    expect(filtros.match_type).toBe('')
    expect(qs(filtros)).toBe('')
  })
})

describe('hayFiltros', () => {
  it('hay filtros ignora vacios y false', () => {
    expect(hayFiltros({})).toBe(false)
    expect(hayFiltros(undefined)).toBe(false)
    expect(hayFiltros({ match_type: '', ranked_only: false, days: '' })).toBe(false)
    expect(hayFiltros({ match_type: 'Ranked' })).toBe(true)
  })
})
