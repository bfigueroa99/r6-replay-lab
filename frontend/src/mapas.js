/**
 * Opciones del selector de mapa. Un mapa rehecho (Consulate, Club House) trae
 * sus versiones debajo: el slug elige todas y el `map_id` una sola, que es lo
 * que entiende `?map=` en la API.
 */

// espacios de no separacion: el <select> se come los espacios comunes
const SANGRIA = '  · '

export function opcionesDeMapa(maps) {
  const opciones = []
  for (const mapa of maps || []) {
    opciones.push({ value: mapa.map_slug, label: mapa.map_name })
    for (const version of mapa.versions || []) {
      opciones.push({ value: String(version.map_id), label: SANGRIA + version.label })
    }
  }
  return opciones
}
