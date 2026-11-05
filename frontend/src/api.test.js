import { afterEach, describe, expect, it, vi } from 'vitest'

import { get } from './api.js'

const fetchOriginal = globalThis.fetch

afterEach(() => {
  globalThis.fetch = fetchOriginal
})

describe('get', () => {
  it('con un 404 tira un error con el status', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false, status: 404, statusText: 'Not Found' })
    const error = await get('/matches/999999/').catch((err) => err)
    expect(error.status).toBe(404)
    expect(error.message).toBe('404 Not Found en /matches/999999/')
  })

  it('con la red caida tira un error sin status', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    const error = await get('/matches/1/').catch((err) => err)
    expect(error).toBeInstanceOf(TypeError)
    expect(error.status).toBeUndefined()
  })
})
