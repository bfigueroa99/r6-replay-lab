/**
 * Tabla "Clutches de tus compañeros" de Compañeros: `teammate_clutches` de
 * `/api/teammates/` con tu fila arriba como referencia.
 */

/** Tus clutches y los de cada compañero habitual, o `[]` si no hay compañeros con intentos. */
export function filasClutchCompaneros(data) {
  if (!data?.rows?.length) return []
  const yo = data.me ?? { attempts: 0, won: 0, pct: null, low_sample: true }
  // `orden` fija el de la API en la tabla (tu fila arriba) hasta que se ordene a mano
  return [
    { clave: 'yo', nombre: 'Tú', esYo: true, playerId: null, ...yo },
    ...data.rows.map((f) => ({
      clave: f.player_id,
      nombre: f.username,
      esYo: false,
      playerId: f.player_id,
      attempts: f.attempts,
      won: f.won,
      pct: f.pct,
      low_sample: f.low_sample,
    })),
  ].map((fila, orden) => ({ ...fila, orden }))
}
