import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { useApi } from '../api.js'
import Rueda from '../components/Rueda.jsx'
import { ErrorBox, Loading, Panel, SideChip } from '../components/ui.jsx'
import {
  AJUSTES_KEY,
  LADOS,
  anguloFinal,
  easeOutCubic,
  gajoBajoPuntero,
  normalizarAjustes,
  operadoresEnRueda,
} from '../ruleta.js'

const HISTORIAL_MAX = 12

function cargarAjustes() {
  try {
    return normalizarAjustes(JSON.parse(localStorage.getItem(AJUSTES_KEY)))
  } catch {
    return normalizarAjustes(null)
  }
}

/**
 * Ruleta de operadores, al estilo de r6roulette.de: eliges lado, giras y la
 * rueda te dice con quien juegas. Todo pasa en el navegador; el backend solo
 * presta el catalogo de operadores con su lado.
 */
export default function Ruleta() {
  const { data, error, loading } = useApi('/operators/catalog/')
  const [ajustes, setAjustes] = useState(cargarAjustes)
  const [angulo, setAngulo] = useState(0)
  const [girando, setGirando] = useState(false)
  const [resaltado, setResaltado] = useState(null)
  const [resultado, setResultado] = useState(null)
  const [historial, setHistorial] = useState([])
  const anguloRef = useRef(0)
  const frameRef = useRef(0)

  const cambiar = useCallback((parche) => setAjustes((actual) => ({ ...actual, ...parche })), [])

  useEffect(() => {
    try {
      localStorage.setItem(AJUSTES_KEY, JSON.stringify(ajustes))
    } catch {
      /* sin localStorage (modo privado) los ajustes duran la sesion y listo */
    }
  }, [ajustes])

  // modo streamer: fondo liso de un color para recortar con chroma en OBS.
  // Es la pagina normal con otro fondo, no una ventana flotante.
  useEffect(() => {
    document.body.classList.toggle('streamer', ajustes.streamer)
    document.body.style.setProperty('--streamer-bg', ajustes.fondo)
    return () => {
      document.body.classList.remove('streamer')
      document.body.style.removeProperty('--streamer-bg')
    }
  }, [ajustes.streamer, ajustes.fondo])

  const catalogo = data?.operators
  const operadores = useMemo(
    () => operadoresEnRueda(catalogo, ajustes.lado, ajustes.excluidos),
    [catalogo, ajustes.lado, ajustes.excluidos],
  )

  // cualquier cambio en la rueda invalida el gajo marcado: ya no apunta al mismo
  useEffect(() => {
    setResaltado(null)
  }, [operadores])

  useEffect(() => () => cancelAnimationFrame(frameRef.current), [])

  const terminar = useCallback((lista) => {
    const indice = gajoBajoPuntero(anguloRef.current, lista.length)
    const elegido = indice >= 0 ? lista[indice] : null
    setGirando(false)
    setResaltado(indice >= 0 ? indice : null)
    setResultado(elegido)
    if (!elegido) return
    setHistorial((previo) => [elegido, ...previo].slice(0, HISTORIAL_MAX))
    // se lee el estado al terminar y no al arrancar: durante el giro se puede
    // haber tocado la lista de excluidos o la casilla
    setAjustes((actual) =>
      actual.quitarElegido && !actual.excluidos.includes(elegido.name)
        ? { ...actual, excluidos: [...actual.excluidos, elegido.name] }
        : actual,
    )
  }, [])

  const girar = useCallback(() => {
    if (girando || !operadores.length) return
    const lista = operadores
    const desde = anguloRef.current
    const hasta = anguloFinal(desde)
    const total = ajustes.duracion * 1000
    let inicio = null
    setGirando(true)
    setResaltado(null)
    setResultado(null)

    const paso = (ahora) => {
      if (inicio === null) inicio = ahora
      const t = Math.min((ahora - inicio) / total, 1)
      anguloRef.current = desde + (hasta - desde) * easeOutCubic(t)
      setAngulo(anguloRef.current)
      if (t < 1) frameRef.current = requestAnimationFrame(paso)
      else terminar(lista)
    }
    frameRef.current = requestAnimationFrame(paso)
  }, [girando, operadores, ajustes.duracion, terminar])

  // espacio gira y Escape sale del modo streamer, como en la ruleta original
  useEffect(() => {
    const onKey = (e) => {
      const enCampo = ['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target?.tagName)
      if (e.code === 'Space' && !enCampo) {
        e.preventDefault()
        girar()
      }
      if (e.code === 'Escape' && ajustes.streamer) cambiar({ streamer: false })
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [girar, ajustes.streamer, cambiar])

  const alternar = (nombre) =>
    cambiar({
      excluidos: ajustes.excluidos.includes(nombre)
        ? ajustes.excluidos.filter((n) => n !== nombre)
        : [...ajustes.excluidos, nombre],
    })

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />

  const porLado = (side) => (catalogo || []).filter((op) => op.side === side)

  return (
    <>
      <div className="page-head ruleta-head">
        <div>
          <h1>Ruleta de operadores</h1>
          <p>Elige lado, gira y juega con lo que salga. Espacio también gira.</p>
        </div>
        <button
          className={`btn ${ajustes.streamer ? 'primary' : ''}`}
          onClick={() => cambiar({ streamer: !ajustes.streamer })}
        >
          {ajustes.streamer ? 'Salir del modo streamer (Esc)' : 'Modo streamer'}
        </button>
      </div>

      <div className="ruleta">
        <div className="ruleta-centro">
          <div className="lados" role="radiogroup" aria-label="Lado">
            {LADOS.map((lado) => (
              <button
                key={lado.key}
                className={`lado-btn ${lado.key} ${ajustes.lado === lado.key ? 'active' : ''}`}
                aria-pressed={ajustes.lado === lado.key}
                disabled={girando}
                onClick={() => cambiar({ lado: lado.key })}
              >
                {lado.label}
              </button>
            ))}
          </div>

          <Rueda
            operadores={operadores}
            angulo={angulo}
            resaltado={resaltado}
            girando={girando}
            onClick={girar}
          />

          <button className="btn primary girar" onClick={girar} disabled={girando || !operadores.length}>
            {girando ? 'Girando...' : 'GIRAR'}
          </button>

          <div className={`resultado ${resultado ? 'show' : ''}`} aria-live="polite">
            {resultado ? (
              <>
                <span className="resultado-label">Te toca</span>
                <span className="resultado-nombre">{resultado.name}</span>
                <SideChip side={resultado.side} />
              </>
            ) : (
              <span className="resultado-label">
                {operadores.length
                  ? `${operadores.length} operadores en la rueda`
                  : 'Repón algún operador para poder girar'}
              </span>
            )}
          </div>
        </div>

        <aside className="ruleta-aside">
          <Panel title="Ajustes">
            <label className="ajuste">
              <span>
                Duración del giro <b>{ajustes.duracion} s</b>
              </span>
              <input
                type="range"
                min="1"
                max="10"
                step="1"
                value={ajustes.duracion}
                onChange={(e) => cambiar({ duracion: Number(e.target.value) })}
              />
            </label>
            <label className="ajuste check">
              <input
                type="checkbox"
                checked={ajustes.quitarElegido}
                onChange={(e) => cambiar({ quitarElegido: e.target.checked })}
              />
              <span>Quitar de la rueda al que salga (para repartir en el equipo)</span>
            </label>
            <label className="ajuste">
              <span>Fondo del modo streamer</span>
              <span className="color-row">
                <input
                  type="color"
                  value={ajustes.fondo}
                  onChange={(e) => cambiar({ fondo: e.target.value })}
                />
                <code>{ajustes.fondo}</code>
              </span>
            </label>
          </Panel>

          <Panel
            title="Operadores en juego"
            hint="Toca uno para sacarlo de la rueda o reponerlo."
            right={
              ajustes.excluidos.length ? (
                <button className="btn small" onClick={() => cambiar({ excluidos: [] })}>
                  Reponer todos ({ajustes.excluidos.length})
                </button>
              ) : null
            }
          >
            {[
              { side: 'Attack', label: 'Ataque' },
              { side: 'Defense', label: 'Defensa' },
            ].map((grupo) => (
              <div key={grupo.side} className="pool">
                <div className="pool-label">{grupo.label}</div>
                <div className="pool-chips">
                  {porLado(grupo.side).map((op) => {
                    const fuera = ajustes.excluidos.includes(op.name)
                    return (
                      <button
                        key={op.name}
                        className={`pool-chip ${grupo.side === 'Attack' ? 'atk' : 'def'} ${fuera ? 'fuera' : ''}`}
                        aria-pressed={!fuera}
                        onClick={() => alternar(op.name)}
                      >
                        {op.name}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
          </Panel>

          {historial.length ? (
            <Panel
              title="Últimos giros"
              right={
                <button className="btn small" onClick={() => setHistorial([])}>
                  Limpiar
                </button>
              }
            >
              <ol className="historial">
                {historial.map((op, i) => (
                  <li key={`${op.name}-${i}`}>
                    <span>{op.name}</span>
                    <SideChip side={op.side} />
                  </li>
                ))}
              </ol>
            </Panel>
          ) : null}
        </aside>
      </div>
    </>
  )
}
