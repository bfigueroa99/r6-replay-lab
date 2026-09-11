import React, { Suspense, lazy, useCallback, useState } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'

import { get, post, useApi } from './api.js'
import Dashboard from './pages/Dashboard.jsx'
import { Loading } from './components/ui.jsx'

// El Resumen entra en el bundle inicial porque es la pantalla de partida. El
// resto se carga al entrar: son 10 paginas y dos de ellas arrastran recharts,
// que pesa mas que todo lo demas junto.
const Coach = lazy(() => import('./pages/Coach.jsx'))
const Datos = lazy(() => import('./pages/Datos.jsx'))
const Duelos = lazy(() => import('./pages/Duelos.jsx'))
const Jugador = lazy(() => import('./pages/Jugador.jsx'))
const MapsPage = lazy(() => import('./pages/Maps.jsx'))
const MatchDetail = lazy(() => import('./pages/MatchDetail.jsx'))
const Matches = lazy(() => import('./pages/Matches.jsx'))
const Operators = lazy(() => import('./pages/Operators.jsx'))
const Posicionamiento = lazy(() => import('./pages/Posicionamiento.jsx'))
const Teammates = lazy(() => import('./pages/Teammates.jsx'))
const Trends = lazy(() => import('./pages/Trends.jsx'))

const LINKS = [
  { to: '/', label: 'Resumen' },
  { to: '/coach', label: 'Coach' },
  { to: '/mapas', label: 'Mapas y sitios' },
  { to: '/posicionamiento', label: 'Posicionamiento' },
  { to: '/operadores', label: 'Operadores' },
  { to: '/companeros', label: 'Compañeros' },
  { to: '/duelos', label: 'Duelos' },
  { to: '/tendencias', label: 'Tendencias' },
  { to: '/partidas', label: 'Partidas' },
  { to: '/datos', label: 'Datos' },
]

/** Cada cuanto se pregunta como va la importacion, y hasta cuando insistir. */
const POLL_MS = 700
const POLL_MAX = Math.round((20 * 60 * 1000) / POLL_MS)

const espera = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

export default function App() {
  const [filters, setFilters] = useState({})
  const [importing, setImporting] = useState(false)
  const [progreso, setProgreso] = useState(null)
  const [flash, setFlash] = useState(null)
  const health = useApi('/health/')

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
      health.reload()
    } catch (err) {
      setFlash(`Error al importar: ${err.message}`)
    } finally {
      setImporting(false)
      setProgreso(null)
    }
  }, [health])

  const etiquetaImport = !importing
    ? 'Importar replays'
    : progreso?.total
      ? `Importando ${Math.min(progreso.done + 1, progreso.total)} de ${progreso.total}`
      : 'Importando...'

  const context = { filters, setFilters, runImport, importing, health: health.data }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          R6 <span>Replay Lab</span>
        </div>
        <nav className="nav">
          {LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.to === '/'}>
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
          <button
            className="btn primary small"
            onClick={runImport}
            disabled={importing}
            title={progreso?.current ? `Leyendo ${progreso.current}` : undefined}
          >
            {etiquetaImport}
          </button>
        </div>
      </header>

      <main>
        {progreso?.current ? (
          <div className="panel" style={{ marginBottom: 14 }}>
            Leyendo <b>{progreso.current}</b> · {progreso.done} de {progreso.total} listas.
          </div>
        ) : null}
        {flash ? <div className="panel" style={{ marginBottom: 14 }}>{flash}</div> : null}
        <Suspense fallback={<Loading />}>
          <Routes>
          <Route path="/" element={<Dashboard {...context} />} />
          <Route path="/coach" element={<Coach {...context} />} />
          <Route path="/mapas" element={<MapsPage {...context} />} />
          <Route path="/posicionamiento" element={<Posicionamiento {...context} />} />
          <Route path="/operadores" element={<Operators {...context} />} />
          <Route path="/companeros" element={<Teammates {...context} />} />
          <Route path="/duelos" element={<Duelos {...context} />} />
          <Route path="/tendencias" element={<Trends {...context} />} />
          <Route path="/partidas" element={<Matches {...context} />} />
          <Route path="/partidas/:id" element={<MatchDetail />} />
          <Route path="/jugadores/:id" element={<Jugador />} />
          <Route path="/datos" element={<Datos />} />
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
