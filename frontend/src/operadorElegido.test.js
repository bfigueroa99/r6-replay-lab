import { describe, expect, it } from 'vitest'

import { claseFilaOperador, sinOperador, textoOperadorElegido } from './operadorElegido.js'

describe('sinOperador', () => {
  it('quita operator y deja el resto', () => {
    const filtros = { side: 'Attack', operator: 'Ash' }
    expect(sinOperador(filtros)).toEqual({ side: 'Attack' })
    expect(filtros.operator).toBe('Ash')
  })

  it('sin operator devuelve los mismos filtros', () => {
    expect(sinOperador({ side: 'Defense', map: 'bank' })).toEqual({ side: 'Defense', map: 'bank' })
    expect(sinOperador(undefined)).toEqual({})
  })
})

describe('claseFilaOperador', () => {
  it('marca solo la fila elegida', () => {
    expect(claseFilaOperador({ operator: 'Ash' }, 'Ash')).toBe('me')
    expect(claseFilaOperador({ operator: 'Zofia' }, 'Ash')).toBe('')
    expect(claseFilaOperador({ operator: 'Ash' }, '')).toBe('')
    expect(claseFilaOperador({ operator: 'Ash' }, undefined)).toBe('')
  })
})

describe('textoOperadorElegido', () => {
  it('vacio sin operador y con el nombre si hay uno', () => {
    expect(textoOperadorElegido('')).toBe('')
    expect(textoOperadorElegido(undefined)).toBe('')
    const texto = textoOperadorElegido('Ash')
    expect(texto).toContain('Con Ash elegido')
    expect(texto).toContain('se filtran a Ash')
    expect(texto).toContain('Tu pool no cambia')
  })
})
