import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react'

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

// ------------------------------------------------------------------ estado

/**
 * Lo poco que la API comparte con toda la app: cuantas peticiones hay en vuelo
 * (para la barra de progreso de la cabecera) y una version de los datos que
 * sube cuando algo cambio en la base. Toda lectura con `useApi` depende de esa
 * version, asi que `invalidar()` despues de importar recarga cada pagina sin
 * que cada una tenga que saber que hubo una importacion.
 */
const estado = { version: 0, enVuelo: 0 }
const oyentes = new Set()

function avisar() {
  for (const oyente of oyentes) oyente()
}

function suscribir(oyente) {
  oyentes.add(oyente)
  return () => oyentes.delete(oyente)
}

export const versionDeDatos = () => estado.version
export const peticionesEnVuelo = () => estado.enVuelo

/** Los datos de la base cambiaron: que todo lo que lee de la API vuelva a leer. */
export function invalidar() {
  estado.version += 1
  avisar()
}

async function pedir(url, options) {
  estado.enVuelo += 1
  avisar()
  try {
    return await fetch(url, options)
  } finally {
    estado.enVuelo -= 1
    avisar()
  }
}

/** Cuantas peticiones a la API estan en curso ahora mismo. */
export function useEnVuelo() {
  return useSyncExternalStore(suscribir, peticionesEnVuelo, peticionesEnVuelo)
}

// ------------------------------------------------------------------ lectura

export async function get(path, params) {
  const response = await pedir(`${BASE}${path}${qs(params)}`)
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText} en ${path}`)
  }
  return response.json()
}

export async function post(path, params, body) {
  const options = { method: 'POST' }
  if (body !== undefined) {
    options.headers = { 'Content-Type': 'application/json' }
    options.body = JSON.stringify(body)
  }
  const response = await pedir(`${BASE}${path}${qs(params)}`, options)
  if (!response.ok) {
    // el backend manda {"error": "..."} en los 400; es mas util que el status
    let detail = `${response.status} ${response.statusText} en ${path}`
    try {
      const data = await response.json()
      if (data?.error) detail = data.error
    } catch {
      /* la respuesta no traia JSON */
    }
    throw new Error(detail)
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
  const version = useSyncExternalStore(suscribir, versionDeDatos, versionDeDatos)

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
  }, [path, serialized, nonce, version, ...deps])

  const reload = useCallback(() => setNonce((n) => n + 1), [])
  return { data, error, loading, reload }
}
