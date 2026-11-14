import { describe, expect, it } from 'vitest'

import { conPocaMuestra, filasMuertesHeadshot, textoCelda } from './muertesHeadshot.js'

const celda = (pct, withData) => ({ deaths: withData, with_data: withData, headshots: 0, pct })

function datos({ me = celda(null, 0), teammates = celda(null, 0) } = {}) {
  return {
    me: { Attack: me, Defense: celda(null, 0), total: me },
    teammates: { Attack: celda(null, 0), Defense: teammates, total: teammates },
  }
}

describe('muertesHeadshot', () => {
  it('sin muertes con dato no hay filas, para mostrar la nota y no ceros', () => {
    expect(filasMuertesHeadshot(undefined)).toEqual([])
    expect(filasMuertesHeadshot(datos())).toEqual([])
  })

  it('va primero Tú y despues tus compañeros, con el orden fijo', () => {
    const filas = filasMuertesHeadshot(datos({ teammates: celda(40, 10) }))
    expect(filas.map((f) => [f.grupo, f.orden])).toEqual([
      ['Tú', 0],
      ['Tus compañeros', 1],
    ])
    expect(filas[1].defensa).toEqual({ pct: 40, with_data: 10 })
  })

  it('una celda sin dato queda con pct nulo y se ve como raya', () => {
    const [tu] = filasMuertesHeadshot(datos({ me: celda(50, 2) }))
    expect(tu.defensa).toEqual({ pct: null, with_data: 0 })
    expect(textoCelda(tu.defensa)).toBe('—')
    expect(textoCelda(tu.ataque)).toBe('50% (2)')
    expect(textoCelda({ pct: 66.7, with_data: 3 })).toBe('67% (3)')
  })

  it('avisa la muestra chica solo entre 1 y 29 muertes con dato', () => {
    const conMuestra = (n) => conPocaMuestra(filasMuertesHeadshot(datos({ me: celda(10, n) })))
    expect(conMuestra(29)).toBe(true)
    expect(conMuestra(1)).toBe(true)
    expect(conMuestra(30)).toBe(false)
    // las celdas en 0 no avisan: salen con raya
    expect(conPocaMuestra([])).toBe(false)
  })
})
