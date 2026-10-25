/** Tests de las filas del panel "Rondas cortas y largas". */

import { describe, expect, it } from 'vitest'

import {
  celdasConPocaMuestra,
  etiquetaDuracion,
  filasDeDuracion,
  hayDuracion,
  resumenDeDuracion,
  textoCelda,
} from './duracion.js'

const celda = (rounds = 0, winrate = null, extra = {}) => ({ rounds, winrate, ...extra })
const fila = (length, ataque = celda(), defensa = celda(), total = celda()) => ({
  length, Attack: ataque, Defense: defensa, total,
})

describe('filasDeDuracion', () => {
  it('etiqueta los tramos en castellano y conserva el orden del backend', () => {
    const filas = filasDeDuracion({
      rows: ['0-45', '45-90', '90-135', '135+', 'plant'].map((l) => fila(l)),
    })
    expect(filas.map((f) => f.tramo)).toEqual([
      '0–45 s', '45–90 s', '90–135 s', '135 s o más', 'Posible plant',
    ])
    expect(filas.map((f) => f.orden)).toEqual([0, 1, 2, 3, 4])
    expect(etiquetaDuracion('200+')).toBe('200+')
  })

  it('sube rating y kpr del total a la fila', () => {
    const [f] = filasDeDuracion({
      rows: [fila('135+', celda(116, 100), celda(87, 0), celda(203, 57.1, { rating: 1, kpr: 0.49 }))],
    })
    expect(f.vista).toEqual({ Attack: '100% (116)', Defense: '0% (87)', total: '57% (203)' })
    expect(f.rating).toBe(1)
    expect(f.kpr).toBe(0.49)
  })
})

describe('textoCelda', () => {
  it('una celda sin rondas muestra guion y no 0 %', () => {
    expect(textoCelda(celda(0, null))).toBe('—')
    expect(textoCelda(undefined)).toBe('—')
    expect(textoCelda(celda(3, 0))).toBe('0% (3)')
  })

  it('la fila de posible plant muestra solo el conteo', () => {
    expect(textoCelda(celda(4, null))).toBe('— (4)')
  })
})

describe('resumenDeDuracion', () => {
  it('el resumen arma ataque, defensa y total con los promedios', () => {
    const resumen = resumenDeDuracion({
      summary: {
        Attack: celda(10, 60, { avg_duration_won: 70.5, avg_duration_lost: 120 }),
        Defense: celda(5, 20, { avg_duration_won: null, avg_duration_lost: 90 }),
        total: celda(15, 46.7, { avg_duration_won: 70.5, avg_duration_lost: 100 }),
      },
    })
    expect(resumen.map((r) => r.lado)).toEqual(['Ataque', 'Defensa', 'Total'])
    expect(resumen[0]).toMatchObject({ rounds: 10, avg_duration_won: 70.5, avg_duration_lost: 120 })
    expect(resumen[1].avg_duration_won).toBeNull()
  })
})

describe('celdasConPocaMuestra', () => {
  it('avisa poca muestra solo con celdas de 1 a 29 rondas y no mira la fila de plant', () => {
    const datos = {
      rows: [
        fila('0-45', celda(40, 50), celda(0), celda(40, 50)),
        fila('135+', celda(30, 50), celda(30, 50), celda(60, 50)),
        fila('plant', celda(2), celda(0), celda(2)),
      ],
    }
    expect(celdasConPocaMuestra(datos)).toEqual([])
    datos.rows[1].Defense = celda(29, 50)
    expect(celdasConPocaMuestra(datos)).toHaveLength(1)
  })
})

describe('respuesta ausente', () => {
  it('respuesta ausente devuelve listas vacias sin romper', () => {
    expect(filasDeDuracion(undefined)).toEqual([])
    expect(resumenDeDuracion(undefined)).toEqual([])
    expect(celdasConPocaMuestra(undefined)).toEqual([])
    expect(hayDuracion(undefined)).toBe(false)
    expect(hayDuracion({ rows: [fila('0-45')], summary: { total: celda(0) } })).toBe(false)
    expect(hayDuracion({ rows: [fila('plant', celda(1), celda(), celda(1))] })).toBe(true)
  })
})
