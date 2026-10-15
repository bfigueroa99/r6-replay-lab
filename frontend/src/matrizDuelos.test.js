/** Tests de la matriz de duelos de una partida. */

import { describe, expect, it } from 'vitest'

import { celda, matrizDeDuelos } from './matrizDuelos.js'

const jugador = (username, team_index, is_me = false) => ({ username, team_index, is_me })
const baja = (order, actor, target, headshot = false) => ({ kind: 'Kill', order, actor, target, headshot })
const JUGADORES = [jugador('yo', 0, true), jugador('compa', 0), jugador('rival1', 1), jugador('rival2', 1)]

describe('matrizDeDuelos', () => {
  it('arma la matriz de una partida de dos rondas con bajas y headshots', () => {
    const rondas = [
      { players: JUGADORES, events: [baja(1, 'yo', 'rival1', true), baja(2, 'rival2', 'compa')] },
      { players: JUGADORES, events: [baja(1, 'yo', 'rival1'), baja(2, 'yo', 'rival2', true)] },
    ]
    const m = matrizDeDuelos(rondas, { miEquipo: 0 })
    expect(m.total).toBe(4)
    expect(celda(m, 'aFavor', 'yo', 'rival1')).toEqual({ bajas: 2, headshots: 1 })
    expect(celda(m, 'aFavor', 'yo', 'rival2')).toEqual({ bajas: 1, headshots: 1 })
    expect(celda(m, 'enContra', 'rival2', 'compa')).toEqual({ bajas: 1, headshots: 0 })
    expect(celda(m, 'aFavor', 'compa', 'rival1')).toEqual({ bajas: 0, headshots: 0 })
    expect(m.mios).toEqual(['yo', 'compa'])
    expect(m.rivales).toEqual(['rival2', 'rival1'])
  })

  it('ignora teamkills y bajas sin autor', () => {
    const rondas = [
      {
        players: JUGADORES,
        events: [
          baja(1, 'yo', 'compa'),
          baja(2, null, 'rival1'),
          baja(3, 'rival1', ''),
          baja(4, 'desconocido', 'yo'),
          { kind: 'Death', order: 5, actor: 'rival2' },
        ],
      },
    ]
    const m = matrizDeDuelos(rondas, { miEquipo: 0 })
    expect(m.total).toBe(0)
    expect(m.aFavor).toEqual({})
    expect(m.enContra).toEqual({})
  })

  it('solo aperturas cuenta la primera baja entre rivales de cada ronda', () => {
    const rondas = [
      { players: JUGADORES, events: [baja(2, 'rival1', 'yo'), baja(1, 'yo', 'rival2')] },
      { players: JUGADORES, events: [baja(1, 'rival1', 'compa'), baja(2, 'yo', 'rival1')] },
    ]
    const m = matrizDeDuelos(rondas, { soloAperturas: true, miEquipo: 0 })
    expect(m.total).toBe(2)
    expect(celda(m, 'aFavor', 'yo', 'rival2').bajas).toBe(1)
    expect(celda(m, 'enContra', 'rival1', 'compa').bajas).toBe(1)
    expect(celda(m, 'enContra', 'rival1', 'yo').bajas).toBe(0)
  })

  it('un teamkill no cuenta como apertura', () => {
    const rondas = [{ players: JUGADORES, events: [baja(1, 'rival1', 'rival2'), baja(2, 'compa', 'rival1')] }]
    const m = matrizDeDuelos(rondas, { soloAperturas: true, miEquipo: 0 })
    expect(m.total).toBe(1)
    expect(celda(m, 'aFavor', 'compa', 'rival1').bajas).toBe(1)
  })

  it('una partida sin eventos devuelve total cero', () => {
    const m = matrizDeDuelos([{ players: JUGADORES, events: [] }], { miEquipo: 0 })
    expect(m.total).toBe(0)
    expect(m.mios).toEqual(['compa', 'yo'])
    expect(matrizDeDuelos(undefined).total).toBe(0)
  })

  it('un nick que cambia de equipo entre rondas cae en la tabla de cada baja', () => {
    const rondas = [
      { players: [jugador('yo', 0, true), jugador('x', 0), jugador('r', 1)], events: [baja(1, 'x', 'r')] },
      { players: [jugador('yo', 0, true), jugador('r', 0), jugador('x', 1)], events: [baja(1, 'x', 'yo')] },
    ]
    const m = matrizDeDuelos(rondas, { miEquipo: 0 })
    expect(m.total).toBe(2)
    expect(celda(m, 'aFavor', 'x', 'r').bajas).toBe(1)
    expect(celda(m, 'enContra', 'x', 'yo').bajas).toBe(1)
    expect(m.rivales).toContain('x')
    expect(m.mios).toContain('yo')
  })

  it('sin tu fila en la ronda usa el equipo de la partida', () => {
    const rondas = [{ players: [jugador('a', 1), jugador('b', 0)], events: [baja(1, 'a', 'b')] }]
    const m = matrizDeDuelos(rondas, { miEquipo: 1 })
    expect(celda(m, 'aFavor', 'a', 'b').bajas).toBe(1)
    expect(m.mios).toEqual(['a'])
  })
})
