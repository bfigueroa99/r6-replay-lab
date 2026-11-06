/**
 * Resumen en texto plano de una sesion de juego, para pegarlo en el chat del
 * grupo al terminar la noche. Sale de una fila de /api/sessions/ que Tendencias
 * ya tiene: ninguna request nueva. Sin React para probarlo con vitest.
 */

// Mismo criterio que `numero` de resumenPartida.js; no se importa para no
// acoplar los dos formatos: si uno cambia el texto, el otro no se entera.
function numero(valor, digitos = 0, sufijo = '') {
  return valor === null || valor === undefined ? '—' : `${Number(valor).toFixed(digitos)}${sufijo}`
}

function lineaCabecera(sesion) {
  // La misma fecha que la columna "Cuando", con el año: el texto sale de la app
  const cuando = (sesion.start || '').slice(0, 16).replace('T', ' ')
  // Una sesion de una partida dura 0 h: decirlo no aporta nada
  return sesion.hours ? `Sesión del ${cuando} · ${sesion.hours} h` : `Sesión del ${cuando}`
}

function lineaResultado(sesion) {
  const partidas = sesion.matches === 1 ? '1 partida' : `${sesion.matches} partidas`
  let texto = `${partidas}: ${sesion.wins}G ${sesion.losses}P`
  if (sesion.undecided > 0) texto += ` ${sesion.undecided} sin resultado`
  return texto
}

function lineaPartida(titulo, partida) {
  return `${titulo}: ${partida.map} · ${partida.score} · rating ${numero(partida.rating, 2)}`
}

export function textoResumenSesion(sesion) {
  const lineas = [
    lineaCabecera(sesion),
    lineaResultado(sesion),
    `Rondas ganadas ${numero(sesion.winrate, 0, '%')} · K/D ${numero(sesion.kd, 2)} · rating ${numero(sesion.rating, 2)}`,
  ]
  if (sesion.best_match) lineas.push(lineaPartida('Mejor partida', sesion.best_match))
  if (sesion.worst_match) lineas.push(lineaPartida('Peor partida', sesion.worst_match))
  return lineas.join('\n')
}
