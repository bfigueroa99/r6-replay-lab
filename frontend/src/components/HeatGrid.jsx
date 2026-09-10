import React, { useMemo } from 'react'

import { winrateColor } from './ui.jsx'

/**
 * Matriz mapa x sitio (o mapa x spawn) coloreada por winrate.
 *
 * Nota importante: el formato .rec no expone coordenadas de las bajas, asi que
 * este es un mapa de calor por zonas del juego (sitio de bomba, spawn de
 * ataque), no un heatmap de posiciones sobre el minimapa.
 */
export default function HeatGrid({ rows, rowKey = 'map', colKey = 'site', minRounds = 1 }) {
  const { rowNames, colNames, cells } = useMemo(() => {
    const cells = new Map()
    const rowSet = new Map()
    const colSet = new Map()
    ;(rows || []).forEach((row) => {
      if ((row.rounds || 0) < minRounds) return
      cells.set(`${row[rowKey]}||${row[colKey]}`, row)
      rowSet.set(row[rowKey], (rowSet.get(row[rowKey]) || 0) + row.rounds)
      colSet.set(row[colKey], (colSet.get(row[colKey]) || 0) + row.rounds)
    })
    return {
      rowNames: [...rowSet.entries()].sort((a, b) => b[1] - a[1]).map(([name]) => name),
      colNames: [...colSet.entries()].sort((a, b) => b[1] - a[1]).map(([name]) => name),
      cells,
    }
  }, [rows, rowKey, colKey, minRounds])

  if (rowNames.length === 0) {
    return <p className="note">Todavia no hay suficientes rondas para armar el mapa de calor.</p>
  }

  const template = `minmax(120px, 170px) repeat(${colNames.length}, minmax(88px, 1fr))`

  return (
    <div>
      <div className="table-wrap">
        <div className="heat" style={{ minWidth: 130 + colNames.length * 92 }}>
          <div className="heat-row" style={{ gridTemplateColumns: template }}>
            <div className="heat-label" />
            {colNames.map((col) => (
              <div key={col} className="heat-label" title={col} style={{ minHeight: 34 }}>
                {col}
              </div>
            ))}
          </div>
          {rowNames.map((name) => (
            <div key={name} className="heat-row" style={{ gridTemplateColumns: template }}>
              <div className="heat-label" title={name}>
                {name}
              </div>
              {colNames.map((col) => {
                const cell = cells.get(`${name}||${col}`)
                if (!cell) {
                  return (
                    <div key={col} className="heat-cell empty">
                      ·
                    </div>
                  )
                }
                return (
                  <div
                    key={col}
                    className="heat-cell"
                    style={{ background: winrateColor(cell.winrate) }}
                    title={`${name} · ${col}\n${cell.rounds} rondas · ${cell.winrate}% ganadas · ${cell.kpr ?? '—'} kills/ronda`}
                  >
                    <div>
                      <b>{cell.winrate === null ? '—' : `${Math.round(cell.winrate)}%`}</b>
                      <br />
                      <small>{cell.rounds}r</small>
                    </div>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>
      <div className="heat-legend">
        <span>Peor</span>
        <div className="heat-scale">
          {[0, 20, 40, 50, 60, 80, 100].map((v) => (
            <i key={v} style={{ background: winrateColor(v) }} />
          ))}
        </div>
        <span>Mejor</span>
        <span style={{ marginLeft: 12 }}>El numero chico es la cantidad de rondas.</span>
      </div>
    </div>
  )
}
