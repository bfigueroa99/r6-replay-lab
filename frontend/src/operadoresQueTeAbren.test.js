/** Tests de la tabla "Operadores que te abren" de Duelos. */

import { describe, expect, it } from 'vitest'

import { filasOperadoresQueTeAbren } from './operadoresQueTeAbren.js'

const fila = (operator, side, openedYou) => ({ operator, side, opened_you: openedYou, you_opened: 1 })

describe('filasOperadoresQueTeAbren', () => {
  it('sin filas no hay tabla', () => {
    expect(filasOperadoresQueTeAbren(undefined)).toEqual([])
    expect(filasOperadoresQueTeAbren([])).toEqual([])
  })

  it('la clave separa el mismo operador en dos lados', () => {
    const filas = filasOperadoresQueTeAbren([fila('Thorn', 'Attack', 2), fila('Thorn', 'Defense', 1)])
    expect(filas.map((f) => f.key)).toEqual(['Thorn-Attack', 'Thorn-Defense'])
    expect(filas[0]).toMatchObject({ operator: 'Thorn', side: 'Attack', opened_you: 2, you_opened: 1 })
  })

  it('no reordena: el orden es el de la API', () => {
    const filas = filasOperadoresQueTeAbren([fila('Ash', 'Attack', 1), fila('Thorn', 'Defense', 3)])
    expect(filas.map((f) => f.operator)).toEqual(['Ash', 'Thorn'])
  })
})
