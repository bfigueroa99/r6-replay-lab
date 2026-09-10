import React, { useMemo, useState } from 'react'

/** Formatea numeros que pueden venir null desde la API. */
export const fmt = (value, digits = 0, suffix = '') =>
  value === null || value === undefined ? '—' : `${Number(value).toFixed(digits)}${suffix}`

export const pct = (value) => fmt(value, 0, '%')
export const ratio = (value) => fmt(value, 2)

export function Stat({ label, value, sub, tone, help }) {
  return (
    <div className={`stat ${tone || ''}`}>
      <div className="label">
        {label}
        {help ? (
          <span className="help" title={help}>
            ?
          </span>
        ) : null}
      </div>
      <div className="value">{value}</div>
      {sub ? <div className="sub">{sub}</div> : null}
    </div>
  )
}

export function Panel({ title, hint, children, right }) {
  return (
    <section className="panel">
      {title ? (
        <div className="page-head" style={{ marginBottom: hint ? 0 : 12 }}>
          <h2 style={{ margin: 0, fontSize: 15, letterSpacing: '0.6px', color: 'var(--muted)', textTransform: 'uppercase' }}>
            {title}
          </h2>
          {right}
        </div>
      ) : null}
      {hint ? <p className="hint">{hint}</p> : null}
      {children}
    </section>
  )
}

export function SideChip({ side }) {
  if (!side) return <span className="chip">?</span>
  const attack = side === 'Attack'
  return <span className={`chip ${attack ? 'atk' : 'def'}`}>{attack ? 'Ataque' : 'Defensa'}</span>
}

export function ResultChip({ won, children }) {
  if (won === null || won === undefined) return <span className="chip">{children || '—'}</span>
  return <span className={`chip ${won ? 'win' : 'loss'}`}>{children || (won ? 'Ganada' : 'Perdida')}</span>
}

/** Barra horizontal 0-100 que colorea segun el valor. */
export function Bar({ value, max = 100 }) {
  if (value === null || value === undefined) return <span className="dim">—</span>
  const width = Math.max(2, Math.min(100, (value / max) * 100))
  return (
    <div className="bar" title={`${Number(value).toFixed(1)}`}>
      <span style={{ width: `${width}%`, background: winrateColor(value) }} />
    </div>
  )
}

/** Rojo bajo 40%, gris al 50%, verde sobre 60%. */
export function winrateColor(value, low = 35, high = 65) {
  if (value === null || value === undefined) return '#2a3441'
  const clamped = Math.max(low, Math.min(high, value))
  const t = (clamped - low) / (high - low)
  const hue = 0 + t * 130 // 0 rojo -> 130 verde
  const light = 26 + Math.abs(t - 0.5) * 18
  return `hsl(${hue} 62% ${light}%)`
}

/**
 * Tabla ordenable. `columns` = [{ key, label, render?, digits?, suffix?, help?, align? }]
 */
export function DataTable({ columns, rows, initialSort, rowKey, rowClass, empty = 'Sin datos.' }) {
  const [sort, setSort] = useState(initialSort || { key: columns[0].key, dir: 'desc' })

  const sorted = useMemo(() => {
    const copy = [...(rows || [])]
    copy.sort((a, b) => {
      const av = a[sort.key]
      const bv = b[sort.key]
      const aNull = av === null || av === undefined
      const bNull = bv === null || bv === undefined
      if (aNull && bNull) return 0
      if (aNull) return 1
      if (bNull) return -1
      if (typeof av === 'string' || typeof bv === 'string') {
        return sort.dir === 'asc'
          ? String(av).localeCompare(String(bv))
          : String(bv).localeCompare(String(av))
      }
      return sort.dir === 'asc' ? av - bv : bv - av
    })
    return copy
  }, [rows, sort])

  if (!rows || rows.length === 0) return <p className="note">{empty}</p>

  const toggle = (key) =>
    setSort((current) =>
      current.key === key ? { key, dir: current.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'desc' },
    )

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={[col.sortable === false ? 'plain' : '', col.left ? 'left' : ''].join(' ').trim()}
                onClick={col.sortable === false ? undefined : () => toggle(col.key)}
                title={col.help}
              >
                {col.label}
                {sort.key === col.key ? <span className="arrow"> {sort.dir === 'asc' ? '↑' : '↓'}</span> : null}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr key={rowKey ? rowKey(row) : i} className={rowClass ? rowClass(row) : ''}>
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={[col.dim ? 'dim' : '', col.left ? 'left' : '', col.wrap ? 'wrap' : '']
                    .join(' ')
                    .trim()}
                >
                  {col.render
                    ? col.render(row)
                    : col.digits !== undefined
                      ? fmt(row[col.key], col.digits, col.suffix || '')
                      : (row[col.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function Loading({ children = 'Cargando...' }) {
  return <p className="loading">{children}</p>
}

export function ErrorBox({ error }) {
  if (!error) return null
  return (
    <div className="error">
      <b>No pude leer la API.</b> {String(error)}
      <br />
      <span className="note">Revisa que Django este corriendo en el puerto 8000.</span>
    </div>
  )
}

export function EmptyState({ onImport, importing }) {
  return (
    <div className="empty-state">
      <h2>Todavia no hay replays importados</h2>
      <p>
        Apunta <code>REPLAY_DIR</code> en el <code>.env</code> a tu carpeta <code>MatchReplay</code> y
        dale a importar.
      </p>
      <p className="note">
        Tambien puedes correr <code>python manage.py import_replays</code> desde <code>backend/</code>.
      </p>
      {onImport ? (
        <button className="btn primary" onClick={onImport} disabled={importing}>
          {importing ? 'Importando...' : 'Importar replays ahora'}
        </button>
      ) : null}
    </div>
  )
}
