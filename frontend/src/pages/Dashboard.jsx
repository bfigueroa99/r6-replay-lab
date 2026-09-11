import React, { Suspense, lazy } from 'react'
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
  fmt,
  pct,
  ratio,
} from '../components/ui.jsx'

// recharts son casi 400 kB y esta pantalla se ve completa sin el grafico: se
// carga aparte para que el Resumen pinte antes.
const EvolucionChart = lazy(() => import('../components/EvolucionChart.jsx'))

export default function Dashboard({ filters, setFilters, runImport, importing }) {
  const overview = useApi('/overview/', filters)
  const coach = useApi('/coach/', filters)
  const trends = useApi('/trends/', { ...filters, limit: 25 })

  if (overview.error) return <ErrorBox error={overview.error} />
  if (overview.loading && !overview.data) return <Loading />

  const total = overview.data?.overall
  if (!total || !total.rounds) {
    return <EmptyState onImport={runImport} importing={importing} />
  }

  const { attack, defense, recent_form: form, data_health: health } = overview.data
  const topInsights = (coach.data?.insights || []).filter((i) => i.severity !== 'positivo').slice(0, 3)
  const series = (trends.data?.by_match || []).map((row, i) => ({
    ...row,
    n: i + 1,
    label: `${row.map} ${row.played_at.slice(5, 10)}`,
  }))

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Resumen</h1>
          <p>
            {total.matches} partidas · {total.rounds} rondas analizadas
          </p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} />

      <div className="kpis" style={{ marginBottom: 18 }}>
        <Stat3 label="Rondas ganadas" value={pct(total.winrate)} sub={`${total.rounds_won} de ${total.rounds}`} value_={total.winrate} />
        <Stat3 label="K/D" value={ratio(total.kd)} sub={`${total.kills} bajas · ${total.deaths} muertes`} value_={total.kd === null ? null : total.kd * 50} />
        <Stat3 label="Kills por ronda" value={ratio(total.kpr)} sub="referencia solida: 0.8" value_={total.kpr === null ? null : total.kpr * 60} />
        <Stat3 label="Headshots" value={pct(total.hs_pct)} sub={`${total.headshots} de ${total.kills}`} value_={total.hs_pct} />
        <Stat3
          label="Duelos de apertura"
          value={pct(total.opening_winrate)}
          sub={`${total.opening_kills}-${total.opening_deaths} en ${total.opening_duels} duelos`}
          value_={total.opening_winrate}
        />
        <Stat3 label="KST" value={pct(total.kst_pct)} sub="rondas donde aportas algo" value_={total.kst_pct} />
        <Stat3 label="Sobrevives" value={pct(total.survival_pct)} sub={`${total.survived} rondas`} value_={total.survival_pct} />
        <Stat3
          label="Muertes sin trade"
          value={pct(total.untraded_death_pct)}
          sub={`${total.untraded_deaths} de ${total.deaths}`}
          value_={total.untraded_death_pct === null ? null : 100 - total.untraded_death_pct}
        />
      </div>

      <div className="grid cols-2">
        <Panel title="Ataque vs defensa">
          <DataTable
            columns={[
              { key: 'name', label: '', sortable: false },
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
              { key: 'kd', label: 'K/D', digits: 2 },
              { key: 'kpr', label: 'KPR', digits: 2 },
              { key: 'opening_winrate', label: 'Aperturas', digits: 0, suffix: '%' },
              {
                key: 'avg_death_elapsed',
                label: 'Mueres a los',
                render: (row) => (row.avg_death_elapsed ? `${Math.round(row.avg_death_elapsed)}s` : '—'),
              },
            ]}
            rows={[
              { name: 'Ataque', ...attack },
              { name: 'Defensa', ...defense },
            ]}
            initialSort={{ key: 'rounds', dir: 'desc' }}
            rowKey={(row) => row.name}
          />
        </Panel>

        <Panel title="Ultimas partidas" right={<Link className="btn small" to="/partidas">Ver todas</Link>}>
          <div className="form-row" style={{ marginBottom: 12 }}>
            {form.map((match) => (
              <Link
                key={match.id}
                to={`/partidas/${match.id}`}
                className={`form-dot ${match.won === null ? 'draw' : match.won ? 'win' : 'loss'}`}
                title={`${match.map} ${match.score} · ${match.kills}/${match.deaths} · ${match.played_at.slice(0, 16).replace('T', ' ')}`}
              >
                {match.won === null ? '=' : match.won ? 'V' : 'D'}
              </Link>
            ))}
          </div>
          <DataTable
            columns={[
              {
                key: 'map',
                label: 'Mapa',
                render: (row) => <Link to={`/partidas/${row.id}`}>{row.map}</Link>,
              },
              { key: 'score', label: 'Marcador', sortable: false },
              { key: 'kills', label: 'K' },
              { key: 'deaths', label: 'D' },
              { key: 'kd', label: 'K/D', digits: 2 },
              { key: 'rating', label: 'Rating', digits: 2, help: 'Aporte por ronda comparado con tu propio promedio: 1.00 es tu ronda tipica.' },
              {
                key: 'played_at',
                label: 'Cuando',
                render: (row) => row.played_at.slice(5, 16).replace('T', ' '),
                dim: true,
              },
            ]}
            rows={form}
            initialSort={{ key: 'played_at', dir: 'desc' }}
            rowKey={(row) => row.id}
          />
        </Panel>
      </div>

      {series.length > 2 ? (
        <Panel title="Evolucion por partida" hint="Rondas ganadas y kills por ronda, en orden cronologico.">
          <Suspense fallback={<Loading>Cargando grafico...</Loading>}>
            <EvolucionChart series={series} />
          </Suspense>
        </Panel>
      ) : null}

      {topInsights.length ? (
        <Panel title="Lo que hay que corregir" right={<Link className="btn small" to="/coach">Ver todo el analisis</Link>}>
          {topInsights.map((insight) => (
            <div key={insight.key} className={`insight ${insight.severity}`}>
              <h3>{insight.title}</h3>
              <p>{insight.detail}</p>
              <div className="action">{insight.action}</div>
            </div>
          ))}
        </Panel>
      ) : null}

      {health ? (
        <Panel title="Que tan completa esta la data" hint="Lo que el formato .rec entrega y lo que hay que inferir.">
          <ul className="note" style={{ margin: 0, paddingLeft: 18 }}>
            <li>{health.rounds} rondas tuyas importadas de {health.matches} partidas.</li>
            <li>
              {health.rounds_uncertain_win_condition} rondas donde la condicion de victoria se
              infiere (el replay ya no expone los eventos del defuser).
            </li>
            <li>{health.rounds_possible_plant} rondas con plant probable segun el reloj.</li>
            <li>
              Trades calculados con una ventana de <b>{fmt(health.trade_window, 0)}s</b>. Se cambia
              en el <code>.env</code> con <code>TRADE_WINDOW_SECONDS</code>, y despues hay que
              correr <code>manage.py recompute</code>.
            </li>
            {health.rounds_without_site ? <li>{health.rounds_without_site} rondas sin sitio detectado.</li> : null}
            {!health.assists_available ? (
              <li>Asistencias no disponibles en esta version del juego.</li>
            ) : null}
          </ul>
        </Panel>
      ) : null}
    </>
  )
}

/** Tarjeta KPI con color segun el valor normalizado a 0-100. */
function Stat3({ label, value, sub, value_ }) {
  const tone = value_ === null || value_ === undefined ? '' : value_ >= 55 ? 'good' : value_ <= 42 ? 'bad' : ''
  return (
    <div className={`stat ${tone}`}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {sub ? <div className="sub">{sub}</div> : null}
    </div>
  )
}
