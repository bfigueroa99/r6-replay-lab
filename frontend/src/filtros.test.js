import { describe, expect, it } from 'vitest'

import { conFiltros, destinoInsight, filtrosDesdeQuery, hayFiltros, queryDesdeFiltros } from './filtros.js'

describe('filtrosDesdeQuery', () => {
  it('lee las claves conocidas', () => {
    expect(filtrosDesdeQuery('?map=bank&side=Attack')).toEqual({ map: 'bank', side: 'Attack' })
  })

  it('acepta un URLSearchParams, que es lo que entrega react-router', () => {
    expect(filtrosDesdeQuery(new URLSearchParams('map=bank'))).toEqual({ map: 'bank' })
  })

  it('ignora lo que la API no entiende', () => {
    expect(filtrosDesdeQuery('?map=bank&orden=desc&utm_source=x')).toEqual({ map: 'bank' })
  })

  it('ranked_only vuelve como booleano', () => {
    expect(filtrosDesdeQuery('ranked_only=1')).toEqual({ ranked_only: true })
    expect(filtrosDesdeQuery('ranked_only=true')).toEqual({ ranked_only: true })
    expect(filtrosDesdeQuery('ranked_only=0')).toEqual({ ranked_only: false })
  })

  it('un valor vacio no es un filtro', () => {
    expect(filtrosDesdeQuery('?map=&side=Attack')).toEqual({ side: 'Attack' })
  })

  it('sin nada devuelve un objeto vacio', () => {
    expect(filtrosDesdeQuery('')).toEqual({})
    expect(filtrosDesdeQuery(undefined)).toEqual({})
  })
})

describe('queryDesdeFiltros', () => {
  it('es el inverso de filtrosDesdeQuery', () => {
    const filtros = { map: 'bank', side: 'Attack', ranked_only: true, days: '30' }
    expect(filtrosDesdeQuery(queryDesdeFiltros(filtros))).toEqual(filtros)
  })

  it('saca lo vacio y lo falso', () => {
    expect(queryDesdeFiltros({ map: '', side: null, ranked_only: false, days: undefined })).toBe('')
  })

  it('siempre escribe las claves en el mismo orden, para que la URL sea estable', () => {
    expect(queryDesdeFiltros({ since: '2026-09-01', map: 'bank' })).toBe('map=bank&since=2026-09-01')
  })

  it('escapa un sitio con coma y espacios', () => {
    expect(queryDesdeFiltros({ site: '2F Gym, 2F Bedroom' })).toBe('site=2F+Gym%2C+2F+Bedroom')
  })
})

describe('hayFiltros', () => {
  it('distingue filtros reales de claves vacias', () => {
    expect(hayFiltros({})).toBe(false)
    expect(hayFiltros({ map: '' })).toBe(false)
    expect(hayFiltros({ map: 'bank' })).toBe(true)
  })
})

describe('conFiltros', () => {
  it('arma el destino de un Link', () => {
    expect(conFiltros('/coach', { map: 'bank' })).toEqual({ pathname: '/coach', search: '?map=bank' })
  })

  it('sin filtros no deja el signo colgando', () => {
    expect(conFiltros('/coach', {})).toEqual({ pathname: '/coach', search: '' })
  })
})

describe('destinoInsight', () => {
  it('una senal con filtros abre el Resumen con esas rondas', () => {
    const insight = { key: 'mapa-debil', filters: { map: 'border' } }
    expect(destinoInsight(insight)).toEqual({ pathname: '/', search: '?map=border' })
  })

  it('los filtros de la senal se suman a los activos y mandan si chocan', () => {
    const insight = { key: 'desbalance-lados', filters: { side: 'Defense' } }
    expect(destinoInsight(insight, { map: 'bank', side: 'Attack' })).toEqual({
      pathname: '/',
      search: '?side=Defense&map=bank',
    })
  })

  it('las de duelos van a Duelos con los filtros activos', () => {
    expect(destinoInsight({ key: 'operador-rival', filters: {} }, { map: 'bank' })).toEqual({
      pathname: '/duelos',
      search: '?map=bank',
    })
    expect(destinoInsight({ key: 'nemesis' })).toEqual({ pathname: '/duelos', search: '' })
  })

  it('sin filtros no hay a donde ir', () => {
    expect(destinoInsight({ key: 'kst', filters: {} })).toBeNull()
    expect(destinoInsight({ key: 'sin-datos' })).toBeNull()
    expect(destinoInsight(null)).toBeNull()
  })
})
