import React, { useState } from 'react'

import { useApi } from '../api.js'

const RANGO_EXACTO = 'rango'

const RANGES = [
  { value: '', label: 'Todo el historial' },
  { value: '7', label: 'Ultimos 7 dias' },
  { value: '30', label: 'Ultimos 30 dias' },
  { value: '90', label: 'Ultimos 90 dias' },
  { value: RANGO_EXACTO, label: 'Entre dos fechas...' },
]

/** "09-09 15:34 · 6 partidas" */
const etiquetaSesion = (s) =>
  `${s.start.slice(5, 16).replace('T', ' ')} · ${s.matches} partida${s.matches === 1 ? '' : 's'}`

/**
 * Barra de filtros compartida. El estado vive en App para que se mantenga al
 * cambiar de pagina.
 */
export default function Filters({
  value,
  onChange,
  showOperator = true,
  showSite = false,
  showSession = false,
}) {
  const { data } = useApi('/filters/')
  const set = (key) => (event) => onChange({ ...value, [key]: event.target.value })

  // el modo vive aca y no en los filtros: hay un momento, entre elegir "entre
  // dos fechas" y escribir la primera, en el que no hay nada que mandar a la API
  const [rangoAbierto, setRangoAbierto] = useState(Boolean(value.since || value.until))

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
      <label>
        Lado
        <select value={value.side || ''} onChange={set('side')}>
          <option value="">Ataque y defensa</option>
          <option value="Attack">Solo ataque</option>
          <option value="Defense">Solo defensa</option>
        </select>
      </label>

      <label>
        Mapa
        <select value={value.map || ''} onChange={set('map')}>
          <option value="">Todos</option>
          {(data?.maps || []).map((m) => (
            <option key={m.map_slug} value={m.map_slug}>
              {m.map_name}
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

      {showSite ? (
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
          Sesion
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
          value={rangoAbierto ? RANGO_EXACTO : value.days || ''}
          onChange={elegirPeriodo}
        >
          {RANGES.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>
      </label>

      {rangoAbierto ? (
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

      <label className="check">
        <input
          type="checkbox"
          checked={Boolean(value.ranked_only)}
          onChange={(event) => onChange({ ...value, ranked_only: event.target.checked })}
        />
        Solo ranked
      </label>

      {Object.values(value).some(Boolean) ? (
        <button className="btn small" onClick={limpiar}>
          Limpiar
        </button>
      ) : null}
    </div>
  )
}
