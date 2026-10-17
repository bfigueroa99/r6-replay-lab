/**
 * Texto de multikills por tamaño (2K, 3K, 4K, ace) para el scoreboard, el
 * perfil de jugador y el Resumen. Separado de las paginas para probarlo solo.
 */

/** [clave, etiqueta corta, bajas] de menor a mayor; ace es 5 o mas. */
export const TAMANOS = [
  ['k2', '2K', 2],
  ['k3', '3K', 3],
  ['k4', '4K', 4],
  ['aces', 'ACE', 5],
]

/** Solo los tamaños con alguna ronda, en orden de tamaño. */
export function partesMultikills(fila) {
  if (!fila) return []
  return TAMANOS.map(([clave, etiqueta, bajas]) => ({ clave, etiqueta, bajas, rondas: fila[clave] || 0 }))
    .filter((parte) => parte.rondas > 0)
}

/** "2×2K · 1×ACE": rondas × tamaño. Sin multikills, cadena vacia. */
export function textoMultikills(fila) {
  return partesMultikills(fila)
    .map((parte) => `${parte.rondas}×${parte.etiqueta}`)
    .join(' · ')
}

/** "2 rondas de 2 bajas · 1 de 5 o más", para el title de la celda. */
export function detalleMultikills(fila) {
  return partesMultikills(fila)
    .map((parte, i) => {
      const bajas = parte.clave === 'aces' ? '5 o más' : String(parte.bajas)
      if (i > 0) return `${parte.rondas} de ${bajas}`
      return `${parte.rondas} ${parte.rondas === 1 ? 'ronda' : 'rondas'} de ${bajas} bajas`
    })
    .join(' · ')
}

/** Rondas con 2 o mas bajas; una respuesta sin el total suma los cuatro tamaños. */
export function rondasConMultikill(fila) {
  if (fila?.multikill_rounds !== undefined && fila?.multikill_rounds !== null) return fila.multikill_rounds
  return partesMultikills(fila).reduce((suma, parte) => suma + parte.rondas, 0)
}
