import React from 'react'

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
  pct,
} from '../components/ui.jsx'

export default function Operators({ filters, setFilters, runImport, importing }) {
  const { data, error, loading } = useApi('/operators/', { ...filters, min_rounds: 1 })

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  if (!data?.operators?.length) return <EmptyState onImport={runImport} importing={importing} />

  const rows = data.operators
  const attack = rows.filter((r) => r.side === 'Attack')
  const defense = rows.filter((r) => r.side === 'Defense')

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Operadores</h1>
          <p>Tu pool real, ordenado por rondas jugadas. Ordena por cualquier columna.</p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} showOperator={false} />

      {[
        { title: 'Ataque', rows: attack },
        { title: 'Defensa', rows: defense },
      ].map((group) =>
        group.rows.length ? (
          <Panel key={group.title} title={group.title}>
            <Table rows={group.rows} nombre={`operadores-${group.title.toLowerCase()}`} />
          </Panel>
        ) : null,
      )}

      {!attack.length && !defense.length ? (
        <Panel title="Todos">
          <Table rows={rows} nombre="operadores" />
        </Panel>
      ) : null}
    </>
  )
}

function Table({ rows, nombre }) {
  return (
    <DataTable
      columns={[
        { key: 'operator', label: 'Operador' },
        { key: 'side', label: 'Lado', render: (row) => <SideChip side={row.side} /> },
        { key: 'rounds', label: 'Rondas' },
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
        { key: 'rating', label: 'Rating', digits: 2, help: 'Aporte por ronda comparado con tu propio promedio: 1.00 es tu ronda tipica. Ver docs/metricas.md para la formula y los pesos.' },
        { key: 'kills', label: 'Bajas' },
        { key: 'kpr', label: 'KPR', digits: 2 },
        { key: 'kd', label: 'K/D', digits: 2 },
        { key: 'hs_pct', label: 'HS%', digits: 0, suffix: '%' },
        { key: 'opening_winrate', label: 'Aperturas', digits: 0, suffix: '%' },
        { key: 'survival_pct', label: 'Sobrevives', digits: 0, suffix: '%' },
        { key: 'kst_pct', label: 'KST', digits: 0, suffix: '%' },
      ]}
      rows={rows}
      initialSort={{ key: 'rounds', dir: 'desc' }}
      rowKey={(row) => `${row.operator}-${row.side}`}
      csvName={nombre}
    />
  )
}
