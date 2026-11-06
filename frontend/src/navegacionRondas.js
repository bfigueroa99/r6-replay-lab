/** Cambiar de ronda con las flechas del teclado en el detalle de una partida. */

/** Ronda a `paso` de `actual`, sin pasarse de la primera ni de la ultima. */
export function rondaVecina(actual, total, paso) {
  if (total <= 0) return 0
  return Math.min(Math.max(actual + paso, 0), total - 1)
}

const CAMPOS = new Set(['INPUT', 'TEXTAREA', 'SELECT'])

/**
 * -1, 1 o 0 (no tomar la tecla). Con modificadores no: Alt+flecha es Atras del
 * navegador y Shift/Ctrl/Meta+flecha seleccionan o saltan texto. En un campo
 * la flecha mueve el cursor o cambia la opcion, no la ronda.
 */
export function pasoDeTecla(evento) {
  if (evento.altKey || evento.ctrlKey || evento.metaKey || evento.shiftKey) return 0
  const destino = evento.target
  if (destino && (CAMPOS.has(destino.tagName) || destino.isContentEditable)) return 0
  if (evento.key === 'ArrowLeft') return -1
  if (evento.key === 'ArrowRight') return 1
  return 0
}
