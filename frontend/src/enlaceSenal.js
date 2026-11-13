/**
 * Enlace "Ver esas rondas" de una señal del Coach: la pagina que la señal
 * nombra, con sus filtros sumados a los de la barra.
 */

import { conFiltros } from './filtrosUrl.js'

const DESTINOS = ['/', '/duelos']

/** El `to` del enlace, o `null` si la señal es general o no sabemos a donde abrirla. */
export function enlaceDeSenal(insight, filtros) {
  const target = insight?.target || '/'
  const propios = insight?.filters || {}
  if (!DESTINOS.includes(target)) return null
  // en el Resumen sin filtros propios el enlace abriria la misma vista general
  if (target === '/' && !Object.keys(propios).length) return null
  // los de la señal pisan los de la barra: "Kafe es tu peor mapa" abre Kafe aunque mires Bank
  return conFiltros(target, { ...filtros, ...propios })
}

export function textoDelEnlace(insight) {
  return insight?.target === '/duelos' ? 'Ver en Duelos' : 'Ver esas rondas'
}
