/**
 * Muestra minima de los cortes de Tendencias. Un corte con pocas rondas no se
 * oculta (la fila dice algo aunque sea poco), pero se avisa para que nadie le
 * crea una diferencia que puede ser varianza.
 */

export const MUESTRA_CORTE = 30

/** Filas con rondas pero menos de `minimo`. Las de 0 no avisan: salen vacias. */
export function filasConPocaMuestra(filas, minimo = MUESTRA_CORTE) {
  return (filas || []).filter((fila) => {
    const rondas = fila?.rounds || 0
    return rondas > 0 && rondas < minimo
  })
}
