/**
 * Tabla "Operadores que te abren" de Duelos: la primera baja de la ronda por
 * operador rival y por tu lado (`opening_operators` de `/api/duels/`).
 */

/** Filas con una clave unica: el mismo operador sale una vez por lado. */
export function filasOperadoresQueTeAbren(rows) {
  return (rows || []).map((fila) => ({ ...fila, key: `${fila.operator}-${fila.side}` }))
}
