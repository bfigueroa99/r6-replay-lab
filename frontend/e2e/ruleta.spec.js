import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

/**
 * La ruleta no depende de los replays: el catalogo sale del parser. Lo que se
 * prueba es la cadena entera, del endpoint al canvas y de ahi al resultado.
 */
test('la ruleta carga, gira y anuncia un operador del lado elegido', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/ruleta')

  await expect(page.locator('h1')).toHaveText('Ruleta de operadores')
  await expect(page.locator('canvas.rueda')).toBeVisible()
  await expect(page.locator('.resultado-label')).toContainText('operadores en la rueda')

  await page.getByRole('button', { name: 'Defensa' }).click()
  // el giro mas corto posible para no esperar de mas en CI
  await page.locator('input[type=range]').fill('1')
  await page.getByRole('button', { name: 'GIRAR', exact: true }).click()

  const nombre = page.locator('.resultado-nombre')
  await expect(nombre).toBeVisible()
  await expect(nombre).not.toBeEmpty()
  await expect(page.locator('.resultado .chip')).toHaveText('Defensa')
  await expect(page.locator('.historial li')).toHaveCount(1)

  expect(errores).toEqual([])
})

test('sacar un operador lo deja fuera de la rueda y sobrevive a recargar', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/ruleta')
  await page.getByRole('button', { name: 'Ataque', exact: true }).first().click()

  const antes = await page.locator('.resultado-label').textContent()
  await page.locator('.pool-chip', { hasText: 'Ash' }).click()
  await expect(page.locator('.pool-chip.fuera')).toHaveText(['Ash'])
  await expect(page.locator('.resultado-label')).not.toHaveText(antes)

  await page.reload()
  await expect(page.locator('.pool-chip.fuera')).toHaveText(['Ash'])
  await page.getByRole('button', { name: /Reponer todos/ }).click()
  await expect(page.locator('.pool-chip.fuera')).toHaveCount(0)

  expect(errores).toEqual([])
})
