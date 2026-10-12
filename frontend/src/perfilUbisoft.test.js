/** Tests de lo que el panel de Ubisoft hace con la respuesta antes de mostrarla. */

import { describe, expect, it } from 'vitest'

import {
  clave,
  cruzarMapas,
  cruzarOperadores,
  filasPlaylists,
  playlistsConDetalle,
} from './components/PerfilUbisoft.jsx'

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

describe('clave', () => {
  it('iguala el mapa de Ubisoft con el del replay', () => {
    expect(clave('CLUBHOUSE')).toBe(clave('Club House'))
    expect(clave('STADIUM BRAVO')).toBe(clave('Stadium (Bravo)'))
  })

  it('iguala un operador con y sin tilde', () => {
    expect(clave('Jäger')).toBe(clave('Jager'))
    expect(clave('Nøkk')).toBe(clave('Nokk'))
    expect(clave('Capitão')).toBe(clave('Capitao'))
  })

  it('sin nombre no revienta', () => {
    expect(clave(undefined)).toBe('')
  })
})

describe('playlistsConDetalle', () => {
  it('pone ranked primero y junta operadores con mapas', () => {
    const playlists = playlistsConDetalle({
      operadores: { casual: [{}], all: [{}] },
      mapas: { ranked: [{}], arcade_nuevo: [{}] },
    })
    expect(playlists).toEqual(['ranked', 'all', 'casual', 'arcade_nuevo'])
  })

  it('una consulta vieja o con error no tiene playlists', () => {
    expect(playlistsConDetalle(undefined)).toEqual([])
    expect(playlistsConDetalle({ error: 'boom' })).toEqual([])
  })
})

describe('cruzarOperadores', () => {
  const temporada = [
    { operador: 'Jäger', lado: 'Defense', rondas: 100 },
    { operador: 'Ash', lado: 'Attack', rondas: 120 },
  ]

  it('pone al lado lo que hizo con el mismo operador en tus replays', () => {
    const filas = cruzarOperadores(temporada, [
      { operator: 'Jager', side: 'Defense', rounds: 29, winrate: 41.4, kd: 0.45 },
    ])
    expect(filas[0]).toMatchObject({
      operador: 'Jäger',
      rondas: 100,
      replay_rondas: 29,
      replay_winrate: 41.4,
      replay_kd: 0.45,
    })
  })

  it('sin rondas en tus replays el cruce queda vacio, no en cero', () => {
    const filas = cruzarOperadores(temporada, [])
    expect(filas[1]).toMatchObject({ replay_rondas: null, replay_winrate: null, replay_kd: null })
  })

  it('el lado importa: el mismo nombre del otro lado no cruza', () => {
    const filas = cruzarOperadores(temporada, [{ operator: 'Ash', side: 'Defense', rounds: 3 }])
    expect(filas[1].replay_rondas).toBeNull()
  })

  it('sin temporada no inventa filas', () => {
    expect(cruzarOperadores(undefined, [{ operator: 'Ash', side: 'Attack' }])).toEqual([])
  })
})

describe('cruzarMapas', () => {
  it('cruza CLUBHOUSE con Club House', () => {
    const filas = cruzarMapas(
      [{ mapa: 'Clubhouse', rondas: 90 }],
      [{ map: 'Club House', rounds: 70, winrate: 57.1, kd: 0.35 }],
    )
    expect(filas[0]).toMatchObject({ replay_rondas: 70, replay_winrate: 57.1, replay_kd: 0.35 })
  })
})
