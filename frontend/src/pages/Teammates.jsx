import React, { useState } from 'react'
import { Link } from 'react-router-dom'

import { useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import {
  Bar,
  DataTable,
  EmptyState,
  ErrorBox,
  Loading,
  Panel,
  SideChip,
  Stat,
  fmt,
  pct,
} from '../components/ui.jsx'
import { filasDeGrupo, textoHabituales } from '../grupo.js'
import { MUESTRA_PARTIDAS } from '../margen.js'
import { filasConPocaMuestra } from '../muestra.js'

const SAMPLES = [
  { value: 5, label: '5+ rondas' },
  { value: 10, label: '10+ rondas' },
  { value: 25, label: '25+ rondas' },
  { value: 50, label: '50+ rondas' },
]

export default function Teammates({ filters, setFilters, runImport, importing }) {
  const [minRounds, setMinRounds] = useState(10)
  const { data, error, loading } = useApi('/teammates/', { ...filters, min_rounds: minRounds })
  const overview = useApi('/overview/', filters)

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />

  const base = overview.data?.overall
  if (base && !base.rounds) return <EmptyState onImport={runImport} importing={importing} />

  const baseline = base?.winrate ?? null
  const rows = (data?.synergy || []).map((row) => ({
    ...row,
    delta: baseline === null || row.winrate === null ? null : row.winrate - baseline,
  }))
  const clutches = data?.clutches || []
  // DataTable ordena y exporta por clave plana: los lados se aplanan aca
  const conversion = (data?.clutch_conversion || []).map((row) => ({
    ...row,
    attack_pct: row.attack.pct,
    defense_pct: row.defense.pct,
  }))
  // El backend ya pone cada total de mapa arriba de sus sitios; `orden` lo conserva al ordenar
  const porSitio = (data?.clutch_by_site || []).map((row, orden) => ({ ...row, orden }))
  const porOperador = data?.clutch_by_operator || []
  // El orden del backend (Ataque, Defensa, Total) se fija con `orden` para que la tabla no lo cambie al ordenar.
  const firstDown = (data?.first_down || []).map((row, orden) => ({ ...row, orden }))
  const firstDownTotal = firstDown.find((row) => row.side === 'total')
  const grupos = filasDeGrupo(data?.by_stack)
  const tk = data?.teamkills
  const sinTeamkills = !tk || (tk.mine + tk.suffered === 0 && tk.rounds_with === 0)

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Compañeros</h1>
          <p>
            Con quien ganas y con quien no. Solo cuentan las rondas que jugaron en tu equipo
            {baseline === null ? '' : `, contra tu ${baseline.toFixed(0)}% general`}.
          </p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} />

      <Panel
        title="Sinergia"
        hint="El winrate de un compañero es el de las rondas compartidas, no el suyo aparte. Con pocas rondas es varianza: sube la muestra minima antes de sacar conclusiones."
        right={
          <label className="note" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            Muestra minima
            <select value={minRounds} onChange={(e) => setMinRounds(Number(e.target.value))}>
              {SAMPLES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
        }
      >
        <DataTable
          columns={[
            {
              key: 'username',
              label: 'Compañero',
              left: true,
              render: (row) => <Link to={`/jugadores/${row.player_id}`}>{row.username}</Link>,
            },
            { key: 'rounds', label: 'Rondas juntos' },
            {
              key: 'winrate',
              label: 'Ganadas',
              render: (row) => (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
                  <Bar value={row.winrate} />
                  <span style={{ minWidth: 38 }}>{pct(row.winrate)}</span>
                </div>
              ),
            },
            {
              key: 'delta',
              label: 'vs tu promedio',
              help: 'Diferencia en puntos entre el winrate con esa persona y tu winrate general con los mismos filtros.',
              render: (row) =>
                row.delta === null ? (
                  <span className="dim">—</span>
                ) : (
                  <span className={row.delta >= 0 ? 'chip win' : 'chip loss'}>
                    {row.delta > 0 ? '+' : ''}
                    {row.delta.toFixed(0)}
                  </span>
                ),
            },
            { key: 'kills', label: 'Sus bajas' },
            { key: 'kpr', label: 'Su KPR', digits: 2 },
          ]}
          rows={rows}
          initialSort={{ key: 'rounds', dir: 'desc' }}
          rowKey={(row) => row.player_id}
          csvName="companeros"
          empty={`Nadie llega a ${minRounds} rondas contigo con estos filtros.`}
        />
      </Panel>

      {data?.by_stack ? (
        <Panel
          title="Solo, en dúo o en stack"
          hint={
            filasConPocaMuestra(grupos.map((f) => ({ rounds: f.matches })), MUESTRA_PARTIDAS).length
              ? `Ojo: algún grupo tiene menos de ${MUESTRA_PARTIDAS} partidas; la diferencia puede ser varianza.`
              : `Habitual: jugó en tu equipo en ${data.by_stack.min_matches} o más partidas de todo tu historial; los filtros no lo cambian. Una partida cuenta por los habituales que estuvieron en cualquiera de sus rondas. El winrate de partida deja fuera empates e incompletas.`
          }
        >
          <DataTable
            columns={[
              { key: 'etiqueta', label: 'Grupo', sortable: false, left: true },
              { key: 'habituales', label: 'Habituales', sortable: false,
                help: 'Compañeros habituales distintos que jugaron en tu equipo esa partida.' },
              { key: 'matches', label: 'Partidas', sortable: false },
              { key: 'match_winrate', label: 'Winrate partida', digits: 0, suffix: '%', sortable: false,
                help: 'Sobre las partidas con ganador; empates e incompletas no entran.' },
              { key: 'rounds', label: 'Rondas', sortable: false },
              { key: 'winrate', label: 'Winrate rondas', digits: 0, suffix: '%', sortable: false },
              { key: 'rating', label: 'Rating', digits: 2, sortable: false },
            ]}
            rows={grupos}
            initialSort={{ key: 'orden', dir: 'asc' }}
            rowKey={(row) => row.group}
            csvName="solo-duo-stack"
          />
          <p className="note">{textoHabituales(data.by_stack)}</p>
        </Panel>
      ) : null}

      <Panel
        title="Primero en caer"
        hint="Primero de tu equipo, no de la ronda: si ya había caído un rival, sigue contando. Distinto de la apertura perdida de Duelos. En un empate al segundo decide el orden del feed."
      >
        {!firstDownTotal || firstDownTotal.rounds === 0 ? (
          <p className="dim">Sin rondas con estos filtros.</p>
        ) : (
          <DataTable
            columns={[
              {
                key: 'side',
                label: 'Lado',
                left: true,
                render: (row) => (row.side === 'total' ? 'Total' : <SideChip side={row.side} />),
              },
              { key: 'rounds', label: 'Rondas' },
              {
                key: 'me_first',
                label: 'Caíste primero',
                render: (row) => `${fmt(row.me_first)} (${pct(row.rounds ? (row.me_first / row.rounds) * 100 : null)})`,
              },
              { key: 'me_first_winrate', label: 'Winrate si caíste', render: (row) => pct(row.me_first_winrate) },
              {
                key: 'mate_first',
                label: 'Cayó un compañero',
                render: (row) => `${fmt(row.mate_first)} (${pct(row.rounds ? (row.mate_first / row.rounds) * 100 : null)})`,
              },
              { key: 'mate_first_winrate', label: 'Winrate si cayó otro', render: (row) => pct(row.mate_first_winrate) },
              { key: 'no_deaths', label: 'Sin bajas' },
              { key: 'no_deaths_winrate', label: 'Winrate sin bajas', render: (row) => pct(row.no_deaths_winrate) },
            ]}
            rows={firstDown}
            initialSort={{ key: 'orden', dir: 'asc' }}
            rowKey={(row) => row.side}
            csvName="primero-en-caer"
          />
        )}
      </Panel>

      <Panel
        title="Teamkills"
        hint="Bajas del feed con autor y víctima en tu equipo esa ronda. Siguen contando en Bajas, KPR, Rating y multikills: acá solo se hacen visibles."
      >
        {sinTeamkills ? (
          <p className="dim">Ningún teamkill en las rondas filtradas.</p>
        ) : (
          <>
            <div className="kpis" style={{ marginBottom: 14 }}>
              <Stat label="Hechos" value={fmt(tk.mine)} sub="compañeros que mataste" />
              <Stat label="Sufridos" value={fmt(tk.suffered)} sub="veces que te mató uno" />
              <Stat
                label="Rondas con teamkill"
                value={fmt(tk.rounds_with)}
                sub={`ganaste ${pct(tk.winrate_with)} · ${pct(tk.winrate_without)} en las demás`}
                help="Rondas con algún teamkill de tu equipo, tuyo o entre otros dos compañeros, y su winrate contra el de las demás rondas filtradas."
              />
            </div>
            <DataTable
              columns={[
                {
                  key: 'username',
                  label: 'Compañero',
                  left: true,
                  render: (row) => <Link to={`/jugadores/${row.player_id}`}>{row.username}</Link>,
                },
                { key: 'made', label: 'Hechos' },
                { key: 'suffered', label: 'Sufridos' },
                { key: 'total', label: 'Total' },
              ]}
              rows={tk.by_teammate}
              initialSort={{ key: 'total', dir: 'desc' }}
              rowKey={(row) => row.player_id}
              csvName="teamkills"
              empty="Los teamkills de estas rondas fueron entre otros compañeros."
            />
          </>
        )}
      </Panel>

      <Panel
        title="Clutches"
        hint="La conversión cuenta cada vez que quedaste último de tu equipo con rivales vivos, ganes o pierdas, y se arma desde el feed de bajas. La lista de clutches ganados usa el 1vX del scoreboard de la ronda."
      >
        <h3>Conversión por rivales</h3>
        <DataTable
          columns={[
            { key: 'label', label: 'Situación', left: true },
            { key: 'attempts', label: 'Intentos', render: (row) => fmt(row.attempts) },
            { key: 'won', label: 'Ganados', render: (row) => fmt(row.won) },
            { key: 'pct', label: 'Conversión', render: (row) => pct(row.pct) },
            { key: 'attack_pct', label: 'Ataque', render: (row) => pct(row.attack_pct) },
            { key: 'defense_pct', label: 'Defensa', render: (row) => pct(row.defense_pct) },
          ]}
          rows={conversion}
          initialSort={{ key: 'vs', dir: 'asc' }}
          rowKey={(row) => row.vs}
          csvName="clutch-conversion"
          empty="Todavía no quedaste último en ninguna ronda."
        />
        <h3>Clutch por mapa y sitio</h3>
        <DataTable
          columns={[
            {
              key: 'map',
              label: 'Mapa',
              left: true,
              render: (row) => (row.kind === 'map' ? <strong>{row.map}</strong> : <span className="dim">{row.map}</span>),
            },
            {
              key: 'site',
              label: 'Sitio',
              left: true,
              render: (row) => (row.kind === 'map' ? <strong>Total</strong> : row.site),
              // sin esto la fila total sale con el sitio vacio y quien sume la columna cuenta doble
              csv: (row) => (row.kind === 'map' ? 'Total' : row.site),
            },
            { key: 'attempts', label: 'Intentos', render: (row) => fmt(row.attempts) },
            { key: 'won', label: 'Ganados', render: (row) => fmt(row.won) },
            {
              key: 'pct',
              label: 'Conversión',
              help: 'Un * marca menos de 5 intentos: con tan poca muestra el % todavía no dice mucho.',
              render: (row) => (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
                  <Bar value={row.pct} />
                  <span style={{ minWidth: 46 }}>
                    {pct(row.pct)}
                    {row.low_sample ? (
                      <span className="dim muestra-chica" title="Menos de 5 intentos">
                        *
                      </span>
                    ) : null}
                  </span>
                </div>
              ),
            },
          ]}
          rows={porSitio}
          initialSort={{ key: 'orden', dir: 'asc' }}
          rowKey={(row) => `${row.slug}-${row.kind}-${row.site}`}
          csvName="clutch-por-sitio"
          empty="Todavía no quedaste último en ninguna ronda."
        />
        <h3>Clutch por operador</h3>
        <DataTable
          columns={[
            { key: 'operator', label: 'Operador', left: true },
            {
              key: 'side',
              label: 'Lado',
              render: (row) => <SideChip side={row.side} />,
              csv: (row) => (row.side === 'Attack' ? 'Ataque' : 'Defensa'),
            },
            { key: 'attempts', label: 'Intentos', render: (row) => fmt(row.attempts) },
            { key: 'won', label: 'Ganados', render: (row) => fmt(row.won) },
            {
              key: 'pct',
              label: 'Conversión',
              help: 'Un * marca menos de 5 intentos: con tan poca muestra el % todavía no dice mucho.',
              render: (row) => (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
                  <Bar value={row.pct} />
                  <span style={{ minWidth: 46 }}>
                    {pct(row.pct)}
                    {row.low_sample ? (
                      <span className="dim muestra-chica" title="Menos de 5 intentos">
                        *
                      </span>
                    ) : null}
                  </span>
                </div>
              ),
            },
          ]}
          rows={porOperador}
          initialSort={{ key: 'attempts', dir: 'desc' }}
          rowKey={(row) => `${row.operator}-${row.side}`}
          csvName="clutch-por-operador"
          empty="Todavía no quedaste último en ninguna ronda."
        />
        <h3>Clutches ganados</h3>
        <DataTable
          columns={[
            {
              key: 'played_at',
              label: 'Cuando',
              render: (row) => (
                <Link to={`/partidas/${row.match_id}`}>
                  {row.played_at.slice(5, 16).replace('T', ' ')}
                </Link>
              ),
            },
            { key: 'match', label: 'Mapa' },
            { key: 'round', label: 'Ronda', render: (row) => `R${row.round}` },
            { key: 'site', label: 'Sitio', left: true, dim: true },
            { key: 'side', label: 'Lado', render: (row) => <SideChip side={row.side} /> },
            { key: 'operator', label: 'Operador' },
            { key: 'vs', label: '1vX', render: (row) => `1v${row.vs}` },
            { key: 'kills', label: 'Bajas', render: (row) => fmt(row.kills) },
          ]}
          rows={clutches}
          initialSort={{ key: 'played_at', dir: 'desc' }}
          rowKey={(row) => `${row.match_id}-${row.round}`}
          csvName="clutches"
          empty="Todavia no ganaste ninguna ronda quedandote solo."
        />
      </Panel>
    </>
  )
}
