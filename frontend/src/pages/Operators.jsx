import React from 'react'

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
  SinRondasFiltradas,
  pct,
} from '../components/ui.jsx'
import { claseSitio, conOrdenDelBackend, etiquetaSitio, textoSinFilas } from '../operadorSitio.js'
import { comoMargen, conSigno } from '../posicion.js'
import { vistaSinRondas } from '../tipoPartida.js'

export default function Operators({ filters, setFilters, runImport, importing }) {
  const { data, error, loading } = useApi('/operators/', { ...filters, min_rounds: 1 })

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  const vista = vistaSinRondas({ vacio: !data?.operators?.length, filtros: filters, cargando: loading })
  if (vista === 'importar') return <EmptyState onImport={runImport} importing={importing} />
  if (vista === 'filtrado') {
    return <SinRondasFiltradas titulo="Operadores" filtros={<Filters value={filters} onChange={setFilters} showOperator={false} />} />
  }

  const rows = data.operators
  const attack = rows.filter((r) => r.side === 'Attack')
  const defense = rows.filter((r) => r.side === 'Defense')

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Operadores</h1>
          <p>
            Tu pool real, ordenado por rondas jugadas. Ordena por cualquier columna. «vs. tu lado»
            compara cada operador con tu winrate en ese lado.
          </p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} showOperator={false} />

      {[
        { title: 'Ataque', rows: attack },
        { title: 'Defensa', rows: defense },
      ].map((group) =>
        group.rows.length ? (
          <Panel key={group.title} title={group.title}>
            <Table rows={group.rows} nombre={`operadores-${group.title.toLowerCase()}`} />
          </Panel>
        ) : null,
      )}

      {!attack.length && !defense.length ? (
        <Panel title="Todos">
          <Table rows={rows} nombre="operadores" />
        </Panel>
      ) : null}

      <PorSitio filters={filters} />
    </>
  )
}

function Table({ rows, nombre }) {
  return (
    <DataTable
      columns={[
        { key: 'operator', label: 'Operador' },
        { key: 'side', label: 'Lado', render: (row) => <SideChip side={row.side} /> },
        { key: 'rounds', label: 'Rondas' },
        {
          key: 'presence_pct',
          label: 'Presencia',
          digits: 0,
          suffix: '%',
          help: 'Rondas con este operador / todas tus rondas de ese lado, con los filtros activos.',
        },
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
          key: 'winrate_delta',
          label: 'vs. tu lado',
          help: 'Winrate con este operador menos tu winrate de todas las rondas de ese lado, en puntos. Un +10 con poca presencia puede ser varianza.',
          render: (row) => <DeltaLado valor={row.winrate_delta} />,
        },
        { key: 'rating', label: 'Rating', digits: 2, help: 'Aporte por ronda comparado con tu propio promedio: 1.00 es tu ronda típica. Ver docs/metricas.md para la fórmula y los pesos.' },
        { key: 'kills', label: 'Bajas' },
        { key: 'kpr', label: 'KPR', digits: 2 },
        { key: 'kd', label: 'K/D', digits: 2 },
        { key: 'hs_pct', label: 'HS%', digits: 0, suffix: '%' },
        { key: 'opening_winrate', label: 'Aperturas', digits: 0, suffix: '%' },
        { key: 'survival_pct', label: 'Sobrevives', digits: 0, suffix: '%' },
        { key: 'kst_pct', label: 'KST', digits: 0, suffix: '%' },
      ]}
      rows={rows}
      initialSort={{ key: 'rounds', dir: 'desc' }}
      rowKey={(row) => `${row.operator}-${row.side}`}
      csvName={nombre}
    />
  )
}

// Request aparte: un error o una tabla vacia aca no tumba la pagina, y la
// vista vacia la sigue decidiendo `/operators/`.
function PorSitio({ filters }) {
  const { data, error, loading } = useApi('/operators/sites/', filters)
  let cuerpo
  if (error) cuerpo = <ErrorBox error={error} />
  else if (loading && !data) cuerpo = <Loading />
  else if (!data?.rows?.length) cuerpo = <p className="note">{textoSinFilas(data)}</p>
  else cuerpo = <TablaPorSitio rows={data.rows} />
  return (
    <Panel
      title="Por sitio"
      hint="Winrate con el operador en ese sitio contra el resto de tus operadores ahí (mismo mapa, sitio y lado)."
    >
      {cuerpo}
    </Panel>
  )
}

function TablaPorSitio({ rows }) {
  return (
    <DataTable
      columns={[
        { key: 'map', label: 'Mapa', left: true },
        { key: 'site', label: 'Sitio', left: true },
        { key: 'side', label: 'Lado', render: (row) => <SideChip side={row.side} /> },
        { key: 'operator', label: 'Operador', left: true },
        { key: 'rounds', label: 'Rondas' },
        { key: 'winrate', label: 'Ganadas', render: (row) => pct(row.winrate) },
        {
          key: 'rest_winrate',
          label: 'Resto',
          help: 'Winrate con tus otros operadores en el mismo mapa, sitio y lado. Pasa el cursor por la celda para ver cuántas rondas son.',
          render: (row) => <span title={`${row.rest_rounds} rondas`}>{pct(row.rest_winrate)}</span>,
        },
        { key: 'winrate_delta', label: 'Diferencia', render: (row) => conSigno(row.winrate_delta) },
        {
          key: 'margin',
          label: 'Margen',
          dim: true,
          help: 'Dos errores estándar de la diferencia. Con muchas filas, una diferencia menor que esto sale sola por azar.',
          render: (row) => comoMargen(row.margin),
        },
        {
          key: 'verdict',
          label: 'Veredicto',
          sortable: false,
          csv: (row) => etiquetaSitio(row.verdict),
          render: (row) => <span className={`chip ${claseSitio(row.verdict)}`.trim()}>{etiquetaSitio(row.verdict)}</span>,
        },
      ]}
      rows={conOrdenDelBackend(rows)}
      initialSort={{ key: 'orden', dir: 'asc' }}
      rowKey={(row) => `${row.slug}-${row.map_id}-${row.site}-${row.side}-${row.operator}`}
      csvName="operadores-por-sitio"
    />
  )
}

function DeltaLado({ valor }) {
  if (valor === null || valor === undefined) return <span className="dim">—</span>
  // Redondear antes de elegir signo y color: un -0.4 se ve 0, no -0.
  const puntos = Math.round(valor) || 0
  const clase = puntos > 0 ? 'chip win' : puntos < 0 ? 'chip loss' : 'chip'
  return (
    <span className={clase}>
      {puntos > 0 ? '+' : ''}
      {puntos}
    </span>
  )
}
