/**
 * Logica pura de la ruleta de operadores: que entra en la rueda, donde para y
 * de que color va cada gajo. No toca el DOM ni el canvas para poder probarse
 * en node; el dibujo vive en `components/Rueda.jsx`.
 */

export const VUELTA = 2 * Math.PI

/** El puntero esta arriba del todo. En canvas 0 es la derecha y crece en sentido horario. */
export const PUNTERO = (3 * Math.PI) / 2

export const LADOS = [
  { key: 'all', label: 'Todos' },
  { key: 'Attack', label: 'Ataque' },
  { key: 'Defense', label: 'Defensa' },
]

export const AJUSTES_DEFAULT = {
  lado: 'all',
  duracion: 4,
  quitarElegido: false,
  streamer: false,
  fondo: '#00ff00',
  excluidos: [],
}

export const AJUSTES_KEY = 'ruleta'

/**
 * Lee los ajustes guardados sin confiar en ellos: lo que haya en localStorage
 * pudo escribirlo una version anterior con otras claves o tipos.
 */
export function normalizarAjustes(raw) {
  const base = { ...AJUSTES_DEFAULT }
  if (!raw || typeof raw !== 'object') return base
  if (LADOS.some((l) => l.key === raw.lado)) base.lado = raw.lado
  const duracion = Number(raw.duracion)
  if (Number.isFinite(duracion)) base.duracion = Math.min(10, Math.max(1, duracion))
  if (typeof raw.quitarElegido === 'boolean') base.quitarElegido = raw.quitarElegido
  if (typeof raw.streamer === 'boolean') base.streamer = raw.streamer
  if (typeof raw.fondo === 'string' && /^#[0-9a-f]{6}$/i.test(raw.fondo)) base.fondo = raw.fondo
  if (Array.isArray(raw.excluidos)) {
    base.excluidos = [...new Set(raw.excluidos.filter((n) => typeof n === 'string' && n))]
  }
  return base
}

/**
 * Lo que de verdad gira: el catalogo filtrado por lado y sin los excluidos.
 * Con "Todos", primero los atacantes y despues los defensores, cada grupo en
 * orden alfabetico: asi la rueda queda partida en dos mitades de color y se
 * lee de un vistazo.
 */
export function operadoresEnRueda(catalogo, lado, excluidos = []) {
  const fuera = new Set(excluidos)
  const orden = { Attack: 0, Defense: 1 }
  return (catalogo || [])
    .filter((op) => (lado === 'all' || op.side === lado) && !fuera.has(op.name))
    .sort(
      (a, b) =>
        (orden[a.side] ?? 2) - (orden[b.side] ?? 2) ||
        a.name.localeCompare(b.name, 'es', { sensitivity: 'base' }),
    )
}

/** Indice del gajo que queda bajo el puntero con la rueda girada `angulo` radianes. */
export function gajoBajoPuntero(angulo, cantidad) {
  if (!cantidad || cantidad < 1) return -1
  const relativo = (((PUNTERO - angulo) % VUELTA) + VUELTA) % VUELTA
  return Math.floor(relativo / (VUELTA / cantidad)) % cantidad
}

/** Entre 6 y 10 vueltas completas mas un resto al azar, para que no se adivine. */
export function anguloFinal(desde, azar = Math.random) {
  return desde + VUELTA * (6 + 4 * azar())
}

/** Arranca rapido y frena suave, como una rueda de verdad. */
export const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3)

const MATIZ = { Attack: 24, Defense: 212 }

/** Alterna dos tonos del color del lado para que se distingan los gajos vecinos. */
export function colorGajo(indice, lado) {
  const matiz = MATIZ[lado] ?? 150
  return `hsl(${matiz} 58% ${indice % 2 === 0 ? 26 : 34}%)`
}

/**
 * Tamano de la letra de cada gajo: cuanto mas operadores, mas chica. Se mide
 * por el espacio que tiene cada gajo en el borde y no por el ancho total.
 */
export function tamanoLetra(radio, cantidad) {
  if (!cantidad) return 16
  const porGajo = (VUELTA * radio) / cantidad
  return Math.max(10, Math.min(18, Math.round(porGajo * 0.62)))
}
