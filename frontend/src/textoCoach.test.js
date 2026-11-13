import { describe, expect, it } from 'vitest'

import { nombreDeModo } from './modoDeJuego.js'
import { GRUPOS_COACH, formatoCoach, lineaDeFiltros, textoCoach } from './textoCoach.js'

const alta = {
  key: 'entry',
  severity: 'alta',
  title: 'Mueres primero demasiado',
  detail: 'Caes primero en 30% de tus rondas.',
  action: 'Juega el segundo contacto.',
  metric: 'Primera muerte',
  value: 30,
  baseline: 20,
  sample: 120,
  scope: 'general',
}

const positivo = {
  key: 'clutch',
  severity: 'positivo',
  title: 'Cierras clutches',
  detail: 'Ganas 1v1 seguido.',
  action: 'Quédate de ancla.',
  metric: 'Rating',
  value: 1.234,
  baseline: null,
  sample: 0,
  scope: 'Bank',
}

describe('textoCoach', () => {
  it('sin señales no hay texto', () => {
    expect(textoCoach([], {})).toBeNull()
    expect(textoCoach(undefined, {})).toBeNull()
  })

  it('sin filtros la primera linea lo dice', () => {
    expect(textoCoach([alta], {}).split('\n')[0]).toBe('Coach · Sin filtros')
    expect(lineaDeFiltros({ side: '', map: '' })).toBe('Sin filtros')
  })

  it('con filtros los nombra en orden', () => {
    const filtros = { ranked_only: true, days: '30', map: 'bank', side: 'Defense' }
    expect(lineaDeFiltros(filtros)).toBe('Filtros: Solo defensa · Mapa: bank · Últimos 30 días · Solo ranked')
    expect(textoCoach([alta], filtros).split('\n')[0]).toBe(
      'Coach · Filtros: Solo defensa · Mapa: bank · Últimos 30 días · Solo ranked',
    )
  })

  it('nombra el resto de los filtros', () => {
    const filtros = {
      side: 'Attack',
      operator: 'Ash',
      site: '2F Office',
      session: '0',
      since: '2026-10-01',
      until: '2026-10-31',
      match_type: 'Ranked',
      gamemode: 'Bomb',
    }
    const linea = lineaDeFiltros(filtros)
    expect(linea.startsWith('Filtros: Solo ataque · Operador: Ash · Sitio: 2F Office · Sesión 1 · ')).toBe(true)
    expect(linea.endsWith(`Desde 2026-10-01 · Hasta 2026-10-31 · Tipo: Ranked · Modo: ${nombreDeModo('Bomb')}`)).toBe(true)
  })

  it('dos señales salen en el orden de los grupos', () => {
    const lineas = textoCoach([positivo, alta], {}).split('\n')
    expect(lineas.indexOf('PRIORIDAD ALTA')).toBeLessThan(lineas.indexOf('TUS FORTALEZAS'))
    expect(lineas.indexOf('- Mueres primero demasiado')).toBeLessThan(lineas.indexOf('- Cierras clutches'))
    expect(lineas).toContain('  Qué hacer: Juega el segundo contacto.')
    expect(lineas.some((l) => l.endsWith(' '))).toBe(false)
    expect(textoCoach([alta], {})).not.toMatch(/[<>]/)
  })

  it('la referencia y la muestra van solo si existen', () => {
    const lineas = textoCoach([alta, positivo], {}).split('\n')
    expect(lineas).toContain('  Primera muerte: 30 (referencia 20) · muestra: 120 rondas')
    expect(lineas).toContain('  Rating: 1.23 · alcance: Bank')
    const sinMetrica = { ...alta, metric: '', sample: 0, scope: 'general' }
    const texto = textoCoach([sinMetrica], {})
    expect(texto).not.toContain('muestra:')
    expect(texto.trimEnd().split('\n').at(-1)).toBe('  Qué hacer: Juega el segundo contacto.')
  })

  it('el numero se formatea como en la pagina', () => {
    expect(formatoCoach(0.456)).toBe('0.46')
    expect(formatoCoach(55)).toBe('55')
    expect(formatoCoach(null)).toBe('—')
    expect(formatoCoach('A')).toBe('A')
  })

  it('los grupos siguen el orden de la pagina', () => {
    expect(GRUPOS_COACH.map((g) => g.key)).toEqual(['alta', 'media', 'baja', 'positivo'])
  })
})
