/**
 * Muertes por headshot (panel de Duelos): de tus muertes a manos de rivales,
 * cuantas fueron headshot, al lado del mismo numero de tus companeros en las
 * mismas rondas. Los numeros salen de `headshot_deaths` de `/api/duels/`.
 */

import { MUESTRA_CORTE } from './muestra.js'

const GRUPOS = [
  { clave: 'me', grupo: 'Tú' },
  { clave: 'teammates', grupo: 'Tus compañeros' },
]

function celda(valor) {
  return { pct: valor?.pct ?? null, with_data: valor?.with_data || 0 }
}

/**
 * Una fila por grupo, Tú primero; `orden` lo fija para la tabla, que si no
 * ordenaria por el nombre. Vacio si nadie tiene muertes con dato: la nota dice
 * mas que una tabla de rayas.
 */
export function filasMuertesHeadshot(data) {
  const filas = GRUPOS.map(({ clave, grupo }, orden) => ({
    clave,
    grupo,
    orden,
    ataque: celda(data?.[clave]?.Attack),
    defensa: celda(data?.[clave]?.Defense),
    total: celda(data?.[clave]?.total),
  }))
  return filas.some((fila) => fila.total.with_data > 0) ? filas : []
}

/** "67% (3)": el porcentaje y sobre cuantas muertes con dato; raya sin dato. */
export function textoCelda(valor) {
  if (!valor?.with_data || valor.pct === null || valor.pct === undefined) return '—'
  // el mismo redondeo que `pct` de ui.jsx, sin atar la logica a los componentes
  return `${Number(valor.pct).toFixed(0)}% (${valor.with_data})`
}

/** Alguna celda con muertes con dato pero menos que el corte comun de muestra. */
export function conPocaMuestra(filas, minimo = MUESTRA_CORTE) {
  return (filas || []).some((fila) =>
    [fila.ataque, fila.defensa, fila.total].some((c) => c.with_data > 0 && c.with_data < minimo),
  )
}
