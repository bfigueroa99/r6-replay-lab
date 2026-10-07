/**
 * Los filtros de la barra viven en la URL (`?map=bank&side=Attack`), no en un
 * estado de React: asi sobreviven a recargar, se pueden compartir y el boton
 * de atras hace lo que uno espera. Este modulo traduce en los dos sentidos y
 * no toca el DOM, para poder probarse en node.
 */

/** Las claves que la API entiende. Cualquier otra cosa en la URL se ignora. */
export const CLAVES = ['side', 'map', 'operator', 'site', 'session', 'days', 'since', 'until', 'ranked_only']

/** `?map=bank&ranked_only=1` -> `{ map: 'bank', ranked_only: true }`. */
export function filtrosDesdeQuery(search) {
  const params = new URLSearchParams(search instanceof URLSearchParams ? search.toString() : search || '')
  const filtros = {}
  for (const clave of CLAVES) {
    const valor = params.get(clave)
    if (valor === null || valor === '') continue
    filtros[clave] = clave === 'ranked_only' ? valor === '1' || valor === 'true' : valor
  }
  return filtros
}

/** El inverso: solo lo que tiene valor, en el orden fijo de `CLAVES`. Sin `?`. */
export function queryDesdeFiltros(filtros) {
  const params = new URLSearchParams()
  for (const clave of CLAVES) {
    const valor = filtros?.[clave]
    if (valor === '' || valor === null || valor === undefined || valor === false) continue
    params.set(clave, valor === true ? '1' : String(valor))
  }
  return params.toString()
}

export const hayFiltros = (filtros) => Object.keys(filtrosDesdeQuery(queryDesdeFiltros(filtros))).length > 0

/** Destino para un `<Link>` que conserva (o fija) los filtros. */
export function conFiltros(pathname, filtros) {
  const search = queryDesdeFiltros(filtros)
  return { pathname, search: search ? `?${search}` : '' }
}

/**
 * A donde lleva una senal del coach. Las que traen filtros abren el Resumen
 * con **esos** filtros encima de los activos: son las rondas que respaldan la
 * frase. Las de duelos no tienen filtro posible (el rival no es un filtro de
 * la API) y van a la pagina de Duelos. El resto no enlaza a ningun lado.
 */
export function destinoInsight(insight, filtrosActivos = {}) {
  if (!insight) return null
  if (insight.key === 'operador-rival' || insight.key === 'nemesis') {
    return conFiltros('/duelos', filtrosActivos)
  }
  const propios = insight.filters || {}
  if (!Object.keys(propios).length) return null
  return conFiltros('/', { ...filtrosActivos, ...propios })
}
