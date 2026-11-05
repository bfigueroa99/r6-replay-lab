import { describe, expect, it } from 'vitest'

import {
  claseVeredicto,
  comoMargen,
  conSigno,
  etiquetaVeredicto,
  hayZonas,
  notaDeMuestra,
} from './posicion.js'

describe('posicion', () => {
  it('cada veredicto tiene su etiqueta', () => {
    expect(etiquetaVeredicto('dormidero')).toBe('Te agarran más')
    expect(etiquetaVeredicto('solido')).toBe('Te sostienes')
    expect(etiquetaVeredicto('ruido')).toBe('Sin señal')
  })

  it('un veredicto desconocido no tiene señal', () => {
    expect(etiquetaVeredicto('otro')).toBe('Sin señal')
    expect(etiquetaVeredicto(null)).toBe('Sin señal')
    expect(etiquetaVeredicto(undefined)).toBe('Sin señal')
  })

  it('dormidero pinta en rojo y solido en verde', () => {
    expect(claseVeredicto('dormidero')).toBe('loss')
    expect(claseVeredicto('solido')).toBe('win')
    expect(claseVeredicto('ruido')).toBe('')
  })

  it('sin filas no hay zonas', () => {
    expect(hayZonas(null)).toBe(false)
    expect(hayZonas({ sites: [], spawns: [] })).toBe(false)
  })

  it('con un spawn solo ya hay zonas', () => {
    expect(hayZonas({ sites: [], spawns: [{ spawn: 'Warehouse' }] })).toBe(true)
  })

  it('la nota de muestra usa el minimo de la api', () => {
    expect(notaDeMuestra({ min_rounds: 8 })).toBe('Solo zonas con 8 rondas o más.')
    expect(notaDeMuestra(null)).toBe('Solo zonas con 5 rondas o más.')
  })

  it('la diferencia lleva signo y el margen la banda', () => {
    expect(conSigno(33.5)).toBe('+33.5')
    expect(conSigno(-1.7)).toBe('-1.7')
    expect(conSigno(null)).toBe('—')
    expect(comoMargen(13.8)).toBe('±13.8')
    expect(comoMargen(null)).toBe('—')
  })
})
