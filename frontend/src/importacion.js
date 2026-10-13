/**
 * Que decir de la importacion en la cabecera. Logica pura, aparte de App.jsx,
 * para poder probarla sin DOM: App solo le pasa lo que devuelve
 * /api/import/progress/.
 *
 * Hay dos origenes. `manual` es el boton, que App ya sigue paso a paso.
 * `auto` es el vigilante del backend, que importa solo al terminar cada
 * partida: la UI no lo lanzo, asi que se entera preguntando cada tanto.
 */

const partidas = (n) => (n === 1 ? '1 partida nueva' : `${n} partidas nuevas`)

/** Texto del boton de importar segun lo que este corriendo. */
export function etiquetaImportacion(job, importando) {
  if (!importando && !job?.running) return 'Importar replays'
  const prefijo = importando ? 'Importando' : 'Importando sola'
  if (!job?.total) return `${prefijo}...`
  return `${prefijo} ${Math.min(job.done + 1, job.total)} de ${job.total}`
}

/**
 * Aviso cuando termina una importacion automatica, o null si no hay nada que
 * decir. `anterior` es lo ultimo que se vio: sin el (primera lectura al abrir
 * la pagina) no se anuncia nada, porque eso ya se importo antes de mirar.
 */
export function avisoAutomatico(anterior, actual) {
  if (!anterior || !actual) return null
  if (actual.origin !== 'auto' || actual.running || !actual.finished_at) return null
  if (actual.finished_at === anterior.finished_at) return null

  const ok = actual.count || 0
  const errores = actual.errors || 0
  if (!ok && !errores) return null
  if (!ok) {
    const cuantas = errores === 1 ? 'una partida' : `${errores} partidas`
    return `No se pudo importar sola ${cuantas}: el detalle está en Datos.`
  }
  const conError = errores ? ` ${errores} con error: el detalle está en Datos.` : ''
  return `${ok === 1 ? 'Se importó sola' : 'Se importaron solas'} ${partidas(ok)}.${conError}`
}
