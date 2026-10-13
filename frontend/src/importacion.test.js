import { describe, expect, it } from 'vitest'

import { avisoAutomatico, etiquetaImportacion } from './importacion.js'

const terminado = (extra = {}) => ({
  running: false,
  origin: 'auto',
  finished_at: '2026-10-07T21:10:00',
  count: 1,
  errors: 0,
  ...extra,
})

describe('etiquetaImportacion', () => {
  it('sin nada corriendo invita a importar', () => {
    expect(etiquetaImportacion(null, false)).toBe('Importar replays')
    expect(etiquetaImportacion(terminado(), false)).toBe('Importar replays')
  })

  it('el boton cuenta la que esta leyendo, no las que ya termino', () => {
    expect(etiquetaImportacion({ running: true, done: 0, total: 3 }, true)).toBe('Importando 1 de 3')
  })

  it('nunca pasa del total', () => {
    expect(etiquetaImportacion({ running: true, done: 3, total: 3 }, true)).toBe('Importando 3 de 3')
  })

  it('sin total todavia no inventa numeros', () => {
    expect(etiquetaImportacion(null, true)).toBe('Importando...')
  })

  it('la automatica se distingue de la del boton', () => {
    expect(etiquetaImportacion({ running: true, done: 1, total: 2, origin: 'auto' }, false)).toBe(
      'Importando sola 2 de 2',
    )
  })
})

describe('avisoAutomatico', () => {
  const antes = terminado({ finished_at: '2026-10-07T20:00:00' })

  it('anuncia la partida que entro sola', () => {
    expect(avisoAutomatico(antes, terminado())).toBe('Se importó sola 1 partida nueva.')
  })

  it('en plural cuando son varias', () => {
    expect(avisoAutomatico(antes, terminado({ count: 3 }))).toBe(
      'Se importaron solas 3 partidas nuevas.',
    )
  })

  it('en la primera lectura no anuncia lo que se importo antes de abrir', () => {
    expect(avisoAutomatico(null, terminado())).toBeNull()
  })

  it('no repite el aviso de la misma importacion', () => {
    expect(avisoAutomatico(terminado(), terminado())).toBeNull()
  })

  it('mientras corre no dice nada todavia', () => {
    expect(avisoAutomatico(antes, terminado({ running: true, finished_at: null }))).toBeNull()
  })

  it('la del boton ya la anuncia el boton', () => {
    expect(avisoAutomatico(antes, terminado({ origin: 'manual' }))).toBeNull()
  })

  it('los errores mandan a Datos', () => {
    expect(avisoAutomatico(antes, terminado({ count: 2, errors: 1 }))).toBe(
      'Se importaron solas 2 partidas nuevas. 1 con error: el detalle está en Datos.',
    )
    expect(avisoAutomatico(antes, terminado({ count: 0, errors: 1 }))).toBe(
      'No se pudo importar sola una partida: el detalle está en Datos.',
    )
  })
})
