import React from 'react'
import { Link } from 'react-router-dom'

import { useApi } from '../api.js'
import { filasConPocaMuestra, MUESTRA_CORTE } from '../muestra.js'
import { enlaceDeRonda, ETIQUETAS_LADO, filasDeGrupos, filasDeLados, hayVentajas } from '../ventajaTirada.js'
import { DataTable, ErrorBox, Loading, Panel, pct } from './ui.jsx'

const ORDEN_API = { key: 'orden', dir: 'asc' }

const COLUMNAS_CUENTA = [
  { key: 'rounds', label: 'Rondas con ventaja', help: 'Rondas con ganador en que tu equipo llegó a tener más vivos.' },
  { key: 'thrown', label: 'Tiradas', help: 'De esas, las que tu equipo perdió.' },
  { key: 'thrown_pct', label: '% tiradas', render: (row) => pct(row.thrown_pct) },
]

/**
 * Panel aparte, con su propia consulta, para que Duelos sume un import y una
 * linea, como `EstadoAlMorir`.
 */
export default function VentajaTirada({ filters }) {
  const { data, error, loading } = useApi('/duels/thrown-advantage/', filters)

  let cuerpo
  if (error) cuerpo = <ErrorBox error={error} />
  else if (loading && !data) cuerpo = <Loading />
  else if (!hayVentajas(data)) {
    cuerpo = <p className="note">No hay rondas con ventaja numérica con estos filtros.</p>
  } else {
    const grupos = filasDeGrupos(data)
    const lados = filasDeLados(data)
    const mapas = data.maps || []
    cuerpo = (
      <>
        <p>
          <strong>{data.thrown}</strong> de <strong>{data.rounds}</strong> rondas con ventaja tiradas (
          {pct(data.thrown_pct)})
        </p>
        <DataTable
          columns={[{ key: 'label', label: 'Ventaja máxima', left: true, sortable: false }, ...COLUMNAS_CUENTA]}
          rows={grupos}
          initialSort={ORDEN_API}
          rowKey={(row) => row.group}
          csvName="ventaja-tirada"
        />
        <h3 style={{ margin: '16px 0 8px' }}>Por lado</h3>
        <DataTable
          columns={[{ key: 'label', label: 'Lado', left: true, sortable: false }, ...COLUMNAS_CUENTA]}
          rows={lados}
          initialSort={ORDEN_API}
          rowKey={(row) => row.side}
          csvName="ventaja-tirada-lados"
        />
        <h3 style={{ margin: '16px 0 8px' }}>Por mapa</h3>
        <DataTable
          columns={[{ key: 'map', label: 'Mapa', left: true }, ...COLUMNAS_CUENTA]}
          rows={mapas}
          initialSort={{ key: 'thrown', dir: 'desc' }}
          rowKey={(row) => row.map}
          csvName="ventaja-tirada-mapas"
        />
        {filasConPocaMuestra([...grupos, ...lados, ...mapas]).length > 0 ? (
          <p className="note">
            Ojo: alguna fila tiene menos de {MUESTRA_CORTE} rondas con ventaja; la diferencia puede ser varianza.
          </p>
        ) : null}
        <h3 style={{ margin: '16px 0 8px' }}>Últimas tiradas</h3>
        <DataTable
          columns={[
            {
              key: 'played_at',
              label: 'Partida',
              left: true,
              render: (row) => <Link to={enlaceDeRonda(row)}>{row.played_at.slice(0, 10)}</Link>,
            },
            { key: 'map', label: 'Mapa', left: true },
            { key: 'round', label: 'Ronda', render: (row) => `R${row.round}` },
            { key: 'side', label: 'Lado', left: true, render: (row) => ETIQUETAS_LADO[row.side] || row.side },
            { key: 'advantage', label: 'Ventaja', render: (row) => `+${row.advantage}` },
          ]}
          rows={(data.recent || []).map((fila, orden) => ({ ...fila, orden }))}
          initialSort={ORDEN_API}
          rowKey={(row) => `${row.match_id}-${row.round}`}
          empty="Ninguna ronda con ventaja tirada con estos filtros."
        />
      </>
    )
  }

  return (
    <Panel
      title="Ventaja numérica tirada"
      hint="Rondas en que tu equipo llegó a tener más vivos que el rival, y cuántas perdió."
    >
      {cuerpo}
    </Panel>
  )
}
