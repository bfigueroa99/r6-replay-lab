import { describe, expect, it } from 'vitest'

import { esTeamkill, marcasDeApertura } from './aperturas.js'
import casos from './casosApertura.json'

function rondaDe(caso) {
  return {
    players: caso.jugadores.map(([username, team_index]) => ({ username, team_index })),
    events: caso.eventos.map(([kind, actor, target], order) => ({ order, kind, actor, target })),
  }
}

describe('marcasDeApertura', () => {
  for (const caso of casos) {
    const esperado = {
      apertura: caso.apertura,
      entry: caso.entry === caso.apertura ? null : caso.entry,
    }

    it(`${caso.nombre}: marca la apertura y el entry`, () => {
      expect(marcasDeApertura(rondaDe(caso), caso.mi_equipo)).toEqual(esperado)
    })

    it(`${caso.nombre}: da lo mismo con los eventos desordenados`, () => {
      const ronda = rondaDe(caso)
      ronda.events.reverse()
      expect(marcasDeApertura(ronda, caso.mi_equipo)).toEqual(esperado)
    })

    it(`${caso.nombre}: sin equipo propio no hay entry`, () => {
      expect(marcasDeApertura(rondaDe(caso), -1)).toEqual({ apertura: caso.apertura, entry: null })
    })
  }

  it('una ronda sin eventos no marca nada', () => {
    expect(marcasDeApertura({ players: [] }, 0)).toEqual({ apertura: null, entry: null })
  })

  it('sin equipo propio solo marca la apertura', () => {
    const ronda = rondaDe(casos.find((c) => c.nombre === 'abre el rival y tu equipo responde'))
    expect(marcasDeApertura(ronda, undefined)).toEqual({ apertura: 0, entry: null })
  })
})

describe('esTeamkill', () => {
  const ronda = {
    players: [
      { username: 'A', team_index: 0 },
      { username: 'B', team_index: 0 },
      { username: 'C', team_index: 1 },
    ],
  }
  const kill = (actor, target, kind = 'Kill') => ({ order: 1, kind, actor, target })

  it('una baja entre companeros es teamkill', () => {
    expect(esTeamkill(ronda, kill('A', 'B'))).toBe(true)
  })

  it('una baja a un rival no lo es', () => {
    expect(esTeamkill(ronda, kill('A', 'C'))).toBe(false)
  })

  it('un nick que no esta entre los jugadores no lo es', () => {
    expect(esTeamkill(ronda, kill('A', 'Fantasma'))).toBe(false)
    expect(esTeamkill(ronda, kill('Fantasma', 'A'))).toBe(false)
  })

  it('un Death no lo es', () => {
    expect(esTeamkill(ronda, kill('A', 'B', 'Death'))).toBe(false)
  })

  it('un suicidio no lo es', () => {
    expect(esTeamkill(ronda, kill('A', 'A'))).toBe(false)
  })

  it('sin players no lo es', () => {
    expect(esTeamkill({}, kill('A', 'B'))).toBe(false)
    expect(esTeamkill(undefined, kill('A', 'B'))).toBe(false)
  })
})
