/**
 * Selector "Tipo" de la barra de filtros (ficha 77).
 *
 * Reemplaza al checkbox "Solo ranked": la API sigue aceptando `ranked_only`,
 * pero la UI solo manda `match_type`, asi nunca viajan los dos
 * contradiciendose (`ranked_only=1&match_type=Unranked` daria 0 rondas sin
 * explicacion).
 */

/** Opciones del `<select>`: "Todos" y cada tipo que hay en la base, en el orden de la API. */
export function opcionesDeTipo(matchTypes) {
  const vistos = new Set()
  const opciones = [{ value: '', label: 'Todos' }]
  for (const tipo of matchTypes || []) {
    if (!tipo || vistos.has(tipo)) continue
    vistos.add(tipo)
    opciones.push({ value: tipo, label: tipo })
  }
  return opciones
}

/**
 * Lo que muestra el selector. Hoy los filtros viven en el estado de App y
 * nadie pone `ranked_only`; si llegan filtros en la URL (A10) con un enlace
 * viejo, se lee como Ranked en vez de mostrar "Todos" filtrando.
 */
export function tipoElegido(filtros) {
  if (!filtros) return ''
  return filtros.match_type || (filtros.ranked_only ? 'Ranked' : '')
}

/** Filtros con el tipo elegido; `false` lo saca `qs()` y no prende "Limpiar". */
export function conTipo(filtros, tipo) {
  return { ...filtros, match_type: tipo, ranked_only: false }
}

/** Hay algun filtro puesto: vacios y `false` no cuentan. */
export function hayFiltros(filtros) {
  return Object.values(filtros || {}).some(Boolean)
}
