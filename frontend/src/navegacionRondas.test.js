/** Tests de la navegacion de rondas con el teclado (ficha 95). */

import { describe, expect, it } from 'vitest'

import {
  anclaDeRonda,
  indiceDeAncla,
  pasoDeTecla,
  pideSiguientePerdida,
  rondaVecina,
  siguientePerdida,
} from './navegacionRondas.js'

describe('rondaVecina', () => {
  it('avanza y retrocede una ronda', () => {
    expect(rondaVecina(3, 9, 1)).toBe(4)
    expect(rondaVecina(3, 9, -1)).toBe(2)
  })

  it('no se pasa de la primera ni de la ultima', () => {
    expect(rondaVecina(0, 9, -1)).toBe(0)
    expect(rondaVecina(8, 9, 1)).toBe(8)
  })

  it('una ronda fuera de rango vuelve al borde', () => {
    expect(rondaVecina(12, 9, 1)).toBe(8)
  })

  it('sin rondas devuelve 0', () => {
    expect(rondaVecina(0, 0, 1)).toBe(0)
    expect(rondaVecina(2, 0, -1)).toBe(0)
  })
})

const cuerpo = { tagName: 'BODY', isContentEditable: false }

describe('pasoDeTecla', () => {
  it('flecha izquierda retrocede y derecha avanza', () => {
    expect(pasoDeTecla({ key: 'ArrowLeft', target: cuerpo })).toBe(-1)
    expect(pasoDeTecla({ key: 'ArrowRight', target: cuerpo })).toBe(1)
  })

  it('cada modificador deja la tecla al navegador', () => {
    for (const mod of ['altKey', 'ctrlKey', 'metaKey', 'shiftKey']) {
      expect(pasoDeTecla({ key: 'ArrowLeft', target: cuerpo, [mod]: true })).toBe(0)
      expect(pasoDeTecla({ key: 'ArrowRight', target: cuerpo, [mod]: true })).toBe(0)
    }
  })

  it('con el foco en un campo no cambia la ronda', () => {
    for (const tagName of ['INPUT', 'SELECT', 'TEXTAREA']) {
      expect(pasoDeTecla({ key: 'ArrowRight', target: { tagName } })).toBe(0)
    }
    expect(pasoDeTecla({ key: 'ArrowRight', target: { tagName: 'DIV', isContentEditable: true } })).toBe(0)
  })

  it('dentro de una tabla con scroll horizontal la flecha desplaza la tabla', () => {
    const celda = { tagName: 'TD', closest: (sel) => (sel.includes('.table-wrap') ? {} : null) }
    expect(pasoDeTecla({ key: 'ArrowRight', target: celda })).toBe(0)
    const fuera = { tagName: 'DIV', closest: () => null }
    expect(pasoDeTecla({ key: 'ArrowRight', target: fuera })).toBe(1)
  })

  it('una tecla que otro widget ya tomo no cambia la ronda', () => {
    expect(pasoDeTecla({ key: 'ArrowRight', target: cuerpo, defaultPrevented: true })).toBe(0)
  })

  it('otra tecla no hace nada', () => {
    expect(pasoDeTecla({ key: 'ArrowUp', target: cuerpo })).toBe(0)
    expect(pasoDeTecla({ key: 'Enter', target: cuerpo })).toBe(0)
  })

  it('sin destino igual lee la tecla', () => {
    expect(pasoDeTecla({ key: 'ArrowRight', target: null })).toBe(1)
  })
})

const rondas = (...numeros) => numeros.map((number) => ({ number }))

describe('indiceDeAncla', () => {
  it('busca la ronda por su numero y no por la posicion', () => {
    expect(indiceDeAncla('#ronda-1', rondas(0, 1, 2))).toBe(0)
    expect(indiceDeAncla('#ronda-3', rondas(0, 1, 2))).toBe(2)
    // falta el .rec de la ronda 3: la R4 esta en la posicion 2
    expect(indiceDeAncla('#ronda-4', rondas(0, 1, 3))).toBe(2)
    expect(indiceDeAncla('#ronda-3', rondas(0, 1, 3))).toBeNull()
  })

  it('un ancla que no es de ronda o que no existe no elige nada', () => {
    for (const hash of ['', '#', '#ronda-', '#ronda-abc', '#ronda-0', '#ronda--1', '#ronda-1.5', '#ronda-01x', '#otra-2', '#ronda-999']) {
      expect(indiceDeAncla(hash, rondas(0, 1, 2)), hash).toBeNull()
    }
  })

  it('aguanta la partida sin rondas o sin datos', () => {
    expect(indiceDeAncla('#ronda-1', [])).toBeNull()
    expect(indiceDeAncla('#ronda-1', undefined)).toBeNull()
    expect(indiceDeAncla(undefined, rondas(0))).toBeNull()
  })
})

describe('anclaDeRonda', () => {
  it('usa el numero humano de la ronda, el de la etiqueta R<n>', () => {
    expect(anclaDeRonda(0)).toBe('#ronda-1')
    expect(anclaDeRonda(6)).toBe('#ronda-7')
  })
})

const ronda = (my_team_won) => ({ my_team_won })

describe('siguientePerdida', () => {
  it('salta a la proxima perdida despues de la elegida', () => {
    const rounds = [ronda(false), ronda(true), ronda(true), ronda(false), ronda(false)]
    expect(siguientePerdida(0, rounds)).toBe(3)
    expect(siguientePerdida(3, rounds)).toBe(4)
  })

  it('da la vuelta al final', () => {
    const rounds = [ronda(true), ronda(false), ronda(true), ronda(true)]
    expect(siguientePerdida(2, rounds)).toBe(1)
    expect(siguientePerdida(3, rounds)).toBe(1)
  })

  it('una ronda sin ganador no cuenta como perdida', () => {
    const rounds = [ronda(true), ronda(null), { }, ronda(false)]
    expect(siguientePerdida(0, rounds)).toBe(3)
  })

  it('sin perdidas devuelve null', () => {
    expect(siguientePerdida(0, [ronda(true), ronda(null)])).toBeNull()
    expect(siguientePerdida(0, [])).toBeNull()
    expect(siguientePerdida(0, undefined)).toBeNull()
  })

  it('con la elegida como unica perdida devuelve la misma', () => {
    expect(siguientePerdida(1, [ronda(true), ronda(false), ronda(true)])).toBe(1)
  })

  it('un indice fuera de rango se acota como en rondaVecina', () => {
    const rounds = [ronda(false), ronda(true), ronda(false)]
    expect(siguientePerdida(9, rounds)).toBe(0)
    expect(siguientePerdida(-3, rounds)).toBe(2)
  })
})

describe('pideSiguientePerdida', () => {
  it('la p pide el salto', () => {
    expect(pideSiguientePerdida({ key: 'p', target: cuerpo })).toBe(true)
    // Bloq Mayus: Shift ya queda afuera por los modificadores
    expect(pideSiguientePerdida({ key: 'P', target: cuerpo })).toBe(true)
  })

  it('con modificadores, en un campo o con la tecla tomada no', () => {
    for (const mod of ['altKey', 'ctrlKey', 'metaKey', 'shiftKey']) {
      expect(pideSiguientePerdida({ key: 'p', target: cuerpo, [mod]: true })).toBe(false)
    }
    for (const tagName of ['INPUT', 'SELECT', 'TEXTAREA']) {
      expect(pideSiguientePerdida({ key: 'p', target: { tagName } })).toBe(false)
    }
    expect(pideSiguientePerdida({ key: 'p', target: { tagName: 'DIV', isContentEditable: true } })).toBe(false)
    expect(pideSiguientePerdida({ key: 'p', target: cuerpo, defaultPrevented: true })).toBe(false)
  })

  it('otra tecla no', () => {
    expect(pideSiguientePerdida({ key: 'o', target: cuerpo })).toBe(false)
    expect(pideSiguientePerdida({ key: 'ArrowRight', target: cuerpo })).toBe(false)
  })
})
