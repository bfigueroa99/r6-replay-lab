/**
 * Filas del panel "Solo, en dúo o en stack" de Compañeros. Separado de la
 * pagina para probar la logica sin montarla.
 */

const GRUPOS = {
  solo: 'Solo',
  duo: 'Dúo',
  trio: 'Trío',
  stack: 'Stack',
}

/** Etiqueta de un grupo; uno desconocido pasa tal cual. */
export function etiquetaGrupo(group) {
  return GRUPOS[group] ?? String(group)
}

/**
 * Una fila por grupo, en el orden del backend. "Stack" son 3 o mas habituales:
 * la columna lo dice para que nadie lo lea como un 5-stack.
 */
export function filasDeGrupo(byStack) {
  return (byStack?.rows || []).map((fila, orden) => ({
    ...fila,
    orden,
    etiqueta: etiquetaGrupo(fila.group),
    habituales: fila.regulars >= 3 ? '3 o más' : fila.regulars,
  }))
}

/** Quienes cuentan como habituales, o por que todo cae en Solo. */
export function textoHabituales(byStack) {
  const habituales = byStack?.regulars || []
  if (!habituales.length) {
    const minimo = byStack?.min_matches ?? 5
    return `Ningún compañero llega a ${minimo} partidas contigo: todo cae en Solo.`
  }
  return `Habituales: ${habituales.map((h) => h.username).join(', ')}.`
}
