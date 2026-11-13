import React, { useState } from 'react'
import { Link } from 'react-router-dom'

import { useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import { enlaceDeSenal, textoDelEnlace } from '../enlaceSenal.js'
import { DataTable, EmptyState, ErrorBox, Loading, Panel, SinRondasFiltradas, Stat } from '../components/ui.jsx'
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
import { GRUPOS_COACH, formatoCoach, textoCoach } from '../textoCoach.js'
import { casosRepetirSitio, filasPorMapa, hayPares, textoPares, textoWinrate } from '../repetirSitio.js'
import { filasRepetirSpawn, hayParesSpawn, textoParesSpawn } from '../repetirSpawn.js'
import { vistaSinRondas } from '../tipoPartida.js'

export default function Coach({ filters, setFilters, runImport, importing }) {
  const { data, error, loading } = useApi('/coach/', filters)
  const posicion = useApi('/positioning/', filters)
  // antes de los returns tempranos: si no, React cambia el orden de los hooks al llegar los datos
  const [copia, setCopia] = useState(null)

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  const vista = vistaSinRondas({ vacio: !data?.totals?.rounds, filtros: filters, cargando: loading })
  if (vista === 'importar') return <EmptyState onImport={runImport} importing={importing} />
  if (vista === 'filtrado') {
    return <SinRondasFiltradas titulo="Coach" filtros={<Filters value={filters} onChange={setFilters} />} />
  }

  const insights = data.insights || []
  const texto = textoCoach(insights, filters)

  async function copiarSenales() {
    // Sin console: un portapapeles negado es esperable (permisos, http) y se avisa en la pagina
    if (!navigator.clipboard?.writeText) {
      setCopia({ estado: 'error', texto })
      return
    }
    try {
      await navigator.clipboard.writeText(texto)
      setCopia({ estado: 'ok', texto })
    } catch {
      setCopia({ estado: 'error', texto })
    }
  }

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
        {texto ? (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            {/* el aviso es del texto que se copio: con otros filtros ya no vale */}
            {copia?.texto === texto && (
              <span className="note">
                {copia.estado === 'ok'
                  ? 'Copiado'
                  : 'No se pudo copiar: el navegador no dio acceso al portapapeles.'}
              </span>
            )}
            <button
              type="button"
              className="btn small"
              onClick={copiarSenales}
              // mientras llega la respuesta de los filtros nuevos, las señales en pantalla son las viejas
              disabled={loading}
              title="Copia las señales que ves, con los filtros, en texto plano."
            >
              Copiar señales
            </button>
          </div>
        ) : null}
      </div>

      <Filters value={filters} onChange={setFilters} />

      {GRUPOS_COACH.map((group) => {
        const rows = insights.filter((i) => i.severity === group.key)
        if (!rows.length) return null
        return (
          <Panel key={group.key} title={group.title} hint={group.hint}>
            {rows.map((insight) => {
              const enlace = enlaceDeSenal(insight, filters)
              return (
                <div key={insight.key} className={`insight ${insight.severity}`}>
                  <h3>{insight.title}</h3>
                  <p>{insight.detail}</p>
                  <div className="action">
                    <b>Qué hacer:</b> {insight.action}
                  </div>
                  <div className="meta">
                    {insight.metric ? (
                      <span>
                        {insight.metric}: <b>{formatoCoach(insight.value)}</b>
                        {insight.baseline !== null && insight.baseline !== undefined
                          ? ` (referencia ${formatoCoach(insight.baseline)})`
                          : ''}
                      </span>
                    ) : null}
                    {insight.sample ? <span>muestra: {insight.sample} rondas</span> : null}
                    {insight.scope && insight.scope !== 'general' ? <span>alcance: {insight.scope}</span> : null}
                    {enlace ? (
                      <Link className="btn small" to={enlace}>
                        {textoDelEnlace(insight)}
                      </Link>
                    ) : null}
                  </div>
                </div>
              )
            })}
          </Panel>
        )
      })}

      <PanelPosicion {...posicion} />
      <PanelSalidaSpawn {...posicion} />
      <PanelRepetirSitio filters={filters} />
      <PanelRepetirSpawn filters={filters} />

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

const SIN_PARES = 'Sin rondas de defensa perdidas seguidas de otra con estos filtros.'

const winrateConMuestra = (caso, label) => ({
  key: `${caso}_winrate`,
  label,
  csv: (row) => row[`${caso}_winrate`],
  render: (row) => textoWinrate(row[`${caso}_winrate`], row[`${caso}_poca`]),
})

const columnasRepetirSitio = [
  { key: 'map', label: 'Mapa', left: true },
  { key: 'repeat_rounds', label: 'Repite', help: 'Rondas en que tu equipo volvió al sitio que acababa de perder.' },
  winrateConMuestra('repeat', 'Winrate repitiendo'),
  { key: 'switch_rounds', label: 'Cambia', help: 'Rondas en que tu equipo defendió otro sitio.' },
  winrateConMuestra('switch', 'Winrate cambiando'),
]

function PanelRepetirSitio({ filters }) {
  const { data, error, loading } = useApi('/positioning/site-after-loss/', filters)
  return (
    <Panel
      title="Repetir el sitio tras perderlo"
      hint="Después de perder una ronda defendiendo un sitio, qué hace tu equipo en la siguiente ronda de defensa de esa partida y cuánto la gana. Con el filtro de sitio, solo las rondas perdidas en ese sitio."
    >
      {error ? (
        <ErrorBox error={error} />
      ) : loading && !data ? (
        <Loading />
      ) : !hayPares(data) ? (
        <p className="note">{SIN_PARES}</p>
      ) : (
        <>
          <p className="note">{textoPares(data.pairs)}.</p>
          <div className="kpis repetir-sitio">
            {casosRepetirSitio(data.total, data.min_rounds).map((caso) => (
              <Stat
                key={caso.clave}
                label={caso.titulo}
                value={caso.rounds}
                sub={`winrate ${textoWinrate(caso.winrate, caso.poca)}`}
              />
            ))}
          </div>
          <DataTable
            columns={columnasRepetirSitio}
            rows={filasPorMapa(data)}
            rowKey={(row) => `${row.slug}-${row.map_id}`}
            initialSort={{ key: 'repeat_rounds', dir: 'desc' }}
            csvName="repetir-sitio-por-mapa"
            empty={SIN_PARES}
          />
        </>
      )}
    </Panel>
  )
}

const SIN_PARES_SPAWN = 'Sin rondas de ataque seguidas de otra con spawn con estos filtros.'

const columnasRepetirSpawn = [
  { key: 'tramo', label: 'Tras', left: true, sortable: false },
  { key: 'repeat_rounds', label: 'Repite', help: 'Rondas en que saliste del mismo spawn.' },
  winrateConMuestra('repeat', 'Winrate repitiendo'),
  { key: 'switch_rounds', label: 'Cambia', help: 'Rondas en que saliste de otro spawn.' },
  winrateConMuestra('switch', 'Winrate cambiando'),
]

function PanelRepetirSpawn({ filters }) {
  const { data, error, loading } = useApi('/positioning/spawn-after-result/', filters)
  return (
    <Panel
      title="Repetir o cambiar el spawn"
      hint="En ataque, después de una ronda, si en tu siguiente ronda de ataque de esa partida saliste del mismo spawn o de otro, y cuánto la ganaste. Tras ganar es la base para comparar. Con el filtro de operador o de sitio, solo las rondas que lo cumplen abren el par."
    >
      {error ? (
        <ErrorBox error={error} />
      ) : loading && !data ? (
        <Loading />
      ) : !hayParesSpawn(data) ? (
        <p className="note">{SIN_PARES_SPAWN}</p>
      ) : (
        <>
          <p className="note">{textoParesSpawn(data.pairs)}.</p>
          <DataTable
            columns={columnasRepetirSpawn}
            rows={filasRepetirSpawn(data)}
            rowKey={(row) => row.tras}
            initialSort={{ key: 'orden', dir: 'asc' }}
            csvName="repetir-spawn"
            empty={SIN_PARES_SPAWN}
          />
        </>
      )}
    </Panel>
  )
}
