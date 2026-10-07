/**
 * Tests de la logica de la ruleta: que entra en la rueda, en que gajo para y
 * que los ajustes guardados no revienten la pagina.
 */

import { describe, expect, it } from 'vitest'

import {
  AJUSTES_DEFAULT,
  PUNTERO,
  VUELTA,
  anguloFinal,
  colorGajo,
  easeOutCubic,
  gajoBajoPuntero,
  normalizarAjustes,
  operadoresEnRueda,
  tamanoLetra,
} from './ruleta.js'

const CATALOGO = [
  { name: 'Mute', side: 'Defense' },
  { name: 'Ash', side: 'Attack' },
  { name: 'Smoke', side: 'Defense' },
  { name: 'Zofia', side: 'Attack' },
  { name: 'IQ', side: 'Attack' },
]

describe('operadoresEnRueda', () => {
  it('con todos van primero los atacantes y despues los defensores, en orden', () => {
    expect(operadoresEnRueda(CATALOGO, 'all').map((o) => o.name)).toEqual([
      'Ash',
      'IQ',
      'Zofia',
      'Mute',
      'Smoke',
    ])
  })

  it('filtra por lado', () => {
    expect(operadoresEnRueda(CATALOGO, 'Defense').map((o) => o.name)).toEqual(['Mute', 'Smoke'])
  })

  it('saca los excluidos', () => {
    expect(operadoresEnRueda(CATALOGO, 'Attack', ['IQ']).map((o) => o.name)).toEqual(['Ash', 'Zofia'])
  })

  it('sin catalogo devuelve una rueda vacia, no un error', () => {
    expect(operadoresEnRueda(null, 'all')).toEqual([])
    expect(operadoresEnRueda(undefined, 'all', undefined)).toEqual([])
  })

  it('no toca el catalogo original', () => {
    const copia = [...CATALOGO]
    operadoresEnRueda(CATALOGO, 'all')
    expect(CATALOGO).toEqual(copia)
  })
})

describe('gajoBajoPuntero', () => {
  it('sin girar, el puntero cae en el gajo que arranca en 3/4 de vuelta', () => {
    // con 4 gajos de un cuarto cada uno, el gajo 3 va de 3pi/2 a 2pi
    expect(gajoBajoPuntero(0, 4)).toBe(3)
  })

  it('girar media vuelta mueve el puntero al gajo de enfrente', () => {
    expect(gajoBajoPuntero(Math.PI, 4)).toBe(1)
  })

  it('las vueltas completas no cambian el resultado', () => {
    for (const n of [1, 3, 7, 60]) {
      expect(gajoBajoPuntero(1.234 + 5 * VUELTA, n)).toBe(gajoBajoPuntero(1.234, n))
    }
  })

  it('los angulos negativos tambien caen dentro del rango', () => {
    for (let a = -20; a < 20; a += 0.37) {
      const i = gajoBajoPuntero(a, 9)
      expect(i).toBeGreaterThanOrEqual(0)
      expect(i).toBeLessThan(9)
    }
  })

  it('justo en el puntero gana el gajo que empieza ahi', () => {
    // el gajo i cubre [angulo + i*gajo, angulo + (i+1)*gajo)
    const gajo = VUELTA / 5
    expect(gajoBajoPuntero(PUNTERO - 2 * gajo, 5)).toBe(2)
  })

  it('con la rueda vacia no hay gajo', () => {
    expect(gajoBajoPuntero(0, 0)).toBe(-1)
  })
})

describe('anguloFinal', () => {
  it('da entre 6 y 10 vueltas mas desde donde estaba', () => {
    expect(anguloFinal(1, () => 0)).toBeCloseTo(1 + 6 * VUELTA)
    expect(anguloFinal(1, () => 0.999)).toBeLessThan(1 + 10 * VUELTA)
  })

  it('siempre gira hacia adelante', () => {
    for (let i = 0; i < 50; i += 1) expect(anguloFinal(3)).toBeGreaterThan(3)
  })
})

describe('easeOutCubic', () => {
  it('empieza en 0, termina en 1 y nunca retrocede', () => {
    expect(easeOutCubic(0)).toBe(0)
    expect(easeOutCubic(1)).toBe(1)
    let previo = 0
    for (let t = 0.05; t <= 1; t += 0.05) {
      const valor = easeOutCubic(t)
      expect(valor).toBeGreaterThanOrEqual(previo)
      previo = valor
    }
  })

  it('frena al final: la segunda mitad avanza menos que la primera', () => {
    expect(easeOutCubic(0.5)).toBeGreaterThan(0.5)
  })
})

describe('colores y letra', () => {
  it('alterna dos tonos del mismo lado', () => {
    expect(colorGajo(0, 'Attack')).not.toBe(colorGajo(1, 'Attack'))
    expect(colorGajo(0, 'Attack')).toBe(colorGajo(2, 'Attack'))
  })

  it('ataque y defensa se distinguen', () => {
    expect(colorGajo(0, 'Attack')).not.toBe(colorGajo(0, 'Defense'))
  })

  it('la letra se achica con mas operadores y tiene piso y techo', () => {
    expect(tamanoLetra(250, 10)).toBeGreaterThan(tamanoLetra(250, 70))
    expect(tamanoLetra(250, 500)).toBe(10)
    expect(tamanoLetra(250, 2)).toBe(18)
    expect(tamanoLetra(250, 0)).toBe(16)
  })
})

describe('normalizarAjustes', () => {
  it('sin nada guardado devuelve los valores por defecto', () => {
    expect(normalizarAjustes(null)).toEqual(AJUSTES_DEFAULT)
    expect(normalizarAjustes('basura')).toEqual(AJUSTES_DEFAULT)
  })

  it('conserva lo valido y descarta lo roto', () => {
    const ajustes = normalizarAjustes({
      lado: 'Defense',
      duracion: '7',
      quitarElegido: 'si',
      fondo: 'verde',
      excluidos: ['Ash', 3, 'Ash', ''],
    })
    expect(ajustes.lado).toBe('Defense')
    expect(ajustes.duracion).toBe(7)
    expect(ajustes.quitarElegido).toBe(false)
    expect(ajustes.fondo).toBe(AJUSTES_DEFAULT.fondo)
    expect(ajustes.excluidos).toEqual(['Ash'])
  })

  it('un lado desconocido vuelve a todos', () => {
    expect(normalizarAjustes({ lado: 'Recruit' }).lado).toBe('all')
  })

  it('la duracion se acota a lo que soporta el control', () => {
    expect(normalizarAjustes({ duracion: 99 }).duracion).toBe(10)
    expect(normalizarAjustes({ duracion: -1 }).duracion).toBe(1)
    expect(normalizarAjustes({ duracion: 'nan' }).duracion).toBe(AJUSTES_DEFAULT.duracion)
  })
})
