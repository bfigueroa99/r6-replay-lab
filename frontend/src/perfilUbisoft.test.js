/** Tests de lo que el panel de Ubisoft hace con la respuesta antes de mostrarla. */

import { describe, expect, it } from 'vitest'

import { filasPlaylists } from './components/PerfilUbisoft.jsx'

describe('filasPlaylists', () => {
  it('deja fuera las playlists sin partidas', () => {
    const filas = filasPlaylists({
      ranked: { partidas: 51, kd: 1.2 },
      event: { partidas: 0, kd: null },
    })
    expect(filas.map((f) => f.id)).toEqual(['ranked'])
  })

  it('nombra las playlists conocidas y deja las nuevas tal cual', () => {
    const filas = filasPlaylists({
      standard: { partidas: 3 },
      arcade_nuevo: { partidas: 2 },
    })
    expect(filas.map((f) => f.nombre)).toEqual(['Estándar', 'arcade_nuevo'])
  })

  it('sin datos no revienta', () => {
    expect(filasPlaylists(undefined)).toEqual([])
    expect(filasPlaylists(null)).toEqual([])
  })
})
