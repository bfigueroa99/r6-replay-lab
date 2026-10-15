import React, { useState } from 'react'
import { Link } from 'react-router-dom'

import { post, useApi } from '../api.js'
import { DataTable, ErrorBox, Loading, Panel, SideChip } from '../components/ui.jsx'

const fecha = (iso) => (iso ? iso.slice(0, 10).split('-').reverse().slice(0, 2).join('-') : '—')

/** "1 partida" y no "1 partidas": se ve en cada fila. */
const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`

const VACIAS = { maps: {}, operators: {}, gamemodes: {}, match_types: {} }

const rango = (row) =>
  row.first_seen === row.last_seen
    ? fecha(row.first_seen)
    : `${fecha(row.first_seen)} a ${fecha(row.last_seen)}`

export default function Datos() {
  const unknown = useApi('/unknown/')
  const status = useApi('/import/status/')
  const [labels, setLabels] = useState(VACIAS)
  const [saving, setSaving] = useState(false)
  const [flash, setFlash] = useState(null)

  if (unknown.error) return <ErrorBox error={unknown.error} />
  if (unknown.loading && !unknown.data) return <Loading />

  const maps = unknown.data?.maps || []
  const operators = unknown.data?.operators || []
  const gamemodes = unknown.data?.gamemodes || []
  const matchTypes = unknown.data?.match_types || []
  const set = (kind, id) => (event) =>
    setLabels((current) => ({ ...current, [kind]: { ...current[kind], [id]: event.target.value } }))

  const pendientes = Object.values(labels).reduce(
    (n, porId) => n + Object.values(porId).filter((v) => v.trim()).length,
    0,
  )

  const guardar = async () => {
    setSaving(true)
    setFlash(null)
    try {
      const limpiar = (obj) =>
        Object.fromEntries(
          Object.entries(obj)
            .map(([id, name]) => [id, name.trim()])
            .filter(([, name]) => name),
        )
      const result = await post('/overrides/', undefined, {
        maps: limpiar(labels.maps),
        operators: limpiar(labels.operators),
        gamemodes: limpiar(labels.gamemodes),
        match_types: limpiar(labels.match_types),
      })
      setLabels(VACIAS)
      setFlash({
        ok: true,
        text: result.changes.length
          ? `${result.changes.map((c) => `${c.old} → ${c.new}`).join(', ')}. Reetiquetadas ` +
            `${result.matches} partidas y ${result.round_players} rondas de jugador.`
          : 'Etiquetas guardadas. No habia nada importado con esos IDs.',
      })
      unknown.reload()
      status.reload()
    } catch (err) {
      setFlash({ ok: false, text: err.message })
    } finally {
      setSaving(false)
    }
  }

  const log = status.data?.log || []

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Datos</h1>
          <p>
            Que tan completa esta tu base: los IDs que el parser no supo nombrar y lo que falta por
            importar.
          </p>
        </div>
      </div>

      {flash ? <div className={`flash ${flash.ok ? '' : 'bad'}`}>{flash.text}</div> : null}

      {maps.length || operators.length || gamemodes.length || matchTypes.length ? (
        <Panel
          title="Sin identificar"
          hint={
            'Ubisoft cambia los IDs de los mapas revampeados y agrega operadores, modos y tipos ' +
            'de partida, y el parser guarda el ID crudo en vez de inventar un nombre. Ponle el ' +
            'nombre y el historial ya importado se reetiqueta solo: no hay que volver a leer ' +
            'los replays.'
          }
          right={
            <button className="btn primary small" onClick={guardar} disabled={!pendientes || saving}>
              {saving ? 'Guardando...' : `Guardar y reetiquetar${pendientes ? ` (${pendientes})` : ''}`}
            </button>
          }
        >
          {maps.map((row) => (
            <div key={row.id} className="unknown">
              <div className="unknown-head">
                <span className="unknown-id">{row.label}</span>
                <span className="note">
                  {plural(row.matches, 'partida', 'partidas')} ·{' '}
                  {plural(row.rounds, 'ronda', 'rondas')} · {rango(row)}
                </span>
              </div>
              <div>
                <div className="note" style={{ marginBottom: 5 }}>
                  Sitios de bomba vistos. El juego los nombra igual aunque cambie el ID del mapa,
                  asi que delatan cual es:
                </div>
                <div className="unknown-sites">
                  {row.sites.length ? (
                    row.sites.map((site) => (
                      <span key={site} className="chip">
                        {site}
                      </span>
                    ))
                  ) : (
                    <span className="note">Ningun sitio detectado en esas rondas.</span>
                  )}
                </div>
              </div>
              <input
                type="text"
                placeholder="Nombre del mapa (ej: Nighthaven Labs)"
                value={labels.maps[row.id] ?? row.pending}
                onChange={set('maps', row.id)}
                maxLength={32}
              />
            </div>
          ))}

          {operators.map((row) => (
            <div key={row.id} className="unknown">
              <div className="unknown-head">
                <span className="unknown-id">{row.label}</span>
                {row.sides.map((side) => (
                  <SideChip key={side} side={side} />
                ))}
                <span className="note">
                  {plural(row.rounds, 'ronda', 'rondas')} · {rango(row)} ·{' '}
                  {row.mine ? 'lo jugaste tu' : 'solo rivales'}
                </span>
              </div>
              {row.maps.length ? (
                <div className="note">Visto en: {row.maps.join(', ')}</div>
              ) : null}
              <input
                type="text"
                placeholder="Nombre del operador"
                value={labels.operators[row.id] ?? row.pending}
                onChange={set('operators', row.id)}
                maxLength={32}
              />
            </div>
          ))}

          {gamemodes.map((row) => (
            <div key={`modo-${row.id}`} className="unknown">
              <div className="unknown-head">
                <span className="unknown-id">{row.label}</span>
                <span className="note">
                  Modo de juego · {plural(row.matches, 'partida', 'partidas')} · {rango(row)}
                </span>
              </div>
              {row.match_types.length ? (
                <div className="note">Tipos de partida vistos: {row.match_types.join(', ')}</div>
              ) : null}
              <input
                type="text"
                placeholder="Nombre del modo de juego"
                value={labels.gamemodes[row.id] ?? row.pending}
                onChange={set('gamemodes', row.id)}
                maxLength={32}
              />
            </div>
          ))}

          {matchTypes.map((row) => (
            <div key={`tipo-${row.id}`} className="unknown">
              <div className="unknown-head">
                <span className="unknown-id">{row.label}</span>
                <span className="note">
                  Tipo de partida · {plural(row.matches, 'partida', 'partidas')} · {rango(row)}
                </span>
              </div>
              {row.gamemodes.length ? (
                <div className="note">Modos vistos: {row.gamemodes.join(', ')}</div>
              ) : null}
              <input
                type="text"
                placeholder="Nombre del tipo de partida"
                value={labels.match_types[row.id] ?? row.pending}
                onChange={set('match_types', row.id)}
                maxLength={32}
              />
            </div>
          ))}
        </Panel>
      ) : (
        <Panel title="Sin identificar">
          <p className="note" style={{ margin: 0 }}>
            Todo identificado: no hay mapas, operadores, modos ni tipos de partida sin nombre.
            Cuando salga una temporada
            nueva van a aparecer aca solos.
          </p>
        </Panel>
      )}

      <Panel
        title="Importacion"
        hint={`Carpeta vigilada: ${status.data?.replay_dir || '—'}`}
      >
        {status.data && !status.data.replay_dir_exists ? (
          <p className="note" style={{ marginTop: 0 }}>
            Esa carpeta no existe en este PC. Si Siege está instalado en otro lado, elige tu
            carpeta <code>MatchReplay</code> en <Link to="/ajustes">Ajustes</Link>.
          </p>
        ) : null}
        <div className="kpis" style={{ marginBottom: 14 }}>
          <div className="stat">
            <div className="label">Carpetas en disco</div>
            <div className="value">{status.data?.folders_on_disk ?? '—'}</div>
          </div>
          <div className="stat">
            <div className="label">Importadas</div>
            <div className="value">{status.data?.folders_imported ?? '—'}</div>
          </div>
          <div className="stat">
            <div className="label">Pendientes</div>
            <div className="value">{status.data?.pending?.length ?? '—'}</div>
            <div className="sub">
              {status.data?.pending?.length
                ? 'Dale a Importar replays arriba'
                : 'Nada esperando'}
            </div>
          </div>
        </div>

        <DataTable
          columns={[
            { key: 'folder', label: 'Carpeta', left: true },
            {
              key: 'started_at',
              label: 'Cuando',
              render: (row) => row.started_at.slice(5, 16).replace('T', ' '),
            },
            {
              key: 'ok',
              label: 'Resultado',
              render: (row) => (
                <span className={`chip ${row.ok ? 'win' : 'loss'}`}>{row.ok ? 'ok' : 'error'}</span>
              ),
            },
            { key: 'rounds', label: 'Rondas' },
            { key: 'message', label: 'Detalle', left: true, dim: true, wrap: true },
          ]}
          rows={log}
          initialSort={{ key: 'started_at', dir: 'desc' }}
          rowKey={(row) => `${row.folder}-${row.started_at}`}
          empty="Todavia no hay importaciones registradas."
        />
      </Panel>
    </>
  )
}
