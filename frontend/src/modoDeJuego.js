/**
 * Selector "Modo" de la barra y tabla "Por modo" de Tendencias (ficha 100).
 *
 * La API devuelve el nombre interno del parser (`Bomb`, `Hostage`...); aca se
 * traduce solo para mostrarlo, el valor que viaja en la query sigue siendo el
 * de la API.
 */

export const NOMBRES_DE_MODO = {
  Bomb: 'Bomba',
  Hostage: 'Rehén',
  SecureArea: 'Área segura',
  QuickMatchBomb: 'Bomba rápida',
}

/** Nombre en castellano; un modo que el parser no conoce (`Unknown(9)`) sale tal cual. */
export function nombreDeModo(modo) {
  if (!modo) return 'Sin modo'
  return NOMBRES_DE_MODO[modo] ?? modo
}

/**
 * Opciones del `<select>`: "Todos" y cada modo de la base, en el orden de la
 * API. El elegido entra aunque la base no lo tenga (un enlace con
 * `?gamemode=X`): sin su opcion el `<select>` mostraria "Todos" filtrando.
 */
export function opcionesDeModo(gamemodes, elegido = '') {
  const vistos = new Set()
  const opciones = [{ value: '', label: 'Todos' }]
  for (const modo of [...(gamemodes || []), elegido]) {
    if (!modo || vistos.has(modo)) continue
    vistos.add(modo)
    opciones.push({ value: modo, label: nombreDeModo(modo) })
  }
  return opciones
}

/**
 * Con un solo modo en la base el selector sobra. Pero si llega un enlace con
 * `?gamemode=X` tiene que verse que se esta filtrando, si no la pagina muestra
 * 0 rondas sin nada que lo explique.
 */
export function mostrarSelectorDeModo(gamemodes, elegido) {
  if (elegido) return true
  return new Set((gamemodes || []).filter(Boolean)).size > 1
}

/** Filas de `by_gamemode` con el nombre que se muestra. */
export function filasPorModo(byGamemode) {
  return (byGamemode ?? []).map((row) => ({ ...row, modo: nombreDeModo(row.gamemode) }))
}

/** La tabla solo dice algo si hay con que comparar. */
export function hayVariosModos(byGamemode) {
  return (byGamemode ?? []).length > 1
}
