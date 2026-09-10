import { useCallback, useEffect, useRef, useState } from 'react'

const BASE = '/api'

export function qs(params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === '' || value === null || value === undefined || value === false) return
    search.set(key, value === true ? '1' : value)
  })
  const text = search.toString()
  return text ? `?${text}` : ''
}

export async function get(path, params) {
  const response = await fetch(`${BASE}${path}${qs(params)}`)
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText} en ${path}`)
  }
  return response.json()
}

export async function post(path, params) {
  const response = await fetch(`${BASE}${path}${qs(params)}`, { method: 'POST' })
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText} en ${path}`)
  }
  return response.json()
}

/** Hook de lectura: devuelve { data, error, loading, reload }. */
export function useApi(path, params, deps = []) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [nonce, setNonce] = useState(0)
  const alive = useRef(true)

  const serialized = qs(params)

  useEffect(() => {
    alive.current = true
    setLoading(true)
    get(path, params)
      .then((payload) => {
        if (alive.current) {
          setData(payload)
          setError(null)
        }
      })
      .catch((err) => alive.current && setError(err.message))
      .finally(() => alive.current && setLoading(false))
    return () => {
      alive.current = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, serialized, nonce, ...deps])

  const reload = useCallback(() => setNonce((n) => n + 1), [])
  return { data, error, loading, reload }
}
