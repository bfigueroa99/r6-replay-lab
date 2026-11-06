import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

// Ficha 96: los filtros globales viajan en la query de la URL. No afirma
// numeros del seed: compara lo que se ve antes y despues de recargar.

test('recargar conserva el filtro y los números', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/')
  const subtitulo = page.locator('.page-head p')
  await expect(subtitulo).toHaveText(/partidas · \d+ rondas analizadas/)
  const sinFiltro = await subtitulo.textContent()

  await page.getByLabel('Lado').selectOption('Defense')
  await expect(page).toHaveURL(/\/\?side=Defense$/)
  await expect(subtitulo).not.toHaveText(sinFiltro)
  await expect(subtitulo).toHaveText(/rondas/)
  const conFiltro = await subtitulo.textContent()

  // un select no deja historial: Atras sale de la app y no vuelve al "sin filtro"
  const largo = await page.evaluate(() => window.history.length)

  // sin esperar, el reload corta los fetch que el Resumen sigue haciendo y la consola los anota
  await page.waitForLoadState('networkidle')
  await page.reload()
  await expect(page.getByLabel('Lado')).toHaveValue('Defense')
  await expect(subtitulo).toHaveText(conFiltro)
  expect(await page.evaluate(() => window.history.length)).toBe(largo)

  expect(errores).toEqual([])
})

test('el menú lleva los filtros a la otra página', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/?side=Defense')
  await expect(page.getByLabel('Lado')).toHaveValue('Defense')

  await page.getByRole('navigation').getByRole('link', { name: 'Tendencias', exact: true }).click()
  await expect(page.locator('h1')).toHaveText('Tendencias')
  await expect(page).toHaveURL(/\/tendencias\?side=Defense$/)
  await expect(page.getByLabel('Lado')).toHaveValue('Defense')

  // Ruleta no tiene barra de filtros: su enlace va sin query
  await expect(page.getByRole('navigation').getByRole('link', { name: 'Ruleta', exact: true })).toHaveAttribute(
    'href',
    '/ruleta',
  )

  expect(errores).toEqual([])
})

test('una URL directa llega a la API sin los valores raros', async ({ page }) => {
  const errores = vigilarConsola(page)
  const pedido = page.waitForRequest(/\/api\/trends\/\?/)
  await page.goto('/tendencias?side=Defense&days=abc&foo=1')
  const url = new URL((await pedido).url())
  expect(url.searchParams.get('side')).toBe('Defense')
  expect(url.searchParams.has('days')).toBe(false)
  expect(url.searchParams.has('foo')).toBe(false)

  await expect(page.getByLabel('Lado')).toHaveValue('Defense')
  await expect(page.getByLabel('Periodo')).toHaveValue('')
  await expect(page).toHaveURL(/\/tendencias\?side=Defense$/)

  expect(errores).toEqual([])
})

test('volver del detalle de una partida no pierde los filtros', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/partidas')
  const mapa = page.getByLabel('Mapa')
  await expect(mapa.locator('option')).not.toHaveCount(1)
  await mapa.selectOption({ index: 1 })
  const elegido = await mapa.inputValue()
  await expect(page).toHaveURL(new RegExp(`/partidas\\?map=${encodeURIComponent(elegido)}$`))

  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/partidas\/\d+$/)

  await page.getByRole('navigation').getByRole('link', { name: 'Partidas', exact: true }).click()
  await expect(page).toHaveURL(new RegExp(`/partidas\\?map=${encodeURIComponent(elegido)}$`))
  await expect(page.getByLabel('Mapa')).toHaveValue(elegido)

  // y Atras desde ahi vuelve al detalle, no a una version sin filtros
  await page.goBack()
  await expect(page).toHaveURL(/\/partidas\/\d+$/)

  expect(errores).toEqual([])
})

test('un enlace interno sin query hereda los filtros', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/partidas?side=Attack')
  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/partidas\/\d+$/)
  // "Ver en Duelos" del aviso de stack rival es un Link a /duelos pelado
  await page.locator('.stacks-rivales').getByRole('link', { name: 'Ver en Duelos' }).click()
  await expect(page).toHaveURL(/\/duelos\?side=Attack$/)
  await expect(page.getByLabel('Lado')).toHaveValue('Attack')

  expect(errores).toEqual([])
})

test('Limpiar deja la URL sin query', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/coach?side=Attack&days=30')
  await expect(page.getByLabel('Lado')).toHaveValue('Attack')
  await expect(page.getByLabel('Periodo')).toHaveValue('30')

  await page.getByRole('button', { name: 'Limpiar' }).click()
  await expect(page).toHaveURL(/\/coach$/)
  await expect(page.getByLabel('Lado')).toHaveValue('')

  expect(errores).toEqual([])
})
