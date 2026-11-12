import { describe, expect, it } from 'vitest'

import { casosRepetirSitio, filasPorMapa, hayPares, textoPares, textoWinrate } from './repetirSitio.js'

describe('repetirSitio', () => {
  it('sin datos o sin pares no hay nada que mostrar', () => {
    expect(hayPares(null)).toBe(false)
    expect(hayPares({ pairs: 0 })).toBe(false)
    expect(hayPares({ pairs: 3 })).toBe(true)
  })

  it('marca poca muestra por debajo del minimo y no en el minimo', () => {
    const total = {
      repeat: { rounds: 8, winrate: 50 },
      switch: { rounds: 7, winrate: 0 },
    }
    const [repite, cambia] = casosRepetirSitio(total, 8)
    expect(repite).toMatchObject({ clave: 'repeat', titulo: 'Repite el sitio', rounds: 8, winrate: 50, poca: false })
    expect(cambia).toMatchObject({ clave: 'switch', titulo: 'Cambia de sitio', rounds: 7, winrate: 0, poca: true })
  })

  it('un caso sin pares tiene 0 rondas y winrate nulo', () => {
    const [repite] = casosRepetirSitio({}, 8)
    expect(repite).toMatchObject({ rounds: 0, winrate: null, poca: true })
  })

  it('singular y plural de los pares', () => {
    expect(textoPares(1)).toBe('1 ronda perdida en defensa seguida de otra')
    expect(textoPares(58)).toBe('58 rondas perdidas en defensa seguidas de otra')
  })

  it('aplana los casos de cada mapa para la tabla', () => {
    const filas = filasPorMapa({
      min_rounds: 8,
      maps: [{ slug: 'bank', map_id: 0, map: 'Bank', repeat: { rounds: 19, winrate: 0 }, switch: { rounds: 1, winrate: null } }],
    })
    expect(filas).toEqual([
      {
        slug: 'bank', map_id: 0, map: 'Bank', repeat_rounds: 19, repeat_winrate: 0,
        switch_rounds: 1, switch_winrate: null, repeat_poca: false, switch_poca: true,
      },
    ])
    expect(filasPorMapa(null)).toEqual([])
  })

  it('el winrate se redondea como la tabla y avisa la muestra chica', () => {
    expect(textoWinrate(33.3, false)).toBe('33%')
    expect(textoWinrate(null, false)).toBe('—')
    expect(textoWinrate(0, true)).toBe('0% · pocas rondas')
  })
})
