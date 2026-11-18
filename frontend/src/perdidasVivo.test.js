import { describe, expect, it } from 'vitest'

import { enlaceDeRonda, filasPorLado, hayPerdidas } from './perdidasVivo.js'

const celda = (lost, alive, pct) => ({ lost, lost_alive: alive, pct })

const datos = {
  total: celda(40, 10, 25),
  sides: [
    { side: 'Attack', ...celda(25, 9, 36) },
    { side: 'Defense', ...celda(15, 1, 6.7) },
  ],
  maps: [],
  recent: [],
}

describe('perdidasVivo', () => {
  it('sin rondas perdidas no hay nada que mostrar', () => {
    expect(hayPerdidas(undefined)).toBe(false)
    expect(hayPerdidas({ total: celda(0, 0, null) })).toBe(false)
    expect(hayPerdidas(datos)).toBe(true)
    expect(filasPorLado(undefined)).toEqual([])
  })

  it('ataque, defensa y total, en ese orden y con su etiqueta', () => {
    const filas = filasPorLado(datos)
    expect(filas.map((f) => [f.lado, f.orden])).toEqual([
      ['Ataque', 0],
      ['Defensa', 1],
      ['Total', 2],
    ])
    expect(filas[2]).toMatchObject({ clave: 'total', lost: 40, lost_alive: 10, pct: 25 })
  })

  it('marca pocas rondas perdidas por debajo del corte, sin avisar en las vacias', () => {
    const filas = filasPorLado({
      total: celda(30, 3, 10),
      sides: [{ side: 'Attack', ...celda(29, 3, 10.3) }, { side: 'Defense', ...celda(0, 0, null) }],
    })
    expect(filas.map((f) => f.poca)).toEqual([true, false, false])
  })

  it('el enlace abre el detalle de la partida en esa ronda', () => {
    expect(enlaceDeRonda({ match_id: 7, number: 0 })).toBe('/partidas/7#ronda-1')
    expect(enlaceDeRonda({ match_id: 12, number: 5 })).toBe('/partidas/12#ronda-6')
  })
})
