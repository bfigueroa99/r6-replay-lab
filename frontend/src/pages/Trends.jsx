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
import { MUESTRA_CORTE, filasConPocaMuestra } from '../muestra.js'
import { filasDeCierre, hayCierres } from '../cierres.js'

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

const MITADES = { first: 'Primera mitad', second: 'Segunda mitad', overtime: 'Prórroga' }
const LADOS = { Attack: 'Ataque', Defense: 'Defensa' }
const RONDA_ANTERIOR = {
  after_win: 'Después de ganar',
  after_loss: 'Después de perder',
  no_previous: 'Sin ronda anterior',
}
const MARCADOR = { ahead: 'Adelante', tied: 'Empatado', behind: 'Atrás', unknown: 'Sin marcador' }
// las etiquetas se arman una vez: la clave del backend es la hora de inicio de la franja
const FRANJAS = Object.fromEntries([0, 3, 6, 9, 12, 15, 18, 21].map((h) => [h, `${h}–${h + 3} h`]))
const DIAS = Object.fromEntries(
  ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'].map((dia, i) => [i + 1, dia]),
)

const SIN_ELIMINACION =
  'Objetivo o tiempo: el .rec de temporadas nuevas no separa plant, defuse ni tiempo agotado; se infiere del reloj.'

/** Porcentaje con el conteo de rondas al lado, para que un 100 % de 2 rondas se vea como tal. */
function columnaCierre(key, label, conteo, help) {
  return {
    key,
    label,
    sortable: false,
    help,
    render: (row) =>
      row[key] === null || row[key] === undefined ? '—' : `${fmt(row[key], 0, '%')} (${row[conteo]})`,
    csv: (row) => (row[key] === null || row[key] === undefined ? '' : String(row[key]).replace('.', ',')),
  }
}

/** Tabla de un corte de Tendencias: una fila por tramo, en el orden del backend. */
function TablaDeCorte({ filas, columna, etiquetas, rowKey, csvName }) {
  const rows = (filas || []).map((row, orden) => ({
    ...row,
    orden,
    tramo: etiquetas[row[rowKey]] || row[rowKey],
  }))
  return (
    <DataTable
      columns={[
        { key: 'tramo', label: columna, sortable: false, left: true },
        { key: 'rounds', label: 'Rondas', sortable: false },
        { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%', sortable: false },
        { key: 'rating', label: 'Rating', digits: 2, sortable: false, help: 'Aporte por ronda comparado con tu propio promedio: 1.00 es tu ronda tipica.' },
        { key: 'kpr', label: 'KPR', digits: 2, sortable: false },
        { key: 'opening_winrate', label: 'Aperturas', digits: 0, suffix: '%', sortable: false },
      ]}
      rows={rows}
      initialSort={{ key: 'orden', dir: 'asc' }}
      rowKey={(row) => row[rowKey]}
      csvName={csvName}
    />
  )
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
  const porMitad = (data.by_half ?? []).map((row, orden) => ({
    ...row,
    orden,
    tramo: MITADES[row.half] || row.half,
  }))
  const porLadoInicial = (data.by_start_side ?? []).map((row, orden) => ({
    ...row,
    orden,
    lado: LADOS[row.side] || row.side,
  }))
  const porAnterior = data.by_previous_round ?? []
  // sin marcador es ruido de replays viejos: solo se muestra si tiene rondas
  const porMarcador = (data.by_score_state ?? []).filter(
    (row) => row.score_state !== 'unknown' || row.rounds > 0,
  )
  const cierres = filasDeCierre(data.round_endings)
  const porHora = data.by_hour ?? []
  const porDia = data.by_weekday ?? []
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

      {porMitad.length ? (
        <Panel
          title="Por mitad de la partida"
          hint={
            'Primera mitad: las rondas en el lado con que arrancaste. ' +
            'Si la segunda o la prórroga caen, el problema es cerrar, no empezar.'
          }
        >
          <DataTable
            columns={[
              { key: 'tramo', label: 'Tramo', sortable: false, left: true },
              { key: 'rounds', label: 'Rondas', sortable: false },
              { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%', sortable: false },
              { key: 'rating', label: 'Rating', digits: 2, sortable: false, help: 'Aporte por ronda comparado con tu propio promedio: 1.00 es tu ronda tipica.' },
              { key: 'kpr', label: 'KPR', digits: 2, sortable: false },
              { key: 'opening_winrate', label: 'Aperturas', digits: 0, suffix: '%', sortable: false },
            ]}
            rows={porMitad}
            initialSort={{ key: 'orden', dir: 'asc' }}
            rowKey={(row) => row.half}
            csvName="por-mitad"
          />
          <h3 style={{ margin: '16px 0 8px' }}>Según el lado con que arrancas</h3>
          <DataTable
            columns={[
              { key: 'lado', label: 'Lado', sortable: false, left: true },
              { key: 'matches', label: 'Partidas', sortable: false },
              { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%', sortable: false, help: 'Partidas ganadas sobre las que tienen resultado.' },
            ]}
            rows={porLadoInicial}
            initialSort={{ key: 'orden', dir: 'asc' }}
            rowKey={(row) => row.side}
            csvName="por-lado-inicial"
          />
        </Panel>
      ) : null}

      {porAnterior.length ? (
        <Panel
          title="Después de ganar o perder la ronda anterior"
          hint={
            filasConPocaMuestra(porAnterior).length
              ? `Ojo: alguna fila tiene menos de ${MUESTRA_CORTE} rondas; la diferencia puede ser varianza.`
              : 'Si después de perder tu winrate o tu rating caen más que tu promedio, la ronda perdida te sigue pesando.'
          }
        >
          <TablaDeCorte
            filas={porAnterior}
            columna="Ronda anterior"
            etiquetas={RONDA_ANTERIOR}
            rowKey="previous"
            csvName="ronda-anterior"
          />
        </Panel>
      ) : null}

      {porMarcador.length ? (
        <Panel
          title="Según el marcador"
          hint={
            filasConPocaMuestra(porMarcador).length
              ? `Ojo: alguna fila tiene menos de ${MUESTRA_CORTE} rondas; la diferencia puede ser varianza.`
              : 'Cómo rindes según cómo iba la partida antes de la ronda.'
          }
        >
          <TablaDeCorte
            filas={porMarcador}
            columna="Marcador"
            etiquetas={MARCADOR}
            rowKey="score_state"
            csvName="segun-marcador"
          />
        </Panel>
      ) : null}

      {hayCierres(cierres) ? (
        <Panel
          title="Cómo se cierran tus rondas"
          hint={
            filasConPocaMuestra(cierres).length
              ? `Ojo: alguna fila tiene menos de ${MUESTRA_CORTE} rondas; la diferencia puede ser varianza.`
              : 'Si en defensa pierdes casi todo por eliminación, el problema son los duelos; si pierdes sin eliminación, es el tiempo o el objetivo.'
          }
        >
          <DataTable
            columns={[
              { key: 'lado', label: 'Lado', sortable: false, left: true },
              { key: 'rounds', label: 'Rondas', sortable: false },
              columnaCierre('won_elimination_pct', 'Ganadas por eliminación', 'won_elimination',
                'De tus ganadas con dato, cuántas terminaron con el otro equipo eliminado. Entre paréntesis, las rondas.'),
              columnaCierre('won_other_pct', 'Ganadas sin eliminación', 'won_other', SIN_ELIMINACION),
              columnaCierre('lost_elimination_pct', 'Perdidas por eliminación', 'lost_elimination',
                'De tus perdidas con dato, cuántas terminaron con tu equipo eliminado. Entre paréntesis, las rondas.'),
              columnaCierre('lost_other_pct', 'Perdidas sin eliminación', 'lost_other', SIN_ELIMINACION),
              { key: 'unknown', label: 'Sin dato', sortable: false, help: 'Rondas sin ganador o sin condición de cierre.' },
            ]}
            rows={cierres}
            initialSort={{ key: 'orden', dir: 'asc' }}
            rowKey={(row) => row.side}
            csvName="como-se-cierran"
          />
        </Panel>
      ) : null}

      {porHora.length ? (
        <Panel
          title="Por hora del día"
          hint={
            filasConPocaMuestra(porHora).length
              ? `Ojo: alguna fila tiene menos de ${MUESTRA_CORTE} rondas; la diferencia puede ser varianza.`
              : 'Hora de inicio de la partida, tal como la guardó tu PC.'
          }
        >
          <TablaDeCorte
            filas={porHora}
            columna="Hora"
            etiquetas={FRANJAS}
            rowKey="hour_from"
            csvName="por-hora"
          />
        </Panel>
      ) : null}

      {porDia.length ? (
        <Panel
          title="Por día de la semana"
          hint={
            filasConPocaMuestra(porDia).length
              ? `Ojo: alguna fila tiene menos de ${MUESTRA_CORTE} rondas; la diferencia puede ser varianza.`
              : 'Día en que empezó la partida.'
          }
        >
          <TablaDeCorte
            filas={porDia}
            columna="Día"
            etiquetas={DIAS}
            rowKey="weekday"
            csvName="por-dia"
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
