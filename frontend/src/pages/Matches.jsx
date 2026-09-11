import React, { useState } from 'react'
import { Link } from 'react-router-dom'

import { useApi } from '../api.js'
import { DataTable, EmptyState, ErrorBox, Loading, Panel, ResultChip } from '../components/ui.jsx'

const PAGE = 50

export default function Matches({ runImport, importing }) {
  const [offset, setOffset] = useState(0)
  const { data, error, loading } = useApi('/matches/', { limit: PAGE, offset })

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  if (!data?.total) return <EmptyState onImport={runImport} importing={importing} />

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Partidas</h1>
          <p>{data.total} partidas importadas.</p>
        </div>
      </div>

      <Panel>
        <DataTable
          columns={[
            {
              key: 'played_at',
              label: 'Cuando',
              render: (row) => (
                <Link to={`/partidas/${row.id}`}>{row.played_at.slice(0, 16).replace('T', ' ')}</Link>
              ),
            },
            { key: 'map', label: 'Mapa' },
            { key: 'match_type', label: 'Tipo', dim: true },
            { key: 'score', label: 'Marcador', sortable: false },
            {
              key: 'won',
              label: 'Resultado',
              render: (row) => <ResultChip won={row.won}>{row.result}</ResultChip>,
            },
            { key: 'rounds', label: 'Rondas' },
            { key: 'my_rating', label: 'Rating', digits: 2, help: 'Aporte por ronda comparado con tu propio promedio: 1.00 es tu ronda tipica. Ver docs/metricas.md para la formula y los pesos.' },
            { key: 'my_kills', label: 'Bajas' },
            { key: 'my_deaths', label: 'Muertes' },
            {
              key: 'my_opening_kills',
              label: 'Aperturas',
              render: (row) => `${row.my_opening_kills}-${row.my_opening_deaths}`,
            },
          ]}
          rows={data.matches}
          initialSort={{ key: 'played_at', dir: 'desc' }}
          rowKey={(row) => row.id}
          csvName="partidas"
        />

        {data.total > PAGE ? (
          <div style={{ display: 'flex', gap: 8, marginTop: 12, alignItems: 'center' }}>
            <button className="btn small" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>
              Anteriores
            </button>
            <button
              className="btn small"
              disabled={offset + PAGE >= data.total}
              onClick={() => setOffset(offset + PAGE)}
            >
              Siguientes
            </button>
            <span className="note">
              {offset + 1}–{Math.min(offset + PAGE, data.total)} de {data.total}
            </span>
          </div>
        ) : null}
      </Panel>
    </>
  )
}
