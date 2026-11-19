import React from 'react'

import { useApi } from '../api.js'
import { MUESTRA_CORTE } from '../muestra.js'
import { avisoPocaMuestra, filasDeEstados, filasDeGrupos, hayMuertes, notaSinFeed } from '../estadoAlMorir.js'
import { DataTable, ErrorBox, Loading, Panel, pct } from './ui.jsx'

const AYUDA_WINRATE = 'Rondas ganadas sobre las que tienen ganador: las que no lo tienen cuentan en Muertes y no acá.'

const ORDEN_API = { key: 'orden', dir: 'asc' }

const COLUMNA_MUERTES = { key: 'rounds', label: 'Muertes', help: 'Cada muerte es una ronda: moriste una vez en ella.' }

const COLUMNA_WINRATE = {
  key: 'winrate',
  label: 'Winrate de la ronda',
  help: AYUDA_WINRATE,
  render: (row) => pct(row.winrate),
}

/**
 * Panel aparte, con su propia consulta, para que Duelos sume un import y una
 * linea y no se pise con otros paneles de la misma pagina.
 */
export default function EstadoAlMorir({ filters }) {
  const { data, error, loading } = useApi('/duels/death-state/', filters)

  let cuerpo
  if (error) cuerpo = <ErrorBox error={error} />
  else if (loading && !data) cuerpo = <Loading />
  else if (!hayMuertes(data)) {
    cuerpo = (
      <>
        <p className="note">No hay muertes tuyas con evento en el feed con estos filtros.</p>
        {notaSinFeed(data?.sin_feed) ? <p className="note">{notaSinFeed(data.sin_feed)}</p> : null}
      </>
    )
  } else {
    const grupos = filasDeGrupos(data)
    const estados = filasDeEstados(data)
    cuerpo = (
      <>
        <DataTable
          columns={[
            { key: 'label', label: 'Situación', left: true, sortable: false },
            COLUMNA_MUERTES,
            COLUMNA_WINRATE,
          ]}
          rows={grupos}
          initialSort={ORDEN_API}
          rowKey={(row) => row.group}
          csvName="estado-al-morir-grupos"
        />
        <h3 style={{ margin: '16px 0 8px' }}>Por estado exacto</h3>
        <DataTable
          columns={[
            {
              key: 'state',
              label: 'Estado',
              left: true,
              sortable: false,
              help: 'Vivos de tu equipo (contándote) contra vivos rivales.',
            },
            COLUMNA_MUERTES,
            COLUMNA_WINRATE,
          ]}
          rows={estados}
          initialSort={ORDEN_API}
          rowKey={(row) => row.state}
          csvName="estado-al-morir"
        />
        {avisoPocaMuestra([...grupos, ...estados]) ? (
          <p className="note">
            Ojo: alguna fila tiene menos de {MUESTRA_CORTE} muertes; la diferencia puede ser varianza.
          </p>
        ) : null}
        {notaSinFeed(data.sin_feed) ? <p className="note">{notaSinFeed(data.sin_feed)}</p> : null}
      </>
    )
  }

  return (
    <Panel
      title="Estado al morir"
      hint="Cuántos quedaban vivos de cada lado justo antes de tu muerte, y cómo terminó esa ronda."
    >
      {cuerpo}
    </Panel>
  )
}
