// Operador elegido en la pagina Operadores. Ataque y Defensa piden sin `operator`
// para no quedar con una sola fila: la elegida se resalta y el resto del pool sigue.

/** Copia de los filtros sin `operator`; no toca el original. */
export function sinOperador(filtros) {
  const { operator: _operador, ...resto } = filtros || {}
  return resto
}

/** `me` reusa el estilo de tu fila en el detalle de partida: sin CSS nuevo. */
export function claseFilaOperador(fila, operador) {
  return operador && fila?.operator === operador ? 'me' : ''
}

export function textoOperadorElegido(operador) {
  if (!operador) return ''
  return `Con ${operador} elegido, Ataque y Defensa siguen mostrando todo tu pool y lo resaltan; Por sitio y Repetir o cambiar tras perder se filtran a ${operador}, Tu pool no cambia.`
}
