import { describe, expect, it } from 'vitest'

import { marcasDeApertura } from './aperturas.js'
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

  it('si el entry es la apertura solo queda la apertura', () => {
    const caso = casos.find((c) => c.nombre === 'abre tu equipo')
    expect(marcasDeApertura(rondaDe(caso), 0)).toEqual({ apertura: 0, entry: null })
  })

  it('una ronda sin eventos no marca nada', () => {
    expect(marcasDeApertura({ players: [] }, 0)).toEqual({ apertura: null, entry: null })
  })

  it('sin equipo propio solo marca la apertura', () => {
    const ronda = rondaDe(casos.find((c) => c.nombre === 'abre el rival y tu equipo responde'))
    expect(marcasDeApertura(ronda, undefined)).toEqual({ apertura: 0, entry: null })
    expect(marcasDeApertura(ronda, -1)).toEqual({ apertura: 0, entry: null })
  })
})
