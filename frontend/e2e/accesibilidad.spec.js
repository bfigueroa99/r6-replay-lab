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

test('el resultado de importar se anuncia', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/')

  // la carpeta de replays del e2e no existe: no hay nada que importar
  await page.getByRole('button', { name: 'Importar replays' }).click()
  await expect(page.getByRole('status')).toHaveText('No había partidas nuevas para importar.')

  expect(errores).toEqual([])
})

test('los avisos de Ajustes salen en regiones que ya estaban en la pagina', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/ajustes')
  await expect(page.locator('h1')).toHaveText('Ajustes')

  // un lector de pantalla anuncia lo que cambia dentro de una region viva que
  // ya existia; una que aparece con el texto adentro puede quedar en silencio
  const regiones = page.locator('[role="status"], [role="alert"]')
  const antes = await regiones.count()
  const input = page.getByLabel('Carpeta de replays')
  await input.fill((await input.inputValue()).replace(/sin-replays$/, 'inventada'))
  await page.getByRole('button', { name: 'Guardar' }).click()

  await expect(page.getByRole('alert')).toContainText('No existe la carpeta')
  await expect(regiones).toHaveCount(antes)

  // el 400 de la API sale en la consola como recurso fallido, y es el esperado
  expect(errores.filter((e) => !e.includes('400'))).toEqual([])
})

const APP = 'R6 Replay Lab'

/** Nombre en el menu -> el h1 de la pagina, que aparece cuando ya cargo sus datos. */
const DEL_MENU = [
  ['Coach', 'Coach'],
  ['Operadores', 'Operadores'],
  ['Compañeros', 'Compañeros'],
  ['Duelos', 'Duelos'],
  ['Tendencias', 'Tendencias'],
  ['Partidas', 'Partidas'],
  ['Ruleta', 'Ruleta de operadores'],
  ['Datos', 'Datos'],
  ['Ajustes', 'Ajustes'],
]

test('cada pagina pone su nombre en el titulo del documento', async ({ page }) => {
  const errores = vigilarConsola(page)

  await page.goto('/')
  await expect(page.locator('h1')).toHaveText('Resumen')
  await expect(page).toHaveTitle(`Resumen · ${APP}`)

  // navegando por el menu, sin recargar: el titulo sigue a la ruta. Se espera
  // el h1 antes de seguir para no cortar las requests de la pagina a medias
  for (const [nombre, h1] of DEL_MENU) {
    await page.getByRole('navigation').getByRole('link', { name: nombre, exact: true }).click()
    await expect(page).toHaveTitle(`${nombre} · ${APP}`)
    await expect(page.locator('h1')).toHaveText(h1)
  }

  const partidas = (await (await page.request.get('/api/matches/?limit=2')).json()).matches
  await page.goto(`/partidas/${partidas[0].id}`)
  await expect(page.locator('h1')).toBeVisible()
  await expect(page).toHaveTitle(`Partida · ${APP}`)
  await page.goto(`/comparar/${partidas[0].id}/${partidas[1].id}`)
  await expect(page.locator('h1')).toHaveText('Comparar partidas')
  await expect(page.locator('table').first()).toBeVisible()
  await expect(page).toHaveTitle(`Comparar partidas · ${APP}`)
  await page.goto('/no-existe')
  await expect(page.getByRole('heading', { name: 'Esa página no existe' })).toBeVisible()
  await expect(page).toHaveTitle(`Esa página no existe · ${APP}`)

  expect(errores).toEqual([])
})
