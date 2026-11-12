import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

/**
 * Lo que un lector de pantalla y el teclado necesitan de la app, y que ni el
 * build ni los tests de logica ven: el titulo del documento, el orden de las
 * tablas sin mouse, los avisos anunciados y el contraste de las etiquetas.
 */

test('una tabla se ordena con el teclado y dice en que orden esta', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/operadores')

  const tabla = page.locator('section.panel', { has: page.getByRole('heading', { name: 'Ataque', exact: true }) }).locator('table')
  const rondas = tabla.locator('th', { hasText: 'Rondas' })
  const boton = rondas.getByRole('button', { name: 'Rondas' })
  const valores = async () => (await tabla.locator('tbody tr td:nth-child(3)').allTextContents()).map(Number)

  // la tabla arranca ordenada por rondas, de mas a menos, y lo dice
  await expect(rondas).toHaveAttribute('aria-sort', 'descending')
  const inicial = await valores()
  expect(inicial.length).toBeGreaterThan(1)
  expect(inicial).toEqual([...inicial].sort((a, b) => b - a))

  // sin mouse: foco en la cabecera y Enter
  await boton.focus()
  await expect(boton).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(rondas).toHaveAttribute('aria-sort', 'ascending')
  expect(await valores()).toEqual([...inicial].sort((a, b) => a - b))
  // el foco no se pierde al reordenar: se puede seguir apretando
  await expect(boton).toBeFocused()
  await page.keyboard.press('Space')
  await expect(rondas).toHaveAttribute('aria-sort', 'descending')

  // solo la columna ordenada lleva aria-sort
  const operador = tabla.locator('th', { hasText: 'Operador' })
  await operador.getByRole('button').click()
  await expect(operador).toHaveAttribute('aria-sort', 'descending')
  await expect(tabla.locator('th[aria-sort]')).toHaveCount(1)

  expect(errores).toEqual([])
})
