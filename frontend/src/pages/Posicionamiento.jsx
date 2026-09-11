import React, { useState } from 'react'

import { useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import {
  DataTable,
  EmptyState,
  ErrorBox,
  Loading,
  Panel,
  SideChip,
  Stat,
  VerdictChip,
  fmt,
  pct,
  signed,
} from '../components/ui.jsx'

const MUESTRAS = [
  { value: 3, label: '3+ rondas' },
  { value: 5, label: '5+ rondas' },
  { value: 8, label: '8+ rondas' },
  { value: 12, label: '12+ rondas' },
]

const AYUDA_FUERA =
  'Rondas donde moriste, sin bajas y sin que nadie te vengara, sobre el total de rondas de esa ' +
  'zona. Ver docs/metricas.md.'

/** El mejor y el peor sitio de los que pasaron la banda de ruido. */
export function destacados(sites) {
  const dormideros = sites.filter((s) => s.verdict === 'dormidero')
  const solidos = sites.filter((s) => s.verdict === 'solido')
  return {
    peor: dormideros.length
      ? dormideros.reduce((a, b) => (a.caught_out_delta >= b.caught_out_delta ? a : b))
      : null,
    mejor: solidos.length
      ? solidos.reduce((a, b) => (a.caught_out_delta <= b.caught_out_delta ? a : b))
      : null,
  }
}

function Destacado({ zona, tone, label, vacio }) {
  if (!zona) return <Stat label={label} value="—" sub={vacio} />
  return (
    <Stat
      label={label}
      tone={tone}
      value={pct(zona.caught_out_pct)}
      sub={`${zona.site} · ${zona.map} · ${zona.rounds} rondas · ${signed(
        zona.caught_out_delta,
      )} pts vs el resto`}
    />
  )
}

export default function Posicionamiento({ filters, setFilters, runImport, importing }) {
  const [minRounds, setMinRounds] = useState(5)
  const { data, error, loading } = useApi('/positioning/', { ...filters, min_rounds: minRounds })

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />

  const overall = data?.overall
  if (!overall?.rounds) return <EmptyState onImport={runImport} importing={importing} />

  const sites = data.sites || []
  const spawns = data.spawns || []
  const sides = data.sides || []
  const { peor, mejor } = destacados(sites)

  const selector = (
    <label className="note" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      Muestra mínima
      <select value={minRounds} onChange={(e) => setMinRounds(Number(e.target.value))}>
        {MUESTRAS.map((m) => (
          <option key={m.value} value={m.value}>
            {m.label}
          </option>
        ))}
      </select>
    </label>
  )

  // Las columnas de "te agarran" y las de "te sostienes" van juntas a proposito:
  // la zona util es la que ademas de no matarte te deja aportar, y separarlas en
  // dos tablas obligaria a cruzarlas a mano.
  const columnasZona = (idKey, idLabel) => [
    { key: 'map', label: 'Mapa', left: true },
    { key: idKey, label: idLabel, left: true },
    { key: 'rounds', label: 'Rondas' },
    {
      key: 'caught_out_pct',
      label: 'Fuera de posición',
      digits: 0,
      suffix: '%',
      help: AYUDA_FUERA,
    },
    {
      key: 'caught_out_delta',
      label: 'vs el resto',
      render: (row) => signed(row.caught_out_delta, 0, ' pts'),
      help: 'Diferencia contra el resto de tu historial, sin contar esta zona.',
    },
    {
      key: 'noise',
      label: 'Banda',
      render: (row) => (row.noise === null ? '—' : `±${fmt(row.noise, 0)}`),
      help: 'Cuánto se mueve solo un porcentaje con esta muestra. Si la diferencia no la pasa, no significa nada.',
    },
    {
      key: 'verdict',
      label: 'Veredicto',
      render: (row) => <VerdictChip verdict={row.verdict} />,
      csv: (row) => row.verdict,
    },
    { key: 'survival_pct', label: 'Sobrevives', digits: 0, suffix: '%' },
    {
      key: 'rating',
      label: 'Rating',
      digits: 2,
      help: 'Aporte por ronda comparado con tu propio promedio: 1.00 es tu ronda típica.',
    },
    { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%' },
  ]

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Posicionamiento</h1>
          <p>Dónde te agarran fuera de posición y dónde te sostienes.</p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} showOperator={false} />

      <Panel
        title="Lo que se puede y lo que no"
        hint="El .rec no trae coordenadas de los jugadores ni de las bajas, así que acá no hay posiciones dentro del sitio, ni ángulos, ni habitaciones, ni un heatmap sobre el minimapa. La granularidad que sí entrega el replay es la zona: sitio de bomba y spawn de ataque. Todo lo de abajo está a ese nivel."
      >
        <div className="kpis">
          <Stat
            label="Rondas fuera de posición"
            value={pct(overall.caught_out_pct)}
            sub={`${overall.caught_out_rounds} de ${overall.rounds} rondas`}
            help={AYUDA_FUERA}
          />
          {sides.map((lado) => (
            <Stat
              key={lado.side}
              label={lado.side === 'Attack' ? 'En ataque' : 'En defensa'}
              value={pct(lado.caught_out_pct)}
              sub={`${lado.rounds} rondas · sobrevives ${pct(lado.survival_pct)}`}
            />
          ))}
          <Destacado
            label="Peor zona"
            tone="bad"
            zona={peor}
            vacio="Ninguna zona pasa la banda de ruido todavía."
          />
          <Destacado
            label="Mejor zona"
            tone="good"
            zona={mejor}
            vacio="Ninguna zona pasa la banda de ruido todavía."
          />
        </div>
      </Panel>

      <Panel
        title="Por sitio de bomba"
        hint="Cada sitio comparado contra el resto de tu historial, no contra el total: la zona está dentro del total, así que incluirla sería compararla en parte consigo misma. El veredicto solo habla cuando la diferencia pasa la banda de ruido. Para mirar un lado en particular usa el filtro de arriba."
        right={selector}
      >
        <DataTable
          columns={columnasZona('site', 'Sitio')}
          rows={sites}
          initialSort={{ key: 'caught_out_pct', dir: 'desc' }}
          rowKey={(row) => `${row.map}-${row.site}`}
          csvName="posicion-sitios"
          empty={`Ninguna zona llega a ${minRounds} rondas con los filtros actuales.`}
        />
      </Panel>

      <Panel
        title="Por spawn de ataque"
        hint="Desde dónde entras. Un spawn que te deja fuera de posición seguido suele ser una ruta de entrada que la defensa ya tiene resuelta."
      >
        <DataTable
          columns={columnasZona('spawn', 'Spawn')}
          rows={spawns}
          initialSort={{ key: 'caught_out_pct', dir: 'desc' }}
          rowKey={(row) => `${row.map}-${row.spawn}`}
          csvName="posicion-spawns"
          empty={`Ningún spawn llega a ${minRounds} rondas con los filtros actuales.`}
        />
      </Panel>

      <Panel title="Por lado" hint="La referencia con la que se leen las dos tablas de arriba.">
        <DataTable
          columns={[
            {
              key: 'side',
              label: 'Lado',
              left: true,
              render: (row) => <SideChip side={row.side} />,
              csv: (row) => (row.side === 'Attack' ? 'Ataque' : 'Defensa'),
            },
            { key: 'rounds', label: 'Rondas' },
            {
              key: 'caught_out_pct',
              label: 'Fuera de posición',
              digits: 0,
              suffix: '%',
              help: AYUDA_FUERA,
            },
            { key: 'survival_pct', label: 'Sobrevives', digits: 0, suffix: '%' },
            {
              key: 'avg_death_elapsed',
              label: 'Mueres a los',
              render: (row) => (row.avg_death_elapsed === null ? '—' : `${fmt(row.avg_death_elapsed, 0)}s`),
            },
            { key: 'rating', label: 'Rating', digits: 2 },
            { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%' },
          ]}
          rows={sides}
          initialSort={{ key: 'rounds', dir: 'desc' }}
          rowKey={(row) => row.side}
          csvName="posicion-lados"
        />
      </Panel>
    </>
  )
}
