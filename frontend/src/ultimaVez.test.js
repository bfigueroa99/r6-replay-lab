import { describe, expect, it } from 'vitest'
import { fechaCorta, fechaCsv } from './ultimaVez.js'

describe('ultimaVez', () => {
  it('fechaCorta da dia, mes y año como el perfil del jugador', () => {
    expect(fechaCorta('2026-09-01T21:30:00')).toBe('01-09-2026')
  })

  it('fechaCorta sin fecha da guion', () => {
    expect(fechaCorta(null)).toBe('—')
    expect(fechaCorta(undefined)).toBe('—')
    expect(fechaCorta('')).toBe('—')
  })

  it('fechaCsv deja la fecha ordenable y sin hora', () => {
    expect(fechaCsv('2026-09-01T21:30:00')).toBe('2026-09-01')
    expect(fechaCsv(null)).toBe('')
  })
})
