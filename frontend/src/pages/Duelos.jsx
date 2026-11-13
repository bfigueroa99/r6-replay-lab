import React, { useState } from 'react'
import { Link } from 'react-router-dom'

import { useApi } from '../api.js'
import EstadoAlMorir from '../components/EstadoAlMorir.jsx'
import Filters from '../components/Filters.jsx'
import { Bar, DataTable, EmptyState, ErrorBox, Loading, Panel, SideChip, SinRondasFiltradas, pct } from '../components/ui.jsx'
import { filasOperadoresQueTeAbren } from '../operadoresQueTeAbren.js'
import { textosSinDuelos, vistaDuelos } from '../tipoPartida.js'
import { fechaCorta, fechaCsv } from '../ultimaVez.js'

const MUESTRAS = [
  { value: 3, label: '3+ duelos' },
  { value: 5, label: '5+ duelos' },
  { value: 10, label: '10+ duelos' },
]

/** Verde si le ganas al rival, rojo si te gana. */
function Balance({ value }) {
  if (value === null || value === undefined) return <span className="dim">—</span>
  if (value === 0) return <span className="chip">0</span>
  return <span className={`chip ${value > 0 ? 'win' : 'loss'}`}>{value > 0 ? `+${value}` : value}</span>
}

/** Diferencia en puntos contra tu promedio. `mejorSiSube` decide el color. */
function Diferencia({ value, mejorSiSube }) {
  if (value === null || value === undefined) return <span className="dim">—</span>
  if (Math.round(value) === 0) return <span className="chip">0</span>
  const bueno = mejorSiSube ? value > 0 : value < 0
  return (
    <span className={`chip ${bueno ? 'win' : 'loss'}`}>
      {value > 0 ? '+' : ''}
      {value.toFixed(0)}
    </span>
  )
}

export default function Duelos({ filters, setFilters, runImport, importing }) {
  const [minDuels, setMinDuels] = useState(3)
  const { data, error, loading } = useApi('/duels/', { ...filters, min_duels: minDuels })

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />

  const totals = data?.totals
  const vista = vistaDuelos({ rondas: data?.rounds, duelos: totals?.duels, filtros: filters, cargando: loading })
  if (vista === 'importar') return <EmptyState onImport={runImport} importing={importing} />
  if (vista === 'filtrado') {
    return <SinRondasFiltradas titulo="Duelos" filtros={<Filters value={filters} onChange={setFilters} />} />
  }
  if (vista === 'sin-duelos') {
    return (
      <SinRondasFiltradas
        titulo="Duelos"
        {...textosSinDuelos(filters)}
        filtros={<Filters value={filters} onChange={setFilters} />}
      />
    )
  }

  const base = totals.winrate
  const nemesis = data.nemesis || []
  const operators = data.operators || []
  const aperturasPorOperador = filasOperadoresQueTeAbren(data.opening_operators)
  const faced = data.faced || { base: {}, operators: [] }
  const rivals = data.rivals ?? []
  const stacks = data.rival_stacks ?? []

  const selector = (
    <label className="note" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      Muestra mínima
      <select value={minDuels} onChange={(e) => setMinDuels(Number(e.target.value))}>
        {MUESTRAS.map((m) => (
          <option key={m.value} value={m.value}>
            {m.label}
          </option>
        ))}
      </select>
    </label>
  )

  const columnaDuelos = {
    key: 'winrate',
    label: 'Ganas',
    render: (row) => (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
        <Bar value={row.winrate} />
        <span style={{ minWidth: 38 }}>{pct(row.winrate)}</span>
      </div>
    ),
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Duelos</h1>
          <p>
            Quién te mata y a quién matas. Sale del kill feed, no de un scoreboard: son duelos
            reales, uno contra uno.
          </p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} />

      <div className="kpis" style={{ marginBottom: 18 }}>
        <div className="stat">
          <div className="label">Duelos</div>
          <div className="value">{totals.duels}</div>
          <div className="sub">bajas y muertes contra rivales</div>
        </div>
        <div className={`stat ${base >= 50 ? 'good' : base <= 40 ? 'bad' : ''}`}>
          <div className="label">Ganados</div>
          <div className="value">{pct(base)}</div>
          <div className="sub">
            {totals.kills} a favor · {totals.deaths} en contra
          </div>
        </div>
      </div>

      <Panel
        title="Por operador rival"
        hint={
          'Con qué operador te estaban matando. El operador sale del scoreboard de esa ronda, ' +
          'porque el kill feed del .rec no lo trae en el evento. Un porcentaje muy bajo suele ' +
          'ser utilidad que no estás limpiando, no puntería.'
        }
        right={selector}
      >
        <DataTable
          columns={[
            { key: 'operator', label: 'Operador', left: true },
            { key: 'duels', label: 'Duelos' },
            { key: 'kills', label: 'Le ganas' },
            { key: 'deaths', label: 'Te gana' },
            { key: 'balance', label: 'Balance', render: (row) => <Balance value={row.balance} /> },
            columnaDuelos,
          ]}
          rows={operators}
          initialSort={{ key: 'duels', dir: 'desc' }}
          rowKey={(row) => row.operator}
          csvName="duelos-por-operador"
          empty={`Ningún operador llega a ${minDuels} duelos con estos filtros.`}
        />
      </Panel>

      <Panel
        title="Operadores que te abren"
        hint={
          'La primera baja de la ronda, por operador rival y por tu lado. Te abre: te sacó a ti ' +
          'en el primer duelo; Le abres: lo sacaste tú. El % es sobre tus muertes de apertura ' +
          'contra rivales de ese lado. Usa la muestra mínima de arriba, contada en aperturas.'
        }
      >
        <DataTable
          columns={[
            { key: 'operator', label: 'Operador', left: true },
            { key: 'side', label: 'Lado', render: (row) => <SideChip side={row.side} /> },
            { key: 'opened_you', label: 'Te abre' },
            { key: 'you_opened', label: 'Le abres' },
            { key: 'balance', label: 'Balance', render: (row) => <Balance value={row.balance} /> },
            { key: 'winrate', label: 'Ganas', render: (row) => pct(row.winrate) },
            {
              key: 'share',
              label: 'De tus aperturas perdidas',
              render: (row) => pct(row.share),
              help: 'Te abre sobre tus muertes de apertura contra rivales de ese lado, también las de operador desconocido.',
            },
          ]}
          rows={aperturasPorOperador}
          initialSort={{ key: 'opened_you', dir: 'desc' }}
          rowKey={(row) => row.key}
          csvName="operadores-que-te-abren"
          empty={`Ningún operador llega a ${minDuels} aperturas con estos filtros.`}
        />
      </Panel>

      <Panel
        title="Rondas contra cada operador"
        hint={
          'Todas las rondas en que ese operador estuvo del otro lado, haya o no un duelo. Mide ' +
          'lo que te condiciona sin matarte: un Mira que corta la entrada o un Jäger que se come ' +
          `tu utilidad. La comparación es contra tus ${faced.base.rounds ?? 0} rondas con estos ` +
          `filtros (mueres en el ${pct(faced.base.death_rate)}, ganas el ` +
          `${pct(faced.base.winrate)}). Desde 10 rondas; con tan poca muestra, una diferencia ` +
          'de 10 o 15 puntos todavía puede ser ruido.'
        }
      >
        <DataTable
          columns={[
            { key: 'operator', label: 'Operador', left: true },
            { key: 'rounds', label: 'Rondas' },
            { key: 'death_rate', label: 'Mueres', render: (row) => pct(row.death_rate) },
            {
              key: 'death_rate_delta',
              label: 'Mueres vs. promedio',
              help: 'Puntos de diferencia entre cuánto mueres con este operador enfrente y cuánto mueres en todas tus rondas filtradas.',
              render: (row) => <Diferencia value={row.death_rate_delta} mejorSiSube={false} />,
            },
            { key: 'winrate', label: 'Ganas la ronda', render: (row) => pct(row.winrate) },
            {
              key: 'winrate_delta',
              label: 'Ganas vs. promedio',
              help: 'Puntos de diferencia entre el winrate de estas rondas y el de todas tus rondas filtradas.',
              render: (row) => <Diferencia value={row.winrate_delta} mejorSiSube />,
            },
          ]}
          rows={faced.operators}
          initialSort={{ key: 'rounds', dir: 'desc' }}
          rowKey={(row) => row.operator}
          csvName="rondas-por-operador-rival"
          empty="Ningún operador rival llega a 10 rondas con estos filtros."
        />
      </Panel>

      <Panel
        title="Por rival"
        hint={
          'Agrupado por persona (profileID), así que un cambio de nick no parte la fila. En ' +
          'ranked solo casi nadie se repite: con pocos duelos esto es anécdota y no patrón, y ' +
          'por eso el coach solo opina desde 8 duelos contra la misma persona.'
        }
      >
        <DataTable
          columns={[
            {
              key: 'username',
              label: 'Rival',
              left: true,
              render: (row) => <Link to={`/jugadores/${row.player_id}`}>{row.username}</Link>,
            },
            { key: 'duels', label: 'Duelos' },
            { key: 'kills', label: 'Le ganas' },
            { key: 'deaths', label: 'Te gana' },
            { key: 'balance', label: 'Balance', render: (row) => <Balance value={row.balance} /> },
            columnaDuelos,
            {
              key: 'opening_duels',
              label: 'De apertura',
              help: 'Duelos que fueron la primera baja de la ronda. Perder siempre el primer contacto contra alguien es distinto a perderlo en general.',
              render: (row) =>
                row.opening_duels ? `${row.opening_kills}-${row.opening_deaths}` : '—',
            },
            {
              key: 'maps',
              label: 'Mapas',
              left: true,
              dim: true,
              wrap: true,
              sortable: false,
              render: (row) => row.maps.join(', ') || '—',
            },
          ]}
          rows={nemesis}
          initialSort={{ key: 'duels', dir: 'desc' }}
          rowKey={(row) => row.player_id}
          csvName="duelos-por-rival"
          empty={`Nadie llega a ${minDuels} duelos contigo con estos filtros.`}
        />
      </Panel>

      <Panel
        title="Rivales repetidos"
        hint={
          'Personas que te tocaron en el equipo contrario en 2 o más partidas, con el ' +
          'resultado de esas partidas. Es tu récord contra ellas, no su nivel: el resto lo ' +
          'deciden los otros ocho.'
        }
      >
        <DataTable
          columns={[
            {
              key: 'username',
              label: 'Rival',
              left: true,
              render: (row) => <Link to={`/jugadores/${row.player_id}`}>{row.username}</Link>,
            },
            { key: 'matches', label: 'Partidas' },
            {
              key: 'last_played',
              label: 'Última vez',
              help: 'La partida más reciente contra esa persona entre las que cuenta la fila.',
              render: (row) => fechaCorta(row.last_played),
              csv: (row) => fechaCsv(row.last_played),
            },
            { key: 'wins', label: 'Ganadas' },
            { key: 'losses', label: 'Perdidas' },
            {
              key: 'record',
              label: 'Récord',
              sortable: false,
              render: (row) => `${row.wins}-${row.losses}`,
              // `record` no viene en las filas: sin esto la celda sale vacia en el CSV
              csv: (row) => `${row.wins}-${row.losses}`,
            },
            {
              key: 'winrate',
              label: 'Winrate',
              help: 'Sobre las partidas con resultado: las que no lo tienen cuentan en Partidas y no acá.',
              render: (row) => pct(row.winrate),
            },
          ]}
          rows={rivals}
          initialSort={{ key: 'matches', dir: 'desc' }}
          rowKey={(row) => row.player_id}
          csvName="rivales-repetidos"
          empty="Nadie te tocó de rival en 2 o más partidas con estos filtros."
        />
      </Panel>

      <Panel
        title="Stacks rivales que se repiten"
        hint={
          'Grupos de 2 o más rivales que te tocaron juntos en el equipo contrario en 2 o más ' +
          'partidas. Si el grupo entero se repite, sale una sola fila con todos; un grupo más ' +
          'chico sale aparte solo si suma partidas propias. El replay no trae nombres de ' +
          'equipo: es solo coincidencia de personas.'
        }
      >
        <DataTable
          columns={[
            {
              key: 'players',
              label: 'Rivales',
              left: true,
              sortable: false,
              render: (row) =>
                row.players.map((p, i) => (
                  <React.Fragment key={p.player_id}>
                    {i > 0 && ' · '}
                    <Link to={`/jugadores/${p.player_id}`}>{p.username}</Link>
                  </React.Fragment>
                )),
              // sin esto la celda sale vacia en el CSV: `players` es una lista
              csv: (row) => row.players.map((p) => p.username).join(' + '),
            },
            { key: 'size', label: 'Juntos' },
            { key: 'matches', label: 'Partidas' },
            {
              key: 'last_played',
              label: 'Última vez',
              help: 'La partida más reciente contra ese grupo entre las que cuenta la fila.',
              render: (row) => fechaCorta(row.last_played),
              csv: (row) => fechaCsv(row.last_played),
            },
            { key: 'wins', label: 'Ganadas' },
            { key: 'losses', label: 'Perdidas' },
            {
              key: 'record',
              label: 'Récord',
              sortable: false,
              render: (row) => `${row.wins}-${row.losses}`,
              csv: (row) => `${row.wins}-${row.losses}`,
            },
            {
              key: 'winrate',
              label: 'Winrate',
              help: 'Sobre las partidas con resultado: las que no lo tienen cuentan en Partidas y no acá.',
              render: (row) => pct(row.winrate),
            },
          ]}
          rows={stacks}
          initialSort={{ key: 'matches', dir: 'desc' }}
          rowKey={(row) => row.players.map((p) => p.player_id).join('-')}
          csvName="stacks-rivales"
          empty="Ningún grupo de rivales se repitió en 2 o más partidas con estos filtros."
        />
      </Panel>

      <EstadoAlMorir filters={filters} />
    </>
  )
}
