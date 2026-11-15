import React, { useState } from 'react'

import { useApi } from '../api.js'
import { opcionesDeMapa } from '../mapas.js'
import { mostrarSelectorDeModo, opcionesDeModo } from '../modoDeJuego.js'
import { conTipo, hayFiltros, opcionesDeTipo, tipoElegido } from '../tipoPartida.js'

const RANGO_EXACTO = 'rango'

// los valores tienen que ser los DIAS_DEL_PERIODO de filtrosUrl.js
const RANGES = [
  { value: '', label: 'Todo el historial' },
  { value: '7', label: 'Últimos 7 días' },
  { value: '30', label: 'Últimos 30 días' },
  { value: '90', label: 'Últimos 90 días' },
  { value: RANGO_EXACTO, label: 'Entre dos fechas...' },
]

/** "09-09 15:34 · 6 partidas" */
const etiquetaSesion = (s) =>
  `${s.start.slice(5, 16).replace('T', ' ')} · ${s.matches} partida${s.matches === 1 ? '' : 's'}`

/**
 * Barra de filtros compartida. El estado vive en App y en la query de la URL,
 * para que se mantenga al cambiar de pagina y al recargar.
 */
export default function Filters({
  value,
  onChange,
  showOperator = true,
  showSite = false,
  showSession = false,
  showSide = true,
  hayExtra = false,
  children = null,
}) {
  const { data } = useApi('/filters/')
  const set = (key) => (event) => onChange({ ...value, [key]: event.target.value })

  // el modo vive aca y no en los filtros: hay un momento, entre elegir "entre
  // dos fechas" y escribir la primera, en el que no hay nada que mandar a la API
  const [rangoAbierto, setRangoAbierto] = useState(Boolean(value.since || value.until))
  // Atras puede traer fechas, o un periodo, sin que la barra se vuelva a montar
  const abierto = (rangoAbierto && !value.days) || Boolean(value.since || value.until)

  const elegirPeriodo = (event) => {
    const elegido = event.target.value
    setRangoAbierto(elegido === RANGO_EXACTO)
    onChange({
      ...value,
      days: elegido === RANGO_EXACTO ? '' : elegido,
      since: '',
      until: '',
    })
  }

  const limpiar = () => {
    setRangoAbierto(false)
    onChange({})
  }

  return (
    <div className="filters">
      {showSide ? (
        <label>
          Lado
          <select value={value.side || ''} onChange={set('side')}>
            <option value="">Ataque y defensa</option>
            <option value="Attack">Solo ataque</option>
            <option value="Defense">Solo defensa</option>
          </select>
        </label>
      ) : null}

      <label>
        Mapa
        <select value={value.map || ''} onChange={set('map')}>
          <option value="">Todos</option>
          {opcionesDeMapa(data?.maps).map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>

      {showOperator ? (
        <label>
          Operador
          <select value={value.operator || ''} onChange={set('operator')}>
            <option value="">Todos</option>
            {(data?.operators || []).map((op) => (
              <option key={op} value={op}>
                {op}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      {/* un enlace del Coach puede traer el sitio a una pagina sin selector: sin esto quedaria puesto y sin verse */}
      {showSite || value.site ? (
        <label>
          Sitio
          <select value={value.site || ''} onChange={set('site')}>
            <option value="">Todos</option>
            {(data?.sites || []).map((site) => (
              <option key={site} value={site}>
                {site}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      {showSession ? (
        <label>
          Sesión
          <select value={value.session ?? ''} onChange={set('session')}>
            <option value="">Todas</option>
            {(data?.sessions || []).map((s) => (
              <option key={s.index} value={s.index}>
                {etiquetaSesion(s)}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      <label>
        Periodo
        <select
          value={abierto ? RANGO_EXACTO : value.days || ''}
          onChange={elegirPeriodo}
        >
          {RANGES.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>
      </label>

      {abierto ? (
        <>
          <label>
            Desde
            <input type="date" value={value.since || ''} onChange={set('since')} max={value.until || undefined} />
          </label>
          <label>
            Hasta
            <input type="date" value={value.until || ''} onChange={set('until')} min={value.since || undefined} />
          </label>
        </>
      ) : null}

      <label>
        Tipo
        <select value={tipoElegido(value)} onChange={(event) => onChange(conTipo(value, event.target.value))}>
          {opcionesDeTipo(data?.match_types).map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>

      {mostrarSelectorDeModo(data?.gamemodes, value.gamemode) ? (
        <label>
          Modo
          <select value={value.gamemode || ''} onChange={set('gamemode')}>
            {opcionesDeModo(data?.gamemodes, value.gamemode).map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      {/* filtros propios de una pagina (el resultado en Partidas), en la misma fila */}
      {children}

      {hayFiltros(value) || hayExtra ? (
        <button className="btn small" onClick={limpiar}>
          Limpiar
        </button>
      ) : null}
    </div>
  )
}
