import React from 'react'

import { useApi } from '../api.js'
import { MUESTRA_CORTE } from '../muestra.js'
import {
  avisoPocaMuestra,
  filasDeEstados,
  filasDeGrupos,
  hayBajas,
  notaPostMortem,
  notaSinFeed,
} from '../estadoAlMatar.js'
import { DataTable, ErrorBox, Loading, Panel, pct } from './ui.jsx'

const ORDEN_API = { key: 'orden', dir: 'asc' }

const COLUMNA_BAJAS = { key: 'kills', label: 'Bajas', help: 'Bajas a rivales; un teamkill no cuenta, pero resta su vivo.' }

// El aviso de muestra va sobre rondas: cada tabla las muestra para que se vea que fila lo dispara.
const COLUMNA_RONDAS = {
  key: 'rounds',
  label: 'Rondas',
  help: 'Una ronda con dos bajas en la misma situación cuenta una vez.',
}

const COLUMNA_WINRATE = {
  key: 'winrate',
  label: 'Winrate de la ronda',
  help: 'Rondas ganadas sobre las que tienen ganador; cada ronda cuenta una vez por fila.',
  render: (row) => pct(row.winrate),
}

/** Las bajas que no entran en las tablas se dicen aparte, para que el total cierre con el Resumen. */
function NotasAparte({ data }) {
  const postMortem = notaPostMortem(data?.post_mortem)
  const sinFeed = notaSinFeed(data?.sin_feed)
  return (
    <>
      {postMortem ? <p className="note">{postMortem}</p> : null}
      {sinFeed ? <p className="note">{sinFeed}</p> : null}
    </>
  )
}

/** Panel aparte, con su propia consulta, como Estado al morir, que queda justo arriba. */
export default function EstadoAlMatar({ filters }) {
  const { data, error, loading } = useApi('/duels/kill-state/', filters)

  let cuerpo
  if (error) cuerpo = <ErrorBox error={error} />
  else if (loading && !data) cuerpo = <Loading />
  else if (!hayBajas(data)) {
    cuerpo = (
      <>
        <p className="note">No hay bajas tuyas con evento en el feed con estos filtros.</p>
        <NotasAparte data={data} />
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
            COLUMNA_BAJAS,
            COLUMNA_RONDAS,
            COLUMNA_WINRATE,
          ]}
          rows={grupos}
          initialSort={ORDEN_API}
          rowKey={(row) => row.group}
          csvName="estado-al-matar-grupos"
        />
        <h3 style={{ margin: '16px 0 8px' }}>Por estado exacto</h3>
        <DataTable
          columns={[
            {
              key: 'state',
              label: 'Estado',
              left: true,
              sortable: false,
              help: 'Vivos de tu equipo (contándote) contra vivos rivales, justo antes de la baja.',
            },
            COLUMNA_BAJAS,
            COLUMNA_RONDAS,
            COLUMNA_WINRATE,
          ]}
          rows={estados}
          initialSort={ORDEN_API}
          rowKey={(row) => row.state}
          csvName="estado-al-matar"
        />
        {avisoPocaMuestra([...grupos, ...estados]) ? (
          <p className="note">
            Ojo: alguna fila tiene menos de {MUESTRA_CORTE} rondas; la diferencia puede ser varianza.
          </p>
        ) : null}
        <NotasAparte data={data} />
      </>
    )
  }

  return (
    <Panel
      title="Estado al matar"
      hint="Cuántos quedaban vivos de cada lado justo antes de cada baja tuya, y cómo terminó esa ronda."
    >
      {cuerpo}
    </Panel>
  )
}
