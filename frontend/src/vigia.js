/**
 * Logica del vigia: la app importa sola las partidas nuevas mientras esta
 * abierta, igual que `manage.py watch_replays` pero sin consola. Aca va lo que
 * se puede probar sin React: que leer de localStorage y que carpetas disparan
 * una importacion.
 */

export const VIGIA_KEY = 'vigia'

/** Cada cuanto se pregunta a la API si hay partidas listas. */
export const VIGIA_MS = 30_000

/**
 * Si el vigia esta encendido. Por defecto si: la app instalada tiene que
 * mostrar la ultima partida sin que nadie toque un boton. Lo guardado solo
 * vale si es exactamente 'off': cualquier otra cosa (nada, basura de una
 * version anterior) es el default.
 */
export function leerVigia(storage) {
  try {
    return storage.getItem(VIGIA_KEY) !== 'off'
  } catch {
    return true
  }
}

export function guardarVigia(storage, encendido) {
  try {
    storage.setItem(VIGIA_KEY, encendido ? 'on' : 'off')
  } catch {
    /* sin localStorage (modo privado) dura la sesion y listo */
  }
}

/**
 * Carpetas listas que todavia no se intentaron en esta sesion.
 *
 * Se recuerda lo intentado para que una carpeta corrupta no dispare una
 * importacion fallida cada 30 segundos: se intenta una vez por sesion y queda
 * registrada en el log de Datos, que es donde hay que mirarla.
 */
export function nuevasParaImportar(listas, intentadas) {
  return (listas || []).filter((carpeta) => !intentadas.has(carpeta))
}
