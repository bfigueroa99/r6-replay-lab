/** Tests de los filtros globales en la URL (ficha 96). */

import { describe, expect, it } from 'vitest'

import { conFiltros, filtrosDeUrl, mismosFiltros, queryDeFiltros, usaFiltros } from './filtrosUrl.js'
import { tipoElegido } from './tipoPartida.js'

describe('filtrosDeUrl y queryDeFiltros', () => {
  it('ida y vuelta sin perdida', () => {
    const f = {
      side: 'Defense',
      map: 'bank',
      operator: 'Ash',
      site: '2F Executive Lounge',
      session: '3',
      since: '2026-01-01',
      until: '2026-02-28',
      match_type: 'Ranked',
      ranked_only: true,
    }
    expect(filtrosDeUrl(queryDeFiltros(f))).toEqual(f)
    expect(filtrosDeUrl(`?${queryDeFiltros({ days: '30', map: '7' })}`)).toEqual({ days: '30', map: '7' })
  })

  it('las claves vacias y false no se escriben', () => {
    expect(queryDeFiltros({ map: '', ranked_only: false, side: 'Attack', operator: null, site: undefined })).toBe(
      'side=Attack',
    )
    expect(queryDeFiltros({})).toBe('')
    expect(queryDeFiltros(undefined)).toBe('')
  })

  it('las claves desconocidas de la url se ignoran', () => {
    expect(filtrosDeUrl('?limit=5&foo=1&map=bank')).toEqual({ map: 'bank' })
    expect(queryDeFiltros({ limit: 5, min_rounds: 3, map: 'bank' })).toBe('map=bank')
  })

  it('days invalido se descarta', () => {
    for (const malo of ['abc', '0', '-3', '99999', '1.5', '45', '']) {
      expect(filtrosDeUrl(`days=${malo}`)).toEqual({})
    }
    for (const bueno of ['7', '30', '90']) expect(filtrosDeUrl(`days=${bueno}`)).toEqual({ days: bueno })
    expect(queryDeFiltros({ days: 'abc', side: 'Attack' })).toBe('side=Attack')
  })

  it('una fecha invalida se descarta y una valida saca a days', () => {
    expect(filtrosDeUrl('since=2026-02-31')).toEqual({})
    expect(filtrosDeUrl('until=ayer')).toEqual({})
    expect(filtrosDeUrl('days=30&since=2026-01-01')).toEqual({ since: '2026-01-01' })
    expect(filtrosDeUrl('days=30&until=2026-01-01')).toEqual({ until: '2026-01-01' })
    expect(filtrosDeUrl('days=30&since=2026-02-31')).toEqual({ days: '30' })
  })

  it('session cero es un filtro valido', () => {
    expect(filtrosDeUrl('session=0')).toEqual({ session: '0' })
    expect(queryDeFiltros({ session: 0 })).toBe('session=0')
    expect(queryDeFiltros({ session: '0' })).toBe('session=0')
    expect(filtrosDeUrl('session=-1')).toEqual({})
  })

  it('ranked_only de un enlace viejo se lee como true', () => {
    expect(filtrosDeUrl('ranked_only=1')).toEqual({ ranked_only: true })
    expect(filtrosDeUrl('ranked_only=true')).toEqual({ ranked_only: true })
    expect(filtrosDeUrl('ranked_only=0')).toEqual({})
    expect(tipoElegido(filtrosDeUrl('ranked_only=1'))).toBe('Ranked')
    expect(queryDeFiltros({ ranked_only: true })).toBe('ranked_only=1')
  })

  it('side solo acepta attack o defense', () => {
    expect(filtrosDeUrl('side=Attack')).toEqual({ side: 'Attack' })
    expect(filtrosDeUrl('side=Defense')).toEqual({ side: 'Defense' })
    expect(filtrosDeUrl('side=attack')).toEqual({})
    expect(filtrosDeUrl('side=Medio')).toEqual({})
  })

  it('el texto se recorta y uno demasiado largo se descarta', () => {
    expect(filtrosDeUrl('map=%20bank%20')).toEqual({ map: 'bank' })
    expect(filtrosDeUrl(`operator=${'x'.repeat(65)}`)).toEqual({})
    expect(filtrosDeUrl('site=%20%20')).toEqual({})
  })

  it('acepta URLSearchParams y la query sin signo', () => {
    expect(filtrosDeUrl(new URLSearchParams('side=Attack'))).toEqual({ side: 'Attack' })
    expect(filtrosDeUrl('side=Attack')).toEqual({ side: 'Attack' })
    expect(filtrosDeUrl('')).toEqual({})
    expect(filtrosDeUrl(undefined)).toEqual({})
  })

  it('el orden de la query es fijo', () => {
    const a = { map: 'bank', side: 'Defense', days: '30' }
    const b = { days: '30', side: 'Defense', map: 'bank', operator: '' }
    expect(queryDeFiltros(a)).toBe('side=Defense&map=bank&days=30')
    expect(mismosFiltros(a, b)).toBe(true)
    expect(mismosFiltros(a, { ...b, days: '7' })).toBe(false)
  })
})

describe('usaFiltros', () => {
  it('usaFiltros distingue partidas de su detalle', () => {
    expect(usaFiltros('/partidas')).toBe(true)
    expect(usaFiltros('/partidas/')).toBe(true)
    expect(usaFiltros('/partidas/12')).toBe(false)
    expect(usaFiltros('/')).toBe(true)
    expect(usaFiltros('/tendencias')).toBe(true)
    expect(usaFiltros('/ruleta')).toBe(false)
    expect(usaFiltros('/jugadores/3')).toBe(false)
    expect(usaFiltros('/ajustes')).toBe(false)
    expect(usaFiltros('')).toBe(false)
  })
})

describe('conFiltros', () => {
  it('conFiltros sin filtros no deja un signo de pregunta suelto', () => {
    expect(conFiltros('/coach', {})).toEqual({ pathname: '/coach', search: '' })
    expect(conFiltros('/coach', { side: '' })).toEqual({ pathname: '/coach', search: '' })
    expect(conFiltros('/coach', { side: 'Attack' })).toEqual({ pathname: '/coach', search: '?side=Attack' })
  })
})
