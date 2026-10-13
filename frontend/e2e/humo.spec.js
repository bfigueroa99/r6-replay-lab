import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'
import { BASE_URL } from './entorno.js'

/** Ruta -> el h1 que tiene que aparecer. Las del menu, menos la Ruleta (tiene su spec). */
const PAGINAS = [
  ['/', 'Resumen'],
  ['/coach', 'Coach'],
  ['/operadores', 'Operadores'],
  ['/companeros', 'Compañeros'],
  ['/duelos', 'Duelos'],
  ['/tendencias', 'Tendencias'],
  ['/partidas', 'Partidas'],
  ['/datos', 'Datos'],
  ['/ajustes', 'Ajustes'],
]

test.describe('todas las paginas cargan', () => {
  for (const [ruta, titulo] of PAGINAS) {
    test(`${titulo} (${ruta}) renderiza y no ensucia la consola`, async ({ page }) => {
      const errores = vigilarConsola(page)

      await page.goto(ruta)
      await expect(page.locator('h1')).toHaveText(titulo)
      // ninguna pagina deberia quedarse en "todavia no hay replays": el seed
      // tiene 200 rondas, asi que un empty state aca es un bug de datos
      await expect(page.locator('.empty-state')).toHaveCount(0)

      expect(errores, `errores de consola en ${ruta}`).toEqual([])
    })
  }
})

test('el menu navega sin recargar y carga los chunks lazy', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/')

  for (const [, titulo] of PAGINAS.slice(1)) {
    await page.getByRole('navigation').getByRole('link', { name: titulo, exact: true }).click()
    await expect(page.locator('h1')).toHaveText(titulo)
  }

  expect(errores).toEqual([])
})

test('el detalle de una partida se abre desde la lista', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/partidas')

  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/partidas\/\d+$/)
  await expect(page.locator('h1')).toContainText(/Club House|Border|Bank/)

  expect(errores).toEqual([])
})

test('el perfil de un jugador se abre desde Compañeros', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/companeros')

  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/jugadores\/\d+$/)
  await expect(page.locator('h1')).not.toBeEmpty()

  expect(errores).toEqual([])
})

test('tu perfil enlaza a los trackers y muestra Ubisoft sin salir a la red', async ({ page }) => {
  const errores = vigilarConsola(page)
  const afuera = []
  page.on('request', (request) => {
    if (!request.url().startsWith(BASE_URL)) afuera.push(request.url())
  })

  await page.goto('/')
  await page.locator('.topbar').getByRole('link', { name: 'BearF99' }).click()
  await expect(page).toHaveURL(/\/jugadores\/\d+$/)
  await expect(page.locator('h1')).toContainText('BearF99')

  // el profileID sale de seed_demo, que lo deriva del nick
  const pid = '14c9dacd-69a1-5ae1-80d8-ce1b96f8948f'
  await expect(page.getByRole('link', { name: /stats\.cc/ })).toHaveAttribute(
    'href',
    `https://stats.cc/siege/BearF99/${pid}`,
  )
  await expect(page.getByRole('link', { name: /R6 Tracker/ })).toHaveAttribute(
    'href',
    `https://r6.tracker.network/r6siege/profile/ubi/${pid}/overview`,
  )

  // la consulta guardada por el seed se ve; sin cuenta no hay boton para repetirla
  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Temporada en Ubisoft' }),
  })
  await expect(panel).toContainText('Oro 1')
  await expect(panel).toContainText('2950 MMR')
  await expect(panel).toContainText('Consultado el 01-09-2026 12:00 · temporada Y10S2.')
  await expect(panel.locator('code', { hasText: 'UBI_EMAIL' })).toBeVisible()
  await expect(panel.getByRole('button')).toHaveCount(0)

  expect(afuera, 'la app pidio algo fuera de localhost').toEqual([])
  expect(errores).toEqual([])
})

test('una ruta que no existe no rompe la app', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/no-existe')

  await expect(page.getByText('Esa pagina no existe')).toBeVisible()
  await page.getByRole('link', { name: 'Volver al resumen' }).click()
  await expect(page.locator('h1')).toHaveText('Resumen')

  expect(errores).toEqual([])
})

test('la cabecera muestra el jugador y el volumen importado', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('.topbar')).toContainText('BearF99')
  await expect(page.locator('.topbar')).toContainText('29 partidas · 203 rondas')
})

test('Datos avisa cuando la carpeta de replays no existe', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/datos')

  // el e2e corre sin Siege: la carpeta detectada o por defecto no existe, y el
  // usuario tiene que enterarse ahi mismo de por que no aparecen partidas
  await expect(page.getByText('Esa carpeta no existe en este PC')).toBeVisible()
  await expect(page.getByText('Carpeta vigilada:')).toBeVisible()

  expect(errores).toEqual([])
})
