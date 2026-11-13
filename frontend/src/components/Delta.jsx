import React from 'react'

import { fmt } from './ui.jsx'

/** Flecha con color segun si la metrica mejoro, empeoro o no se movio. */
export default function Delta({ metric }) {
  if (metric.delta === null || metric.delta === undefined) return <span className="dim">—</span>
  const signo = metric.delta > 0 ? '+' : ''
  const texto = `${signo}${fmt(metric.delta, Math.abs(metric.delta) < 1 ? 2 : 1)}${metric.suffix}`
  if (metric.verdict === 'mejor') return <span className="chip win">{texto}</span>
  if (metric.verdict === 'peor') return <span className="chip loss">{texto}</span>
  return <span className="chip">{texto}</span>
}
