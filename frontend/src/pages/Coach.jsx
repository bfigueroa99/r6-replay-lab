import React from 'react'

import { useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import { DataTable, EmptyState, ErrorBox, Loading, Panel, SinRondasFiltradas } from '../components/ui.jsx'
import {
  claseSalida,
  claseVeredicto,
  comoMargen,
  conSigno,
  etiquetaSalida,
  etiquetaVeredicto,
  hayZonas,
  notaDeMuestra,
  textoSinSalidas,
} from '../posicion.js'
import { vistaSinRondas } from '../tipoPartida.js'

const GROUPS = [
  { key: 'alta', title: 'Prioridad alta', hint: 'Lo que más te está costando rondas.' },
  { key: 'media', title: 'Para trabajar', hint: 'Patrones claros con muestra suficiente.' },
  { key: 'baja', title: 'Para tener en el radar', hint: 'Señales más débiles o de contexto.' },
  { key: 'positivo', title: 'Tus fortalezas', hint: 'Apóyate en esto al elegir rol y picks.' },
]

export default function Coach({ filters, setFilters, runImport, importing }) {
  const { data, error, loading } = useApi('/coach/', filters)
  const posicion = useApi('/positioning/', filters)

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  const vista = vistaSinRondas({ vacio: !data?.totals?.rounds, filtros: filters, cargando: loading })
  if (vista === 'importar') return <EmptyState onImport={runImport} importing={importing} />
  if (vista === 'filtrado') {
    return <SinRondasFiltradas titulo="Coach" filtros={<Filters value={filters} onChange={setFilters} />} />
  }

  const insights = data.insights || []

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Coach</h1>
          <p>
            Reglas sobre {data.totals.rounds} rondas. Cada punto trae el número, con qué se compara
            y cuántas rondas lo respaldan.
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
                  <b>Qué hacer:</b> {insight.action}
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
      <PanelSalidaSpawn {...posicion} />

      <p className="note">
        Las reglas exigen una muestra mínima antes de opinar (20 rondas en general, 8-15 por
        mapa/sitio/operador, {posicion.data?.min_rounds ?? 5} por zona en la tabla de posición),
        así que si algo no aparece es porque todavía no hay datos para afirmarlo.
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
                rowKey={(row) => `${row.map}-${row.map_id}-${row.site}`}
                initialSort={ORDEN_ZONAS}
                csvName="fuera-de-posicion-sitios"
                empty="Ningún sitio con muestra suficiente."
              />
              <h3>Spawns de ataque</h3>
              <DataTable
                columns={columnasDeZona('spawn', 'Spawn')}
                rows={data.spawns}
                rowKey={(row) => `${row.map}-${row.map_id}-${row.spawn}`}
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

const columnasDeSalida = (segundos) => [
  { key: 'map', label: 'Mapa', left: true },
  { key: 'spawn', label: 'Spawn', left: true },
  { key: 'rounds', label: 'Rondas' },
  {
    key: 'early_deaths',
    label: 'Mueres temprano',
    help: `Rondas de ataque con este spawn en que moriste antes de los ${segundos} s de acción.`,
  },
  pctCol('early_death_pct', '%', 'Mueres temprano sobre las rondas de ataque con este spawn.'),
  pctCol('rest_early_death_pct', 'Resto', 'El mismo porcentaje en el resto de tu ataque.'),
  { key: 'early_death_delta', label: 'Diferencia', render: (row) => conSigno(row.early_death_delta) },
  {
    key: 'margin',
    label: 'Margen',
    dim: true,
    help: 'Dos errores estándar de la diferencia. Con muchos spawns, una diferencia menor que esto sale sola por azar.',
    render: (row) => comoMargen(row.margin),
  },
  {
    key: 'early_kills',
    label: 'Bajas tempranas',
    help: `Tus bajas a rivales antes de los ${segundos} s de acción en esas rondas. Los teamkills no cuentan.`,
  },
  {
    key: 'verdict',
    label: 'Veredicto',
    sortable: false,
    csv: (row) => etiquetaSalida(row.verdict),
    render: (row) => <span className={`chip ${claseSalida(row.verdict)}`.trim()}>{etiquetaSalida(row.verdict)}</span>,
  },
]

function PanelSalidaSpawn({ data, error, loading }) {
  const segundos = data?.spawn_exit_seconds ?? 15
  const ataque = data?.spawn_exit_attack
  return (
    <Panel
      title="Salida del spawn"
      hint={`Rondas de ataque en que moriste en los primeros ${segundos} s de acción, por spawn, contra el resto de tu ataque.`}
    >
      {error ? (
        <ErrorBox error={error} />
      ) : loading && !data ? (
        <Loading />
      ) : !data?.spawn_exits?.length ? (
        <p className="note">{textoSinSalidas(data)}</p>
      ) : (
        <>
          <p className="note salida-ataque">
            En todo tu ataque mueres antes de los {segundos} s en el {ataque.early_death_pct ?? 0}% de las
            rondas ({ataque.early_deaths} de {ataque.rounds}). {notaDeMuestra(data)}
          </p>
          <DataTable
            columns={columnasDeSalida(segundos)}
            rows={data.spawn_exits}
            rowKey={(row) => `${row.map}-${row.map_id}-${row.spawn}`}
            initialSort={{ key: 'early_death_pct', dir: 'desc' }}
            csvName="salida-del-spawn"
            empty={textoSinSalidas(data)}
          />
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
