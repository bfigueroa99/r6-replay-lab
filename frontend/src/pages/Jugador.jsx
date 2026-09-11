import React from 'react'
import { Link, useParams } from 'react-router-dom'

import { useApi } from '../api.js'
import {
  Bar,
  DataTable,
  ErrorBox,
  Loading,
  Panel,
  ResultChip,
  SideChip,
  fmt,
  pct,
  ratio,
} from '../components/ui.jsx'

const fecha = (iso) => (iso ? iso.slice(0, 10).split('-').reverse().join('-') : '—')

/** Con menos de 20 rondas la comparacion es ruido, y hay que decirlo. */
const MUESTRA_MINIMA = 20

export default function Jugador() {
  const { id } = useParams()
  const { data, error, loading } = useApi(`/players/${id}/`)

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  if (!data) return null

  const { player, with: con, without: sin, against: contra, theirs, duels } = data
  const juntos = data.rounds_together
  const enContra = data.rounds_against
  const flaco = Math.min(con.rounds || 0, sin.rounds || 0) < MUESTRA_MINIMA

  const comparacion = [
    { name: 'Con esta persona en tu equipo', ...con },
    { name: 'Sin ella', ...sin },
  ]
  if (enContra) comparacion.push({ name: 'Contra ella', ...contra })

  return (
    <>
      <div className="page-head">
        <div>
          <h1>
            {player.username}
            {player.is_me ? <span className="chip" style={{ marginLeft: 10 }}>eres tu</span> : null}
          </h1>
          <p>
            {juntos} rondas en tu equipo
            {enContra ? ` · ${enContra} en contra` : ''} · visto entre {fecha(player.first_seen)} y{' '}
            {fecha(player.last_seen)}
            {player.aliases?.length ? ` · antes: ${player.aliases.join(', ')}` : ''}
          </p>
        </div>
        <Link className="btn small" to="/companeros">
          Volver
        </Link>
      </div>

      <Panel
        title="Tu rendimiento con y sin"
        hint={
          flaco
            ? 'Ojo: uno de los dos lados tiene menos de 20 rondas, asi que la diferencia puede ser varianza y no la persona.'
            : 'Tus numeros en las rondas que compartieron, contra el resto de tu historial.'
        }
      >
        <DataTable
          columns={[
            { key: 'name', label: '', sortable: false, left: true },
            { key: 'rounds', label: 'Rondas' },
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
            { key: 'rating', label: 'Rating', digits: 2 },
            { key: 'kd', label: 'K/D', digits: 2 },
            { key: 'kpr', label: 'KPR', digits: 2 },
            { key: 'opening_winrate', label: 'Aperturas', digits: 0, suffix: '%' },
            { key: 'kst_pct', label: 'KST', digits: 0, suffix: '%' },
          ]}
          rows={comparacion}
          initialSort={{ key: 'rounds', dir: 'desc' }}
          rowKey={(row) => row.name}
          csvName={`con-y-sin-${player.username}`}
        />
      </Panel>

      {duels ? (
        <Panel title="Duelos entre ustedes" hint="Bajas directas, sacadas del kill feed.">
          <div className="kpis">
            <div className="stat">
              <div className="label">Le ganaste</div>
              <div className="value">{duels.kills}</div>
            </div>
            <div className="stat">
              <div className="label">Te gano</div>
              <div className="value">{duels.deaths}</div>
            </div>
            <div className={`stat ${duels.balance > 0 ? 'good' : duels.balance < 0 ? 'bad' : ''}`}>
              <div className="label">Balance</div>
              <div className="value">
                {duels.balance > 0 ? '+' : ''}
                {duels.balance}
              </div>
              <div className="sub">
                {pct(duels.winrate)} ganados
                {duels.opening_duels
                  ? ` · ${duels.opening_duels} fueron el primer duelo de la ronda`
                  : ''}
              </div>
            </div>
          </div>
        </Panel>
      ) : null}

      <Panel
        title="Sus numeros"
        hint="Lo que hizo esa persona en las rondas que compartieron. Sale del kill feed, asi que no incluye su scoreboard completo. Sin rating: el 1.00 es tu promedio, no el suyo."
      >
        <div className="kpis" style={{ marginBottom: 14 }}>
          <div className="stat">
            <div className="label">Rondas</div>
            <div className="value">{theirs.rounds}</div>
          </div>
          <div className="stat">
            <div className="label">K/D</div>
            <div className="value">{ratio(theirs.kd)}</div>
            <div className="sub">
              {theirs.kills} bajas · {theirs.deaths} muertes
            </div>
          </div>
          <div className="stat">
            <div className="label">KPR</div>
            <div className="value">{ratio(theirs.kpr)}</div>
          </div>
          <div className="stat">
            <div className="label">Aperturas</div>
            <div className="value">{pct(theirs.opening_winrate)}</div>
            <div className="sub">
              {theirs.opening_kills}-{theirs.opening_deaths}
            </div>
          </div>
          <div className="stat">
            <div className="label">Sobrevive</div>
            <div className="value">{pct(theirs.survival_pct)}</div>
          </div>
        </div>

        <DataTable
          columns={[
            { key: 'operator', label: 'Operador', left: true },
            { key: 'side', label: 'Lado', render: (row) => <SideChip side={row.side} /> },
            { key: 'rounds', label: 'Rondas' },
            { key: 'kills', label: 'Bajas' },
            { key: 'kpr', label: 'KPR', digits: 2 },
            { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%' },
          ]}
          rows={data.their_operators}
          initialSort={{ key: 'rounds', dir: 'desc' }}
          rowKey={(row) => `${row.operator}-${row.side}`}
          csvName={`operadores-${player.username}`}
          empty="Sin operadores registrados en esas rondas."
        />
      </Panel>

      <Panel title="Partidas compartidas">
        <DataTable
          columns={[
            {
              key: 'played_at',
              label: 'Cuando',
              render: (row) => (
                <Link to={`/partidas/${row.id}`}>{row.played_at.slice(5, 16).replace('T', ' ')}</Link>
              ),
            },
            { key: 'map', label: 'Mapa' },
            {
              key: 'role',
              label: 'Jugo de',
              render: (row) => (
                <span className={`chip ${row.role === 'companero' ? 'win' : 'loss'}`}>
                  {row.role}
                </span>
              ),
            },
            { key: 'rounds', label: 'Rondas juntos' },
            { key: 'score', label: 'Marcador', sortable: false },
            {
              key: 'won',
              label: 'Resultado',
              render: (row) => <ResultChip won={row.won}>{row.result}</ResultChip>,
              csv: (row) => row.result,
            },
          ]}
          rows={data.matches}
          initialSort={{ key: 'played_at', dir: 'desc' }}
          rowKey={(row) => row.id}
          csvName={`partidas-con-${player.username}`}
          empty="No comparten ninguna partida con estos filtros."
        />
      </Panel>

      <p className="note">
        Todo lo de esta pagina sale de tus propios replays: son las rondas que jugaste con o contra
        esa persona, no su historial completo. {fmt(data.matches.length)} partidas compartidas.
      </p>
    </>
  )
}
