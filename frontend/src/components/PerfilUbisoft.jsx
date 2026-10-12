import React, { useState } from 'react'

import { post } from '../api.js'
import { DataTable, Panel, SideChip, Stat, fmt, pct, ratio } from './ui.jsx'

/** Nombres de las playlists que devuelve Ubisoft; lo que no esta sale tal cual. */
export const PLAYLISTS = {
  ranked: 'Ranked',
  standard: 'Estándar',
  unranked: 'Sin clasificar',
  casual: 'Partida rápida',
  event: 'Evento',
  warmup: 'Calentamiento',
  all: 'Todas',
}

/** Las playlists jugadas esta temporada: una sin partidas es una fila de ceros. */
export function filasPlaylists(tableros) {
  return Object.entries(tableros || {})
    .filter(([, t]) => t.partidas > 0)
    .map(([id, t]) => ({ id, nombre: PLAYLISTS[id] || id, ...t }))
}

/**
 * El nombre con que se cruzan Ubisoft y el replay. Ubisoft escribe los mapas en
 * mayusculas y sin el espacio que tiene el replay ("CLUBHOUSE" contra "Club
 * House"), y un operador puede venir con o sin tilde.
 */
export function clave(nombre) {
  return String(nombre || '')
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/ø/gi, 'o')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')
}

// ranked primero porque es la playlist del rango que se ve arriba
const ORDEN_PLAYLISTS = ['ranked', 'all', 'unranked', 'casual']

/** Las playlists que trajeron operadores o mapas, en un orden fijo. */
export function playlistsConDetalle(estadisticas) {
  const ids = new Set([
    ...Object.keys(estadisticas?.operadores || {}),
    ...Object.keys(estadisticas?.mapas || {}),
  ])
  const lugar = (id) => (ORDEN_PLAYLISTS.includes(id) ? ORDEN_PLAYLISTS.indexOf(id) : ORDEN_PLAYLISTS.length)
  return [...ids].sort((a, b) => lugar(a) - lugar(b) || a.localeCompare(b))
}

function cruzar(temporada, enReplays, claveTemporada, claveReplay) {
  const propias = new Map((enReplays || []).map((fila) => [claveReplay(fila), fila]))
  return (temporada || []).map((fila) => {
    const propia = propias.get(claveTemporada(fila))
    return {
      ...fila,
      replay_rondas: propia ? propia.rounds : null,
      replay_winrate: propia ? propia.winrate : null,
      replay_kd: propia ? propia.kd : null,
    }
  })
}

/** Cada operador de la temporada con lo que hizo con el mismo operador y lado en tus replays. */
export const cruzarOperadores = (temporada, enReplays) =>
  cruzar(
    temporada,
    enReplays,
    (fila) => `${clave(fila.operador)}|${fila.lado}`,
    (fila) => `${clave(fila.operator)}|${fila.side}`,
  )

/** Cada mapa de la temporada con lo que hizo en ese mapa en tus replays. */
export const cruzarMapas = (temporada, enReplays) =>
  cruzar(
    temporada,
    enReplays,
    (fila) => clave(fila.mapa),
    (fila) => clave(fila.map),
  )

const abandonos = (n) => (n ? ` · ${n} ${n === 1 ? 'abandono' : 'abandonos'}` : '')

const dia = (iso) => (iso ? iso.slice(0, 10).split('-').reverse().join('-') : '')

const cuando = (iso) => (iso ? `${dia(iso)} ${iso.slice(11, 16)}` : '')

const COLUMNAS_REPLAY = [
  {
    key: 'replay_rondas',
    label: 'Rondas en replays',
    help: 'Rondas de esta persona en tus replays, con los filtros de arriba.',
  },
  { key: 'replay_winrate', label: 'Ganadas en replays', digits: 0, suffix: '%' },
  { key: 'replay_kd', label: 'K/D en replays', digits: 2 },
]

/**
 * Lo que stats.cc muestra en sus pestañas de operadores y mapas, cruzado con
 * tus replays. Vive en su propio panel porque son dos tablas largas.
 */
function DetalleTemporada({ estadisticas, operadoresReplay, mapasReplay, nombre }) {
  const playlists = playlistsConDetalle(estadisticas)
  const [elegida, setElegida] = useState(null)
  const playlist = playlists.includes(elegida) ? elegida : playlists[0]

  const operadores = cruzarOperadores(estadisticas?.operadores?.[playlist], operadoresReplay)
  const mapas = cruzarMapas(estadisticas?.mapas?.[playlist], mapasReplay)

  return (
    <Panel
      title="Operadores y mapas en Ubisoft"
      hint="Las pestañas de operadores y mapas de stats.cc, desde la misma API de Ubisoft: toda la temporada de esta persona. Al lado, lo que hizo en tus replays con el mismo operador o en el mismo mapa. Ganadas son rondas, no partidas."
      right={
        playlists.length > 1 ? (
          <label className="note" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            Playlist
            <select value={playlist} onChange={(e) => setElegida(e.target.value)}>
              {playlists.map((id) => (
                <option key={id} value={id}>
                  {PLAYLISTS[id] || id}
                </option>
              ))}
            </select>
          </label>
        ) : null
      }
    >
      {!estadisticas ? (
        <p className="note">
          La consulta guardada es de antes de que la app trajera operadores y mapas. Actualízala para
          verlos.
        </p>
      ) : estadisticas.error ? (
        <div className="error">{estadisticas.error}</div>
      ) : !playlist ? (
        <p className="note">Ubisoft no devolvió operadores ni mapas para este periodo.</p>
      ) : (
        <>
          <DataTable
            columns={[
              { key: 'operador', label: 'Operador', left: true },
              {
                key: 'lado',
                label: 'Lado',
                render: (row) => <SideChip side={row.lado} />,
                csv: (row) => (row.lado === 'Attack' ? 'Ataque' : 'Defensa'),
              },
              { key: 'rondas', label: 'Rondas' },
              { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%' },
              { key: 'kd', label: 'K/D', digits: 2 },
              { key: 'kpr', label: 'KPR', digits: 2 },
              { key: 'hs_pct', label: 'HS%', digits: 0, suffix: '%' },
              ...COLUMNAS_REPLAY,
            ]}
            rows={operadores}
            initialSort={{ key: 'rondas', dir: 'desc' }}
            rowKey={(row) => `${row.operador}-${row.lado}`}
            csvName={`operadores-temporada-${nombre}`}
            empty="Ubisoft no devolvió operadores en esta playlist."
          />

          <div style={{ height: 18 }} />

          <DataTable
            columns={[
              { key: 'mapa', label: 'Mapa', left: true },
              { key: 'partidas', label: 'Partidas' },
              { key: 'rondas', label: 'Rondas' },
              { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%' },
              { key: 'winrate_attack', label: 'En ataque', digits: 0, suffix: '%' },
              { key: 'winrate_defense', label: 'En defensa', digits: 0, suffix: '%' },
              { key: 'kd', label: 'K/D', digits: 2 },
              ...COLUMNAS_REPLAY,
            ]}
            rows={mapas}
            initialSort={{ key: 'rondas', dir: 'desc' }}
            rowKey={(row) => row.mapa}
            csvName={`mapas-temporada-${nombre}`}
            empty="Ubisoft no devolvió mapas en esta playlist."
          />

          {estadisticas.desde && estadisticas.hasta ? (
            <p className="note">
              Periodo según Ubisoft: del {dia(estadisticas.desde)} al {dia(estadisticas.hasta)}.
            </p>
          ) : null}
        </>
      )}
    </Panel>
  )
}

export default function PerfilUbisoft({ jugadorId, inicial, nombre, operadoresReplay, mapasReplay }) {
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
    <>
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

      {datos ? (
        <DetalleTemporada
          estadisticas={datos.estadisticas}
          operadoresReplay={operadoresReplay}
          mapasReplay={mapasReplay}
          nombre={nombre}
        />
      ) : null}
    </>
  )
}
