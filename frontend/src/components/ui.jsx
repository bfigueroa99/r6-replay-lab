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

/** Numero con signo explicito: +6 y -6 se leen distinto de un 6 pelado. */
export const signed = (value, digits = 0, suffix = '') => {
  if (value === null || value === undefined) return '—'
  const texto = Number(value).toFixed(digits)
  // -0.4 redondeado a cero decimales es "-0", que se lee como un signo perdido.
  // El signo se decide sobre el numero ya redondeado, no sobre el original.
  const limpio = Number(texto) === 0 ? Math.abs(Number(texto)).toFixed(digits) : texto
  return `${Number(limpio) > 0 ? '+' : ''}${limpio}${suffix}`
}

/**
 * Como se presenta el veredicto de una zona.
 *
 * "Sin señal" y no "normal": cuando la diferencia no pasa la banda de ruido no
 * sabemos que la zona sea corriente, sabemos que no alcanza la muestra para
 * decir nada. Son cosas distintas y la etiqueta no las puede confundir.
 */
export const VEREDICTO = {
  dormidero: { label: 'Te agarran ahí', tone: 'loss' },
  solido: { label: 'Te sostienes', tone: 'win' },
  ruido: { label: 'Sin señal', tone: '' },
}

export function VerdictChip({ verdict }) {
  const v = VEREDICTO[verdict] || VEREDICTO.ruido
  return <span className={`chip ${v.tone}`}>{v.label}</span>
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
 * CSV pensado para Excel en espanol: punto y coma, coma decimal y BOM para que
 * las tildes no salgan rotas. El endpoint /api/export/ hace el CSV estandar,
 * que es el que quiere pandas.
 *
 * Una columna puede traer `csv: (row) => valor` para exportar algo distinto de
 * lo que muestra, o `csv: false` para quedarse fuera del archivo.
 */
function celdaCsv(col, row) {
  if (typeof col.csv === 'function') return col.csv(row)
  const valor = row[col.key]
  if (valor === null || valor === undefined) return ''
  if (Array.isArray(valor)) return valor.join(' / ')
  if (typeof valor === 'boolean') return valor ? 'si' : 'no'
  if (typeof valor === 'number') return String(valor).replace('.', ',')
  return String(valor)
}

const escaparCsv = (texto) =>
  /[";\r\n]/.test(texto) ? `"${texto.replace(/"/g, '""')}"` : texto

/** El contenido del archivo, separado del acto de bajarlo para poder probarlo. */
export function csvText(columns, rows) {
  const cols = columns.filter((col) => col.csv !== false)
  const lineas = [cols.map((col) => escaparCsv(col.label || col.key)).join(';')]
  for (const row of rows || []) {
    lineas.push(cols.map((col) => escaparCsv(celdaCsv(col, row))).join(';'))
  }
  return lineas.join('\r\n')
}

export function descargarCsv(columns, rows, nombre) {
  const blob = new Blob([`\ufeff${csvText(columns, rows)}`], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  // fecha local y no toISOString(): en UTC-4 un archivo bajado a las 21:00 se
  // llamaria con el dia siguiente
  const hoy = new Date()
  const fecha = [hoy.getFullYear(), hoy.getMonth() + 1, hoy.getDate()]
    .map((parte) => String(parte).padStart(2, '0'))
    .join('-')
  enlace.download = `${nombre}-${fecha}.csv`
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  URL.revokeObjectURL(url)
}

/**
 * Tabla ordenable. `columns` = [{ key, label, render?, digits?, suffix?, help?, align? }]
 *
 * Con `csvName` aparece el boton de descarga, que exporta exactamente lo que se
 * ve: las mismas columnas, en el orden en que estan ordenadas.
 */
/**
 * Orden de la tabla. Los nulos van siempre al final, en las dos direcciones: un
 * "sin datos" no es ni el mejor ni el peor, y verlos arriba al invertir el
 * orden es lo que hace desconfiar de una tabla.
 */
export function ordenarFilas(rows, sort) {
  const copia = [...(rows || [])]
  copia.sort((a, b) => {
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
  return copia
}

export function DataTable({
  columns,
  rows,
  initialSort,
  rowKey,
  rowClass,
  csvName,
  empty = 'Sin datos.',
}) {
  const [sort, setSort] = useState(initialSort || { key: columns[0].key, dir: 'desc' })

  const sorted = useMemo(() => ordenarFilas(rows, sort), [rows, sort])

  if (!rows || rows.length === 0) return <p className="note">{empty}</p>

  const toggle = (key) =>
    setSort((current) =>
      current.key === key ? { key, dir: current.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'desc' },
    )

  return (
    <div className="table-wrap">
      {csvName ? (
        <div className="table-tools">
          <button
            className="btn small"
            onClick={() => descargarCsv(columns, sorted, csvName)}
            title="Baja esta tabla tal como se ve, para abrirla en Excel"
          >
            Descargar CSV
          </button>
        </div>
      ) : null}
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
