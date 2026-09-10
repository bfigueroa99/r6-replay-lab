import React from 'react'

import { useApi } from '../api.js'
import Filters from '../components/Filters.jsx'
import HeatGrid from '../components/HeatGrid.jsx'
import { Bar, DataTable, EmptyState, ErrorBox, Loading, Panel, pct } from '../components/ui.jsx'

export default function MapsPage({ filters, setFilters, runImport, importing }) {
  const { data, error, loading } = useApi('/maps/', { ...filters, min_rounds: 1 })

  if (error) return <ErrorBox error={error} />
  if (loading && !data) return <Loading />
  if (!data?.maps?.length) return <EmptyState onImport={runImport} importing={importing} />

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Mapas y sitios</h1>
          <p>Donde ganas y donde se te cae el winrate.</p>
        </div>
      </div>

      <Filters value={filters} onChange={setFilters} showOperator={false} />

      <Panel title="Por mapa">
        <DataTable
          columns={[
            { key: 'map', label: 'Mapa' },
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
            {
              key: 'attack_winrate',
              label: 'Ataque',
              render: (row) => `${pct(row.attack_winrate)} (${row.attack_rounds}r)`,
            },
            {
              key: 'defense_winrate',
              label: 'Defensa',
              render: (row) => `${pct(row.defense_winrate)} (${row.defense_rounds}r)`,
            },
            { key: 'kd', label: 'K/D', digits: 2 },
            { key: 'kpr', label: 'KPR', digits: 2 },
            { key: 'opening_winrate', label: 'Aperturas', digits: 0, suffix: '%' },
            { key: 'kst_pct', label: 'KST', digits: 0, suffix: '%' },
          ]}
          rows={data.maps}
          initialSort={{ key: 'rounds', dir: 'desc' }}
          rowKey={(row) => row.map}
        />
      </Panel>

      <Panel
        title="Mapa de calor por sitio"
        hint="Winrate en cada sitio de bomba. El .rec no trae coordenadas de las bajas, asi que el calor es por zona del juego, no por posicion exacta."
      >
        <HeatGrid rows={data.sites} rowKey="map" colKey="site" />
      </Panel>

      <Panel title="Detalle por sitio">
        <DataTable
          columns={[
            { key: 'map', label: 'Mapa' },
            { key: 'site', label: 'Sitio', left: true },
            { key: 'rounds', label: 'Rondas' },
            { key: 'winrate', label: 'Ganadas', digits: 0, suffix: '%' },
            { key: 'kd', label: 'K/D', digits: 2 },
            { key: 'kpr', label: 'KPR', digits: 2 },
            { key: 'opening_winrate', label: 'Aperturas', digits: 0, suffix: '%' },
            { key: 'untraded_death_pct', label: 'Muertes sin trade', digits: 0, suffix: '%' },
          ]}
          rows={data.sites}
          initialSort={{ key: 'rounds', dir: 'desc' }}
          rowKey={(row) => `${row.map}-${row.site}`}
        />
      </Panel>

      <Panel
        title="Spawns de ataque"
        hint="Desde donde entras y como te va. Si un spawn rinde mal, probablemente siempre haces la misma ruta."
      >
        <HeatGrid rows={data.spawns} rowKey="map" colKey="spawn" />
      </Panel>
    </>
  )
}
