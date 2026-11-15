/**
 * Que URL es la app y cual puede salir al navegador del sistema.
 *
 * Aparte de main.cjs y sin Electron adentro para poder probarlo con vitest
 * (`src/electronOrigen.test.js`): son las dos preguntas de las que cuelga que
 * la ventana no termine mostrando un sitio ajeno con el puente del preload a
 * mano, ni lanzando un programa del sistema.
 *
 * Se compara el origen parseado y no el texto: con `startsWith`,
 * `http://127.0.0.1:8000@otro.sitio/` empieza igual que la app y es otro host.
 */

function parsear(url) {
  try {
    return new URL(String(url))
  } catch {
    return null
  }
}

/** True si `url` tiene el mismo origen (esquema, host y puerto) que la app. */
function esDeLaApp(url, appUrl) {
  const app = parsear(appUrl)
  const destino = parsear(url)
  // "null" es el origen opaco de file:, data: y compania: no identifica a nadie
  if (!app || !destino || app.origin === 'null') return false
  return destino.origin === app.origin
}

/**
 * True si `url` se puede pasar a `shell.openExternal`: solo http y https.
 *
 * Cualquier otro esquema lo resuelve el sistema operativo: un `file:` abre (o
 * ejecuta) el archivo, y un protocolo registrado lanza su programa.
 */
function esWebExterna(url) {
  const destino = parsear(url)
  return Boolean(destino) && (destino.protocol === 'http:' || destino.protocol === 'https:')
}

module.exports = { esDeLaApp, esWebExterna }
