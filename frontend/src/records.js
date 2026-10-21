/**
 * Filas del panel "Tus records" del Resumen. Separado de la pagina para
 * probar el orden y el formato sin montarla.
 */

const fecha = (iso) => (iso ? iso.slice(0, 10) : '')

/** Orden fijo del panel: clave del backend, etiqueta y como se escribe el valor. */
const RECORDS = [
  ['best_match_rating', 'Mejor partida', (r) => `${Number(r.value).toFixed(2)} de rating`],
  ['most_kills_match', 'Más bajas en una partida', (r) => `${r.value} ${r.value === 1 ? 'baja' : 'bajas'}`],
  ['most_kills_round', 'Más bajas en una ronda', (r) => `${r.value} ${r.value === 1 ? 'baja' : 'bajas'}`],
  ['biggest_clutch', 'Clutch más grande', (r) => `1v${r.value}`],
  ['longest_round_streak', 'Racha de rondas', (r) => `${r.value} ${r.value === 1 ? 'ronda ganada' : 'rondas ganadas seguidas'}`],
  ['best_day', 'Mejor día', (r) => `${Math.round(r.value)} % de rondas ganadas`],
]

function detalle(clave, record) {
  if (clave === 'best_day') return `${fecha(record.day)} · ${record.rounds_won} de ${record.rounds} rondas`
  if (record.round_label) return `ronda ${record.round_label} · ${record.map} · ${fecha(record.played_at)}`
  return `${record.map} · ${fecha(record.played_at)} · ${record.rounds} rondas`
}

/** Los records que existen, en orden fijo; los nulos no se muestran. */
export function filasDeRecords(records) {
  return RECORDS.filter(([clave]) => records?.[clave]).map(([clave, etiqueta, valor], orden) => {
    const record = records[clave]
    return {
      orden,
      clave,
      etiqueta,
      valor: valor(record),
      detalle: detalle(clave, record),
      href: record.match_id ? `/partidas/${record.match_id}` : null,
    }
  })
}
