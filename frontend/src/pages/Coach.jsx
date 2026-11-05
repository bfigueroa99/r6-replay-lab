import React from 'react'

import { useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import { DataTable, EmptyState, ErrorBox, Loading, Panel } from '../components/ui.jsx'
import {
  claseVeredicto,
  comoMargen,
  conSigno,
  etiquetaVeredicto,
  hayZonas,
  notaDeMuestra,
} from '../posicion.js'

const GROUPS = [
  { key: 'alta', title: 'Prioridad alta', hint: 'Lo que mas te esta costando rondas.' },
  { key: 'media', title: 'Para trabajar', hint: 'Patrones claros con muestra suficiente.' },
  { key: 'baja', title: 'Para tener en el radar', hint: 'Señales mas debiles o de contexto.' },
  { key: 'positivo', title: 'Tus fortalezas', hint: 'Apoyate en esto al elegir rol y picks.' },
]

export default function Coach({ filters, setFilters, runImport, importing }) {
  const { data, error, loading } = useApi('/coach/', filters)
  const posicion = useApi('/positioning/', filters)

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  if (!data?.totals?.rounds) return <EmptyState onImport={runImport} importing={importing} />

  const insights = data.insights || []

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Coach</h1>
          <p>
            Reglas sobre {data.totals.rounds} rondas. Cada punto trae el numero, con que se compara
            y cuantas rondas lo respaldan.
          </p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} />

      {GROUPS.map((group) => {
        const rows = insights.filter((i) => i.severity === group.key)
        if (!rows.length) return null
        return (
          <Panel key={group.key} title={group.title} hint={group.hint}>
            {rows.map((insight) => (
              <div key={insight.key} className={`insight ${insight.severity}`}>
                <h3>{insight.title}</h3>
                <p>{insight.detail}</p>
                <div className="action">
                  <b>Que hacer:</b> {insight.action}
                </div>
                <div className="meta">
                  {insight.metric ? (
                    <span>
                      {insight.metric}: <b>{format(insight.value)}</b>
                      {insight.baseline !== null && insight.baseline !== undefined
                        ? ` (referencia ${format(insight.baseline)})`
                        : ''}
                    </span>
                  ) : null}
                  {insight.sample ? <span>muestra: {insight.sample} rondas</span> : null}
                  {insight.scope && insight.scope !== 'general' ? <span>alcance: {insight.scope}</span> : null}
                </div>
              </div>
            ))}
          </Panel>
        )
      })}

      <PanelPosicion {...posicion} />

      <p className="note">
        Las reglas exigen una muestra minima antes de opinar (20 rondas en general, 8-15 por
        mapa/sitio/operador, 5 por zona en la tabla de posición), asi que si algo no aparece es porque todavia no hay datos para
        afirmarlo.
      </p>
    </>
  )
}

const pctCol = (key, label, help) => ({ key, label, help, digits: 0, suffix: '%' })

const columnasDeZona = (clave, etiqueta) => [
  { key: 'map', label: 'Mapa', left: true },
  { key: clave, label: etiqueta, left: true },
  { key: 'rounds', label: 'Rondas' },
  pctCol('caught_out_pct', 'Fuera de posición', 'Rondas en que moriste sin bajas y sin que nadie te vengara.'),
  pctCol(
    'rest_caught_out_pct',
    'Resto',
    'El mismo porcentaje en el resto de tus rondas; para un spawn, el resto de tu ataque.',
  ),
  { key: 'caught_out_delta', label: 'Diferencia', render: (row) => conSigno(row.caught_out_delta) },
  {
    key: 'margin',
    label: 'Margen',
    dim: true,
    help: 'Dos errores estándar de la diferencia. Con muchas zonas, una diferencia menor que esto sale sola por azar.',
    render: (row) => comoMargen(row.margin),
  },
  {
    key: 'verdict',
    label: 'Veredicto',
    sortable: false,
    csv: (row) => etiquetaVeredicto(row.verdict),
    render: (row) => <span className={`chip ${claseVeredicto(row.verdict)}`.trim()}>{etiquetaVeredicto(row.verdict)}</span>,
  },
]

const ORDEN_ZONAS = { key: 'caught_out_delta', dir: 'desc' }

function PanelPosicion({ data, error, loading }) {
  return (
    <Panel
      title="Dónde quedas fuera de posición"
      hint="Rondas en que moriste sin bajas y sin que nadie te vengara, por zona, contra el resto de tu historial."
    >
      {error ? (
        <ErrorBox error={error} />
      ) : loading && !data ? (
        <Loading />
      ) : (
        <>
          <p className="note">
            El .rec no trae coordenadas: la zona es el sitio de bomba o el spawn de ataque.{' '}
            {notaDeMuestra(data)} Usa el filtro Lado para ver solo tu defensa o tu ataque.
          </p>
          {!hayZonas(data) ? (
            <p className="note">Todavía no hay zonas con {data?.min_rounds ?? 5} rondas.</p>
          ) : (
            <>
              <h3>Sitios</h3>
              <DataTable
                columns={columnasDeZona('site', 'Sitio')}
                rows={data.sites}
                rowKey={(row) => `${row.slug}-${row.map_id}-${row.site}`}
                initialSort={ORDEN_ZONAS}
                csvName="fuera-de-posicion-sitios"
                empty="Ningún sitio con muestra suficiente."
              />
              <h3>Spawns de ataque</h3>
              <DataTable
                columns={columnasDeZona('spawn', 'Spawn')}
                rows={data.spawns}
                rowKey={(row) => `${row.slug}-${row.map_id}-${row.spawn}`}
                initialSort={ORDEN_ZONAS}
                csvName="fuera-de-posicion-spawns"
                empty="Ningún spawn de ataque con muestra suficiente."
              />
            </>
          )}
        </>
      )}
    </Panel>
  )
}

const format = (value) =>
  value === null || value === undefined
    ? '—'
    : typeof value === 'number'
      ? Number(value).toFixed(Math.abs(value) < 10 && !Number.isInteger(value) ? 2 : 0)
      : value
