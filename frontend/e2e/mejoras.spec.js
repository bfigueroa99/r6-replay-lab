import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

/**
 * Filtros en la URL, senales que llevan a sus rondas, racha, filtros de la
 * lista de partidas, teclado en el detalle y el vigia de importacion. Todo
 * sobre el seed de `manage.py seed_demo`, que es deterministico.
 */

test('los filtros viven en la URL, siguen al menu y sobreviven a recargar', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/')

  await page.getByLabel('Mapa').selectOption({ label: 'Border' })
  await expect(page).toHaveURL(/\?map=border$/)
  await expect(page.locator('.page-head p')).toContainText('9 partidas')

  await page.getByRole('navigation').getByRole('link', { name: 'Operadores', exact: true }).click()
  await expect(page).toHaveURL(/\/operadores\?map=border$/)
  await expect(page.getByLabel('Mapa')).toHaveValue('border')

  await page.reload()
  await expect(page.getByLabel('Mapa')).toHaveValue('border')

  await page.getByRole('button', { name: 'Limpiar' }).click()
  await expect(page).toHaveURL(/\/operadores$/)
  await expect(page.getByLabel('Mapa')).toHaveValue('')

  expect(errores).toEqual([])
})

test('una senal del coach lleva al Resumen con las rondas que la respaldan', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/coach')

  const enlace = page.getByRole('link', { name: /Ver esas rondas/ }).first()
  await expect(enlace).toBeVisible()
  await enlace.click()

  await expect(page).toHaveURL(/\/\?(side|operator|map)=/)
  await expect(page.locator('h1')).toHaveText('Resumen')
  await expect(page.getByRole('button', { name: 'Limpiar' })).toBeVisible()

  expect(errores).toEqual([])
})

test('el Resumen muestra la racha actual', async ({ page }) => {
  await page.goto('/')
  // el seed gana todas las partidas 4-3: la racha es el historial entero
  await expect(page.locator('.page-head').first()).toContainText('racha: 29 victorias')
})

test('la lista de partidas se filtra por mapa y por resultado', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/partidas')
  await expect(page.locator('.page-head p')).toContainText('29 partidas importadas')
  // la lista es de partidas: lado y operador no aplican y no se ofrecen
  await expect(page.getByLabel('Lado')).toHaveCount(0)

  await page.getByLabel('Mapa').selectOption({ label: 'Border' })
  await expect(page.locator('.page-head p')).toContainText('9 partidas con estos filtros')
  await expect(page.locator('table tbody tr')).toHaveCount(9)

  await page.getByLabel('Resultado').selectOption('derrota')
  await expect(page.locator('.page-head p')).toContainText('0 partidas con estos filtros')
  await expect(page.getByText('Ninguna partida pasa estos filtros.')).toBeVisible()
  // sin partidas por un filtro no es "no hay replays"
  await expect(page.locator('.empty-state')).toHaveCount(0)

  expect(errores).toEqual([])
})

test('en el detalle las flechas cambian de ronda y se salta a la partida vecina', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/partidas')
  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/partidas\/\d+$/)

  const activa = page.locator('.round-tab.active .n')
  await expect(activa).toHaveText('R1')
  await page.keyboard.press('ArrowRight')
  await expect(activa).toHaveText('R2')
  await page.keyboard.press('ArrowRight')
  await expect(activa).toHaveText('R3')
  await page.keyboard.press('ArrowLeft')
  await expect(activa).toHaveText('R2')

  // mis eventos van marcados y cada nombre trae su operador de la ronda
  await expect(page.locator('.timeline li.me').first()).toBeVisible()
  await expect(page.locator('.timeline .who.yo').first()).toContainText('BearF99')

  // la mas reciente no tiene siguiente, pero si anterior
  await expect(page.getByRole('link', { name: /Siguiente/ })).toHaveCount(0)
  const antes = page.url()
  await page.getByRole('link', { name: /Anterior/ }).click()
  await expect(page).toHaveURL(/\/partidas\/\d+$/)
  expect(page.url()).not.toBe(antes)
  await expect(page.getByRole('link', { name: /Siguiente/ })).toBeVisible()

  expect(errores).toEqual([])
})

test('el vigia viene encendido, se apaga en Datos y se acuerda', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/datos')

  const casilla = page.getByLabel('Importar sola mientras la app esté abierta')
  await expect(casilla).toBeChecked()
  await expect(page.locator('.topbar .chip.vigia')).toHaveText('vigilando')

  await casilla.uncheck()
  await expect(page.locator('.topbar .chip.vigia')).toHaveCount(0)
  await expect(page.getByText('Apagado: las partidas nuevas se importan solo con el botón de arriba.')).toBeVisible()

  await page.reload()
  await expect(page.getByLabel('Importar sola mientras la app esté abierta')).not.toBeChecked()
  await expect(page.locator('.topbar .chip.vigia')).toHaveCount(0)

  expect(errores).toEqual([])
})

test('Operadores muestra el pick rate y el perfil de un companero respeta los filtros', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/operadores')
  await expect(page.locator('table thead').first()).toContainText('Pick')
  await expect(page.locator('table tbody tr').first()).toContainText('%')

  await page.goto('/companeros?map=border')
  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/jugadores\/\d+\?map=border$/)
  await expect(page.getByLabel('Mapa')).toHaveValue('border')
  await expect(page.getByText('con los filtros activos')).toBeVisible()
  await page.getByRole('link', { name: 'Volver' }).click()
  await expect(page).toHaveURL(/\/companeros\?map=border$/)

  expect(errores).toEqual([])
})
