import React, { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useApi } from '../api.js'
import {
  DataTable,
  ErrorBox,
  Loading,
  Panel,
  ResultChip,
  SideChip,
  fmt,
  pct,
} from '../components/ui.jsx'

export default function MatchDetail() {
  const { id } = useParams()
  const { data, error, loading } = useApi(`/matches/${id}/`)
  const [selected, setSelected] = useState(0)

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  if (!data) return null

  const { match, rounds, scoreboard, my_totals: mine } = data
  const round = rounds[Math.min(selected, rounds.length - 1)]

  return (
    <>
      <div className="page-head">
        <div>
          <h1>
            {match.map} · {match.score}{' '}
            <ResultChip won={match.won}>{match.result}</ResultChip>
          </h1>
          <p>
            {match.played_at.slice(0, 16).replace('T', ' ')} · {match.match_type} · {match.gamemode} ·{' '}
            {match.game_version}
          </p>
        </div>
        <Link className="btn small" to="/partidas">
          Volver
        </Link>
      </div>

      {match.warnings?.length ? (
        <div className="error">
          {match.warnings.map((w) => (
            <div key={w}>{w}</div>
          ))}
        </div>
      ) : null}

      <div className="kpis" style={{ marginBottom: 18 }}>
        <Mini label="Rondas ganadas" value={pct(mine.winrate)} sub={`${mine.rounds_won} de ${mine.rounds}`} />
        <Mini label="Bajas / muertes" value={`${mine.kills} / ${mine.deaths}`} sub={`K/D ${fmt(mine.kd, 2)}`} />
        <Mini label="Headshots" value={pct(mine.hs_pct)} sub={`${mine.headshots} de ${mine.kills}`} />
        <Mini
          label="Duelos de apertura"
          value={`${mine.opening_kills}-${mine.opening_deaths}`}
          sub={`${pct(mine.opening_winrate)} ganados`}
        />
        <Mini label="KST" value={pct(mine.kst_pct)} sub={`${mine.kst_rounds} rondas con aporte`} />
        <Mini
          label="Muertes sin trade"
          value={`${mine.untraded_deaths}`}
          sub={`${pct(mine.untraded_death_pct)} de tus muertes`}
        />
      </div>

      <Panel title="Rondas" hint="Clic en una ronda para ver su timeline.">
        <div className="round-tabs">
          {rounds.map((r, i) => (
            <button
              key={r.number}
              className={`round-tab ${r.my_team_won === null ? '' : r.my_team_won ? 'win' : 'loss'} ${
                i === selected ? 'active' : ''
              }`}
              onClick={() => setSelected(i)}
              title={`${r.site || 'sitio desconocido'} · ${r.my_side === 'Attack' ? 'ataque' : 'defensa'}`}
            >
              <span className="n">{r.label}</span>
              <span className="dot" />
              <span style={{ fontSize: 10 }}>{r.my_side === 'Attack' ? 'ATK' : 'DEF'}</span>
            </button>
          ))}
        </div>

        <div className="round-detail">
          <div>
            <h3 style={{ marginTop: 0, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              {round.label} <SideChip side={round.my_side} />
              <ResultChip won={round.my_team_won} />
            </h3>
            <p className="note" style={{ marginTop: 0 }}>
              Sitio: <b>{round.site || 'desconocido'}</b> · marcador {round.score_before?.join('-')} →{' '}
              {round.score_after?.join('-')} · duro {Math.round(round.duration)}s
              <br />
              Condicion: {translateCondition(round.win_condition)}
              {round.win_condition_certain ? '' : ' (inferida)'}
              {round.possible_plant ? ' · plant probable' : ''}
            </p>
            <Timeline round={round} />
          </div>

          <div>
            <h3 style={{ marginTop: 0 }}>Jugadores de la ronda</h3>
            <DataTable
              columns={[
                {
                  key: 'username',
                  label: 'Jugador',
                  left: true,
                  render: (row) =>
                    row.player_id ? (
                      <Link to={`/jugadores/${row.player_id}`}>{row.username}</Link>
                    ) : (
                      row.username
                    ),
                },
                { key: 'operator', label: 'Operador', left: true },
                { key: 'kills', label: 'K' },
                { key: 'died', label: 'Murio', render: (row) => (row.died ? 'si' : 'no') },
                { key: 'hs_pct', label: 'HS%', digits: 0, suffix: '%' },
                {
                  key: 'death_elapsed',
                  label: 'Murio a los',
                  render: (row) => (row.death_elapsed ? `${Math.round(row.death_elapsed)}s` : '—'),
                },
                {
                  key: 'flags',
                  label: 'Notas',
                  sortable: false,
                  wrap: true,
                  render: (row) => (
                    <span className="tags">
                      {row.opening_kill ? <span className="chip win">1a baja</span> : null}
                      {row.opening_death ? <span className="chip loss">1a muerte</span> : null}
                      {row.trade_kills ? <span className="chip">{row.trade_kills} trade</span> : null}
                      {row.untraded_death ? <span className="chip loss">sin trade</span> : null}
                      {row.one_vx ? <span className="chip win">1v{row.one_vx}</span> : null}
                    </span>
                  ),
                },
              ]}
              rows={round.players}
              initialSort={{ key: 'kills', dir: 'desc' }}
              rowKey={(row) => row.username}
              rowClass={(row) => (row.is_me ? 'me' : '')}
            />
          </div>
        </div>
      </Panel>

      <Panel title="Scoreboard de la partida" hint="Los dos equipos, con las metricas derivadas.">
        <DataTable
          columns={[
            {
              key: 'username',
              label: 'Jugador',
              left: true,
              render: (row) =>
                row.player_id ? (
                  <Link to={`/jugadores/${row.player_id}`}>{row.username}</Link>
                ) : (
                  row.username
                ),
            },
            { key: 'team_index', label: 'Equipo', render: (row) => (row.team_index === match.my_team_index ? 'tuyo' : 'rival') },
            { key: 'rounds', label: 'Rondas' },
            { key: 'kills', label: 'Bajas' },
            { key: 'deaths', label: 'Muertes' },
            { key: 'kd', label: 'K/D', digits: 2 },
            { key: 'hs_pct', label: 'HS%', digits: 0, suffix: '%' },
            {
              key: 'opening_kills',
              label: 'Aperturas',
              render: (row) => `${row.opening_kills}-${row.opening_deaths}`,
            },
            { key: 'trade_kills', label: 'Trades' },
            { key: 'untraded_deaths', label: 'Sin trade' },
            { key: 'clutches', label: '1vX' },
            { key: 'kst_pct', label: 'KST', digits: 0, suffix: '%' },
          ]}
          rows={scoreboard}
          initialSort={{ key: 'kills', dir: 'desc' }}
          rowKey={(row) => `${row.player_id}-${row.team_index}`}
          rowClass={(row) => (row.is_me ? 'me' : '')}
        />
      </Panel>
    </>
  )
}

function Timeline({ round }) {
  const mineTeam = new Set(round.players.filter((p) => p.team_index === myTeam(round)).map((p) => p.username))

  if (!round.events.length) {
    return <p className="note">Esta ronda no registro eventos en el feed.</p>
  }

  return (
    <ul className="timeline">
      {round.events.map((event) => {
        const actorIsMine = mineTeam.has(event.actor)
        const cls = event.kind === 'Kill' ? (actorIsMine ? 'mine' : 'against') : ''
        return (
          <li key={event.order} className={cls}>
            <span className="clock">{event.clock_raw || '—'}</span>
            {event.kind === 'Kill' ? (
              <>
                <span className="who">{event.actor}</span> mato a <span className="who">{event.target}</span>
              </>
            ) : event.kind === 'Death' ? (
              <>
                <span className="who">{event.actor}</span> murio
              </>
            ) : (
              <>
                {event.kind} {event.actor} {event.operator ? `→ ${event.operator}` : ''} {event.message}
              </>
            )}
            <span className="tags">
              {event.headshot ? <span className="chip">HS</span> : null}
              {event.traded ? <span className="chip">tradeada</span> : null}
            </span>
          </li>
        )
      })}
    </ul>
  )
}

const myTeam = (round) => {
  const me = round.players.find((p) => p.is_me)
  return me ? me.team_index : (round.teams || []).findIndex((t) => t.mine)
}

const CONDITIONS = {
  KilledOpponents: 'eliminacion del equipo rival',
  DefusedBomb: 'bomba plantada y detonada',
  DisabledDefuser: 'defuser desactivado',
  Time: 'se acabo el tiempo',
  ObjectiveOrTime: 'objetivo o tiempo',
  '': 'sin determinar',
}
const translateCondition = (value) => CONDITIONS[value] || value

function Mini({ label, value, sub }) {
  return (
    <div className="stat">
      <div className="label">{label}</div>
      <div className="value" style={{ fontSize: 20 }}>
        {value}
      </div>
      {sub ? <div className="sub">{sub}</div> : null}
    </div>
  )
}
