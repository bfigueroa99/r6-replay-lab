import React, { useState } from 'react'
import { Link } from 'react-router-dom'

import { useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import {
  Bar,
  DataTable,
  EmptyState,
  ErrorBox,
  Loading,
  Panel,
  SideChip,
  fmt,
  pct,
} from '../components/ui.jsx'

const SAMPLES = [
  { value: 5, label: '5+ rondas' },
  { value: 10, label: '10+ rondas' },
  { value: 25, label: '25+ rondas' },
  { value: 50, label: '50+ rondas' },
]

export default function Teammates({ filters, setFilters, runImport, importing }) {
  const [minRounds, setMinRounds] = useState(10)
  const { data, error, loading } = useApi('/teammates/', { ...filters, min_rounds: minRounds })
  const overview = useApi('/overview/', filters)

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />

  const base = overview.data?.overall
  if (base && !base.rounds) return <EmptyState onImport={runImport} importing={importing} />

  const baseline = base?.winrate ?? null
  const rows = (data?.synergy || []).map((row) => ({
    ...row,
    delta: baseline === null || row.winrate === null ? null : row.winrate - baseline,
  }))
  const clutches = data?.clutches || []

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Compañeros</h1>
          <p>
            Con quien ganas y con quien no. Solo cuentan las rondas que jugaron en tu equipo
            {baseline === null ? '' : `, contra tu ${baseline.toFixed(0)}% general`}.
          </p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} />

      <Panel
        title="Sinergia"
        hint="El winrate de un compañero es el de las rondas compartidas, no el suyo aparte. Con pocas rondas es varianza: sube la muestra minima antes de sacar conclusiones."
        right={
          <label className="note" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            Muestra minima
            <select value={minRounds} onChange={(e) => setMinRounds(Number(e.target.value))}>
              {SAMPLES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
        }
      >
        <DataTable
          columns={[
            { key: 'username', label: 'Compañero', left: true },
            { key: 'rounds', label: 'Rondas juntos' },
            {
              key: 'winrate',
              label: 'Ganadas',
              render: (row) => (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
                  <Bar value={row.winrate} />
                  <span style={{ minWidth: 38 }}>{pct(row.winrate)}</span>
                </div>
              ),
            },
            {
              key: 'delta',
              label: 'vs tu promedio',
              help: 'Diferencia en puntos entre el winrate con esa persona y tu winrate general con los mismos filtros.',
              render: (row) =>
                row.delta === null ? (
                  <span className="dim">—</span>
                ) : (
                  <span className={row.delta >= 0 ? 'chip win' : 'chip loss'}>
                    {row.delta > 0 ? '+' : ''}
                    {row.delta.toFixed(0)}
                  </span>
                ),
            },
            { key: 'kills', label: 'Sus bajas' },
            { key: 'kpr', label: 'Su KPR', digits: 2 },
          ]}
          rows={rows}
          initialSort={{ key: 'rounds', dir: 'desc' }}
          rowKey={(row) => row.player_id}
          csvName="companeros"
          empty={`Nadie llega a ${minRounds} rondas contigo con estos filtros.`}
        />
      </Panel>

      <Panel
        title="Clutches"
        hint="Rondas que cerraste quedandote solo. El .rec no dice cuando quedaste ultimo, asi que el 1vX sale del scoreboard de la ronda."
      >
        <DataTable
          columns={[
            {
              key: 'played_at',
              label: 'Cuando',
              render: (row) => (
                <Link to={`/partidas/${row.match_id}`}>
                  {row.played_at.slice(5, 16).replace('T', ' ')}
                </Link>
              ),
            },
            { key: 'match', label: 'Mapa' },
            { key: 'round', label: 'Ronda', render: (row) => `R${row.round}` },
            { key: 'site', label: 'Sitio', left: true, dim: true },
            { key: 'side', label: 'Lado', render: (row) => <SideChip side={row.side} /> },
            { key: 'operator', label: 'Operador' },
            { key: 'vs', label: '1vX', render: (row) => `1v${row.vs}` },
            { key: 'kills', label: 'Bajas', render: (row) => fmt(row.kills) },
          ]}
          rows={clutches}
          initialSort={{ key: 'played_at', dir: 'desc' }}
          rowKey={(row) => `${row.match_id}-${row.round}`}
          csvName="clutches"
          empty="Todavia no ganaste ninguna ronda quedandote solo."
        />
      </Panel>
    </>
  )
}
