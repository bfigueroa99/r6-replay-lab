import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

// Ninguna prueba de aca cambia la carpeta de replays por una que exista: el
// resto de la suite cuenta con que no exista (ver servidor.js). Elegir una de
// verdad y verla aplicada en toda la app lo prueban los tests del backend.

test('Ajustes muestra la carpeta, el vigilante y las copias', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/ajustes')

  await expect(page.locator('h1')).toHaveText('Ajustes')
  await expect(page.getByText('No existe en este PC')).toBeVisible()
  await expect(page.getByLabel('Carpeta de replays')).toHaveValue(/sin-replays$/)
  await expect(page.getByText('Todavía no hay copias.')).toBeVisible()
  // en el navegador no hay selector nativo: eso es de la app de escritorio
  await expect(page.getByRole('button', { name: 'Elegir carpeta…' })).toHaveCount(0)

  expect(errores).toEqual([])
})

test('una carpeta que no existe no se guarda y lo dice', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/ajustes')

  const input = page.getByLabel('Carpeta de replays')
  const inventada = (await input.inputValue()).replace(/sin-replays$/, 'inventada')
  await input.fill(inventada)
  await page.getByRole('button', { name: 'Guardar' }).click()

  await expect(page.locator('.flash.bad')).toContainText('No existe la carpeta')
  await page.reload()
  await expect(page.getByLabel('Carpeta de replays')).toHaveValue(/sin-replays$/)

  // el 400 de la API sale en la consola como recurso fallido, y es el esperado
  expect(errores.filter((e) => !e.includes('400'))).toEqual([])
})

test('la importacion automatica se apaga y queda apagada', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/ajustes')

  const check = page.getByRole('checkbox', { name: /Importar solas las partidas nuevas/ })
  await expect(check).toBeChecked()
  await check.click()
  await expect(page.locator('.flash')).toContainText('Importación automática apagada')

  await page.reload()
  await expect(check).not.toBeChecked()
  await check.click()
  await expect(check).toBeChecked()

  expect(errores).toEqual([])
})

test('una copia de seguridad aparece en la lista', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/ajustes')

  await page.getByRole('button', { name: 'Hacer una copia ahora' }).click()
  await expect(page.locator('.flash')).toContainText('Copia lista: db-')
  await expect(page.locator('table tbody tr').first()).toContainText('db-')

  expect(errores).toEqual([])
})

test('el aviso de Datos lleva a Ajustes', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/datos')

  await page.getByRole('link', { name: 'Ajustes' }).last().click()
  await expect(page).toHaveURL(/\/ajustes$/)
  await expect(page.locator('h1')).toHaveText('Ajustes')

  expect(errores).toEqual([])
})
