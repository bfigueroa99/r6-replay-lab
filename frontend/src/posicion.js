/**
 * Logica del panel "Dónde quedas fuera de posición" del Coach (ficha 80).
 * El veredicto lo decide el backend; aca solo se traduce y se pinta.
 */

export const VEREDICTOS = {
  dormidero: 'Te agarran más',
  solido: 'Te sostienes',
  ruido: 'Sin señal',
}

/** Etiqueta del veredicto; uno desconocido o ausente no dice nada. */
export function etiquetaVeredicto(veredicto) {
  return VEREDICTOS[veredicto] ?? VEREDICTOS.ruido
}

/** Clase del chip: rojo donde te agarran mas, verde donde te sostienes. */
export function claseVeredicto(veredicto) {
  if (veredicto === 'dormidero') return 'loss'
  if (veredicto === 'solido') return 'win'
  return ''
}

/** Si hay alguna zona con muestra, de sitio o de spawn. */
export function hayZonas(datos) {
  return Boolean(datos?.sites?.length || datos?.spawns?.length)
}

/** La muestra minima sale de la api, asi la nota no se desfasa de la constante. */
export function notaDeMuestra(datos) {
  const minimo = datos?.min_rounds ?? 5
  return `Solo zonas con ${minimo} rondas o más.`
}

/** Diferencia con signo y un decimal: `+33.5`, `-1.7`. */
export function conSigno(valor) {
  if (valor === null || valor === undefined) return '—'
  const n = Number(valor)
  return `${n > 0 ? '+' : ''}${n.toFixed(1)}`
}

/** Margen como banda: `±13.8`. */
export function comoMargen(valor) {
  if (valor === null || valor === undefined) return '—'
  return `±${Number(valor).toFixed(1)}`
}
