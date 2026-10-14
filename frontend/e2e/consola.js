/**
 * Recolecta los errores de consola y las excepciones de una pagina.
 *
 * Esto es el corazon del e2e y no un extra. El item #17 del roadmap dejo la
 * leccion escrita: al sacar el grafico del Resumen se fue tambien un import que
 * el panel de salud seguia usando, **el build no dijo nada y los tests tampoco**
 * (era un error de runtime en una pagina que ningun test renderiza) y lo mostro
 * la consola del navegador. Esta funcion es esa consola, automatizada.
 */
export function vigilarConsola(page) {
  const errores = []
  page.on('console', (mensaje) => {
    if (mensaje.type() === 'error') errores.push(mensaje.text())
  })
  page.on('pageerror', (error) => errores.push(`pageerror: ${error.message}`))
  page.on('requestfailed', (request) => {
    // favicon y compania no importan; lo que importa es que la app pida algo
    // suyo y no este
    const url = request.url()
    if (url.includes('/api/') || url.includes('/assets/')) {
      errores.push(`request fallida: ${url} (${request.failure()?.errorText})`)
    }
  })
  return errores
}

/**
 * Junta todo lo que la pagina pide fuera de la app. "Nada sale a la red sin un
 * clic" (CLAUDE.md): un enlace a un sitio de afuera se abre con un clic, pero
 * renderizarlo no puede bajar nada de ese sitio, ni una miniatura.
 */
export function vigilarRed(page, base) {
  const afuera = []
  page.on('request', (request) => {
    if (!request.url().startsWith(base)) afuera.push(request.url())
  })
  return afuera
}
