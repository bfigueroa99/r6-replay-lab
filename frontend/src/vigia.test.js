import { describe, expect, it } from 'vitest'

import { VIGIA_KEY, guardarVigia, leerVigia, nuevasParaImportar } from './vigia.js'

const memoria = (inicial = {}) => {
  const datos = { ...inicial }
  return {
    getItem: (k) => (k in datos ? datos[k] : null),
    setItem: (k, v) => {
      datos[k] = String(v)
    },
    datos,
  }
}

describe('leerVigia', () => {
  it('por defecto esta encendido', () => {
    expect(leerVigia(memoria())).toBe(true)
  })

  it('solo "off" lo apaga', () => {
    expect(leerVigia(memoria({ [VIGIA_KEY]: 'off' }))).toBe(false)
    expect(leerVigia(memoria({ [VIGIA_KEY]: 'false' }))).toBe(true)
    expect(leerVigia(memoria({ [VIGIA_KEY]: '' }))).toBe(true)
  })

  it('un storage roto no tumba la app', () => {
    const roto = {
      getItem: () => {
        throw new Error('bloqueado')
      },
    }
    expect(leerVigia(roto)).toBe(true)
  })
})

describe('guardarVigia', () => {
  it('escribe on/off y se vuelve a leer igual', () => {
    const storage = memoria()
    guardarVigia(storage, false)
    expect(leerVigia(storage)).toBe(false)
    guardarVigia(storage, true)
    expect(leerVigia(storage)).toBe(true)
  })

  it('un storage que no deja escribir no revienta', () => {
    const roto = {
      setItem: () => {
        throw new Error('lleno')
      },
    }
    expect(() => guardarVigia(roto, true)).not.toThrow()
  })
})

describe('nuevasParaImportar', () => {
  it('devuelve solo las carpetas que no se intentaron', () => {
    const intentadas = new Set(['Match-a'])
    expect(nuevasParaImportar(['Match-a', 'Match-b'], intentadas)).toEqual(['Match-b'])
  })

  it('sin listas no hay nada que importar', () => {
    expect(nuevasParaImportar([], new Set())).toEqual([])
    expect(nuevasParaImportar(undefined, new Set())).toEqual([])
  })

  it('una carpeta corrupta ya intentada no vuelve a disparar', () => {
    const intentadas = new Set(['Match-corrupta'])
    expect(nuevasParaImportar(['Match-corrupta'], intentadas)).toEqual([])
  })
})
