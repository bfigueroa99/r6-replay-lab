/** Tests de la navegacion de rondas con el teclado (ficha 95). */

import { describe, expect, it } from 'vitest'

import { pasoDeTecla, rondaVecina } from './navegacionRondas.js'

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

  it('otra tecla no hace nada', () => {
    expect(pasoDeTecla({ key: 'ArrowUp', target: cuerpo })).toBe(0)
    expect(pasoDeTecla({ key: 'Enter', target: cuerpo })).toBe(0)
  })

  it('sin destino igual lee la tecla', () => {
    expect(pasoDeTecla({ key: 'ArrowRight', target: null })).toBe(1)
  })
})
