/**
 * Filtros globales en la query de la URL (ficha 96).
 *
 * El estado sigue en App, pero se copia a la URL para que recargar, Atras y
 * un marcador devuelvan la misma vista. Todo lo que entra por la URL pasa por
 * aca y se valida: un enlace pegado a mano no puede mandarle a la API algo
 * que la barra no sabria mostrar.
 */

/** Las claves de `_filters` del backend, en orden fijo: la query sale canonica. */
export const CLAVES_DE_URL = [
  'side',
  'map',
  'operator',
  'site',
  'session',
  'days',
  'since',
  'until',
  'match_type',
  'gamemode',
  'ranked_only',
]

/** Paginas con barra de filtros global; el resto no lee ni escribe la query. */
export const RUTAS_CON_FILTROS = ['/', '/coach', '/operadores', '/companeros', '/duelos', '/tendencias', '/partidas']

const LARGO_TEXTO = 64

/**
 * Los periodos del select de Filters.jsx: otro `days` la API lo entiende, pero
 * la barra mostraria "Todo el historial" filtrando otra cosa.
 */
export const DIAS_DEL_PERIODO = ['7', '30', '90']

export function usaFiltros(pathname) {
  if (!pathname) return false
  const limpio = pathname.length > 1 ? pathname.replace(/\/+$/, '') || '/' : pathname
  return RUTAS_CON_FILTROS.includes(limpio)
}

/** `2026-02-31` no existe: Date lo corre a marzo, y eso lo delata. */
function fechaValida(texto) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(texto)) return false
  const fecha = new Date(`${texto}T00:00:00Z`)
  return !Number.isNaN(fecha.getTime()) && fecha.toISOString().slice(0, 10) === texto
}

function texto(valor) {
  const limpio = String(valor).trim()
  return limpio && limpio.length <= LARGO_TEXTO ? limpio : null
}

/** El valor tal como se guarda en el estado, o `null` si no vale. */
function validar(clave, valor) {
  if (valor === undefined || valor === null || valor === '' || valor === false) return null
  if (clave === 'ranked_only') return valor === true || valor === '1' || valor === 'true' ? true : null
  const crudo = String(valor).trim()
  switch (clave) {
    case 'side':
      return crudo === 'Attack' || crudo === 'Defense' ? crudo : null
    case 'days':
      return DIAS_DEL_PERIODO.includes(crudo) ? crudo : null
    case 'session':
      return /^\d{1,5}$/.test(crudo) ? crudo : null
    case 'since':
    case 'until':
      return fechaValida(crudo) ? crudo : null
    default:
      return texto(crudo)
  }
}

function limpiar(entradas) {
  const filtros = {}
  for (const clave of CLAVES_DE_URL) {
    const valor = validar(clave, entradas(clave))
    if (valor !== null) filtros[clave] = valor
  }
  // como elegirPeriodo de Filters.jsx: con fechas no hay "ultimos N dias", y
  // el backend igual ignora days si viene since
  if (filtros.since || filtros.until) delete filtros.days
  return filtros
}

/** Filtros validos de una query (`'?a=b'`, `'a=b'` o `URLSearchParams`). */
export function filtrosDeUrl(search) {
  const params = search instanceof URLSearchParams ? search : new URLSearchParams(search || '')
  return limpiar((clave) => (params.has(clave) ? params.get(clave) : null))
}

/** Query sin `?`, solo con lo que vale; `''` sin filtros. */
export function queryDeFiltros(filtros) {
  const validos = limpiar((clave) => (filtros ? filtros[clave] : null))
  const params = new URLSearchParams()
  for (const clave of CLAVES_DE_URL) {
    if (clave in validos) params.set(clave, validos[clave] === true ? '1' : validos[clave])
  }
  return params.toString()
}

/** El `to` de un `NavLink` o `navigate` con los filtros en la query. */
export function conFiltros(pathname, filtros) {
  const query = queryDeFiltros(filtros)
  return { pathname, search: query ? `?${query}` : '' }
}

/** Corta los bucles de sincronizacion: mismo filtro aunque cambie el orden o haya vacios. */
export function mismosFiltros(a, b) {
  return queryDeFiltros(a) === queryDeFiltros(b)
}
