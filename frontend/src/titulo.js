/**
 * Titulo del documento segun la ruta. Logica pura, aparte de App.jsx.
 *
 * Con un solo titulo fijo, el historial del navegador, las pestañas y el
 * lector de pantalla no distinguen una pagina de otra (y la ventana de la app
 * de escritorio, que muestra el titulo del documento, tampoco). El nombre de
 * la pagina va adelante: es lo que queda a la vista en una pestaña angosta.
 */

export const APP = 'R6 Replay Lab'

/** Rutas con parametro, que no estan en el menu. */
const CON_PARAMETRO = [
  [/^\/partidas\/[^/]+$/, 'Partida'],
  [/^\/comparar\/[^/]+(\/[^/]+)?$/, 'Comparar partidas'],
  [/^\/jugadores\/[^/]+$/, 'Jugador'],
]

/** `links` es el menu de App.jsx: [{ to, label }]. */
export function tituloDePagina(pathname, links) {
  if (!pathname) return APP
  // React Router no distingue mayusculas ni la barra del final: /COACH/ es el Coach
  const ruta = (pathname.length > 1 ? pathname.replace(/\/+$/, '') : pathname).toLowerCase()
  const delMenu = (links || []).find((link) => link.to === ruta)
  const nombre =
    delMenu?.label ??
    CON_PARAMETRO.find(([patron]) => patron.test(ruta))?.[1] ??
    'Esa página no existe'
  return `${nombre} · ${APP}`
}
