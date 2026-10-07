import React, { useState } from 'react'

import { post } from '../api.js'
import { DataTable, Panel, Stat, fmt, pct, ratio } from './ui.jsx'

/** Nombres de las playlists que devuelve Ubisoft; lo que no esta sale tal cual. */
export const PLAYLISTS = {
  ranked: 'Ranked',
  standard: 'Estándar',
  unranked: 'Sin clasificar',
  casual: 'Partida rápida',
  event: 'Evento',
  warmup: 'Calentamiento',
}

/** Las playlists jugadas esta temporada: una sin partidas es una fila de ceros. */
export function filasPlaylists(tableros) {
  return Object.entries(tableros || {})
    .filter(([, t]) => t.partidas > 0)
    .map(([id, t]) => ({ id, nombre: PLAYLISTS[id] || id, ...t }))
}

const abandonos = (n) => (n ? ` · ${n} ${n === 1 ? 'abandono' : 'abandonos'}` : '')

const cuando = (iso) => (iso ? `${iso.slice(0, 10).split('-').reverse().join('-')} ${iso.slice(11, 16)}` : '')

export default function PerfilUbisoft({ jugadorId, inicial }) {
  const [estado, setEstado] = useState(inicial)
  const [consultando, setConsultando] = useState(false)
  const [error, setError] = useState(null)

  const consultar = () => {
    setConsultando(true)
    setError(null)
    post(`/players/${jugadorId}/ubisoft/`)
      .then(setEstado)
      .catch((err) => setError(err.message))
      .finally(() => setConsultando(false))
  }

  const listo = estado.configurado && estado.consultable
  const datos = estado.datos
  const ranked = datos?.tableros?.ranked

  return (
    <Panel
      title="Temporada en Ubisoft"
      hint="Rango, MMR y K/D de la temporada actual según la API de Ubisoft, la misma que leen stats.cc y R6 Tracker. Es su historial completo, no solo tus partidas, y se consulta solo cuando aprietas el botón."
      right={
        listo ? (
          <button className="btn small" onClick={consultar} disabled={consultando}>
            {consultando ? 'Consultando...' : datos ? 'Actualizar' : 'Consultar Ubisoft'}
          </button>
        ) : null
      }
    >
      {!estado.consultable ? (
        <p className="note">
          Este jugador no trae profileID en el replay, así que no hay a quién consultar.
        </p>
      ) : !estado.configurado ? (
        <p className="note">
          Para consultar a Ubisoft agrega <code>UBI_EMAIL</code> y <code>UBI_PASSWORD</code> de una
          cuenta de Ubisoft a tu <code>.env</code> y reinicia la app. Las cuentas con verificación en
          dos pasos no funcionan: usa una secundaria.
        </p>
      ) : null}

      {error ? <div className="error">{error}</div> : null}

      {listo && !datos && !error ? <p className="note">Todavía no lo consultaste.</p> : null}

      {datos ? (
        <>
          {ranked ? (
            <div className="kpis" style={{ marginBottom: 14 }}>
              <Stat label="Rango" value={ranked.rango || '—'} sub={`${fmt(ranked.mmr)} MMR`} />
              <Stat
                label="Máximo de la temporada"
                value={ranked.rango_maximo || '—'}
                sub={`${fmt(ranked.mmr_maximo)} MMR`}
              />
              <Stat
                label="K/D ranked"
                value={ratio(ranked.kd)}
                sub={`${ranked.bajas} bajas · ${ranked.muertes} muertes`}
              />
              <Stat
                label="Partidas ganadas"
                value={pct(ranked.winrate)}
                sub={`${ranked.ganadas}-${ranked.perdidas}${abandonos(ranked.abandonos)}`}
              />
              <Stat label="Nivel" value={fmt(datos.nivel)} />
              <Stat label="Horas jugadas" value={fmt(datos.horas)} />
            </div>
          ) : null}

          <DataTable
            columns={[
              { key: 'nombre', label: 'Playlist', left: true },
              { key: 'partidas', label: 'Partidas' },
              { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%' },
              { key: 'kd', label: 'K/D', digits: 2 },
              { key: 'bajas', label: 'Bajas' },
              { key: 'muertes', label: 'Muertes' },
            ]}
            rows={filasPlaylists(datos.tableros)}
            initialSort={{ key: 'partidas', dir: 'desc' }}
            rowKey={(row) => row.id}
            empty="No jugó ninguna playlist esta temporada."
          />

          <p className="note">
            Consultado el {cuando(estado.consultado)}
            {ranked?.temporada ? ` · temporada ${ranked.temporada}` : ''}.
          </p>
        </>
      ) : null}
    </Panel>
  )
}
