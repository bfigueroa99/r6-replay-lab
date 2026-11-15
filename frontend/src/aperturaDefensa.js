/**
 * El sitio con el que abres la defensa (panel del Coach, ficha 138): logica
 * pura del panel. Los numeros salen de `/api/positioning/defense-opener/`.
 */

export function hayAperturas(data) {
  return !!data?.matches
}

/**
 * DataTable ordena por clave plana: una fila por mapa y sitio, con `orden` para
 * quedarse con el orden de la API (mapas por aperturas, sitios por aperturas).
 * `poca` marca el winrate abriendo con menos partidas que el corte: se avisa,
 * no se oculta.
 */
export function filasAperturaDefensa(data) {
  const minimo = data?.min_matches || 0
  const filas = []
  for (const mapa of data?.maps || []) {
    for (const sitio of mapa.sites || []) {
      filas.push({
        clave: `${mapa.slug}-${mapa.map_id}-${sitio.site}`,
        orden: filas.length,
        map: mapa.map,
        site: sitio.site,
        opens: sitio.opens || 0,
        opens_share: sitio.opens_share ?? null,
        opens_winrate: sitio.opens_winrate ?? null,
        rest_rounds: sitio.rest_rounds || 0,
        rest_winrate: sitio.rest_winrate ?? null,
        poca: (sitio.opens || 0) < minimo,
      })
    }
  }
  return filas
}

// El mismo redondeo que las columnas de porcentaje (digits: 0); sin winrate no
// hay nada que avisar.
export function textoWinrateApertura(winrate, poca) {
  if (winrate === null || winrate === undefined) return '—'
  return poca ? `${Math.round(winrate)}% · pocas partidas` : `${Math.round(winrate)}%`
}

export function textoAperturas(n) {
  return n === 1 ? '1 partida con apertura de defensa' : `${n || 0} partidas con apertura de defensa`
}

/** Las partidas que se dejan afuera se dicen: sin esto el total no cierra con las partidas filtradas. */
export function textoSinApertura(n) {
  if (!n) return null
  return n === 1
    ? '1 partida con defensa no entra: falta una ronda antes de su primera defensa, o le falta lado o sitio.'
    : `${n} partidas con defensa no entran: falta una ronda antes de su primera defensa, o les falta lado o sitio.`
}
