/**
 * Matriz de duelos de una partida: quien mato a quien entre los dos equipos.
 * Se arma en el navegador con las rondas de `/api/matches/<id>/`; separado
 * del componente para probar la logica sin montarlo.
 */

const clave = (autor, victima) => `${autor}\u0000${victima}`

/** Bajas entre rivales de una ronda, en orden del feed. */
function bajasEntreRivales(ronda) {
  // Los eventos traen solo nombres; el equipo sale de los jugadores de la
  // misma ronda, donde un nick no puede estar en los dos lados.
  const equipo = new Map((ronda.players || []).map((p) => [p.username, p.team_index]))
  return (ronda.events || [])
    .filter((e) => e.kind === 'Kill')
    .slice()
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
    .filter((e) => {
      if (!e.actor || !e.target) return false
      if (!equipo.has(e.actor) || !equipo.has(e.target)) return false
      return equipo.get(e.actor) !== equipo.get(e.target)
    })
}

/**
 * `{ mios, rivales, celdas, total }` para `rondas`. Con `soloAperturas`
 * cuenta solo la primera baja entre rivales de cada ronda: un teamkill no
 * abre la ronda. `miEquipo` es el `team_index` de tu equipo.
 */
export function matrizDeDuelos(rondas, { soloAperturas = false, miEquipo } = {}) {
  const celdas = {}
  const equipoDe = new Map()
  const bajasDe = new Map()
  let total = 0
  for (const ronda of rondas || []) {
    for (const p of ronda.players || []) {
      if (!equipoDe.has(p.username)) equipoDe.set(p.username, p.team_index)
    }
    const bajas = bajasEntreRivales(ronda)
    for (const e of soloAperturas ? bajas.slice(0, 1) : bajas) {
      const k = clave(e.actor, e.target)
      const celda = (celdas[k] ??= { bajas: 0, headshots: 0 })
      celda.bajas += 1
      if (e.headshot) celda.headshots += 1
      bajasDe.set(e.actor, (bajasDe.get(e.actor) || 0) + 1)
      total += 1
    }
  }
  // Mas bajas primero y nick como desempate, para que el orden sea estable.
  const ordenar = (nombres) =>
    nombres.sort((a, b) => (bajasDe.get(b) || 0) - (bajasDe.get(a) || 0) || a.localeCompare(b))
  const nombres = [...equipoDe.keys()]
  return {
    mios: ordenar(nombres.filter((n) => equipoDe.get(n) === miEquipo)),
    rivales: ordenar(nombres.filter((n) => equipoDe.get(n) !== miEquipo)),
    celdas,
    total,
  }
}

/** Bajas y headshots de `autor` sobre `victima`; ceros si nunca se cruzaron. */
export function celda(matriz, autor, victima) {
  return matriz.celdas[clave(autor, victima)] || { bajas: 0, headshots: 0 }
}
