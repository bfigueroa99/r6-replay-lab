import React, { Suspense, lazy, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { NavLink, Route, Routes, useLocation, useSearchParams } from 'react-router-dom'

import { get, invalidar, post, useApi, useEnVuelo } from './api.js'
import { filtrosDesdeQuery, queryDesdeFiltros } from './filtros.js'
import Dashboard from './pages/Dashboard.jsx'
import { Loading } from './components/ui.jsx'
import { VIGIA_MS, guardarVigia, leerVigia, nuevasParaImportar } from './vigia.js'

// El Resumen entra en el bundle inicial porque es la pantalla de partida. El
// resto se carga al entrar: son 8 paginas y dos de ellas arrastran recharts,
// que pesa mas que todo lo demas junto.
const Coach = lazy(() => import('./pages/Coach.jsx'))
const Datos = lazy(() => import('./pages/Datos.jsx'))
const Duelos = lazy(() => import('./pages/Duelos.jsx'))
const Jugador = lazy(() => import('./pages/Jugador.jsx'))
const MatchDetail = lazy(() => import('./pages/MatchDetail.jsx'))
const Matches = lazy(() => import('./pages/Matches.jsx'))
const Operators = lazy(() => import('./pages/Operators.jsx'))
const Ruleta = lazy(() => import('./pages/Ruleta.jsx'))
const Teammates = lazy(() => import('./pages/Teammates.jsx'))
const Trends = lazy(() => import('./pages/Trends.jsx'))

const LINKS = [
  { to: '/', label: 'Resumen' },
  { to: '/coach', label: 'Coach' },
  { to: '/operadores', label: 'Operadores' },
  { to: '/companeros', label: 'Compañeros' },
  { to: '/duelos', label: 'Duelos' },
  { to: '/tendencias', label: 'Tendencias' },
  { to: '/partidas', label: 'Partidas' },
  { to: '/ruleta', label: 'Ruleta' },
  { to: '/datos', label: 'Datos' },
]

/** Cada cuanto se pregunta como va la importacion, y hasta cuando insistir. */
const POLL_MS = 700
const POLL_MAX = Math.round((20 * 60 * 1000) / POLL_MS)

const espera = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

export default function App() {
  // los filtros viven en la URL: recargar no los pierde, el enlace se puede
  // compartir y una senal del coach puede apuntar a "estas rondas"
  const [searchParams, setSearchParams] = useSearchParams()
  const search = searchParams.toString()
  const filters = useMemo(() => filtrosDesdeQuery(search), [search])
  const setFilters = useCallback(
    (next) => setSearchParams(queryDesdeFiltros(next), { replace: true }),
    [setSearchParams],
  )
  const { search: searchActual } = useLocation()

  const [importing, setImporting] = useState(false)
  const [progreso, setProgreso] = useState(null)
  const [flash, setFlash] = useState(null)
  const [vigilar, setVigilarEstado] = useState(() => leerVigia(localStorage))
  const health = useApi('/health/')
  // `health` es un objeto nuevo en cada render; `reload` no. Si runImport
  // dependiera del objeto, el vigia reiniciaria su timer en cada render.
  const recargarHealth = health.reload
  const enVuelo = useEnVuelo()

  const setVigilar = useCallback((encendido) => {
    guardarVigia(localStorage, encendido)
    setVigilarEstado(encendido)
  }, [])

  const runImport = useCallback(async () => {
    setImporting(true)
    setFlash(null)
    setProgreso(null)
    try {
      // el POST lanza la importacion y vuelve enseguida; el avance va aparte
      let job = await post('/import/')
      for (let i = 0; job.running && i < POLL_MAX; i += 1) {
        setProgreso(job)
        await espera(POLL_MS)
        job = await get('/import/progress/')
      }

      const ok = job.count || 0
      setFlash(
        job.error
          ? `Error al importar: ${job.error}`
          : ok
            ? `Importadas ${ok} partida(s).` + (job.errors ? ` ${job.errors} con error.` : '')
            : 'No habia partidas nuevas para importar.' +
              (job.errors ? ` ${job.errors} con error.` : ''),
      )
      // hubo cambios en la base: cada pagina vuelve a leer lo suyo
      if (ok || job.errors) invalidar()
      recargarHealth()
    } catch (err) {
      setFlash(`Error al importar: ${err.message}`)
    } finally {
      setImporting(false)
      setProgreso(null)
    }
  }, [recargarHealth])

  // El vigia: mientras la app esta abierta, pregunta cada tanto si hay partidas
  // listas (terminadas y quietas) y las importa solas. Es la version sin consola
  // de `manage.py watch_replays`. Lo intentado se recuerda para que una carpeta
  // corrupta no dispare una importacion fallida en cada revision.
  const intentadas = useRef(new Set())
  const importingRef = useRef(false)
  importingRef.current = importing
  useEffect(() => {
    if (!vigilar) return undefined
    let activo = true
    const revisar = async () => {
      if (!activo || importingRef.current) return
      try {
        const status = await get('/import/status/')
        const nuevas = nuevasParaImportar(status.ready, intentadas.current)
        if (!activo || !nuevas.length) return
        nuevas.forEach((carpeta) => intentadas.current.add(carpeta))
        await runImport()
      } catch {
        /* sin backend no hay nada que vigilar; la proxima revision lo reintenta */
      }
    }
    revisar()
    const timer = setInterval(revisar, VIGIA_MS)
    return () => {
      activo = false
      clearInterval(timer)
    }
  }, [vigilar, runImport])

  const etiquetaImport = !importing
    ? 'Importar replays'
    : progreso?.total
      ? `Importando ${Math.min(progreso.done + 1, progreso.total)} de ${progreso.total}`
      : 'Importando...'

  const context = {
    filters,
    setFilters,
    runImport,
    importing,
    health: health.data,
    vigilar,
    setVigilar,
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          R6 <span>Replay Lab</span>
        </div>
        <nav className="nav">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={{ pathname: link.to, search: searchActual }}
              end={link.to === '/'}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="topbar-right">
          {health.data?.player ? <span className="chip">{health.data.player}</span> : null}
          {health.data ? (
            <span className="note">
              {health.data.matches} partidas · {health.data.rounds} rondas
            </span>
          ) : null}
          {vigilar ? (
            <span
              className="chip vigia"
              title={`Importa sola las partidas nuevas mientras la app está abierta (revisa cada ${VIGIA_MS / 1000} s). Se apaga en Datos.`}
            >
              vigilando
            </span>
          ) : null}
          <button
            className="btn primary small"
            onClick={runImport}
            disabled={importing}
            title={progreso?.current ? `Leyendo ${progreso.current}` : undefined}
          >
            {etiquetaImport}
          </button>
        </div>
        <div className={`progreso ${enVuelo ? 'activo' : ''}`} aria-hidden="true" />
      </header>

      <main>
        {progreso?.current ? (
          <div className="panel" style={{ marginBottom: 14 }}>
            Leyendo <b>{progreso.current}</b> · {progreso.done} de {progreso.total} listas.
          </div>
        ) : null}
        {flash ? (
          <div className="panel flash-import" style={{ marginBottom: 14 }}>
            {flash}
            <button className="btn small" onClick={() => setFlash(null)} aria-label="Cerrar aviso">
              ×
            </button>
          </div>
        ) : null}
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<Dashboard {...context} />} />
            <Route path="/coach" element={<Coach {...context} />} />
            <Route path="/operadores" element={<Operators {...context} />} />
            <Route path="/companeros" element={<Teammates {...context} />} />
            <Route path="/duelos" element={<Duelos {...context} />} />
            <Route path="/tendencias" element={<Trends {...context} />} />
            <Route path="/partidas" element={<Matches {...context} />} />
            <Route path="/partidas/:id" element={<MatchDetail {...context} />} />
            <Route path="/jugadores/:id" element={<Jugador {...context} />} />
            <Route path="/ruleta" element={<Ruleta />} />
            <Route path="/datos" element={<Datos {...context} />} />
            <Route
              path="*"
              element={
                <div className="empty-state">
                  <h2>Esa pagina no existe</h2>
                  <NavLink className="btn" to="/">
                    Volver al resumen
                  </NavLink>
                </div>
              }
            />
          </Routes>
        </Suspense>
      </main>
    </div>
  )
}
