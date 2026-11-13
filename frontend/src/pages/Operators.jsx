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
import { claseFilaOperador, sinOperador, textoOperadorElegido } from '../operadorElegido.js'
import { claseSitio, conOrdenDelBackend, etiquetaSitio, textoSinFilas } from '../operadorSitio.js'
import {
  filasCambioTrasPerder,
  filasTrasResultado,
  textoWinrate,
  winrateCsv,
} from '../operadorTrasResultado.js'
import { bloquesDelPool, fechaCorta, textoHintPool, textoRondas } from '../poolOperadores.js'
import { comoMargen, conSigno } from '../posicion.js'
import { vistaSinRondas } from '../tipoPartida.js'

export default function Operators({ filters, setFilters, runImport, importing }) {
  // Sin `operator`: con el filtro puesto Ataque y Defensa quedarian con una sola fila;
  // la elegida se resalta. La vista sin rondas si mira los filtros enteros.
  const { data, error, loading } = useApi('/operators/', { ...sinOperador(filters), min_rounds: 1 })

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  const vista = vistaSinRondas({ vacio: !data?.operators?.length, filtros: filters, cargando: loading })
  if (vista === 'importar') return <EmptyState onImport={runImport} importing={importing} />
  if (vista === 'filtrado') {
    return <SinRondasFiltradas titulo="Operadores" filtros={<Filters value={filters} onChange={setFilters} />} />
  }

  const rows = data.operators
  const attack = rows.filter((r) => r.side === 'Attack')
  const defense = rows.filter((r) => r.side === 'Defense')
  const operador = filters.operator
  const notaOperador = textoOperadorElegido(operador)

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Operadores</h1>
          <p>
            Tu pool real, ordenado por rondas jugadas. Ordena por cualquier columna. «vs. tu lado»
            compara cada operador con tu winrate en ese lado.
          </p>
          {notaOperador ? <p className="note">{notaOperador}</p> : null}
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} />

      {[
        { title: 'Ataque', rows: attack },
        { title: 'Defensa', rows: defense },
      ].map((group) =>
        group.rows.length ? (
          <Panel key={group.title} title={group.title}>
            <Table rows={group.rows} nombre={`operadores-${group.title.toLowerCase()}`} operador={operador} />
          </Panel>
        ) : null,
      )}

      {!attack.length && !defense.length ? (
        <Panel title="Todos">
          <Table rows={rows} nombre="operadores" operador={operador} />
        </Panel>
      ) : null}

      <TuPool filters={filters} />

      <PorSitio filters={filters} />

      <TrasResultado filters={filters} />
    </>
  )
}

function Table({ rows, nombre, operador }) {
  return (
    <DataTable
      columns={[
        {
          key: 'operator',
          label: 'Operador',
          // DataTable no pone atributos por fila: el nombre accesible del resaltado va en la celda
          render: (row) =>
            row.operator === operador ? <strong aria-current="true">{row.operator}</strong> : row.operator,
        },
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
      rowClass={(row) => claseFilaOperador(row, operador)}
      csvName={nombre}
    />
  )
}

// Request aparte, como PorSitio: un error del panel no tumba la pagina.
function TuPool({ filters }) {
  const { data, error, loading } = useApi('/operators/pool/', filters)
  let cuerpo
  if (error) cuerpo = <ErrorBox error={error} />
  else if (loading && !data) cuerpo = <Loading />
  else {
    const bloques = bloquesDelPool(data, filters?.side)
    cuerpo = bloques.length ? (
      bloques.map((b) => (
        <div key={b.lado}>
          <h3>{b.titulo}</h3>
          <p>{b.resumen}</p>
          <p>
            Sin jugar hace más de {data.stale_days} días:{' '}
            {b.stale.length
              ? b.stale.map((s) => `${s.operator} (último: ${fechaCorta(s.last_played)}, ${textoRondas(s.rounds)})`).join(', ')
              : 'ninguno'}
          </p>
          <p>Nunca jugados ({b.never.length}):</p>
          <div>
            {b.never.map((nombre) => (
              <span key={nombre} className="chip">{nombre}</span>
            ))}
          </div>
        </div>
      ))
    ) : (
      <p className="note">Sin partidas con estos filtros.</p>
    )
  }
  return (
    <Panel
      title="Tu pool"
      hint={textoHintPool(data?.stale_days)}
    >
      {cuerpo}
    </Panel>
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

const winrateConMuestra = (caso, label) => ({
  key: `${caso}_winrate`,
  label,
  csv: (row) => winrateCsv(row[`${caso}_winrate`]),
  render: (row) => textoWinrate(row[`${caso}_winrate`], row[`${caso}_poca`]),
})

const COLUMNAS_TRAS_RESULTADO = [
  { key: 'lado', label: 'Lado', left: true },
  { key: 'tras', label: 'Tras', left: true },
  { key: 'repeat_rounds', label: 'Repite', help: 'Rondas en que volviste a jugar el mismo operador.' },
  winrateConMuestra('repeat', 'Winrate repitiendo'),
  { key: 'switch_rounds', label: 'Cambia', help: 'Rondas en que jugaste otro operador.' },
  winrateConMuestra('switch', 'Winrate cambiando'),
]

const COLUMNAS_CAMBIO_TRAS_PERDER = [
  { key: 'lado', label: 'Lado', left: true },
  { key: 'desde', label: 'Perdiste con', left: true },
  { key: 'hacia', label: 'Cambiaste a', left: true },
  { key: 'rondas', label: 'Rondas', help: 'Rondas con el operador nuevo, tras perder con el anterior.' },
  {
    key: 'winrate',
    label: 'Winrate',
    csv: (row) => winrateCsv(row.winrate),
    render: (row) => textoWinrate(row.winrate, row.poca),
  },
]

function TrasResultado({ filters }) {
  const { data, error, loading } = useApi('/operators/after-result/', filters)
  let cuerpo
  if (error) cuerpo = <ErrorBox error={error} />
  else if (loading && !data) cuerpo = <Loading />
  else {
    const filas = filasTrasResultado(data, filters?.side)
    cuerpo = filas.length ? (
      <DataTable
        columns={COLUMNAS_TRAS_RESULTADO}
        rows={filas}
        rowKey={(row) => row.clave}
        initialSort={{ key: 'orden', dir: 'asc' }}
        csvName="operador-tras-resultado"
      />
    ) : (
      <p className="note">Sin rondas seguidas del mismo lado con estos filtros.</p>
    )
  }
  const cambios = data && !error ? filasCambioTrasPerder(data, filters?.side) : null
  return (
    <Panel
      title="Repetir o cambiar tras perder"
      hint={`Tu siguiente ronda del mismo lado en la partida: si repetiste el operador o cambiaste, y cuánto la ganaste. «Tras ganar» es la base para comparar. Con el filtro de operador o de sitio, solo los pares que empiezan en una ronda con ese operador o en ese sitio. Con menos de ${data?.min_rounds ?? 12} rondas se avisa «pocas rondas». Abajo, a qué operador cambiaste y cómo te fue con cada uno; con menos de ${data?.switch_min_rounds ?? 5} rondas por par se avisa «pocas rondas».`}
    >
      {cuerpo}
      {cambios && (
        <>
          <h3>A qué operador cambias tras perder</h3>
          {cambios.length ? (
            <DataTable
              columns={COLUMNAS_CAMBIO_TRAS_PERDER}
              rows={cambios}
              rowKey={(row) => row.clave}
              initialSort={{ key: 'rondas', dir: 'desc' }}
              csvName="operador-cambio-tras-perder"
            />
          ) : (
            <p className="note">No cambiaste de operador tras perder con estos filtros.</p>
          )}
        </>
      )}
    </Panel>
  )
}
