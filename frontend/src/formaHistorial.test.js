/** Tests del panel "Tu forma contra tu historial" del Resumen. */

import { describe, expect, it } from 'vitest'

import { METRICAS_FORMA, estadoDeForma, filasDeForma } from './formaHistorial.js'

const metrica = (key) => ({ key, label: key, suffix: '%', current: 1, previous: 1, delta: 0, noise: 1 })

const respuesta = (actual, previa, suficiente = true) => ({
  enough_sample: suficiente,
  current: { rounds: actual },
  previous: { rounds: previa },
  metrics: ['kd', 'untraded_death_pct', 'rating', 'hs_pct', 'kst_pct', 'winrate'].map(metrica),
})

describe('filasDeForma', () => {
  it('deja solo las cuatro metricas de la forma, en su orden', () => {
    const filas = filasDeForma(respuesta(60, 120))
    expect(filas.map((f) => f.key)).toEqual(METRICAS_FORMA)
    expect(filas.map((f) => f.orden)).toEqual([0, 1, 2, 3])
  })

  it('sin datos no hay filas', () => {
    expect(filasDeForma(null)).toEqual([])
    expect(filasDeForma({})).toEqual([])
  })
})

describe('estadoDeForma', () => {
  it('sin rondas recientes no hay nada que mostrar', () => {
    expect(estadoDeForma(null)).toBe('sin-datos')
    expect(estadoDeForma(respuesta(0, 0))).toBe('sin-datos')
  })

  it('sin resto avisa que falta historial', () => {
    expect(estadoDeForma(respuesta(60, 0, false))).toBe('sin-resto')
  })

  it('con poca muestra avisa pero muestra la tabla', () => {
    expect(estadoDeForma(respuesta(12, 30, false))).toBe('poca-muestra')
  })

  it('con muestra de los dos lados no hay aviso', () => {
    expect(estadoDeForma(respuesta(60, 120))).toBeNull()
  })
})
