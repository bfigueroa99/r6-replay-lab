/**
 * Marcas de la timeline de una ronda: la apertura (primera baja de la ronda)
 * y el entry (primera baja de tu equipo). Las reglas son las de
 * `opening_kill`/`opening_death` y `entry_kill` en
 * `replays/analytics/metrics.py`; `casosApertura.json` las prueba de los dos
 * lados, asi que si una cambia, cae el test del otro.
 */

const porOrden = (a, b) => (a.order ?? 0) - (b.order ?? 0)

/**
 * `{ apertura, entry }` con el `order` del evento marcado o `null`.
 * `miEquipo` es tu `team_index`; sin equipo (`undefined` o negativo) solo se
 * marca la apertura. Si el entry es la misma baja que la apertura, va `null`:
 * esa fila ya lleva su chip.
 */
export function marcasDeApertura(ronda, miEquipo) {
  const bajas = (ronda?.events || [])
    .filter((e) => e.kind === 'Kill' || e.kind === 'Death')
    .slice()
    .sort(porOrden)
  const apertura = bajas.length ? bajas[0].order : null
  if (typeof miEquipo !== 'number' || miEquipo < 0) return { apertura, entry: null }

  // Como en metrics.py: un nick que no esta entre los jugadores de la ronda
  // no tiene equipo y no abre por nadie; un teamkill si cuenta como entry.
  const equipo = new Map((ronda.players || []).map((p) => [p.username, p.team_index]))
  const primera = bajas.find((e) => e.kind === 'Kill' && equipo.get(e.actor) === miEquipo)
  const entry = primera ? primera.order : null
  return { apertura, entry: entry === apertura ? null : entry }
}
