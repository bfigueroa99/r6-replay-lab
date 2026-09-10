import React from 'react'
import {
  Bar as RBar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import { DataTable, EmptyState, ErrorBox, Loading, Panel, fmt } from '../components/ui.jsx'

const AXIS = { stroke: '#8b98a9', fontSize: 11 }
const TOOLTIP = {
  contentStyle: { background: '#171e29', border: '1px solid #263041', borderRadius: 8 },
  labelStyle: { color: '#8b98a9' },
}

export default function Trends({ filters, setFilters, runImport, importing }) {
  const { data, error, loading } = useApi('/trends/', { ...filters, limit: 60 })

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  if (!data?.by_match?.length) return <EmptyState onImport={runImport} importing={importing} />

  const byDay = data.by_day.map((row) => ({ ...row, dia: row.day.slice(5) }))
  const byMatch = data.by_match.map((row, i) => ({
    ...row,
    n: i + 1,
    label: `${row.map} · ${row.played_at.slice(5, 16).replace('T', ' ')}`,
  }))
  const byRound = data.by_round_number.map((row) => ({
    ...row,
    ronda: `R${row.round_number + 1}`,
  }))

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Tendencias</h1>
          <p>Como se mueven tus numeros en el tiempo y en que momento de la partida te caes.</p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} />

      <Panel title="Por dia de juego" hint="Cada punto es una sesion. Sirve para ver si mejoras o si solo tuviste un buen dia.">
        <div style={{ height: 260 }}>
          <ResponsiveContainer>
            <LineChart data={byDay} margin={{ top: 6, right: 12, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#263041" strokeDasharray="3 3" />
              <XAxis dataKey="dia" {...AXIS} />
              <YAxis yAxisId="pct" domain={[0, 100]} {...AXIS} />
              <YAxis yAxisId="kpr" orientation="right" domain={[0, 'auto']} {...AXIS} />
              <Tooltip {...TOOLTIP} formatter={(v, n) => [fmt(v, n === 'KPR' ? 2 : 0), n]} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line yAxisId="pct" type="monotone" dataKey="winrate" name="Rondas ganadas %" stroke="#ff8a3d" strokeWidth={2} />
              <Line yAxisId="pct" type="monotone" dataKey="opening_winrate" name="Aperturas %" stroke="#4aa8ff" strokeWidth={2} />
              <Line yAxisId="pct" type="monotone" dataKey="kst_pct" name="KST %" stroke="#3fb950" strokeWidth={2} />
              <Line yAxisId="kpr" type="monotone" dataKey="kpr" name="KPR" stroke="#d29922" strokeWidth={2} strokeDasharray="4 3" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel title="Por partida" hint="Orden cronologico, de la mas vieja a la mas reciente.">
        <div style={{ height: 240 }}>
          <ResponsiveContainer>
            <LineChart data={byMatch} margin={{ top: 6, right: 12, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#263041" strokeDasharray="3 3" />
              <XAxis dataKey="n" {...AXIS} />
              <YAxis domain={[0, 100]} {...AXIS} />
              <Tooltip
                {...TOOLTIP}
                labelFormatter={(n) => byMatch[n - 1]?.label || ''}
                formatter={(v, n) => [fmt(v, 0), n]}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="winrate" name="Rondas ganadas %" stroke="#ff8a3d" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="kst_pct" name="KST %" stroke="#3fb950" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel
        title="Por numero de ronda"
        hint="Si el winrate cae en las rondas finales, el problema es de decisiones bajo presion, no de aim."
      >
        <div style={{ height: 220 }}>
          <ResponsiveContainer>
            <BarChart data={byRound} margin={{ top: 6, right: 12, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#263041" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="ronda" {...AXIS} />
              <YAxis domain={[0, 100]} {...AXIS} />
              <Tooltip {...TOOLTIP} formatter={(v, n) => [fmt(v, 0), n]} />
              <RBar dataKey="winrate" name="Rondas ganadas %" fill="#ff8a3d" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <DataTable
          columns={[
            { key: 'ronda', label: 'Ronda', sortable: false },
            { key: 'rounds', label: 'Jugadas' },
            { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%' },
            { key: 'kpr', label: 'KPR', digits: 2 },
            { key: 'opening_winrate', label: 'Aperturas', digits: 0, suffix: '%' },
            { key: 'kst_pct', label: 'KST', digits: 0, suffix: '%' },
          ]}
          rows={byRound}
          initialSort={{ key: 'ronda', dir: 'asc' }}
          rowKey={(row) => row.ronda}
        />
      </Panel>
    </>
  )
}
