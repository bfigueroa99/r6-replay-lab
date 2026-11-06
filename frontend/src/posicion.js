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

/*
 * Panel "Salida del spawn" (ficha 89): muertes en los primeros segundos de
 * ataque, por spawn, contra el resto de tu ataque.
 */
export const VEREDICTOS_SALIDA = {
  temprano: 'Caes temprano',
  aguanta: 'Sales bien',
  ruido: 'Sin señal',
}

export function etiquetaSalida(veredicto) {
  return VEREDICTOS_SALIDA[veredicto] ?? VEREDICTOS_SALIDA.ruido
}

/** Rojo donde caes antes que en el resto de tu ataque, verde donde sales mejor. */
export function claseSalida(veredicto) {
  if (veredicto === 'temprano') return 'loss'
  if (veredicto === 'aguanta') return 'win'
  return ''
}

/**
 * Por que la tabla esta vacia: sin ataque con spawn (o con el filtro Lado en
 * defensa) no es lo mismo que tener rondas sin la muestra minima.
 */
export function textoSinSalidas(datos) {
  if (!datos?.spawn_exit_attack?.rounds) {
    return 'Todavía no hay rondas de ataque con spawn con estos filtros.'
  }
  return `Ningún spawn llega a ${datos?.min_rounds ?? 5} rondas de ataque.`
}
