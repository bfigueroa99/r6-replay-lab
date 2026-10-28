/** Tests del resumen en texto de una partida. */

import { describe, expect, it } from 'vitest'

import { textoResumenPartida } from './resumenPartida.js'

function ronda(numero, lado, gano, misBajas, nick = 'BearF99') {
  return {
    number: numero,
    label: `R${numero + 1}`,
    my_side: lado,
    my_team_won: gano,
    players: [
      { username: nick, is_me: true, kills: misBajas },
      { username: 'Rival', is_me: false, kills: 4 },
    ],
  }
}

function payload(cambios = {}) {
  return {
    match: {
      map: 'Club House',
      score: '4-3',
      result: 'victoria',
      played_at: '2026-08-01T20:00:00-03:00',
      match_type: 'Ranked',
    },
    rounds: [
      ronda(0, 'Attack', true, 1),
      ronda(1, 'Attack', true, 0),
      ronda(2, 'Attack', false, 2),
      ronda(3, 'Attack', true, 0),
      ronda(4, 'Defense', true, 3),
      ronda(5, 'Defense', false, 1),
      ronda(6, 'Defense', false, 1),
    ],
    my_totals: {
      kills: 8,
      deaths: 5,
      kd: 1.6,
      hs_pct: 37.5,
      opening_kills: 2,
      opening_deaths: 1,
      kst_pct: 71.4,
    },
    ...cambios,
  }
}

describe('textoResumenPartida', () => {
  it('arma las cinco lineas con mapa, marcador y resultado primero', () => {
    expect(textoResumenPartida(payload())).toBe(
      [
        'Club House · 4-3 · victoria',
        '2026-08-01 20:00 · Ranked',
        'BearF99: 8 bajas / 5 muertes · K/D 1.60 · HS 38% · aperturas 2-1 · KST 71%',
        'Rondas ganadas: ataque 3 de 4 · defensa 1 de 3',
        'Mejor ronda: R5, 3 bajas',
      ].join('\n'),
    )
  })

  it('una partida sin bajas tuyas no tiene mejor ronda', () => {
    const datos = payload({ rounds: [ronda(0, 'Attack', true, 0), ronda(1, 'Defense', false, 0)] })
    const texto = textoResumenPartida(datos)
    expect(texto).not.toContain('Mejor ronda')
    expect(texto.split('\n')).toHaveLength(4)
  })

  it('una ronda de una sola baja usa el singular', () => {
    const datos = payload({ rounds: [ronda(0, 'Attack', true, 1)] })
    expect(textoResumenPartida(datos)).toContain('Mejor ronda: R1, 1 baja')
  })

  it('un lado sin rondas no aparece en la linea de rondas ganadas', () => {
    const datos = payload({
      rounds: [ronda(0, 'Attack', true, 1), ronda(1, 'Attack', true, 0), ronda(2, 'Attack', true, 0), ronda(3, 'Attack', true, 0)],
    })
    const texto = textoResumenPartida(datos)
    expect(texto).toContain('Rondas ganadas: ataque 4 de 4')
    expect(texto).not.toContain('defensa')
  })

  it('una partida incompleta lo dice en la primera linea', () => {
    const datos = payload()
    datos.match.result = 'incompleta'
    datos.match.score = '3-2'
    expect(textoResumenPartida(datos).split('\n')[0]).toBe('Club House · 3-2 · incompleta')
  })

  it('el empate de bajas elige la primera ronda', () => {
    const datos = payload({
      rounds: [ronda(0, 'Attack', true, 1), ronda(1, 'Attack', true, 2), ronda(2, 'Defense', false, 2)],
    })
    expect(textoResumenPartida(datos)).toContain('Mejor ronda: R2, 2 bajas')
  })

  it('el nick sale tal cual, sin escapar ni formatear', () => {
    const nick = '<b>Ñandú_*|'
    const datos = payload({ rounds: [ronda(0, 'Attack', true, 1, 'Viejo'), ronda(1, 'Defense', false, 0, nick)] })
    const texto = textoResumenPartida(datos)
    expect(texto).toContain(`${nick}: 8 bajas`)
    expect(texto).not.toContain('Viejo')
    expect(texto.replace(nick, '')).not.toMatch(/[<>*_|]/)
  })

  it('sin rondas ni fila tuya no rompe', () => {
    const texto = textoResumenPartida(payload({ rounds: [], my_totals: {} }))
    expect(texto.split('\n')).toEqual([
      'Club House · 4-3 · victoria',
      '2026-08-01 20:00 · Ranked',
      'Tú: — bajas / — muertes · K/D — · HS — · aperturas —-— · KST —',
    ])
    const sinNada = textoResumenPartida({ match: payload().match })
    expect(sinNada.split('\n')[2]).toMatch(/^Tú: /)
  })

  it('un K/D nulo se escribe con raya', () => {
    const datos = payload()
    datos.my_totals.kd = null
    datos.my_totals.hs_pct = null
    expect(textoResumenPartida(datos)).toContain('K/D — · HS — ·')
  })
})
