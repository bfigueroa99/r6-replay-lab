import { describe, expect, it } from 'vitest'

import { APP, tituloDePagina } from './titulo.js'

const LINKS = [
  { to: '/', label: 'Resumen' },
  { to: '/companeros', label: 'Compañeros' },
  { to: '/partidas', label: 'Partidas' },
]

describe('tituloDePagina', () => {
  it('una pagina del menu lleva su nombre delante del de la app', () => {
    expect(tituloDePagina('/', LINKS)).toBe(`Resumen · ${APP}`)
    expect(tituloDePagina('/companeros', LINKS)).toBe(`Compañeros · ${APP}`)
  })

  it('la barra del final no cambia la pagina', () => {
    expect(tituloDePagina('/partidas/', LINKS)).toBe(`Partidas · ${APP}`)
  })

  it('las mayusculas tampoco: React Router no las distingue', () => {
    // /COACH muestra el Coach; el titulo no puede decir que no existe
    expect(tituloDePagina('/COMPANEROS', LINKS)).toBe(`Compañeros · ${APP}`)
    expect(tituloDePagina('/Partidas/12', LINKS)).toBe(`Partida · ${APP}`)
    expect(tituloDePagina('/Comparar/3/4', LINKS)).toBe(`Comparar partidas · ${APP}`)
  })

  it('las paginas que no estan en el menu tienen su propio nombre', () => {
    expect(tituloDePagina('/partidas/12', LINKS)).toBe(`Partida · ${APP}`)
    expect(tituloDePagina('/comparar/3', LINKS)).toBe(`Comparar partidas · ${APP}`)
    expect(tituloDePagina('/comparar/3/4', LINKS)).toBe(`Comparar partidas · ${APP}`)
    expect(tituloDePagina('/jugadores/7', LINKS)).toBe(`Jugador · ${APP}`)
  })

  it('una ruta que no existe lo dice', () => {
    expect(tituloDePagina('/no-existe', LINKS)).toBe(`Esa página no existe · ${APP}`)
    expect(tituloDePagina('/partidas/12/otra', LINKS)).toBe(`Esa página no existe · ${APP}`)
  })

  it('sin ruta queda el nombre de la app', () => {
    expect(tituloDePagina('', LINKS)).toBe(APP)
    expect(tituloDePagina(undefined, LINKS)).toBe(APP)
  })
})
