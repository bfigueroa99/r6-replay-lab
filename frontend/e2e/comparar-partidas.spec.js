import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

test('dos partidas se comparan lado a lado desde el detalle y la URL se puede recargar', async ({ page }) => {
  const errores = vigilarConsola(page)
  // los ids salen de la API: seed_demo es deterministico pero el orden de los ids no es contrato
  const listado = await (await page.request.get('/api/matches/?limit=2')).json()
  const [a, b] = listado.matches
  expect(b).toBeTruthy()
  const tabla = page.locator('table.comparar')

  await page.goto(`/partidas/${a.id}`)
  await page.getByRole('link', { name: 'Comparar con…' }).click()
  await expect(page).toHaveURL(new RegExp(`/comparar/${a.id}$`))
  await expect(page.locator('h1')).toHaveText('Comparar partidas')
  await expect(page.getByText('Elegí la partida con la que comparar.')).toBeVisible()

  const selector = page.getByLabel('Comparar con')
  await expect(selector).toBeEnabled()
  await selector.selectOption(String(b.id))
  await expect(page).toHaveURL(new RegExp(`/comparar/${a.id}/${b.id}$`))

  const verComparacion = async () => {
    await expect(tabla.getByRole('columnheader', { name: 'Diferencia' })).toBeVisible()
    const marcador = tabla.locator('tr', { has: page.getByRole('rowheader', { name: 'Marcador' }) })
    await expect(marcador.locator('td').nth(0)).toContainText(a.score)
    await expect(marcador.locator('td').nth(1)).toContainText(b.score)
    await expect(selector).toHaveValue(String(b.id))
  }
  await verComparacion()

  await page.reload()
  await verComparacion()

  await page.goto(`/comparar/${a.id}/999999`)
  await expect(page.locator('main h2')).toHaveText('Esa partida no existe')

  // Chromium loguea el 404 esperado como "Failed to load resource" sin la URL
  const de404 = errores.filter((e) => e.includes('status of 404'))
  expect(de404).toHaveLength(1)
  expect(errores.filter((e) => !e.includes('status of 404'))).toEqual([])
})
