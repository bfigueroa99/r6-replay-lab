/**
 * Panel "Por sitio" de Operadores (ficha 93): winrate con un operador en un
 * sitio contra el resto de tus operadores ahi. El veredicto lo decide el
 * backend; aca solo se traduce y se pinta.
 */

export const VEREDICTOS_SITIO = {
  rinde: 'Te rinde',
  hunde: 'Te hunde',
  ruido: 'Sin señal',
}

/** Etiqueta del veredicto; uno desconocido o ausente no dice nada. */
export function etiquetaSitio(veredicto) {
  return VEREDICTOS_SITIO[veredicto] ?? VEREDICTOS_SITIO.ruido
}

/** Clase del chip: verde donde el operador te rinde, rojo donde te hunde. */
export function claseSitio(veredicto) {
  if (veredicto === 'rinde') return 'win'
  if (veredicto === 'hunde') return 'loss'
  return ''
}

/** El minimo sale de la api, asi el texto no se desfasa de la constante. */
export function textoSinFilas(datos) {
  const minimo = datos?.min_rounds ?? 10
  return `Ningún operador llega a ${minimo} rondas en un sitio (ni el resto del sitio).`
}
