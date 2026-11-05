import React, { useState } from 'react'
import { Link } from 'react-router-dom'

import { useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import { DataTable, EmptyState, ErrorBox, Loading, Panel, ResultChip } from '../components/ui.jsx'
import {
  OPCIONES_DE_RESULTADO,
  claveDeFiltros,
  filtrosDePartida,
  offsetVigente,
  paramsDePartidas,
  subtituloDePartidas,
} from '../partidas.js'
import { hayFiltros } from '../tipoPartida.js'

const PAGE = 50

export default function Matches({ filters, setFilters, runImport, importing }) {
  // el resultado es local: en el Inicio o el Coach un `result=` no significaria
  // nada y prenderia "Limpiar" con un filtro que esa pagina no muestra
  const [resultado, setResultado] = useState('')
  const clave = claveDeFiltros(filters, resultado)
  const [pagina, setPagina] = useState({ clave, offset: 0 })
  const offset = offsetVigente(pagina, clave)
  const { data, error, loading } = useApi('/matches/', paramsDePartidas(filters, resultado, offset, PAGE))

  const filtrado = hayFiltros(filtrosDePartida(filters)) || Boolean(resultado)

  const cambiarFiltros = (nuevos) => {
    setFilters(nuevos)
    // "Limpiar" manda {}: tambien borra el resultado, que vive aca
    if (Object.keys(nuevos).length === 0) setResultado('')
  }

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  if (!data?.total && !filtrado) return <EmptyState onImport={runImport} importing={importing} />

  const total = data?.total || 0

  const cabecera = (
    <>
      <div className="page-head">
        <div>
          <h1>Partidas</h1>
          <p>{subtituloDePartidas(total, filtrado)}</p>
        </div>
      </div>

      <Filters
        value={filters}
        onChange={cambiarFiltros}
        showSide={false}
        showOperator={false}
        showSession
        hayExtra={Boolean(resultado)}
      >
        <label>
          Resultado
          <select value={resultado} onChange={(event) => setResultado(event.target.value)}>
            {OPCIONES_DE_RESULTADO.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </Filters>
    </>
  )

  if (!total) {
    return (
      <>
        {cabecera}
        <p className="note">Ninguna partida con estos filtros. Cambia alguno o usa Limpiar.</p>
      </>
    )
  }

  return (
    <>
      {cabecera}

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
            { key: 'my_rating', label: 'Rating', digits: 2, help: 'Aporte por ronda comparado con tu propio promedio: 1.00 es tu ronda típica. Ver docs/metricas.md para la fórmula y los pesos.' },
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
            <button className="btn small" disabled={offset === 0} onClick={() => setPagina({ clave, offset: Math.max(0, offset - PAGE) })}>
              Anteriores
            </button>
            <button
              className="btn small"
              disabled={offset + PAGE >= data.total}
              onClick={() => setPagina({ clave, offset: offset + PAGE })}
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
