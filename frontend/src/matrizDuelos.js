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

/** Tu `team_index` en una ronda: el de tu fila si estas; si no, el de la partida. */
function tuEquipoEn(ronda, miEquipo) {
  const yo = (ronda.players || []).find((p) => p.is_me)
  return yo ? yo.team_index : miEquipo
}

/**
 * `{ mios, rivales, aFavor, enContra, total }` para `rondas`. Con
 * `soloAperturas` cuenta solo la primera baja entre rivales de cada ronda: un
 * teamkill no abre la ronda. `miEquipo` es tu `team_index` cuando una ronda no
 * trae tu fila.
 *
 * El lado de cada baja se decide ronda por ronda: el mismo nick puede caer en
 * equipos distintos en dos rondas (el parser reparte equipos por orden de
 * lectura), y asi toda baja contada aparece en una de las dos tablas.
 */
export function matrizDeDuelos(rondas, { soloAperturas = false, miEquipo } = {}) {
  const aFavor = {}
  const enContra = {}
  const mios = new Map()
  const rivales = new Map()
  const suma = (grupo, nombre, n) => grupo.set(nombre, (grupo.get(nombre) || 0) + n)
  let total = 0
  for (const ronda of rondas || []) {
    const tuyo = tuEquipoEn(ronda, miEquipo)
    for (const p of ronda.players || []) {
      suma(p.team_index === tuyo ? mios : rivales, p.username, 0)
    }
    const bajas = bajasEntreRivales(ronda)
    const equipo = new Map((ronda.players || []).map((p) => [p.username, p.team_index]))
    for (const e of soloAperturas ? bajas.slice(0, 1) : bajas) {
      const tuya = equipo.get(e.actor) === tuyo
      const celdas = tuya ? aFavor : enContra
      const c = (celdas[clave(e.actor, e.target)] ??= { bajas: 0, headshots: 0 })
      c.bajas += 1
      if (e.headshot) c.headshots += 1
      suma(tuya ? mios : rivales, e.actor, 1)
      suma(tuya ? rivales : mios, e.target, 0)
      total += 1
    }
  }
  // Mas bajas primero y nick como desempate, para que el orden sea estable.
  const ordenar = (grupo) =>
    [...grupo.keys()].sort((a, b) => grupo.get(b) - grupo.get(a) || a.localeCompare(b))
  return { mios: ordenar(mios), rivales: ordenar(rivales), aFavor, enContra, total }
}

/**
 * Bajas y headshots de `autor` sobre `victima` en una direccion
 * (`'aFavor'`: tu equipo mata; `'enContra'`: el rival mata); ceros si nunca
 * se cruzaron.
 */
export function celda(matriz, direccion, autor, victima) {
  return matriz[direccion][clave(autor, victima)] || { bajas: 0, headshots: 0 }
}
