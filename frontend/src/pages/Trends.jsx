import React, { useState } from 'react'
import {
  Bar as RBar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import { DataTable, EmptyState, ErrorBox, Loading, Panel, fmt } from '../components/ui.jsx'

const AXIS = { stroke: '#8b98a9', fontSize: 11 }
const TOOLTIP = {
  contentStyle: { background: '#171e29', border: '1px solid #263041', borderRadius: 8 },
  labelStyle: { color: '#8b98a9' },
}

const VENTANAS = [
  { by: 'matches', n: 5, label: '5 partidas' },
  { by: 'matches', n: 10, label: '10 partidas' },
  { by: 'matches', n: 20, label: '20 partidas' },
  { by: 'days', n: 7, label: '7 dias' },
  { by: 'days', n: 30, label: '30 dias' },
]

/** Flecha con color segun si la metrica mejoro, empeoro o no se movio. */
function Delta({ metric }) {
  if (metric.delta === null || metric.delta === undefined) return <span className="dim">—</span>
  const signo = metric.delta > 0 ? '+' : ''
  const texto = `${signo}${fmt(metric.delta, Math.abs(metric.delta) < 1 ? 2 : 1)}${metric.suffix}`
  if (metric.verdict === 'mejor') return <span className="chip win">{texto}</span>
  if (metric.verdict === 'peor') return <span className="chip loss">{texto}</span>
  return <span className="chip">{texto}</span>
}

export default function Trends({ filters, setFilters, runImport, importing }) {
  const { data, error, loading } = useApi('/trends/', { ...filters, limit: 60 })
  const sesiones = useApi('/sessions/', filters)
  const [ventana, setVentana] = useState(1)
  const rango = VENTANAS[ventana]
  const progreso = useApi('/compare/', { ...filters, by: rango.by, n: rango.n })

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  if (!data?.by_match?.length) return <EmptyState onImport={runImport} importing={importing} />

  const byDay = data.by_day.map((row) => ({ ...row, dia: row.day.slice(5) }))
  const byMatch = data.by_match.map((row, i) => ({
    ...row,
    n: i + 1,
    label: `${row.map} · ${row.played_at.slice(5, 16).replace('T', ' ')}`,
  }))
  const byRound = data.by_round_number.map((row) => ({
    ...row,
    ronda: `R${row.round_number + 1}`,
  }))
  const muertes = data.deaths_by_time || []
  const timing = data.death_timing
  const porPosicion = sesiones.data?.by_position || []
  const horas = Math.round((sesiones.data?.gap_minutes || 120) / 60)

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Tendencias</h1>
          <p>Como se mueven tus numeros en el tiempo y en que momento de la partida te caes.</p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} showSession />

      {progreso.data ? (
        <Panel
          title="Progreso"
          hint={
            'Lo reciente contra lo inmediatamente anterior. La banda de ruido es cuanto se mueve ' +
            'sola una metrica con esta cantidad de rondas: si el cambio no la pasa, no es un ' +
            'cambio. Solo se calcula para porcentajes; en el resto la flecha es solo la direccion.'
          }
          right={
            <label className="note" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              Ventana
              <select value={ventana} onChange={(e) => setVentana(Number(e.target.value))}>
                {VENTANAS.map((v, i) => (
                  <option key={v.label} value={i}>
                    Ultimas {v.label}
                  </option>
                ))}
              </select>
            </label>
          }
        >
          {progreso.data.enough_sample ? null : (
            <div className="flash bad" style={{ marginTop: 0 }}>
              Muestra insuficiente: {progreso.data.current.rounds} rondas contra{' '}
              {progreso.data.previous.rounds}, y hacen falta {progreso.data.min_rounds} de cada
              lado. Los numeros estan abajo, pero no alcanzan para decir que algo cambio.
            </div>
          )}

          <DataTable
            columns={[
              { key: 'label', label: 'Metrica', sortable: false, left: true },
              {
                key: 'previous',
                label: progreso.data.previous.label,
                render: (row) => fmt(row.previous, row.suffix === '' ? 2 : 0, row.suffix),
                csv: (row) => row.previous,
              },
              {
                key: 'current',
                label: progreso.data.current.label,
                render: (row) => fmt(row.current, row.suffix === '' ? 2 : 0, row.suffix),
                csv: (row) => row.current,
              },
              { key: 'delta', label: 'Cambio', render: (row) => <Delta metric={row} /> },
              {
                key: 'noise',
                label: 'Ruido',
                help: 'Error estandar de la diferencia: el tamano tipico de un cambio que no significa nada.',
                render: (row) => (row.noise === null ? <span className="dim">—</span> : `±${fmt(row.noise, 1)}`),
                dim: true,
              },
            ]}
            rows={progreso.data.metrics}
            initialSort={{ key: 'label', dir: 'asc' }}
            rowKey={(row) => row.key}
            csvName="progreso"
          />
        </Panel>
      ) : null}

      <Panel title="Por dia de juego" hint="Cada punto es una sesion. Sirve para ver si mejoras o si solo tuviste un buen dia.">
        <div style={{ height: 260 }}>
          <ResponsiveContainer>
            <LineChart data={byDay} margin={{ top: 6, right: 12, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#263041" strokeDasharray="3 3" />
              <XAxis dataKey="dia" {...AXIS} />
              <YAxis yAxisId="pct" domain={[0, 100]} {...AXIS} />
              <YAxis yAxisId="kpr" orientation="right" domain={[0, 'auto']} {...AXIS} />
              <Tooltip {...TOOLTIP} formatter={(v, n) => [fmt(v, n === 'KPR' ? 2 : 0), n]} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line yAxisId="pct" type="monotone" dataKey="winrate" name="Rondas ganadas %" stroke="#ff8a3d" strokeWidth={2} />
              <Line yAxisId="pct" type="monotone" dataKey="opening_winrate" name="Aperturas %" stroke="#4aa8ff" strokeWidth={2} />
              <Line yAxisId="pct" type="monotone" dataKey="kst_pct" name="KST %" stroke="#3fb950" strokeWidth={2} />
              <Line yAxisId="kpr" type="monotone" dataKey="kpr" name="KPR" stroke="#d29922" strokeWidth={2} strokeDasharray="4 3" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel title="Por partida" hint="Orden cronologico, de la mas vieja a la mas reciente.">
        <div style={{ height: 240 }}>
          <ResponsiveContainer>
            <LineChart data={byMatch} margin={{ top: 6, right: 12, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#263041" strokeDasharray="3 3" />
              <XAxis dataKey="n" {...AXIS} />
              <YAxis yAxisId="pct" domain={[0, 100]} {...AXIS} />
              <YAxis yAxisId="rating" orientation="right" domain={[0, 'auto']} {...AXIS} />
              <Tooltip
                {...TOOLTIP}
                labelFormatter={(n) => byMatch[n - 1]?.label || ''}
                formatter={(v, n) => [fmt(v, n === 'Rating' ? 2 : 0), n]}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line yAxisId="pct" type="monotone" dataKey="winrate" name="Rondas ganadas %" stroke="#ff8a3d" strokeWidth={2} dot={false} />
              <Line yAxisId="pct" type="monotone" dataKey="kst_pct" name="KST %" stroke="#3fb950" strokeWidth={2} dot={false} />
              <Line yAxisId="rating" type="monotone" dataKey="rating" name="Rating" stroke="#d29922" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      {porPosicion.length > 2 ? (
        <Panel
          title="Curva de la sesion"
          hint={`Como rindes segun si fue tu primera partida de la noche o la quinta. Una sesion se corta despues de ${horas} horas sin jugar (SESSION_GAP_MINUTES en el .env).`}
        >
          <div style={{ height: 220 }}>
            <ResponsiveContainer>
              <BarChart data={porPosicion} margin={{ top: 6, right: 12, bottom: 0, left: -18 }}>
                <CartesianGrid stroke="#263041" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" {...AXIS} />
                <YAxis domain={[0, 100]} {...AXIS} />
                <Tooltip
                  {...TOOLTIP}
                  labelFormatter={(l) => `${l} partida de la sesion`}
                  formatter={(v, n) => [fmt(v, 0), n]}
                />
                <RBar dataKey="winrate" name="Rondas ganadas %" fill="#ff8a3d" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <DataTable
            columns={[
              { key: 'label', label: 'Partida', sortable: false },
              { key: 'matches', label: 'Partidas' },
              { key: 'rounds', label: 'Rondas' },
              { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%' },
              { key: 'rating', label: 'Rating', digits: 2, help: 'Aporte por ronda comparado con tu propio promedio: 1.00 es tu ronda tipica.' },
              { key: 'kpr', label: 'KPR', digits: 2 },
              { key: 'kd', label: 'K/D', digits: 2 },
              { key: 'opening_winrate', label: 'Aperturas', digits: 0, suffix: '%' },
              {
                key: 'avg_death_elapsed',
                label: 'Mueres a los',
                render: (row) => (row.avg_death_elapsed ? `${Math.round(row.avg_death_elapsed)}s` : '—'),
              },
            ]}
            rows={porPosicion}
            initialSort={{ key: 'position', dir: 'asc' }}
            rowKey={(row) => row.position}
            csvName="curva-de-sesion"
          />
        </Panel>
      ) : null}

      {sesiones.data?.sessions?.length ? (
        <Panel title="Sesiones" hint="Cada bloque de juego, de la mas reciente hacia atras.">
          <DataTable
            columns={[
              {
                key: 'start',
                label: 'Cuando',
                render: (row) => row.start.slice(5, 16).replace('T', ' '),
              },
              { key: 'matches', label: 'Partidas' },
              { key: 'hours', label: 'Duro', render: (row) => `${row.hours}h` },
              { key: 'rounds', label: 'Rondas' },
              { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%' },
              { key: 'rating', label: 'Rating', digits: 2, help: 'Aporte por ronda comparado con tu propio promedio: 1.00 es tu ronda tipica.' },
              { key: 'kd', label: 'K/D', digits: 2 },
              { key: 'kpr', label: 'KPR', digits: 2 },
              { key: 'kst_pct', label: 'KST', digits: 0, suffix: '%' },
            ]}
            rows={sesiones.data.sessions}
            initialSort={{ key: 'start', dir: 'desc' }}
            rowKey={(row) => row.index}
            csvName="sesiones"
          />
        </Panel>
      ) : null}

      {muertes.length ? (
        <Panel
          title="Cuando mueres"
          hint={
            'El promedio esconde la forma: morir siempre a los 100s no es lo mismo que morir ' +
            'la mitad de las veces a los 20 y la otra mitad a los 170, y las dos cosas se ' +
            'arreglan distinto. Los segundos son de fase de accion, no del reloj de la ronda.'
          }
        >
          <div style={{ height: 240 }}>
            <ResponsiveContainer>
              <BarChart data={muertes} margin={{ top: 6, right: 12, bottom: 0, left: -18 }}>
                <CartesianGrid stroke="#263041" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" {...AXIS} />
                <YAxis {...AXIS} />
                <Tooltip {...TOOLTIP} formatter={(v, n) => [fmt(v, 0), n]} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <RBar dataKey="attack" name="Ataque" stackId="lado" fill="#ff8a3d" radius={[0, 0, 0, 0]} />
                <RBar dataKey="defense" name="Defensa" stackId="lado" fill="#4aa8ff" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {timing ? (
            <div className="kpis" style={{ marginTop: 12 }}>
              {[
                { lado: 'Ataque', fila: timing.attack },
                { lado: 'Defensa', fila: timing.defense },
              ].map(({ lado, fila }) => (
                <React.Fragment key={lado}>
                  <div className="stat">
                    <div className="label">{lado}: sales muy temprano</div>
                    <div className="value">{fmt(fila.first30_pct, 0, '%')}</div>
                    <div className="sub">
                      {fila.first30} de {fila.deaths} muertes en los primeros 30s de accion
                    </div>
                  </div>
                  <div className="stat">
                    <div className="label">{lado}: te quedas sin tiempo</div>
                    <div className="value">{fmt(fila.last30_pct, 0, '%')}</div>
                    <div className="sub">
                      {fila.last30} de {fila.deaths} con menos de 30s de reloj
                    </div>
                  </div>
                </React.Fragment>
              ))}
            </div>
          ) : null}

          <DataTable
            columns={[
              { key: 'label', label: 'Tramo', sortable: false, left: true },
              { key: 'deaths', label: 'Muertes' },
              { key: 'pct', label: 'Del total', digits: 0, suffix: '%' },
              { key: 'attack', label: 'Ataque' },
              { key: 'defense', label: 'Defensa' },
              {
                key: 'untraded_pct',
                label: 'Sin trade',
                digits: 0,
                suffix: '%',
                help: 'De las muertes de ese tramo, cuantas quedaron sin vengar.',
              },
            ]}
            rows={muertes}
            initialSort={{ key: 'start', dir: 'asc' }}
            rowKey={(row) => row.start}
            csvName="cuando-mueres"
          />
        </Panel>
      ) : null}

      <Panel
        title="Por numero de ronda"
        hint="Si el winrate cae en las rondas finales, el problema es de decisiones bajo presion, no de aim."
      >
        <div style={{ height: 220 }}>
          <ResponsiveContainer>
            <BarChart data={byRound} margin={{ top: 6, right: 12, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#263041" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="ronda" {...AXIS} />
              <YAxis domain={[0, 100]} {...AXIS} />
              <Tooltip {...TOOLTIP} formatter={(v, n) => [fmt(v, 0), n]} />
              <RBar dataKey="winrate" name="Rondas ganadas %" fill="#ff8a3d" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <DataTable
          columns={[
            { key: 'ronda', label: 'Ronda', sortable: false },
            { key: 'rounds', label: 'Jugadas' },
            { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%' },
            { key: 'kpr', label: 'KPR', digits: 2 },
            { key: 'opening_winrate', label: 'Aperturas', digits: 0, suffix: '%' },
            { key: 'kst_pct', label: 'KST', digits: 0, suffix: '%' },
          ]}
          rows={byRound}
          initialSort={{ key: 'ronda', dir: 'asc' }}
          rowKey={(row) => row.ronda}
          csvName="por-numero-de-ronda"
        />
      </Panel>
    </>
  )
}
