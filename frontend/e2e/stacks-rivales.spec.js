import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

test('Duelos muestra el stack rival del seed con su récord', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/duelos')

  const panel = page.locator('section.panel', { hasText: 'Stacks rivales que se repiten' })
  await expect(panel).toBeVisible()
  // seed_demo pone a los mismos tres rivales en todas las rondas de sus 29 partidas, todas ganadas
  const filas = panel.locator('table tbody tr')
  await expect(filas).toHaveCount(1)
  const enlaces = filas.first().getByRole('link')
  await expect(enlaces).toHaveText(['Kaid_', 'Mozzie99', 'Thorn.exe'])
  for (let i = 0; i < 3; i++) {
    await expect(enlaces.nth(i)).toHaveAttribute('href', /\/jugadores\/\d+$/)
  }
  await expect(filas.first()).toContainText('29-0')
  await expect(filas.first().locator('td').nth(2)).toHaveText('29')

  await enlaces.first().click()
  await expect(page).toHaveURL(/\/jugadores\/\d+$/)

  expect(errores).toEqual([])
})
