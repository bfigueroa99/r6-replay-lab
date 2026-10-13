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
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/ø/gi, 'o')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')
}

// ranked primero porque es la playlist del rango que se ve arriba
const ORDEN_PLAYLISTS = ['ranked', 'all', 'unranked', 'casual']

/** Las playlists que trae alguna de las tablas (cada una es `{playlist: filas}`), en un orden fijo. */
export function playlistsDe(...tablas) {
  const ids = new Set(tablas.flatMap((tabla) => Object.keys(tabla || {})))
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

/** Cada temporada del historial con sus replays de esa temporada (por la versión del juego). */
export const cruzarTemporadas = (historial, enReplays) =>
  cruzar(
    historial,
    enReplays,
    (fila) => fila.temporada,
    (fila) => fila.season,
  )

const abandonos = (n) => (n ? ` · ${n} ${n === 1 ? 'abandono' : 'abandonos'}` : '')

const dia = (iso) => (iso ? iso.slice(0, 10).split('-').reverse().join('-') : '')

const cuando = (iso) => (iso ? `${dia(iso)} ${iso.slice(11, 16)}` : '')

// la pagina del jugador no tiene barra de filtros: es todo lo que hay en tus replays
const COLUMNAS_REPLAY = [
  {
    key: 'replay_rondas',
    label: 'Rondas en replays',
    help: 'Rondas de esta persona en todos tus replays.',
  },
  { key: 'replay_winrate', label: 'Ganadas en replays', digits: 0, suffix: '%' },
  { key: 'replay_kd', label: 'K/D en replays', digits: 2 },
]

/** La playlist elegida; si deja de existir (otra consulta), vuelve a la primera. */
function usePlaylist(playlists) {
  const [elegida, setElegida] = useState(null)
  return [playlists.includes(elegida) ? elegida : playlists[0], setElegida]
}

function SelectorPlaylist({ playlists, value, onChange }) {
  if (playlists.length < 2) return null
  return (
    <label className="note" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      Playlist
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {playlists.map((id) => (
          <option key={id} value={id}>
            {PLAYLISTS[id] || id}
          </option>
        ))}
      </select>
    </label>
  )
}

const ANTERIOR = (que) => (
  <p className="note">
    La consulta guardada es de antes de que la app trajera {que}. Actualízala para verlos.
  </p>
)

const Separador = () => <div style={{ height: 18 }} />

/**
 * Lo que stats.cc muestra en sus pestañas de operadores, mapas y armas, cruzado
 * con tus replays donde se puede. Vive en su propio panel porque son tablas largas.
 */
function DetalleTemporada({ estadisticas, operadoresReplay, mapasReplay, nombre }) {
  const playlists = playlistsDe(estadisticas?.operadores, estadisticas?.mapas, estadisticas?.armas)
  const [playlist, setPlaylist] = usePlaylist(playlists)

  const operadores = cruzarOperadores(estadisticas?.operadores?.[playlist], operadoresReplay)
  const mapas = cruzarMapas(estadisticas?.mapas?.[playlist], mapasReplay)
  const armas = estadisticas?.armas?.[playlist] || []

  return (
    <Panel
      title="Operadores, mapas y armas en Ubisoft"
      hint="Las pestañas de operadores, mapas y armas de stats.cc, desde la misma API de Ubisoft: toda la temporada de esta persona. Al lado, lo que hizo en tus replays con el mismo operador o en el mismo mapa; las armas no tienen cruce porque el replay no las trae. Ganadas son rondas, no partidas."
      right={<SelectorPlaylist playlists={playlists} value={playlist} onChange={setPlaylist} />}
    >
      {!estadisticas ? (
        ANTERIOR('operadores y mapas')
      ) : estadisticas.error ? (
        <div className="error">{estadisticas.error}</div>
      ) : !playlist ? (
        <p className="note">Ubisoft no devolvió operadores, mapas ni armas para este periodo.</p>
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

          <Separador />

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

          {estadisticas.armas ? (
            <>
              <Separador />
              <DataTable
                columns={[
                  { key: 'arma', label: 'Arma', left: true },
                  { key: 'ranura', label: 'Ranura', left: true },
                  { key: 'tipo', label: 'Tipo', left: true, dim: true },
                  { key: 'rondas', label: 'Rondas' },
                  { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%' },
                  { key: 'bajas', label: 'Bajas' },
                  { key: 'kpr', label: 'Bajas por ronda', digits: 2 },
                  { key: 'hs_pct', label: 'HS%', digits: 0, suffix: '%' },
                ]}
                rows={armas}
                initialSort={{ key: 'rondas', dir: 'desc' }}
                rowKey={(row) => `${row.arma}-${row.ranura}`}
                csvName={`armas-temporada-${nombre}`}
                empty="Ubisoft no devolvió armas en esta playlist."
              />
            </>
          ) : (
            ANTERIOR('las armas')
          )}

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

/**
 * La pestaña de temporadas de stats.cc, sin el rango de cada una (Ubisoft solo
 * lo da para la actual), y cada temporada con tus replays de esa temporada.
 */
function HistorialTemporadas({ historial, temporadasReplay, nombre }) {
  const playlists = playlistsDe(historial?.temporadas)
  const [playlist, setPlaylist] = usePlaylist(playlists)
  const filas = cruzarTemporadas(historial?.temporadas?.[playlist], temporadasReplay)

  return (
    <Panel
      title="Temporadas en Ubisoft"
      hint="El historial por temporada de stats.cc, desde la misma API de Ubisoft: todas sus partidas de cada temporada. Al lado, sus rondas en tus replays de esa temporada, que sale de la versión del juego de cada replay. Ubisoft no da el rango de las temporadas pasadas."
      right={<SelectorPlaylist playlists={playlists} value={playlist} onChange={setPlaylist} />}
    >
      {!historial ? (
        ANTERIOR('el historial por temporada')
      ) : historial.error ? (
        <div className="error">{historial.error}</div>
      ) : (
        <DataTable
          columns={[
            { key: 'temporada', label: 'Temporada', left: true },
            { key: 'partidas', label: 'Partidas' },
            {
              key: 'winrate_partidas',
              label: 'Partidas ganadas',
              digits: 0,
              suffix: '%',
              help: 'Ganadas / (ganadas + perdidas). Los abandonos no entran.',
            },
            { key: 'rondas', label: 'Rondas' },
            { key: 'winrate', label: 'Rondas ganadas', digits: 0, suffix: '%' },
            { key: 'kd', label: 'K/D', digits: 2 },
            { key: 'kpr', label: 'KPR', digits: 2 },
            { key: 'hs_pct', label: 'HS%', digits: 0, suffix: '%' },
            ...COLUMNAS_REPLAY,
          ]}
          rows={filas}
          initialSort={{ key: 'temporada', dir: 'desc' }}
          rowKey={(row) => row.temporada}
          csvName={`temporadas-${nombre}`}
          empty="Ubisoft no devolvió temporadas jugadas."
        />
      )}
    </Panel>
  )
}

export default function PerfilUbisoft({
  jugadorId,
  inicial,
  nombre,
  operadoresReplay,
  mapasReplay,
  temporadasReplay,
}) {
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
        <>
          <DetalleTemporada
            estadisticas={datos.estadisticas}
            operadoresReplay={operadoresReplay}
            mapasReplay={mapasReplay}
            nombre={nombre}
          />
          <HistorialTemporadas
            historial={datos.historial}
            temporadasReplay={temporadasReplay}
            nombre={nombre}
          />
        </>
      ) : null}
    </>
  )
}
