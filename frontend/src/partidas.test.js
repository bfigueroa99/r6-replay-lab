/** Tests de los filtros de la pagina Partidas (ficha 78). */

import { describe, expect, it } from 'vitest'

import { qs } from './api.js'
import {
  claveDeFiltros,
  filtrosDePartida,
  offsetVigente,
  paramsDePartidas,
  subtituloDePartidas,
} from './partidas.js'

describe('filtrosDePartida', () => {
  it('filtros de partida dejan afuera lado operador y sitio', () => {
    expect(
      filtrosDePartida({ side: 'Attack', operator: 'Ash', site: 'X', map: 'bank', days: '7', session: '0' }),
    ).toEqual({ map: 'bank', days: '7', session: '0' })
  })

  it('el modo de juego es de partida y pasa', () => {
    expect(filtrosDePartida({ side: 'Attack', gamemode: 'Hostage', match_type: 'Ranked' })).toEqual({
      match_type: 'Ranked',
      gamemode: 'Hostage',
    })
  })

  it('filtros de partida sin datos dan un objeto vacio', () => {
    expect(filtrosDePartida(null)).toEqual({})
    expect(filtrosDePartida(undefined)).toEqual({})
  })
})

describe('paramsDePartidas', () => {
  it('los params mandan el resultado y la pagina', () => {
    expect(paramsDePartidas({ map: 'bank', side: 'Attack' }, 'derrota', 50, 50)).toEqual({
      map: 'bank',
      result: 'derrota',
      limit: 50,
      offset: 50,
    })
  })

  it('resultado Todos no viaja en la query', () => {
    expect(qs(paramsDePartidas({}, '', 0, 50))).toBe('?limit=50&offset=0')
  })
})

describe('offsetVigente', () => {
  it('cambiar un filtro vuelve a la primera pagina', () => {
    expect(offsetVigente({ clave: 'a', offset: 50 }, 'b')).toBe(0)
  })

  it('sin cambiar filtros la pagina se mantiene', () => {
    expect(offsetVigente({ clave: 'a', offset: 50 }, 'a')).toBe(50)
  })

  it('cambiar el lado no cambia la clave de Partidas', () => {
    expect(claveDeFiltros({ map: 'bank', side: 'Attack' }, 'victoria')).toBe(
      claveDeFiltros({ map: 'bank' }, 'victoria'),
    )
    expect(claveDeFiltros({ map: 'bank' }, 'victoria')).not.toBe(claveDeFiltros({ map: 'bank' }, 'derrota'))
  })
})

describe('subtituloDePartidas', () => {
  it('el subtitulo dice importadas sin filtros y con estos filtros con filtros', () => {
    expect(subtituloDePartidas(29, false)).toBe('29 partidas importadas.')
    expect(subtituloDePartidas(12, true)).toBe('12 partidas con estos filtros.')
  })

  it('el subtitulo usa singular con una partida', () => {
    expect(subtituloDePartidas(1, false)).toBe('1 partida importada.')
    expect(subtituloDePartidas(1, true)).toBe('1 partida con estos filtros.')
  })
})
