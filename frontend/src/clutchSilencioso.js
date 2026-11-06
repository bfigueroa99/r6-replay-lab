/**
 * Textos de los clutches silenciosos (ganados sin bajas tuyas desde que
 * quedaste solo). Puro y sin `ui.jsx`, para probarlo sin montar la pagina.
 */

/** Celda "Silenciosos" de una fila 1vX: cantidad y % sobre los ganados. */
export function celdaSilenciosos(row) {
  // sin ganados no hay sobre que medir: un 0 se leeria como "ninguno silencioso"
  if (!row?.won) return '—'
  return `${row.silent} (${Math.round(row.silent_pct)}%)`
}

/** Nota con el reparto por condicion de victoria; `null` si no ganaste ninguno. */
export function notaSilenciosos(resumen) {
  if (!resumen?.won) return null
  const { won, silent, by_condition: cond } = resumen
  const ganados = won === 1 ? 'De tu único clutch ganado' : `De tus ${won} clutches ganados`
  const fueron = silent === 1 ? 'fue silencioso' : 'fueron silenciosos'
  const sinDato = cond.unknown ? `, ${cond.unknown} sin dato` : ''
  return (
    `${ganados}, ${silent} ${fueron} (sin bajas tuyas desde que quedaste solo): ` +
    `${cond.elimination} por eliminación, ${cond.other} sin eliminación ` +
    `(plant, defuse o tiempo; en temporadas nuevas, inferido del reloj)${sinDato}.`
  )
}
