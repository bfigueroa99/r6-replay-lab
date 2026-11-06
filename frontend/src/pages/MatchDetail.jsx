import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useApi } from '../api.js'
import {
  DataTable,
  ErrorBox,
  NoExiste,
  Loading,
  Panel,
  ResultChip,
  SideChip,
  fmt,
  pct,
} from '../components/ui.jsx'
import MatrizDuelos from '../components/MatrizDuelos.jsx'
import { detalleMultikills, textoMultikills } from '../multikills.js'
import { marcasDeApertura } from '../aperturas.js'
import { textoDeRachas } from '../rachas.js'
import { textoResumenPartida } from '../resumenPartida.js'
import { filasTradesEquipo, textoTradesEquipo } from '../tradesEquipo.js'
import { filasDeFases, hayBajas, notaDeFases } from '../fasesRonda.js'
import { separadorAntes, textoStackRival } from '../stacksRivales.js'
import { pasoDeTecla, rondaVecina } from '../navegacionRondas.js'

export default function MatchDetail() {
  const { id } = useParams()
  // La ruta reusa el componente al ir a otra partida: con la key cambia todo el
  // estado (ronda elegida, copia) y useApi no muestra la partida previa mientras carga
  return <DetallePartida key={id} id={id} />
}

function DetallePartida({ id }) {
  const { data, error, status, loading } = useApi(`/matches/${id}/`)
  const [selected, setSelected] = useState(0)
  const [copia, setCopia] = useState(null)
  const total = data?.rounds?.length ?? 0

  useEffect(() => {
    function alApretar(e) {
      const paso = pasoDeTecla(e)
      if (!paso || !total) return
      // sin esto la flecha ademas desplaza la pagina
      e.preventDefault()
      setSelected((s) => rondaVecina(s, total, paso))
    }
    window.addEventListener('keydown', alApretar)
    return () => window.removeEventListener('keydown', alApretar)
  }, [total])

  if (status === 404) return <NoExiste titulo="Esa partida no existe" a="/partidas" texto="Ver tus partidas" />
  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  if (!data) return null

  const { match, rounds, scoreboard, my_totals: mine } = data
  const rachas = textoDeRachas(data.round_streaks)
  // Un .rec cortado deja la partida sin rondas: rounds[-1] seria undefined y tumbaria la pagina
  const round = rounds.length ? rounds[Math.min(selected, rounds.length - 1)] : null

  async function copiarResumen() {
    // Sin console: un portapapeles negado es esperable (permisos, http) y se avisa en la pagina
    if (!navigator.clipboard?.writeText) {
      setCopia('error')
      return
    }
    try {
      await navigator.clipboard.writeText(textoResumenPartida(data))
      setCopia('ok')
    } catch {
      setCopia('error')
    }
  }

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
          {rachas && <p className="note">{rachas}</p>}
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <EnlacePartida id={match.prev_id} title="Jugada antes">
            ← Partida anterior
          </EnlacePartida>
          <EnlacePartida id={match.next_id} title="Jugada después">
            Partida siguiente →
          </EnlacePartida>
          {copia && (
            <span className="note">
              {copia === 'ok' ? 'Copiado' : 'No se pudo copiar: el navegador no dio acceso al portapapeles.'}
            </span>
          )}
          <button type="button" className="btn small" onClick={copiarResumen}>
            Copiar resumen
          </button>
          <Link className="btn small" to="/partidas">
            Volver
          </Link>
        </div>
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

      <StacksRivales stacks={data.rival_stacks} />

      {round ? (
        <Panel title="Rondas" hint="Clic en una ronda o ← → para ver su timeline.">
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
                {round.score_after?.join('-')} · duró {Math.round(round.duration)}s
                <br />
                Condición: {translateCondition(round.win_condition)}
                {round.win_condition_certain ? '' : ' (inferida)'}
                {round.possible_plant ? ' · plant probable' : ''}
              </p>
              {round.summary?.length ? (
                <p className="resumen">{round.summary.join(' ')}</p>
              ) : null}
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
                  { key: 'died', label: 'Murio', render: (row) => (row.died ? 'sí' : 'no') },
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
      ) : (
        <Panel title="Rondas">
          <p className="note" style={{ margin: 0 }}>
            Esta partida no tiene rondas importadas.
          </p>
        </Panel>
      )}

      <Panel title="Matriz de duelos" hint="Quién mató a quién en esta partida. Filas: el que mata.">
        <MatrizDuelos
          rounds={rounds}
          miEquipo={rounds.length && myTeam(rounds[0]) >= 0 ? myTeam(rounds[0]) : match.my_team_index}
        />
      </Panel>

      <Panel
        title="Trades por equipo"
        hint="Muertes que tu equipo y el rival dejaron sin vengar en la ventana de trade."
      >
        <TradesPorEquipo teamTrades={data.team_trades} />
      </Panel>

      <Panel
        title="Fases de la ronda"
        hint="Bajas de cada equipo según el momento de la ronda, y cómo terminaron las rondas en que un equipo dominó esa fase."
      >
        <FasesDeLaRonda phases={data.phases} />
      </Panel>

      <Panel title="Scoreboard de la partida" hint="Los dos equipos, con las métricas derivadas.">
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
            {
              key: 'multikill_rounds',
              label: 'Multikills',
              help: 'Rondas con 2, 3, 4 y 5 o más bajas. Ordena por el total de rondas con 2 o más.',
              render: (row) => <span title={detalleMultikills(row)}>{textoMultikills(row)}</span>,
              csv: textoMultikills,
            },
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

function StacksRivales({ stacks }) {
  // Sin grupos no se muestra nada: un panel vacio en cada partida contra desconocidos seria ruido
  if (!stacks?.length) return null
  return (
    <div className="note stacks-rivales">
      {stacks.map((grupo) => (
        <div key={grupo.players.map((j) => j.player_id).join('-')}>
          {grupo.players.map((j, i) => (
            <React.Fragment key={j.player_id}>
              {separadorAntes(i, grupo.players.length)}
              <Link to={`/jugadores/${j.player_id}`}>{j.username}</Link>
            </React.Fragment>
          ))}{' '}
          {textoStackRival(grupo)} · <Link to="/duelos">Ver en Duelos</Link>
        </div>
      ))}
    </div>
  )
}

function TradesPorEquipo({ teamTrades }) {
  const filas = filasTradesEquipo(teamTrades)
  const nota = textoTradesEquipo(teamTrades)
  // La celda del equipo que sale mejor en esa columna va resaltada
  const resaltar = (col, texto) => (row) =>
    row.mejor[col] ? <span className="chip win">{texto(row)}</span> : texto(row)
  return (
    <>
      <DataTable
        columns={[
          { key: 'label', label: 'Equipo', left: true, sortable: false },
          { key: 'deaths', label: 'Muertes', sortable: false },
          { key: 'traded_deaths', label: 'Tradeadas', sortable: false },
          {
            key: 'untraded_deaths',
            label: 'Sin trade',
            sortable: false,
            render: resaltar('untraded_deaths', (row) => row.untraded_deaths),
          },
          {
            key: 'untraded_pct',
            label: '% sin trade',
            sortable: false,
            render: resaltar('untraded_pct', (row) => fmt(row.untraded_pct, 0, '%')),
          },
          {
            key: 'trade_kills',
            label: 'Trade kills',
            sortable: false,
            render: resaltar('trade_kills', (row) => row.trade_kills),
          },
        ]}
        rows={filas}
        initialSort={{ key: 'orden', dir: 'asc' }}
        rowKey={(row) => row.key}
        rowClass={(row) => (row.key === 'mine' ? 'me' : '')}
        empty="Esta partida no trae trades por equipo."
      />
      {nota ? <p className="note">{nota}</p> : null}
    </>
  )
}

function FasesDeLaRonda({ phases }) {
  if (!hayBajas(phases)) {
    return <p className="note">Esta partida no tiene bajas con reloj entre equipos.</p>
  }
  const nota = notaDeFases(phases)
  const resaltar = (lado) => (row) =>
    row.mejor === lado ? <span className="chip win">{row[lado]}</span> : row[lado]
  return (
    <>
      <DataTable
        columns={[
          { key: 'label', label: 'Fase', left: true, sortable: false },
          { key: 'mine', label: 'Tu equipo', sortable: false, render: resaltar('mine') },
          { key: 'rival', label: 'Rival', sortable: false, render: resaltar('rival') },
          {
            key: 'ganadasAdelante',
            label: 'Rondas que dominaste (ganadas)',
            sortable: false,
            help: 'Rondas en que tu equipo sacó más bajas que el rival en esta fase, y cuántas ganaste.',
          },
          {
            key: 'ganadasAtras',
            label: 'Rondas que dominó el rival (ganadas)',
            sortable: false,
            help: 'Rondas en que el rival sacó más bajas en esta fase, y cuántas ganaste igual.',
          },
        ]}
        rows={filasDeFases(phases)}
        initialSort={{ key: 'orden', dir: 'asc' }}
        rowKey={(row) => row.key}
      />
      {nota ? <p className="note">{nota}</p> : null}
    </>
  )
}

function Timeline({ round }) {
  const mineTeam = new Set(round.players.filter((p) => p.team_index === myTeam(round)).map((p) => p.username))
  const marcas = marcasDeApertura(round, myTeam(round))

  if (!round.events.length) {
    return <p className="note">Esta ronda no registró eventos en el feed.</p>
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
                <span className="who">{event.actor}</span> mató a <span className="who">{event.target}</span>
              </>
            ) : event.kind === 'Death' ? (
              <>
                <span className="who">{event.actor}</span> murió
              </>
            ) : (
              <>
                {event.kind} {event.actor} {event.operator ? `→ ${event.operator}` : ''} {event.message}
              </>
            )}
            <span className="tags">
              {event.order === marcas.apertura ? (
                <span className="chip" title="Primera baja de la ronda">
                  apertura
                </span>
              ) : null}
              {event.order === marcas.entry ? (
                <span className="chip" title="Primera baja de tu equipo">
                  entry
                </span>
              ) : null}
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
  KilledOpponents: 'eliminación del equipo rival',
  DefusedBomb: 'bomba plantada y detonada',
  DisabledDefuser: 'defuser desactivado',
  Time: 'se acabó el tiempo',
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

function EnlacePartida({ id, title, children }) {
  // en el extremo del historial, un boton apagado y no un Link a /partidas/null
  if (id == null) {
    return (
      <button type="button" className="btn small" disabled title={title}>
        {children}
      </button>
    )
  }
  return (
    <Link className="btn small" to={`/partidas/${id}`} title={title}>
      {children}
    </Link>
  )
}
