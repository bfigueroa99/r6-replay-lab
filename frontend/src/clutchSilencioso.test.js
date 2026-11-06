/** Tests de los textos de clutches silenciosos de Compañeros. */

import { describe, expect, it } from 'vitest'

import { celdaSilenciosos, notaSilenciosos } from './clutchSilencioso.js'

const resumen = (extra) => ({
  won: 2,
  silent: 1,
  silent_pct: 50,
  by_condition: { elimination: 0, other: 1, unknown: 0 },
  ...extra,
})

describe('celdaSilenciosos', () => {
  it('celdaSilenciosos da guion sin ganados', () => {
    expect(celdaSilenciosos({ won: 0, silent: 0, silent_pct: null })).toBe('—')
  })

  it('celdaSilenciosos da cantidad y porcentaje', () => {
    expect(celdaSilenciosos({ won: 2, silent: 1, silent_pct: 50 })).toBe('1 (50%)')
    expect(celdaSilenciosos({ won: 3, silent: 2, silent_pct: 66.7 })).toBe('2 (67%)')
  })
})

describe('notaSilenciosos', () => {
  it('notaSilenciosos es null sin ganados', () => {
    expect(notaSilenciosos(undefined)).toBeNull()
    expect(notaSilenciosos(resumen({ won: 0, silent: 0 }))).toBeNull()
  })

  it('notaSilenciosos usa singular con un ganado y un silencioso', () => {
    const nota = notaSilenciosos(
      resumen({ won: 1, silent: 1, by_condition: { elimination: 1, other: 0, unknown: 0 } }),
    )
    expect(nota).toBe(
      'De tus 1 clutch ganado, 1 fue silencioso (sin bajas tuyas desde que quedaste solo): ' +
        '1 por eliminación, 0 sin eliminación (plant, defuse o tiempo; inferido del reloj).',
    )
  })

  it('notaSilenciosos usa plural con varios', () => {
    expect(notaSilenciosos(resumen({ won: 4, silent: 2 }))).toMatch(
      /^De tus 4 clutches ganados, 2 fueron silenciosos/,
    )
  })

  it('notaSilenciosos agrega sin dato solo si hay', () => {
    expect(notaSilenciosos(resumen())).not.toMatch(/sin dato/)
    expect(
      notaSilenciosos(resumen({ silent: 2, by_condition: { elimination: 0, other: 1, unknown: 1 } })),
    ).toMatch(/, 1 sin dato\.$/)
  })
})
