import { describe, expect, it } from 'vitest'

import { nombresDelGrupo, separadorAntes, textoStackRival } from './stacksRivales.js'

const jugadores = (...nicks) => nicks.map((username, i) => ({ player_id: i + 1, username }))

describe('stacksRivales', () => {
  it('une dos nombres con y', () => {
    expect(nombresDelGrupo(jugadores('A', 'B'))).toBe('A y B')
  })

  it('une tres nombres con comas y y', () => {
    expect(nombresDelGrupo(jugadores('Kaid_', 'Mozzie99', 'Thorn.exe'))).toBe('Kaid_, Mozzie99 y Thorn.exe')
  })

  it('los separadores reconstruyen el mismo texto', () => {
    const grupo = jugadores('A', 'B', 'C', 'D')
    const texto = grupo.map((j, i) => separadorAntes(i, grupo.length) + j.username).join('')
    expect(texto).toBe(nombresDelGrupo(grupo))
  })

  it('el texto lleva partidas y record', () => {
    expect(textoStackRival({ matches: 4, wins: 1, losses: 3 })).toBe(
      'ya te tocaron juntos en 4 partidas, récord 1-3',
    )
  })

  it('una sola partida va en singular', () => {
    expect(textoStackRival({ matches: 1, wins: 1, losses: 0 })).toBe('ya te tocaron juntos en 1 partida, récord 1-0')
  })

  it('avisa las partidas sin resultado', () => {
    expect(textoStackRival({ matches: 5, wins: 2, losses: 1 })).toBe(
      'ya te tocaron juntos en 5 partidas, récord 2-1 (2 sin resultado)',
    )
  })
})
