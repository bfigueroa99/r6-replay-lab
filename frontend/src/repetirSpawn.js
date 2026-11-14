// Repetir o cambiar el spawn de ataque tras perder (ficha 128): logica pura del panel del Coach.

// Orden fijo: "Tras ganar" es la base con la que se compara "Tras perder".
const TRAMOS = [
  { tras: 'after_loss', tramo: 'Tras perder' },
  { tras: 'after_win', tramo: 'Tras ganar' },
]

export function hayParesSpawn(data) {
  return !!data?.pairs
}

export function textoParesSpawn(n) {
  return n === 1 ? '1 par de rondas de ataque seguidas' : `${n || 0} pares de rondas de ataque seguidas`
}

// DataTable ordena por clave plana: se aplanan los dos casos de cada tramo.
export function filasRepetirSpawn(data) {
  const minimo = data?.min_rounds || 0
  return TRAMOS.map(({ tras, tramo }, orden) => {
    const bloque = data?.[tras] || {}
    const fila = { tras, tramo, orden }
    for (const caso of ['repeat', 'switch']) {
      const rondas = bloque[caso]?.rounds || 0
      fila[`${caso}_rounds`] = rondas
      fila[`${caso}_winrate`] = bloque[caso]?.winrate ?? null
      fila[`${caso}_poca`] = rondas < minimo
    }
    return fila
  })
}
