import React, { Suspense, lazy, useCallback, useEffect, useRef, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation, useNavigate, useNavigationType } from 'react-router-dom'

import { get, post, useApi } from './api.js'
import { conFiltros, filtrosDeUrl, mismosFiltros, queryDeFiltros, usaFiltros } from './filtrosUrl.js'
import { avisoAutomatico, etiquetaImportacion } from './importacion.js'
import Dashboard from './pages/Dashboard.jsx'
import { Loading } from './components/ui.jsx'

// El Resumen entra en el bundle inicial porque es la pantalla de partida. El
// resto se carga al entrar: son 10 paginas y dos de ellas arrastran recharts,
// que pesa mas que todo lo demas junto.
const Ajustes = lazy(() => import('./pages/Ajustes.jsx'))
const Coach = lazy(() => import('./pages/Coach.jsx'))
const Comparar = lazy(() => import('./pages/Comparar.jsx'))
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
  { to: '/ajustes', label: 'Ajustes' },
]

/** Cada cuanto se pregunta como va la importacion, y hasta cuando insistir. */
const POLL_MS = 700
const POLL_MAX = Math.round((20 * 60 * 1000) / POLL_MS)
/** Sin nada corriendo, cada cuanto se mira si el vigilante empezo a importar. */
const IDLE_MS = 10_000

const espera = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

export default function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const navigationType = useNavigationType()
  // perezoso y no en un efecto: Filters decide si abre el rango de fechas al
  // montarse y las paginas piden a la API en el primer render
  const [filters, setFilters] = useState(() =>
    usaFiltros(location.pathname) ? filtrosDeUrl(location.search) : {},
  )
  const filtrosActuales = useRef(filters)
  filtrosActuales.current = filters
  const [importing, setImporting] = useState(false)
  const [progreso, setProgreso] = useState(null)
  const [flash, setFlash] = useState(null)
  const [auto, setAuto] = useState(null)
  const health = useApi('/health/')
  const recargarHealth = health.reload

  // El vigilante del backend importa solo al terminar cada partida. La UI no lo
  // lanzo, asi que se entera preguntando: rapido mientras corre, cada 10 s si
  // no. Mientras el boton importa, su propio bucle ya sigue el trabajo.
  useEffect(() => {
    if (importing) return undefined
    let vivo = true
    let timer
    let anterior = null
    const mirar = async () => {
      let job = null
      try {
        job = await get('/import/progress/')
      } catch {
        /* el backend puede estar reiniciando: se vuelve a mirar en el proximo */
      }
      if (!vivo) return
      if (job) {
        const aviso = avisoAutomatico(anterior, job)
        if (aviso) {
          setFlash(aviso)
          recargarHealth()
        }
        setAuto(job.running && job.origin === 'auto' ? job : null)
        anterior = job
      }
      timer = setTimeout(mirar, job?.running ? POLL_MS : IDLE_MS)
    }
    mirar()
    return () => {
      vivo = false
      clearTimeout(timer)
    }
  }, [importing, recargarHealth])

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
            : 'No había partidas nuevas para importar.' +
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

  // replace siempre: cada cambio de select no tiene que ser una entrada de historial
  const cambiarFiltros = useCallback(
    (nuevos) => {
      setFilters(nuevos)
      if (usaFiltros(location.pathname)) navigate(conFiltros(location.pathname, nuevos), { replace: true })
    },
    [location.pathname, navigate],
  )

  // La URL manda cuando la trae el navegador (carga, recarga, Atras, URL
  // pegada) o cuando viene con filtros; un Link interno sin query ("Ver en
  // Duelos") hereda los del estado, que es lo que mantiene los filtros al
  // cambiar de pagina. Solo se navega si la query difiere: sin eso, bucle.
  useEffect(() => {
    if (!usaFiltros(location.pathname)) return
    const actual = location.search.replace(/^\?/, '')
    const desdeUrl = filtrosDeUrl(actual)
    const canonica = queryDeFiltros(desdeUrl)
    if (navigationType === 'POP' || canonica !== '' || actual !== '') {
      if (!mismosFiltros(desdeUrl, filtrosActuales.current)) setFilters(desdeUrl)
      // ?days=abc&x=1: la barra de direcciones no puede decir algo que la pagina no hace
      if (canonica !== actual) navigate(conFiltros(location.pathname, desdeUrl), { replace: true })
    } else if (queryDeFiltros(filtrosActuales.current) !== '') {
      navigate(conFiltros(location.pathname, filtrosActuales.current), { replace: true })
    }
  }, [location.pathname, location.search, navigationType, navigate])

  const enCurso = importing ? progreso : auto
  const etiquetaImport = etiquetaImportacion(enCurso, importing)

  const context = { filters, setFilters: cambiarFiltros, runImport, importing, health: health.data }

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
              to={usaFiltros(link.to) ? conFiltros(link.to, filters) : link.to}
              end={link.to === '/'}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="topbar-right">
          {health.data?.player_id ? (
            <Link className="chip" to={`/jugadores/${health.data.player_id}`} title="Tu perfil">
              {health.data.player}
            </Link>
          ) : health.data?.player ? (
            <span className="chip">{health.data.player}</span>
          ) : null}
          {health.data ? (
            <span className="note">
              {health.data.matches} partidas · {health.data.rounds} rondas
            </span>
          ) : null}
          <button
            className="btn primary small"
            onClick={runImport}
            disabled={importing || Boolean(auto)}
            title={enCurso?.current ? `Leyendo ${enCurso.current}` : undefined}
          >
            {etiquetaImport}
          </button>
        </div>
      </header>

      <main>
        {enCurso?.current ? (
          <div className="panel" style={{ marginBottom: 14 }}>
            {importing ? 'Leyendo' : 'Importando sola'} <b>{enCurso.current}</b> · {enCurso.done} de{' '}
            {enCurso.total} listas.
          </div>
        ) : null}
        {flash ? <div className="panel" style={{ marginBottom: 14 }}>{flash}</div> : null}
        <Suspense fallback={<Loading />}>
          <Routes>
          <Route path="/" element={<Dashboard {...context} />} />
          <Route path="/coach" element={<Coach {...context} />} />
          <Route path="/operadores" element={<Operators {...context} />} />
          <Route path="/companeros" element={<Teammates {...context} />} />
          <Route path="/duelos" element={<Duelos {...context} />} />
          <Route path="/tendencias" element={<Trends {...context} />} />
          <Route path="/partidas" element={<Matches {...context} />} />
          <Route path="/partidas/:id" element={<MatchDetail />} />
          <Route path="/comparar/:a" element={<Comparar />} />
          <Route path="/comparar/:a/:b" element={<Comparar />} />
          <Route path="/jugadores/:id" element={<Jugador />} />
          <Route path="/ruleta" element={<Ruleta />} />
          <Route path="/datos" element={<Datos />} />
          <Route path="/ajustes" element={<Ajustes onCambio={recargarHealth} />} />
          <Route
            path="*"
            element={
              <div className="empty-state">
                <h2>Esa página no existe</h2>
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
