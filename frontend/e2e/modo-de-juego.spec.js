import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

// Ficha 100: modo de juego como filtro y como tabla. seed_demo es todo Bomb,
// asi que el segundo modo entra interceptando la API y ningun numero del seed
// se mueve.

async function conRehen(page) {
  await page.route('**/api/filters/', async (route) => {
    const respuesta = await route.fetch()
    const json = await respuesta.json()
    await route.fulfill({ response: respuesta, json: { ...json, gamemodes: [...json.gamemodes, 'Hostage'] } })
  })
}

test('con un solo modo la barra no muestra el selector', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/')
  await expect(page.locator('.page-head p')).toHaveText(/rondas analizadas/)
  await expect(page.getByLabel('Tipo')).toBeVisible()
  await expect(page.getByRole('combobox', { name: 'Modo', exact: true })).toHaveCount(0)
  expect(errores).toEqual([])
})

test('el selector de modo filtra y Limpiar lo saca', async ({ page }) => {
  const errores = vigilarConsola(page)
  await conRehen(page)
  await page.goto('/')

  const subtitulo = page.locator('.page-head p')
  await expect(subtitulo).toHaveText(/rondas analizadas/)
  const sinFiltro = await subtitulo.textContent()
  const modo = page.getByRole('combobox', { name: 'Modo', exact: true })
  await expect(modo.locator('option')).toHaveText(['Todos', 'Bomba', 'Rehén'])

  const pedido = page.waitForRequest(/\/api\/overview\/\?.*gamemode=Hostage/)
  await modo.selectOption('Hostage')
  await pedido
  await expect(page).toHaveURL(/[?&]gamemode=Hostage/)
  await expect(subtitulo).toHaveText('0 rondas con estos filtros')
  await expect(page.locator('.filters')).toBeVisible()

  await page.getByRole('button', { name: 'Limpiar' }).click()
  await expect(subtitulo).toHaveText(sinFiltro)
  await expect(modo).toHaveValue('')
  expect(errores).toEqual([])
})

test('un enlace con modo muestra el selector aunque la base tenga uno solo', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/?gamemode=Hostage')
  await expect(page.getByRole('combobox', { name: 'Modo', exact: true })).toHaveValue('Hostage')
  await expect(page.locator('.page-head p')).toHaveText('0 rondas con estos filtros')
  expect(errores).toEqual([])
})

test('Partidas manda el modo al listado', async ({ page }) => {
  const errores = vigilarConsola(page)
  const pedido = page.waitForRequest(/\/api\/matches\/\?.*gamemode=Hostage/)
  await page.goto('/partidas?gamemode=Hostage')
  await pedido
  await expect(page.getByRole('combobox', { name: 'Modo', exact: true })).toHaveValue('Hostage')
  await expect(page.locator('table tbody a[href^="/partidas/"]')).toHaveCount(0)
  expect(errores).toEqual([])
})

test('Tendencias muestra Por modo solo con más de un modo', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')
  await page.waitForLoadState('networkidle')
  await expect(page.getByRole('heading', { name: 'Por hora del día', exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Por modo', exact: true })).toHaveCount(0)

  await page.route('**/api/trends/**', async (route) => {
    const respuesta = await route.fetch()
    const json = await respuesta.json()
    const rehen = {
      gamemode: 'Hostage',
      matches: 1,
      matches_decided: 1,
      matches_won: 1,
      match_winrate: 100,
      rounds: 7,
      rounds_won: 4,
      winrate: 57.1,
      kd: 1.2,
      rating: 1.05,
    }
    await route.fulfill({ response: respuesta, json: { ...json, by_gamemode: [...json.by_gamemode, rehen] } })
  })
  // sin esperar, el reload corta los fetch de la pagina y la consola los anota
  await page.waitForLoadState('networkidle')
  await page.reload()
  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Por modo', exact: true }),
  })
  await expect(panel).toBeVisible()
  await expect(panel.locator('tbody tr')).toHaveCount(2)
  await expect(panel.locator('tbody')).toContainText('Bomba')
  await expect(panel.locator('tbody')).toContainText('Rehén')
  expect(errores).toEqual([])
})
