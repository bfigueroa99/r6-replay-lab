import { describe, expect, it } from 'vitest'

import { enlaceDeSenal, textoDelEnlace } from './enlaceSenal.js'

const general = { key: 'kst', filters: {}, target: '/' }
const mapa = { key: 'mapa-debil', filters: { map: 'kafe' }, target: '/' }
const rival = { key: 'nemesis', filters: {}, target: '/duelos' }

describe('enlaceDeSenal', () => {
  it('una señal general no tiene enlace', () => {
    expect(enlaceDeSenal(general, { days: '30' })).toBeNull()
    expect(enlaceDeSenal({ key: 'vieja' }, {})).toBeNull()
  })

  it('la señal de mapa abre el Resumen y conserva el periodo y el tipo', () => {
    expect(enlaceDeSenal(mapa, { days: '30', match_type: 'Ranked' })).toEqual({
      pathname: '/',
      search: '?map=kafe&days=30&match_type=Ranked',
    })
  })

  it('conserva las fechas y el modo de la barra', () => {
    const { search } = enlaceDeSenal(mapa, { since: '2026-09-01', until: '2026-09-30', gamemode: 'Bomb' })
    const params = new URLSearchParams(search)
    expect(params.get('map')).toBe('kafe')
    expect(params.get('since')).toBe('2026-09-01')
    expect(params.get('until')).toBe('2026-09-30')
    expect(params.get('gamemode')).toBe('Bomb')
  })

  it('el filtro de la señal pisa el de la barra', () => {
    expect(enlaceDeSenal(mapa, { map: 'bank', side: 'Defense' })).toEqual({
      pathname: '/',
      search: '?side=Defense&map=kafe',
    })
  })

  it('la señal de rival abre Duelos con los filtros de la barra', () => {
    expect(enlaceDeSenal(rival, { session: '0' })).toEqual({ pathname: '/duelos', search: '?session=0' })
    expect(enlaceDeSenal(rival, {})).toEqual({ pathname: '/duelos', search: '' })
  })

  it('un destino desconocido no tiene enlace', () => {
    expect(enlaceDeSenal({ ...mapa, target: '/ajustes' }, {})).toBeNull()
  })

  it('el texto dice a donde lleva', () => {
    expect(textoDelEnlace(mapa)).toBe('Ver esas rondas')
    expect(textoDelEnlace(rival)).toBe('Ver en Duelos')
  })
})
