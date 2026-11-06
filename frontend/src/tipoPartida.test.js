/** Tests del selector de tipo de partida (ficha 77). */

import { describe, expect, it } from 'vitest'

import { qs } from './api.js'
import { conTipo, hayFiltros, opcionesDeTipo, tipoElegido, textosSinDuelos, vistaDuelos, vistaSinRondas } from './tipoPartida.js'

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

describe('vistaSinRondas (ficha 85)', () => {
  it('con rondas no hay vista vacia', () => {
    expect(vistaSinRondas({ vacio: false, filtros: { map: 'bank' }, cargando: false })).toBe(null)
  })

  it('con filtros y 0 rondas se queda la barra', () => {
    expect(vistaSinRondas({ vacio: true, filtros: { match_type: 'Unranked' }, cargando: false })).toBe(
      'filtrado',
    )
  })

  it('sin filtros y base vacia ofrece importar', () => {
    expect(vistaSinRondas({ vacio: true, filtros: {}, cargando: false })).toBe('importar')
    expect(vistaSinRondas({ vacio: true, filtros: { match_type: '', days: '' }, cargando: false })).toBe(
      'importar',
    )
  })

  it('recien limpiado y cargando no pasa por el EmptyState', () => {
    expect(vistaSinRondas({ vacio: true, filtros: {}, cargando: true })).toBe('filtrado')
  })
})

describe('vistaDuelos (ficha 86)', () => {
  it('con rondas y duelos no hay vista especial', () => {
    expect(vistaDuelos({ rondas: 3, duelos: 2, filtros: { map: 'bank' }, cargando: false })).toBe(null)
  })

  it('con rondas y sin duelos es sin-duelos', () => {
    expect(vistaDuelos({ rondas: 1, duelos: 0, filtros: { map: 'bank' }, cargando: false })).toBe('sin-duelos')
    expect(vistaDuelos({ rondas: 1, duelos: 0, filtros: {}, cargando: false })).toBe('sin-duelos')
  })

  it('sin rondas y con filtros es filtrado', () => {
    expect(vistaDuelos({ rondas: 0, duelos: 0, filtros: { map: 'bank' }, cargando: false })).toBe('filtrado')
  })

  it('sin rondas ni filtros es importar', () => {
    expect(vistaDuelos({ rondas: 0, duelos: 0, filtros: {}, cargando: false })).toBe('importar')
  })

  it('sin rondas mientras carga es filtrado', () => {
    expect(vistaDuelos({ rondas: 0, duelos: 0, filtros: {}, cargando: true })).toBe('filtrado')
  })
})

describe('textosSinDuelos (ficha 86)', () => {
  it('con filtros habla de los filtros y de Limpiar', () => {
    const t = textosSinDuelos({ map: 'bank' })
    expect(t.subtitulo).toBe('0 duelos con estos filtros')
    expect(t.nota).toContain('usa Limpiar')
  })

  it('sin filtros no menciona filtros ni Limpiar', () => {
    const t = textosSinDuelos({})
    expect(t.subtitulo).toBe('0 duelos')
    expect(t.nota).not.toMatch(/filtro|Limpiar/)
  })
})
