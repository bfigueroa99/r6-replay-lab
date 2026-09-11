import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

/** Ruta -> el h1 que tiene que aparecer. Son las diez del menu. */
const PAGINAS = [
  ['/', 'Resumen'],
  ['/coach', 'Coach'],
  ['/mapas', 'Mapas y sitios'],
  ['/posicionamiento', 'Posicionamiento'],
  ['/operadores', 'Operadores'],
  ['/companeros', 'Compañeros'],
  ['/duelos', 'Duelos'],
  ['/tendencias', 'Tendencias'],
  ['/partidas', 'Partidas'],
  ['/datos', 'Datos'],
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
