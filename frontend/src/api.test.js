/**
 * El estado compartido de la API: la version de los datos y las peticiones en
 * vuelo. Se prueba con un fetch falso; no hace falta servidor ni DOM.
 */

import { afterEach, describe, expect, it, vi } from 'vitest'

import { get, invalidar, peticionesEnVuelo, post, versionDeDatos } from './api.js'

const respuesta = (body, ok = true, status = 200) => ({
  ok,
  status,
  statusText: ok ? 'OK' : 'Bad Request',
  json: async () => body,
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('invalidar', () => {
  it('sube la version cada vez', () => {
    const antes = versionDeDatos()
    invalidar()
    invalidar()
    expect(versionDeDatos()).toBe(antes + 2)
  })
})

describe('peticiones en vuelo', () => {
  it('cuenta mientras la peticion no vuelve y baja al terminar', async () => {
    let liberar
    vi.stubGlobal(
      'fetch',
      () => new Promise((resolve) => {
        liberar = () => resolve(respuesta({ ok: true }))
      }),
    )
    expect(peticionesEnVuelo()).toBe(0)
    const pendiente = get('/health/')
    expect(peticionesEnVuelo()).toBe(1)
    liberar()
    await expect(pendiente).resolves.toEqual({ ok: true })
    expect(peticionesEnVuelo()).toBe(0)
  })

  it('baja tambien si la peticion falla', async () => {
    vi.stubGlobal('fetch', async () => respuesta({ error: 'no' }, false, 400))
    await expect(get('/x/')).rejects.toThrow('400')
    expect(peticionesEnVuelo()).toBe(0)
  })

  it('un fallo de red tambien libera el contador', async () => {
    vi.stubGlobal('fetch', async () => {
      throw new TypeError('Failed to fetch')
    })
    await expect(get('/x/')).rejects.toThrow('Failed to fetch')
    expect(peticionesEnVuelo()).toBe(0)
  })
})

describe('post', () => {
  it('prefiere el error que manda el backend al status', async () => {
    vi.stubGlobal('fetch', async () => respuesta({ error: 'no mandaste ninguna etiqueta' }, false, 400))
    await expect(post('/overrides/', undefined, {})).rejects.toThrow('no mandaste ninguna etiqueta')
  })

  it('manda el cuerpo como JSON', async () => {
    const llamadas = []
    vi.stubGlobal('fetch', async (url, options) => {
      llamadas.push([url, options])
      return respuesta({ ok: true })
    })
    await post('/import/', { force: true }, { a: 1 })
    expect(llamadas[0][0]).toBe('/api/import/?force=1')
    expect(llamadas[0][1].body).toBe('{"a":1}')
    expect(llamadas[0][1].headers['Content-Type']).toBe('application/json')
  })
})
