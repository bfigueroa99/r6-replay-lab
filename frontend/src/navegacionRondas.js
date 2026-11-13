/** Cambiar de ronda en el detalle de una partida: flechas del teclado y ancla `#ronda-N`. */

/** Ronda a `paso` de `actual`, sin pasarse de la primera ni de la ultima. */
export function rondaVecina(actual, total, paso) {
  if (total <= 0) return 0
  return Math.min(Math.max(actual + paso, 0), total - 1)
}

const CAMPOS = new Set(['INPUT', 'TEXTAREA', 'SELECT'])
// tablas anchas con scroll horizontal: ahi la flecha desplaza la tabla
const CON_SCROLL = '.table-wrap, .matriz-scroll'

/**
 * -1, 1 o 0 (no tomar la tecla). Con modificadores no: Alt+flecha es Atras del
 * navegador y Shift/Ctrl/Meta+flecha seleccionan o saltan texto. En un campo
 * la flecha mueve el cursor o cambia la opcion, no la ronda; si otro widget ya
 * tomo la tecla, tampoco.
 */
export function pasoDeTecla(evento) {
  if (evento.defaultPrevented) return 0
  if (evento.altKey || evento.ctrlKey || evento.metaKey || evento.shiftKey) return 0
  const destino = evento.target
  if (destino && (CAMPOS.has(destino.tagName) || destino.isContentEditable)) return 0
  if (destino?.closest?.(CON_SCROLL)) return 0
  if (evento.key === 'ArrowLeft') return -1
  if (evento.key === 'ArrowRight') return 1
  return 0
}

const ANCLA = /^#ronda-([1-9]\d*)$/

/** Ancla de una ronda: el numero humano de la etiqueta `R<n>`, no el `number` 0-based. */
export const anclaDeRonda = (number) => `#ronda-${number + 1}`

/**
 * Indice en `rounds` de la ronda que pide el hash, o null. Se busca por
 * `number` y no por posicion: con un `.rec` faltante las dos se separan.
 */
export function indiceDeAncla(hash, rounds) {
  const ancla = ANCLA.exec(hash || '')
  if (!ancla || !rounds?.length) return null
  const numero = Number(ancla[1]) - 1
  const indice = rounds.findIndex((ronda) => ronda.number === numero)
  return indice === -1 ? null : indice
}
