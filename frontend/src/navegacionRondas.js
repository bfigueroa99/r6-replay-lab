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
 * Si la tecla queda para la pagina. Con modificadores no: Alt+flecha es Atras
 * del navegador y Shift/Ctrl/Meta+flecha seleccionan o saltan texto. En un
 * campo la tecla escribe, mueve el cursor o cambia la opcion; si otro widget
 * ya la tomo, tampoco.
 */
function teclaLibre(evento) {
  if (evento.defaultPrevented) return false
  if (evento.altKey || evento.ctrlKey || evento.metaKey || evento.shiftKey) return false
  const destino = evento.target
  if (destino && (CAMPOS.has(destino.tagName) || destino.isContentEditable)) return false
  return true
}

/** -1, 1 o 0 (no tomar la tecla). */
export function pasoDeTecla(evento) {
  if (!teclaLibre(evento)) return 0
  // en una tabla con scroll la flecha la desplaza; la `p` no desplaza nada y ahi si vale
  if (evento.target?.closest?.(CON_SCROLL)) return 0
  if (evento.key === 'ArrowLeft') return -1
  if (evento.key === 'ArrowRight') return 1
  return 0
}

/** La `p` pide la siguiente ronda perdida; `P` tambien, por el Bloq Mayus (Shift ya quedo afuera). */
export function pideSiguientePerdida(evento) {
  return teclaLibre(evento) && (evento.key === 'p' || evento.key === 'P')
}

/**
 * Indice de la proxima ronda que tu equipo perdio despues de `actual`, dando
 * la vuelta, o null si no hay ninguna. Una ronda sin ganador (`my_team_won`
 * nulo, partida cortada) no es una derrota: se saltea. Con la elegida como
 * unica perdida devuelve la misma.
 */
export function siguientePerdida(actual, rounds) {
  const n = rounds?.length ?? 0
  if (!n) return null
  const desde = Math.min(Math.max(actual, 0), n - 1)
  for (let k = 1; k <= n; k += 1) {
    const indice = (desde + k) % n
    if (rounds[indice]?.my_team_won === false) return indice
  }
  return null
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
