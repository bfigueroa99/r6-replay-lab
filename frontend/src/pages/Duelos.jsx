import React, { useState } from 'react'
import { Link } from 'react-router-dom'

import { useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import { Bar, DataTable, EmptyState, ErrorBox, Loading, Panel, pct } from '../components/ui.jsx'

const MUESTRAS = [
  { value: 3, label: '3+ duelos' },
  { value: 5, label: '5+ duelos' },
  { value: 10, label: '10+ duelos' },
]

/** Verde si le ganas al rival, rojo si te gana. */
function Balance({ value }) {
  if (value === null || value === undefined) return <span className="dim">—</span>
  if (value === 0) return <span className="chip">0</span>
  return <span className={`chip ${value > 0 ? 'win' : 'loss'}`}>{value > 0 ? `+${value}` : value}</span>
}

/** Diferencia en puntos contra tu promedio. `mejorSiSube` decide el color. */
function Diferencia({ value, mejorSiSube }) {
  if (value === null || value === undefined) return <span className="dim">—</span>
  if (Math.round(value) === 0) return <span className="chip">0</span>
  const bueno = mejorSiSube ? value > 0 : value < 0
  return (
    <span className={`chip ${bueno ? 'win' : 'loss'}`}>
      {value > 0 ? '+' : ''}
      {value.toFixed(0)}
    </span>
  )
}

export default function Duelos({ filters, setFilters, runImport, importing }) {
  const [minDuels, setMinDuels] = useState(3)
  const { data, error, loading } = useApi('/duels/', { ...filters, min_duels: minDuels })

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />

  const totals = data?.totals
  if (!totals?.duels) return <EmptyState onImport={runImport} importing={importing} />

  const base = totals.winrate
  const nemesis = data.nemesis || []
  const operators = data.operators || []
  const faced = data.faced || { base: {}, operators: [] }

  const selector = (
    <label className="note" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      Muestra minima
      <select value={minDuels} onChange={(e) => setMinDuels(Number(e.target.value))}>
        {MUESTRAS.map((m) => (
          <option key={m.value} value={m.value}>
            {m.label}
          </option>
        ))}
      </select>
    </label>
  )

  const columnaDuelos = {
    key: 'winrate',
    label: 'Ganas',
    render: (row) => (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
        <Bar value={row.winrate} />
        <span style={{ minWidth: 38 }}>{pct(row.winrate)}</span>
      </div>
    ),
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Duelos</h1>
          <p>
            Quien te mata y a quien matas. Sale del kill feed, no de un scoreboard: son duelos
            reales, uno contra uno.
          </p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} />

      <div className="kpis" style={{ marginBottom: 18 }}>
        <div className="stat">
          <div className="label">Duelos</div>
          <div className="value">{totals.duels}</div>
          <div className="sub">bajas y muertes contra rivales</div>
        </div>
        <div className={`stat ${base >= 50 ? 'good' : base <= 40 ? 'bad' : ''}`}>
          <div className="label">Ganados</div>
          <div className="value">{pct(base)}</div>
          <div className="sub">
            {totals.kills} a favor · {totals.deaths} en contra
          </div>
        </div>
      </div>

      <Panel
        title="Por operador rival"
        hint={
          'Con que operador te estaban matando. El operador sale del scoreboard de esa ronda, ' +
          'porque el kill feed del .rec no lo trae en el evento. Un porcentaje muy bajo suele ' +
          'ser utilidad que no estas limpiando, no punteria.'
        }
        right={selector}
      >
        <DataTable
          columns={[
            { key: 'operator', label: 'Operador', left: true },
            { key: 'duels', label: 'Duelos' },
            { key: 'kills', label: 'Le ganas' },
            { key: 'deaths', label: 'Te gana' },
            { key: 'balance', label: 'Balance', render: (row) => <Balance value={row.balance} /> },
            columnaDuelos,
          ]}
          rows={operators}
          initialSort={{ key: 'duels', dir: 'desc' }}
          rowKey={(row) => row.operator}
          csvName="duelos-por-operador"
          empty={`Ningun operador llega a ${minDuels} duelos con estos filtros.`}
        />
      </Panel>

      <Panel
        title="Rondas contra cada operador"
        hint={
          'Todas las rondas en que ese operador estuvo del otro lado, haya o no un duelo. Mide ' +
          'lo que te condiciona sin matarte: un Mira que corta la entrada o un Jäger que se come ' +
          `tu utilidad. La comparación es contra tus ${faced.base.rounds ?? 0} rondas con estos ` +
          `filtros (mueres en el ${pct(faced.base.death_rate)}, ganas el ` +
          `${pct(faced.base.winrate)}). Desde 10 rondas; con tan poca muestra, una diferencia ` +
          'de 10 o 15 puntos todavía puede ser ruido.'
        }
      >
        <DataTable
          columns={[
            { key: 'operator', label: 'Operador', left: true },
            { key: 'rounds', label: 'Rondas' },
            { key: 'death_rate', label: 'Mueres', render: (row) => pct(row.death_rate) },
            {
              key: 'death_rate_delta',
              label: 'Mueres vs. promedio',
              help: 'Puntos de diferencia entre cuánto mueres con este operador enfrente y cuánto mueres en todas tus rondas filtradas.',
              render: (row) => <Diferencia value={row.death_rate_delta} mejorSiSube={false} />,
            },
            { key: 'winrate', label: 'Ganas la ronda', render: (row) => pct(row.winrate) },
            {
              key: 'winrate_delta',
              label: 'Ganas vs. promedio',
              help: 'Puntos de diferencia entre el winrate de estas rondas y el de todas tus rondas filtradas.',
              render: (row) => <Diferencia value={row.winrate_delta} mejorSiSube />,
            },
          ]}
          rows={faced.operators}
          initialSort={{ key: 'rounds', dir: 'desc' }}
          rowKey={(row) => row.operator}
          csvName="rondas-por-operador-rival"
          empty="Ningún operador rival llega a 10 rondas con estos filtros."
        />
      </Panel>

      <Panel
        title="Por rival"
        hint={
          'Agrupado por persona (profileID), asi que un cambio de nick no parte la fila. En ' +
          'ranked solo casi nadie se repite: con pocos duelos esto es anecdota y no patron, y ' +
          'por eso el coach solo opina desde 8 duelos contra la misma persona.'
        }
      >
        <DataTable
          columns={[
            {
              key: 'username',
              label: 'Rival',
              left: true,
              render: (row) => <Link to={`/jugadores/${row.player_id}`}>{row.username}</Link>,
            },
            { key: 'duels', label: 'Duelos' },
            { key: 'kills', label: 'Le ganas' },
            { key: 'deaths', label: 'Te gana' },
            { key: 'balance', label: 'Balance', render: (row) => <Balance value={row.balance} /> },
            columnaDuelos,
            {
              key: 'opening_duels',
              label: 'De apertura',
              help: 'Duelos que fueron la primera baja de la ronda. Perder siempre el primer contacto contra alguien es distinto a perderlo en general.',
              render: (row) =>
                row.opening_duels ? `${row.opening_kills}-${row.opening_deaths}` : '—',
            },
            {
              key: 'maps',
              label: 'Mapas',
              left: true,
              dim: true,
              wrap: true,
              sortable: false,
              render: (row) => row.maps.join(', ') || '—',
            },
          ]}
          rows={nemesis}
          initialSort={{ key: 'duels', dir: 'desc' }}
          rowKey={(row) => row.player_id}
          csvName="duelos-por-rival"
          empty={`Nadie llega a ${minDuels} duelos contigo con estos filtros.`}
        />
      </Panel>
    </>
  )
}
