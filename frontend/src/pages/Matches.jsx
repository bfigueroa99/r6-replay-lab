import React, { useEffect, useState } from 'react'

import { qs, useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import { DataTable, EmptyState, Enlace, ErrorBox, Loading, Panel, ResultChip } from '../components/ui.jsx'

const PAGE = 50

const RESULTADOS = [
  { value: '', label: 'Todas' },
  { value: 'victoria', label: 'Victorias' },
  { value: 'derrota', label: 'Derrotas' },
  { value: 'empate', label: 'Empates e incompletas' },
]

export default function Matches({ filters, setFilters, runImport, importing }) {
  const [offset, setOffset] = useState(0)
  const [resultado, setResultado] = useState('')
  // lado, operador y sitio son de ronda: una partida tiene los dos lados y diez
  // operadores, asi que la lista solo entiende mapa, periodo, sesion y ranked
  const { side, operator, site, ...deMatch } = filters
  const consulta = { ...deMatch, result: resultado, limit: PAGE, offset }
  const { data, error, loading } = useApi('/matches/', consulta)

  // cambiar el filtro con la pagina 3 abierta dejaria una lista vacia
  const clave = qs({ ...deMatch, result: resultado })
  useEffect(() => {
    setOffset(0)
  }, [clave])

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  if (!data) return null

  const filtrada = Boolean(clave)

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Partidas</h1>
          <p>
            {data.total} partidas{filtrada ? ' con estos filtros' : ' importadas'}.
          </p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} showSide={false} showOperator={false} showSession>
        <label>
          Resultado
          <select value={resultado} onChange={(event) => setResultado(event.target.value)}>
            {RESULTADOS.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </label>
      </Filters>

      {!data.total && !filtrada ? (
        <EmptyState onImport={runImport} importing={importing} />
      ) : (
        <Panel>
          <DataTable
            columns={[
              {
                key: 'played_at',
                label: 'Cuando',
                render: (row) => (
                  <Enlace to={`/partidas/${row.id}`}>{row.played_at.slice(0, 16).replace('T', ' ')}</Enlace>
                ),
              },
              { key: 'map', label: 'Mapa' },
              { key: 'match_type', label: 'Tipo', dim: true },
              { key: 'score', label: 'Marcador', sortable: false },
              {
                key: 'won',
                label: 'Resultado',
                render: (row) => <ResultChip won={row.won}>{row.result}</ResultChip>,
                csv: (row) => row.result,
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
            empty="Ninguna partida pasa estos filtros."
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
      )}
    </>
  )
}
