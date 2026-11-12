// Repetir el sitio tras perderlo en defensa (ficha 107): logica pura del panel del Coach.

const CASOS = [
  { clave: 'repeat', titulo: 'Repite el sitio' },
  { clave: 'switch', titulo: 'Cambia de sitio' },
]

export function hayPares(data) {
  return !!data?.pairs
}

// `poca` no oculta el winrate: lo marca, como los cortes de Tendencias.
export function casosRepetirSitio(total, minRondas) {
  return CASOS.map(({ clave, titulo }) => {
    const caso = total?.[clave] || {}
    const rondas = caso.rounds || 0
    return { clave, titulo, rounds: rondas, winrate: caso.winrate ?? null, poca: rondas < (minRondas || 0) }
  })
}

export function textoPares(n) {
  return n === 1
    ? '1 ronda perdida en defensa seguida de otra'
    : `${n || 0} rondas perdidas en defensa seguidas de otra`
}

// DataTable ordena por clave plana: se aplanan los dos casos de cada mapa.
export function filasPorMapa(data) {
  return (data?.maps || []).map((m) => ({
    slug: m.slug,
    map_id: m.map_id,
    map: m.map,
    repeat_rounds: m.repeat?.rounds || 0,
    repeat_winrate: m.repeat?.winrate ?? null,
    switch_rounds: m.switch?.rounds || 0,
    switch_winrate: m.switch?.winrate ?? null,
  }))
}
