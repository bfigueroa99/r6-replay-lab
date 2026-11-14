/**
 * Marca de prorroga en el selector de rondas del detalle (ficha 136). Misma
 * regla que `celdasDeTira` de la tira de Partidas, pero sobre las rondas del
 * detalle: aquella recibe el `strip` del listado y arma otros campos.
 */

/** Una entrada por ronda, en el mismo orden: el JSX las recorre por indice junto a `rounds`. */
export function pestanasDeRondas(rounds) {
  let enProrroga = false
  return (rounds || []).map((ronda) => {
    const prorroga = Boolean(ronda.overtime)
    const corteAntes = prorroga && !enProrroga
    if (prorroga) enProrroga = true
    return { prorroga, corteAntes }
  })
}
