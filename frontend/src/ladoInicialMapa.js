/**
 * Filas de la tabla "Lado inicial por mapa" de Tendencias. Separado de la
 * pagina para probar la logica sin montarla.
 */

/**
 * Partidas con resultado que necesita un lado para tener porcentaje. Espejo de
 * `MIN_PARTIDAS_LADO_INICIAL` de `aggregates.py`: la respuesta es una lista y
 * no trae el minimo.
 */
export const MIN_PARTIDAS_LADO = 3

const VEREDICTOS = {
  ataque: 'Mejor arrancando en ataque',
  defensa: 'Mejor arrancando en defensa',
  ruido: 'Dentro del ruido',
}

/** Texto del veredicto; sin veredicto es que algun lado no llego al minimo. */
export function textoVeredicto(fila) {
  return VEREDICTOS[fila?.verdict] ?? 'Poca muestra'
}

/** Aplana cada fila del backend para el `DataTable` (una columna por campo). */
export function filasLadoInicialMapa(filas) {
  return (filas || []).map((fila) => ({
    slug: fila.slug,
    map_id: fila.map_id,
    map: fila.map,
    matches: fila.matches,
    attack_matches: fila.attack?.matches ?? 0,
    attack_winrate: fila.attack?.winrate ?? null,
    defense_matches: fila.defense?.matches ?? 0,
    defense_winrate: fila.defense?.winrate ?? null,
    delta: fila.delta ?? null,
    margin: fila.margin ?? null,
    verdict: fila.verdict ?? null,
    veredicto: textoVeredicto(fila),
  }))
}
