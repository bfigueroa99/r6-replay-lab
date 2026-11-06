import { describe, expect, it } from 'vitest'

import { claseSitio, etiquetaSitio, textoSinFilas } from './operadorSitio.js'

describe('operadorSitio', () => {
  it('cada veredicto tiene su etiqueta', () => {
    expect(etiquetaSitio('rinde')).toBe('Te rinde')
    expect(etiquetaSitio('hunde')).toBe('Te hunde')
    expect(etiquetaSitio('ruido')).toBe('Sin señal')
  })

  it('un veredicto desconocido o ausente no dice nada', () => {
    expect(etiquetaSitio('otro')).toBe('Sin señal')
    expect(etiquetaSitio(undefined)).toBe('Sin señal')
    expect(claseSitio('otro')).toBe('')
    expect(claseSitio(undefined)).toBe('')
  })

  it('rinde va en verde, hunde en rojo y el ruido sin color', () => {
    expect(claseSitio('rinde')).toBe('win')
    expect(claseSitio('hunde')).toBe('loss')
    expect(claseSitio('ruido')).toBe('')
  })

  it('el texto sin filas usa el minimo que manda la api', () => {
    expect(textoSinFilas({ min_rounds: 5 })).toBe(
      'Ningún operador llega a 5 rondas en un sitio (ni el resto del sitio).',
    )
  })

  it('sin minimo en la respuesta cae en 10', () => {
    expect(textoSinFilas({})).toContain('llega a 10 rondas')
    expect(textoSinFilas(null)).toContain('llega a 10 rondas')
  })
})
