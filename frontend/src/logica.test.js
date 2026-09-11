/**
 * Tests de la logica pura del frontend: armado de query strings, formateo de
 * numeros que pueden venir null, orden de las tablas y generacion del CSV.
 *
 * Corren en node, sin jsdom: nada de lo que se prueba aca necesita un DOM, y
 * montar uno para probar un comparador es pagar por nada. Lo que si toca el DOM
 * (`descargarCsv`) esta separado justamente para que el resto se pueda probar.
 */

import { describe, expect, it } from 'vitest'

import { qs } from './api.js'
import {
  VEREDICTO,
  csvText,
  fmt,
  ordenarFilas,
  pct,
  ratio,
  signed,
  winrateColor,
} from './components/ui.jsx'
import { destacados } from './pages/Posicionamiento.jsx'

describe('qs', () => {
  it('arma la query string', () => {
    expect(qs({ side: 'Attack', map: 'bank' })).toBe('?side=Attack&map=bank')
  })

  it('sin parametros no deja el signo colgando', () => {
    expect(qs()).toBe('')
    expect(qs({})).toBe('')
  })

  it('saca lo vacio para no mandar filtros fantasma', () => {
    expect(qs({ side: '', map: null, operator: undefined, site: false })).toBe('')
  })

  it('el cero si viaja', () => {
    expect(qs({ min_rounds: 0 })).toBe('?min_rounds=0')
  })

  it('true se manda como 1, que es lo que entiende la API', () => {
    expect(qs({ ranked_only: true })).toBe('?ranked_only=1')
  })

  it('escapa lo que rompe una URL', () => {
    expect(qs({ site: '2F Bathroom, 2F Office' })).toContain('2F+Bathroom%2C+2F+Office')
  })
})

describe('formato de numeros', () => {
  it('null se muestra como raya y no como cero', () => {
    expect(fmt(null)).toBe('—')
    expect(fmt(undefined)).toBe('—')
    expect(pct(null)).toBe('—')
    expect(ratio(null)).toBe('—')
  })

  it('el cero es un valor, no un vacio', () => {
    expect(fmt(0)).toBe('0')
    expect(pct(0)).toBe('0%')
  })

  it('redondea y agrega el sufijo', () => {
    expect(fmt(43.27, 1, '%')).toBe('43.3%')
    expect(pct(43.27)).toBe('43%')
    expect(ratio(0.8149)).toBe('0.81')
  })
})

describe('winrateColor', () => {
  it('sin dato devuelve el gris del fondo', () => {
    expect(winrateColor(null)).toBe('#2a3441')
  })

  it('va de rojo a verde', () => {
    const matiz = (valor) => Number(winrateColor(valor).match(/hsl\((\d+(?:\.\d+)?)/)[1])
    expect(matiz(20)).toBe(0)
    expect(matiz(80)).toBe(130)
    expect(matiz(50)).toBeGreaterThan(matiz(35))
    expect(matiz(50)).toBeLessThan(matiz(65))
  })

  it('los extremos se recortan', () => {
    expect(winrateColor(0)).toBe(winrateColor(35))
    expect(winrateColor(100)).toBe(winrateColor(65))
  })
})

describe('ordenarFilas', () => {
  const filas = [
    { map: 'Bank', winrate: 31.6 },
    { map: 'Club House', winrate: 36.0 },
    { map: 'Villa', winrate: null },
    { map: 'Consulate', winrate: 52.9 },
  ]

  it('ordena numeros de mayor a menor', () => {
    const orden = ordenarFilas(filas, { key: 'winrate', dir: 'desc' }).map((f) => f.map)
    expect(orden.slice(0, 3)).toEqual(['Consulate', 'Club House', 'Bank'])
  })

  it('los nulos quedan al final en las dos direcciones', () => {
    for (const dir of ['asc', 'desc']) {
      const orden = ordenarFilas(filas, { key: 'winrate', dir })
      expect(orden[orden.length - 1].map).toBe('Villa')
    }
  })

  it('ordena texto alfabeticamente', () => {
    const orden = ordenarFilas(filas, { key: 'map', dir: 'asc' }).map((f) => f.map)
    expect(orden).toEqual(['Bank', 'Club House', 'Consulate', 'Villa'])
  })

  it('no toca el arreglo original', () => {
    const copia = [...filas]
    ordenarFilas(filas, { key: 'winrate', dir: 'asc' })
    expect(filas).toEqual(copia)
  })

  it('sin filas no revienta', () => {
    expect(ordenarFilas(null, { key: 'winrate', dir: 'asc' })).toEqual([])
    expect(ordenarFilas([], { key: 'x', dir: 'asc' })).toEqual([])
  })
})

describe('csvText', () => {
  const columnas = [
    { key: 'map', label: 'Mapa' },
    { key: 'winrate', label: 'Ganadas' },
  ]

  it('usa las etiquetas de la tabla como cabecera', () => {
    expect(csvText(columnas, []).split('\r\n')[0]).toBe('Mapa;Ganadas')
  })

  it('punto y coma y coma decimal, que es lo que abre Excel en espanol', () => {
    const texto = csvText(columnas, [{ map: 'Bank', winrate: 31.6 }])
    expect(texto.split('\r\n')[1]).toBe('Bank;31,6')
  })

  it('null queda vacio, no como "null"', () => {
    expect(csvText(columnas, [{ map: 'Villa', winrate: null }]).split('\r\n')[1]).toBe('Villa;')
  })

  it('los booleanos van en palabras', () => {
    const cols = [{ key: 'ok', label: 'Ok' }]
    expect(csvText(cols, [{ ok: true }, { ok: false }]).split('\r\n').slice(1)).toEqual(['si', 'no'])
  })

  it('las listas se juntan en una celda', () => {
    const cols = [{ key: 'maps', label: 'Mapas' }]
    expect(csvText(cols, [{ maps: ['Bank', 'Villa'] }]).split('\r\n')[1]).toBe('Bank / Villa')
  })

  it('escapa lo que rompe el formato', () => {
    const cols = [{ key: 'site', label: 'Sitio' }]
    const texto = csvText(cols, [{ site: '2F Bathroom; 2F "Office"' }])
    expect(texto.split('\r\n')[1]).toBe('"2F Bathroom; 2F ""Office"""')
  })

  it('una columna puede exportar algo distinto de lo que muestra', () => {
    const cols = [{ key: 'won', label: 'Resultado', csv: (row) => (row.won ? 'victoria' : 'derrota') }]
    expect(csvText(cols, [{ won: true }]).split('\r\n')[1]).toBe('victoria')
  })

  it('una columna puede quedarse fuera del archivo', () => {
    const cols = [...columnas, { key: 'acciones', label: 'Acciones', csv: false }]
    expect(csvText(cols, []).split('\r\n')[0]).toBe('Mapa;Ganadas')
  })

  it('sin filas devuelve solo la cabecera', () => {
    expect(csvText(columnas, null)).toBe('Mapa;Ganadas')
  })
})

describe('signed', () => {
  it('le pone el signo a los positivos', () => {
    expect(signed(6)).toBe('+6')
    expect(signed(6.4, 1, ' pts')).toBe('+6.4 pts')
  })

  it('deja el menos que ya trae el numero', () => {
    expect(signed(-6)).toBe('-6')
  })

  it('el cero va sin signo: no subio ni bajo', () => {
    expect(signed(0)).toBe('0')
  })

  it('un null no se inventa un cero', () => {
    expect(signed(null)).toBe('—')
    expect(signed(undefined)).toBe('—')
  })

  it('no deja un "-0" cuando el redondeo se come la diferencia', () => {
    expect(signed(-0.4)).toBe('0')
    expect(signed(0.4)).toBe('0')
  })
})

describe('VEREDICTO', () => {
  it('cubre los tres veredictos que manda la API', () => {
    expect(Object.keys(VEREDICTO).sort()).toEqual(['dormidero', 'ruido', 'solido'])
  })

  it('el ruido no afirma que la zona sea normal', () => {
    // "sin señal" y no "normal": no sabemos que la zona sea corriente, sabemos
    // que la muestra no alcanza para decirlo
    expect(VEREDICTO.ruido.label).toBe('Sin señal')
    expect(VEREDICTO.ruido.tone).toBe('')
  })
})

describe('destacados', () => {
  const zona = (site, verdict, delta) => ({ site, verdict, caught_out_delta: delta })

  it('elige el peor dormidero y el mejor solido', () => {
    const { peor, mejor } = destacados([
      zona('A', 'dormidero', 12),
      zona('B', 'dormidero', 31),
      zona('C', 'solido', -9),
      zona('D', 'solido', -22),
    ])
    expect(peor.site).toBe('B')
    expect(mejor.site).toBe('D')
  })

  it('ignora las zonas que no pasaron la banda de ruido', () => {
    // una diferencia enorme marcada como ruido no puede ganarle a una chica
    // que si paso la banda: el veredicto manda, no el delta
    const { peor } = destacados([zona('A', 'ruido', 80), zona('B', 'dormidero', 11)])
    expect(peor.site).toBe('B')
  })

  it('sin zonas concluyentes no inventa una', () => {
    expect(destacados([zona('A', 'ruido', 40)])).toEqual({ peor: null, mejor: null })
    expect(destacados([])).toEqual({ peor: null, mejor: null })
  })
})
