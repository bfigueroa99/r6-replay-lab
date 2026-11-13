/**
 * Columna "Última vez" de las tablas de rivales de Duelos. En pantalla, la
 * fecha como el perfil del jugador; en el CSV, AAAA-MM-DD para que la planilla
 * la ordene bien.
 */
export function fechaCorta(iso) {
  return iso ? iso.slice(0, 10).split('-').reverse().join('-') : '—'
}

export function fechaCsv(iso) {
  return iso ? iso.slice(0, 10) : ''
}
