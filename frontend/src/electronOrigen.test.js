import { describe, expect, it } from 'vitest'

import origen from '../electron/origen.cjs'

const { esDeLaApp, esWebExterna } = origen

const APP = 'http://127.0.0.1:8000'

describe('esDeLaApp', () => {
  it('las rutas de la app son de la app', () => {
    for (const url of [APP, `${APP}/`, `${APP}/partidas/12?side=Attack#r3`, `${APP}/api/settings/`]) {
      expect(esDeLaApp(url, APP), url).toBe(true)
    }
  })

  it('una URL que solo empieza igual que la app no es la app', () => {
    // comparar con startsWith dejaba pasar las tres: son otro host
    for (const url of [
      `${APP}@atacante.example/`,
      `${APP}:x@atacante.example/`,
      'http://127.0.0.1:8000.atacante.example/',
    ]) {
      expect(esDeLaApp(url, APP), url).toBe(false)
    }
  })

  it('otro puerto que empieza con el mismo numero es otro origen', () => {
    expect(esDeLaApp('http://127.0.0.1:45021/', 'http://127.0.0.1:4502')).toBe(false)
    expect(esDeLaApp('http://127.0.0.1:80/', APP)).toBe(false)
  })

  it('otro esquema u otro host no son la app', () => {
    for (const url of [
      'https://127.0.0.1:8000/',
      'http://localhost:8000/',
      'file:///C:/Windows/System32/calc.exe',
      'ms-settings:privacy',
      'javascript:alert(1)',
      'about:blank',
      'data:text/html,hola',
    ]) {
      expect(esDeLaApp(url, APP), url).toBe(false)
    }
  })

  it('lo que no es una URL no es la app', () => {
    for (const url of ['', 'no es una url', null, undefined, 42]) {
      expect(esDeLaApp(url, APP), String(url)).toBe(false)
    }
  })

  it('con --url la app es el dev server de Vite', () => {
    expect(esDeLaApp('http://localhost:5173/coach', 'http://localhost:5173')).toBe(true)
    expect(esDeLaApp(`${APP}/coach`, 'http://localhost:5173')).toBe(false)
  })

  it('una app sin origen (file:, texto suelto) no reconoce a nadie', () => {
    // el origen de file: es opaco ("null"): dos archivos cualquiera darian igual
    expect(esDeLaApp('file:///etc/passwd', 'file:///app/index.html')).toBe(false)
    expect(esDeLaApp('http://x/', 'no es una url')).toBe(false)
  })
})

describe('esWebExterna', () => {
  it('http y https salen al navegador del sistema', () => {
    for (const url of ['https://stats.cc/siege/Nick/abc', 'http://example.com/', 'HTTPS://R6.TRACKER.NETWORK/x']) {
      expect(esWebExterna(url), url).toBe(true)
    }
  })

  it('ningun otro esquema llega a shell.openExternal', () => {
    // en Windows un file: o un protocolo registrado ejecuta lo que apunta
    for (const url of [
      'file:///C:/Windows/System32/calc.exe',
      'ms-settings:privacy',
      'search-ms:query=x',
      'httpx://raro',
      'javascript:alert(1)',
      'data:text/html,hola',
      'smb://host/recurso',
      '',
      'no es una url',
      null,
      undefined,
    ]) {
      expect(esWebExterna(url), String(url)).toBe(false)
    }
  })
})
