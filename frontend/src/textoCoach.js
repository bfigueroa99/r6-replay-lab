/**
 * Texto plano de las señales del Coach, para pegar en el chat del equipo.
 * Los grupos y el formato del numero viven aca y la pagina los importa: lo
 * copiado sale en el mismo orden y con los mismos numeros que se ven.
 */

import { CLAVES_DE_URL } from './filtrosUrl.js'
import { nombreDeModo } from './modoDeJuego.js'
import { hayFiltros } from './tipoPartida.js'

export const GRUPOS_COACH = [
  { key: 'alta', title: 'Prioridad alta', hint: 'Lo que más te está costando rondas.' },
  { key: 'media', title: 'Para trabajar', hint: 'Patrones claros con muestra suficiente.' },
  { key: 'baja', title: 'Para tener en el radar', hint: 'Señales más débiles o de contexto.' },
  { key: 'positivo', title: 'Tus fortalezas', hint: 'Apóyate en esto al elegir rol y picks.' },
]

/** `—` para nulo; 2 decimales debajo de 10 si no es entero. */
export function formatoCoach(value) {
  if (value === null || value === undefined) return '—'
  if (typeof value !== 'number') return value
  return Number(value).toFixed(Math.abs(value) < 10 && !Number.isInteger(value) ? 2 : 0)
}

const NOMBRES_DE_FILTRO = {
  side: (v) => (v === 'Defense' ? 'Solo defensa' : 'Solo ataque'),
  map: (v) => `Mapa: ${v}`,
  operator: (v) => `Operador: ${v}`,
  site: (v) => `Sitio: ${v}`,
  session: (v) => `Sesión ${Number(v) + 1}`,
  days: (v) => `Últimos ${v} días`,
  since: (v) => `Desde ${v}`,
  until: (v) => `Hasta ${v}`,
  match_type: (v) => `Tipo: ${v}`,
  gamemode: (v) => `Modo: ${nombreDeModo(v)}`,
  ranked_only: () => 'Solo ranked',
}

/** Los filtros activos en el orden de la URL, o "Sin filtros". */
export function lineaDeFiltros(filtros) {
  if (!hayFiltros(filtros)) return 'Sin filtros'
  const partes = CLAVES_DE_URL.filter((clave) => filtros[clave] && NOMBRES_DE_FILTRO[clave]).map((clave) =>
    NOMBRES_DE_FILTRO[clave](filtros[clave]),
  )
  return partes.length ? `Filtros: ${partes.join(' · ')}` : 'Sin filtros'
}

/** La linea de numeros de una señal, con las mismas condiciones que `.meta` de la pagina. */
function lineaDeNumeros(senal) {
  const partes = []
  if (senal.metric) {
    const tieneReferencia = senal.baseline !== null && senal.baseline !== undefined
    const referencia = tieneReferencia ? ` (referencia ${formatoCoach(senal.baseline)})` : ''
    partes.push(`${senal.metric}: ${formatoCoach(senal.value)}${referencia}`)
  }
  if (senal.sample) partes.push(`muestra: ${senal.sample} rondas`)
  if (senal.scope && senal.scope !== 'general') partes.push(`alcance: ${senal.scope}`)
  return partes.join(' · ')
}

/** Texto para el portapapeles, o `null` si no hay señales que copiar. */
export function textoCoach(insights, filtros) {
  if (!insights?.length) return null
  const lineas = [`Coach · ${lineaDeFiltros(filtros)}`]
  for (const grupo of GRUPOS_COACH) {
    const senales = insights.filter((i) => i.severity === grupo.key)
    if (!senales.length) continue
    lineas.push('', grupo.title.toUpperCase())
    for (const senal of senales) {
      lineas.push(`- ${senal.title}`, `  ${senal.detail}`, `  Qué hacer: ${senal.action}`)
      const numeros = lineaDeNumeros(senal)
      if (numeros) lineas.push(`  ${numeros}`)
    }
  }
  return lineas.map((linea) => linea.trimEnd()).join('\n')
}
