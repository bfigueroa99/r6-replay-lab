/**
 * Panel "Tu forma contra tu historial" del Resumen: tus ultimas partidas
 * contra todo lo anterior, con la respuesta de `/api/compare/?against=rest`.
 */

/** Las metricas que dicen si estas en racha o en bajon, en el orden del panel. */
export const METRICAS_FORMA = ['winrate', 'rating', 'kst_pct', 'untraded_death_pct']

/** Filas del panel: solo las metricas de la forma, con su orden fijo. */
export function filasDeForma(data) {
  const metricas = data?.metrics || []
  return METRICAS_FORMA.map((clave) => metricas.find((m) => m.key === clave))
    .filter(Boolean)
    .map((m) => ({ ...m, orden: METRICAS_FORMA.indexOf(m.key) }))
}

/**
 * Que aviso lleva el panel. Sin resto no se compara (ceros que parecen un
 * cambio); con poca muestra se compara igual y se avisa, como en Progreso.
 */
export function estadoDeForma(data) {
  if (!data?.current?.rounds) return 'sin-datos'
  if (!data.previous?.rounds) return 'sin-resto'
  if (!data.enough_sample) return 'poca-muestra'
  return null
}
