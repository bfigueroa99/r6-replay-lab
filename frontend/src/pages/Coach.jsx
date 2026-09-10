import React from 'react'

import { useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import { EmptyState, ErrorBox, Loading, Panel } from '../components/ui.jsx'

const GROUPS = [
  { key: 'alta', title: 'Prioridad alta', hint: 'Lo que mas te esta costando rondas.' },
  { key: 'media', title: 'Para trabajar', hint: 'Patrones claros con muestra suficiente.' },
  { key: 'baja', title: 'Para tener en el radar', hint: 'Señales mas debiles o de contexto.' },
  { key: 'positivo', title: 'Tus fortalezas', hint: 'Apoyate en esto al elegir rol y picks.' },
]

export default function Coach({ filters, setFilters, runImport, importing }) {
  const { data, error, loading } = useApi('/coach/', filters)

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  if (!data?.totals?.rounds) return <EmptyState onImport={runImport} importing={importing} />

  const insights = data.insights || []

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Coach</h1>
          <p>
            Reglas sobre {data.totals.rounds} rondas. Cada punto trae el numero, con que se compara
            y cuantas rondas lo respaldan.
          </p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} />

      {GROUPS.map((group) => {
        const rows = insights.filter((i) => i.severity === group.key)
        if (!rows.length) return null
        return (
          <Panel key={group.key} title={group.title} hint={group.hint}>
            {rows.map((insight) => (
              <div key={insight.key} className={`insight ${insight.severity}`}>
                <h3>{insight.title}</h3>
                <p>{insight.detail}</p>
                <div className="action">
                  <b>Que hacer:</b> {insight.action}
                </div>
                <div className="meta">
                  {insight.metric ? (
                    <span>
                      {insight.metric}: <b>{format(insight.value)}</b>
                      {insight.baseline !== null && insight.baseline !== undefined
                        ? ` (referencia ${format(insight.baseline)})`
                        : ''}
                    </span>
                  ) : null}
                  {insight.sample ? <span>muestra: {insight.sample} rondas</span> : null}
                  {insight.scope && insight.scope !== 'general' ? <span>alcance: {insight.scope}</span> : null}
                </div>
              </div>
            ))}
          </Panel>
        )
      })}

      <p className="note">
        Las reglas exigen una muestra minima antes de opinar (20 rondas en general, 8-15 por
        mapa/sitio/operador), asi que si algo no aparece es porque todavia no hay datos para
        afirmarlo.
      </p>
    </>
  )
}

const format = (value) =>
  value === null || value === undefined
    ? '—'
    : typeof value === 'number'
      ? Number(value).toFixed(Math.abs(value) < 10 && !Number.isInteger(value) ? 2 : 0)
      : value
