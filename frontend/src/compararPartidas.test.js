import { describe, expect, it } from 'vitest'

import { filasDeComparacion, opcionesParaComparar, rondasPorLado } from './compararPartidas.js'

const totales = (extra = {}) => ({
  rounds: 9,
  kills: 8,
  deaths: 5,
  opening_kills: 2,
  opening_deaths: 1,
  untraded_deaths: 3,
  kst_pct: 70,
  rating: 1.2,
  ...extra,
})

const ronda = (my_side, my_team_won) => ({ my_side, my_team_won })

const partida = ({ match = {}, rounds, my_totals } = {}) => ({
  match: {
    map: 'Clubhouse',
    played_at: '2026-11-01T20:15:42+00:00',
    match_type: 'Ranked',
    score: '4-3',
    result: 'Victoria',
    ...match,
  },
  rounds: rounds ?? [ronda('Attack', true), ronda('Defense', false)],
  my_totals,
})

const fila = (filas, clave) => filas.find((f) => f.clave === clave)

describe('filasDeComparacion', () => {
  it('la diferencia lleva signo y respeta si mas es mejor', () => {
    const filas = filasDeComparacion(
      partida({ my_totals: totales({ kills: 8, deaths: 8 }) }),
      partida({ my_totals: totales({ kills: 5, deaths: 5 }) }),
    )
    expect(fila(filas, 'kills')).toMatchObject({ a: '8', b: '5', diferencia: '+3', mejor: 'a' })
    expect(fila(filas, 'deaths')).toMatchObject({ diferencia: '+3', mejor: 'b' })
    const menos = filasDeComparacion(
      partida({ my_totals: totales({ kills: 4 }) }),
      partida({ my_totals: totales({ kills: 5 }) }),
    )
    expect(fila(menos, 'kills')).toMatchObject({ diferencia: '-1', mejor: 'b' })
  })

  it('diferencia cero no marca a nadie', () => {
    const filas = filasDeComparacion(partida({ my_totals: totales() }), partida({ my_totals: totales() }))
    expect(fila(filas, 'kills')).toMatchObject({ diferencia: '0', mejor: null })
    expect(fila(filas, 'rating')).toMatchObject({ diferencia: '0.00', mejor: null })
  })

  it('kst va en puntos y rating con dos decimales', () => {
    const filas = filasDeComparacion(
      partida({ my_totals: totales({ kst_pct: 82, rating: 1.35 }) }),
      partida({ my_totals: totales({ kst_pct: 70, rating: 1.2 }) }),
    )
    expect(fila(filas, 'kst_pct')).toMatchObject({ a: '82%', b: '70%', diferencia: '+12', mejor: 'a' })
    expect(fila(filas, 'rating')).toMatchObject({ a: '1.35', b: '1.20', diferencia: '+0.15', mejor: 'a' })
  })

  it('las rondas por lado comparan winrate y no conteo', () => {
    // A: 4 de 6 en ataque (67%); B: 3 de 3 (100%): B sale mejor aunque gano menos
    const a = partida({
      rounds: [true, true, true, true, false, false].map((w) => ronda('Attack', w)),
      my_totals: totales(),
    })
    const b = partida({ rounds: [true, true, true].map((w) => ronda('Attack', w)), my_totals: totales() })
    const ataque = fila(filasDeComparacion(a, b), 'Attack')
    expect(ataque).toMatchObject({ a: '4 de 6', b: '3 de 3', diferencia: '-33', mejor: 'b' })
  })

  it('una ronda sin ganador cuenta en el total y no en las ganadas', () => {
    expect(rondasPorLado([ronda('Defense', null), ronda('Defense', true)])).toEqual({
      Attack: { won: 0, total: 0 },
      Defense: { won: 1, total: 2 },
    })
  })

  it('partida sin tu fila devuelve guiones y no rompe', () => {
    for (const sinFila of [partida({ my_totals: { rounds: 0, kills: 0 } }), partida()]) {
      const filas = filasDeComparacion(partida({ my_totals: totales() }), sinFila)
      for (const clave of ['kills', 'deaths', 'kst_pct', 'rating']) {
        expect(fila(filas, clave)).toMatchObject({ b: '—', diferencia: '', mejor: null })
      }
      expect(fila(filas, 'kills').a).toBe('8')
    }
  })

  it('partida sin rondas devuelve guiones en los lados', () => {
    const filas = filasDeComparacion(partida({ my_totals: totales() }), partida({ rounds: [] }))
    expect(fila(filas, 'Attack')).toMatchObject({ a: '1 de 1', b: '—', diferencia: '', mejor: null })
    expect(fila(filas, 'Defense')).toMatchObject({ a: '0 de 1', b: '—', diferencia: '', mejor: null })
    expect(fila(filas, 'score').b).toBe('4-3 Victoria')
  })

  it('rating nulo es guion', () => {
    const filas = filasDeComparacion(
      partida({ my_totals: totales({ rating: null }) }),
      partida({ my_totals: totales() }),
    )
    expect(fila(filas, 'rating')).toMatchObject({ a: '—', b: '1.20', diferencia: '', mejor: null })
  })

  it('las filas de texto van primero y sin diferencia', () => {
    const filas = filasDeComparacion(partida({ my_totals: totales() }), partida({ my_totals: totales() }))
    expect(filas.map((f) => f.etiqueta)).toEqual([
      'Mapa',
      'Fecha',
      'Tipo',
      'Marcador',
      'Rondas en ataque',
      'Rondas en defensa',
      'Bajas',
      'Muertes',
      'Aperturas ganadas',
      'Aperturas perdidas',
      'Muertes sin trade',
      'KST',
      'Rating',
    ])
    expect(fila(filas, 'played_at')).toMatchObject({ a: '2026-11-01 20:15', diferencia: '', mejor: null })
  })
})

describe('opcionesParaComparar', () => {
  it('las opciones sacan la partida actual y separan el mismo mapa', () => {
    const matches = [
      { id: 3, map: 'Consulate (Y10)', map_slug: 'consulate', played_at: '2026-11-03T10:00:00', score: '4-2', result: 'Victoria' },
      { id: 2, map: 'Consulate', map_slug: 'consulate', played_at: '2026-11-02T10:00:00', score: '1-4', result: 'Derrota' },
      { id: 1, map: 'Consulate (Y10)', map_slug: 'consulate', played_at: '2026-11-01T10:00:00', score: '4-3', result: 'Victoria' },
      { id: 4, map: 'Bank', map_slug: 'bank', played_at: '2026-10-30T10:00:00', score: '4-0', result: 'Victoria' },
    ]
    const { mismoMapa, otras } = opcionesParaComparar(matches, { id: '1', map: 'Consulate (Y10)' })
    expect(mismoMapa).toEqual([{ id: 3, texto: '2026-11-03 10:00 · Consulate (Y10) · 4-2 · Victoria' }])
    expect(otras.map((o) => o.id)).toEqual([2, 4])
  })
})
