import { describe, expect, it } from 'vitest'

import { bloquesDelPool, fechaCorta, textoResumen } from './poolOperadores.js'

const DATA = {
  matches: 25,
  recent_matches: 20,
  sides: {
    Attack: { distinct_recent: 3, distinct_all: 5, never: ['Sledge'], stale: [{ operator: 'Ash', last_played: '2026-07-01T20:00:00', rounds: 4 }] },
    Defense: { distinct_recent: 1, distinct_all: 1, never: [], stale: [] },
  },
}

describe('poolOperadores', () => {
  it('sin datos o sin partidas no hay bloques', () => {
    expect(bloquesDelPool(null)).toEqual([])
    expect(bloquesDelPool(undefined, 'Attack')).toEqual([])
    expect(bloquesDelPool({ ...DATA, matches: 0 })).toEqual([])
  })

  it('sin filtro de lado salen ataque y defensa en ese orden', () => {
    expect(bloquesDelPool(DATA).map((b) => b.titulo)).toEqual(['Ataque', 'Defensa'])
    expect(bloquesDelPool(DATA, '').map((b) => b.titulo)).toEqual(['Ataque', 'Defensa'])
  })

  it('con el lado filtrado sale un solo bloque', () => {
    expect(bloquesDelPool(DATA, 'Defense').map((b) => b.titulo)).toEqual(['Defensa'])
    const [ataque] = bloquesDelPool(DATA, 'Attack')
    expect(ataque.never).toEqual(['Sledge'])
    expect(ataque.stale[0].operator).toBe('Ash')
  })

  it('el resumen dice plural y singular', () => {
    expect(textoResumen(DATA.sides.Attack, 20)).toBe(
      '3 operadores distintos en tus últimas 20 partidas · 5 en todo el historial',
    )
    expect(textoResumen(DATA.sides.Defense, 1)).toBe(
      '1 operador distinto en tu última partida · 1 en todo el historial',
    )
  })

  it('con menos de 20 partidas usa el numero real', () => {
    expect(textoResumen({ distinct_recent: 2, distinct_all: 2 }, 7)).toContain('tus últimas 7 partidas')
    expect(bloquesDelPool({ ...DATA, recent_matches: 7 })[0].resumen).toContain('tus últimas 7 partidas')
  })

  it('la fecha se corta al dia', () => {
    expect(fechaCorta('2026-07-01T20:00:00')).toBe('2026-07-01')
    expect(fechaCorta(null)).toBe('')
  })
})
