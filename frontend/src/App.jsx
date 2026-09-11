import React, { useCallback, useState } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'

import { post, useApi } from './api.js'
import Coach from './pages/Coach.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Datos from './pages/Datos.jsx'
import Duelos from './pages/Duelos.jsx'
import Jugador from './pages/Jugador.jsx'
import MapsPage from './pages/Maps.jsx'
import MatchDetail from './pages/MatchDetail.jsx'
import Matches from './pages/Matches.jsx'
import Operators from './pages/Operators.jsx'
import Teammates from './pages/Teammates.jsx'
import Trends from './pages/Trends.jsx'

const LINKS = [
  { to: '/', label: 'Resumen' },
  { to: '/coach', label: 'Coach' },
  { to: '/mapas', label: 'Mapas y sitios' },
  { to: '/operadores', label: 'Operadores' },
  { to: '/companeros', label: 'Compañeros' },
  { to: '/duelos', label: 'Duelos' },
  { to: '/tendencias', label: 'Tendencias' },
  { to: '/partidas', label: 'Partidas' },
  { to: '/datos', label: 'Datos' },
]

export default function App() {
  const [filters, setFilters] = useState({})
  const [importing, setImporting] = useState(false)
  const [flash, setFlash] = useState(null)
  const health = useApi('/health/')

  const runImport = useCallback(async () => {
    setImporting(true)
    setFlash(null)
    try {
      const result = await post('/import/')
      const ok = result.count || 0
      setFlash(
        ok
          ? `Importadas ${ok} partida(s).`
          : 'No habia partidas nuevas para importar.' +
              (result.errors ? ` ${result.errors} con error.` : ''),
      )
      health.reload()
    } catch (err) {
      setFlash(`Error al importar: ${err.message}`)
    } finally {
      setImporting(false)
    }
  }, [health])

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
          <button className="btn primary small" onClick={runImport} disabled={importing}>
            {importing ? 'Importando...' : 'Importar replays'}
          </button>
        </div>
      </header>

      <main>
        {flash ? <div className="panel" style={{ marginBottom: 14 }}>{flash}</div> : null}
        <Routes>
          <Route path="/" element={<Dashboard {...context} />} />
          <Route path="/coach" element={<Coach {...context} />} />
          <Route path="/mapas" element={<MapsPage {...context} />} />
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
      </main>
    </div>
  )
}
