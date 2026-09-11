import React from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { fmt } from './ui.jsx'

const AXIS = { stroke: '#8b98a9', fontSize: 11 }
const TOOLTIP = {
  contentStyle: { background: '#171e29', border: '1px solid #263041', borderRadius: 8 },
  labelStyle: { color: '#8b98a9' },
}

/**
 * El unico grafico del Resumen, en su propio archivo.
 *
 * Vive aparte para que `recharts` no entre en el bundle inicial: son casi 400 kB
 * y esta pantalla se ve completa sin el. El Resumen lo carga con `React.lazy`,
 * asi que la libreria llega despues de que la pagina ya se pinto.
 */
export default function EvolucionChart({ series }) {
  return (
    <div style={{ height: 240 }}>
      <ResponsiveContainer>
        <LineChart data={series} margin={{ top: 6, right: 12, bottom: 0, left: -18 }}>
          <CartesianGrid stroke="#263041" strokeDasharray="3 3" />
          <XAxis dataKey="n" {...AXIS} />
          <YAxis yAxisId="wr" domain={[0, 100]} {...AXIS} />
          <YAxis yAxisId="kpr" orientation="right" domain={[0, 'auto']} {...AXIS} />
          <Tooltip
            {...TOOLTIP}
            labelFormatter={(n) => series[n - 1]?.label || ''}
            formatter={(value, name) => [fmt(value, name === 'KPR' ? 2 : 0), name]}
          />
          <Line
            yAxisId="wr"
            type="monotone"
            dataKey="winrate"
            name="Rondas ganadas %"
            stroke="#ff8a3d"
            strokeWidth={2}
            dot={false}
          />
          <Line
            yAxisId="kpr"
            type="monotone"
            dataKey="kpr"
            name="KPR"
            stroke="#4aa8ff"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
