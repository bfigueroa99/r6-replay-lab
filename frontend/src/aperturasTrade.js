/**
 * Filas del panel "Aperturas que pesan" del Resumen (ficha 76). Separado de la
 * pagina para probar la logica sin montarla. `aperturas.js` es otra cosa: las
 * marcas de apertura del timeline.
 */

const GRUPOS = [
  { key: 'kill_clean', label: 'Ganada limpia', rondas: 'opening_kills_clean', winrate: 'winrate_opening_kill_clean' },
  { key: 'kill_traded', label: 'Ganada devuelta', rondas: 'opening_kills_traded', winrate: 'winrate_opening_kill_traded' },
  { key: 'death_traded', label: 'Perdida vengada', rondas: 'opening_deaths_traded', winrate: 'winrate_opening_death_traded' },
  { key: 'death_untraded', label: 'Perdida sin vengar', rondas: 'opening_deaths_untraded', winrate: 'winrate_opening_death_untraded' },
]

/**
 * Cuatro filas en orden fijo: primero las ganadas y despues las perdidas.
 * `orden` lo sostiene al ordenar la tabla. Un backend sin las claves nuevas
 * (respuesta vieja cacheada) da `null` en vez de romper.
 */
export function filasDeAperturasConTrade(overall) {
  return GRUPOS.map((g, orden) => ({
    key: g.key,
    label: g.label,
    orden,
    rondas: overall?.[g.rondas] ?? null,
    winrate: overall?.[g.winrate] ?? null,
  }))
}
