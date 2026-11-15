import { describe, expect, it } from 'vitest'

import { textoRonda } from './textoRonda.js'

const JUGADORES = [
  { username: 'Yo', team_index: 0, is_me: true },
  { username: 'Socio', team_index: 0, is_me: false },
  { username: 'Rival', team_index: 1, is_me: false },
  { username: 'Otro', team_index: 1, is_me: false },
]

function ronda(extra = {}) {
  return {
    label: 'R3',
    my_side: 'Attack',
    site: 'CEO Office',
    my_team_won: true,
    players: JUGADORES,
    events: [],
    ...extra,
  }
}

const baja = (order, actor, target, extra = {}) => ({
  order,
  kind: 'Kill',
  actor,
  target,
  clock_raw: `2:${String(50 - order).padStart(2, '0')}`,
  headshot: false,
  traded: false,
  ...extra,
})

describe('textoRonda', () => {
  it('la primera linea dice mapa, ronda, lado, sitio y resultado', () => {
    const texto = textoRonda(ronda(), 'Bank', 0)
    expect(texto.split('\n')[0]).toBe('Bank · R3 · ataque · sitio CEO Office · ganada')
  })

  it('una ronda de tres bajas sale en orden con sus marcas', () => {
    const eventos = [
      baja(7, 'Socio', 'Otro', { traded: true }),
      baja(2, 'Rival', 'Socio', { headshot: true }),
      baja(5, 'Yo', 'Rival'),
    ]
    const lineas = textoRonda(ronda({ events: eventos }), 'Bank', 0).split('\n')
    expect(lineas).toEqual([
      'Bank · R3 · ataque · sitio CEO Office · ganada',
      '2:48 Rival mató a Socio (apertura, HS)',
      '2:45 Yo mató a Rival (entry)',
      '2:43 Socio mató a Otro (tradeada)',
    ])
  })

  it('sin bajas dice Sin bajas', () => {
    expect(textoRonda(ronda(), 'Bank', 0).split('\n')).toEqual([
      'Bank · R3 · ataque · sitio CEO Office · ganada',
      'Sin bajas',
    ])
    const soloOperador = ronda({ events: [{ order: 1, kind: 'OperatorSwap', actor: 'Yo', operator: 'Ash' }] })
    expect(textoRonda(soloOperador, 'Bank', 0).split('\n')).toEqual([
      'Bank · R3 · ataque · sitio CEO Office · ganada',
      'Sin bajas',
    ])
  })

  it('un teamkill y una muerte sin autor usan la etiqueta de la timeline', () => {
    const eventos = [
      baja(1, 'Yo', 'Socio'),
      { order: 2, kind: 'Death', actor: 'Otro', target: '', clock_raw: '1:10', headshot: false, traded: false },
    ]
    const lineas = textoRonda(ronda({ events: eventos }), 'Bank', 0).split('\n')
    expect(lineas[1]).toBe('2:49 Yo mató a Socio (apertura, TK)')
    expect(lineas[2]).toBe('1:10 Otro murió')
  })

  it('sin resultado ni sitio ni lado lo dice', () => {
    const texto = textoRonda(ronda({ my_side: '', site: '', my_team_won: null }), 'Bank', 0)
    expect(texto.split('\n')[0]).toBe('Bank · R3 · lado desconocido · sitio desconocido · sin resultado')
    const defensa = textoRonda(ronda({ my_side: 'Defense', my_team_won: false }), '', 0)
    expect(defensa.split('\n')[0]).toBe('R3 · defensa · sitio CEO Office · perdida')
  })

  it('un evento sin reloj usa la raya de la timeline', () => {
    const texto = textoRonda(ronda({ events: [baja(1, 'Yo', 'Rival', { clock_raw: '' })] }), 'Bank', 0)
    expect(texto.split('\n')[1]).toBe('— Yo mató a Rival (apertura)')
  })

  it('ninguna linea termina en espacio', () => {
    const eventos = [baja(1, 'Yo', 'Rival'), baja(2, 'Rival', 'Socio', { traded: true, headshot: true })]
    const texto = textoRonda(ronda({ events: eventos, site: '' }), null, 0)
    for (const linea of texto.split('\n')) expect(linea).toBe(linea.trimEnd())
    expect(texto).not.toMatch(/[<>]/)
  })

  it('sin ronda no hay texto', () => {
    expect(textoRonda(null, 'Bank', 0)).toBeNull()
    expect(textoRonda(undefined, 'Bank', 0)).toBeNull()
  })
})
