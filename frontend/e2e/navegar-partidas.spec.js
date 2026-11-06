import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

test('el detalle pasa a la partida anterior y siguiente, y las flechas cambian la ronda', async ({ page }) => {
  const errores = vigilarConsola(page)
  // la matriz de duelos tambien usa .round-tab: la ronda activa se busca solo en Rondas
  const activa = page
    .locator('section.panel', { has: page.getByRole('heading', { name: 'Rondas', exact: true }) })
    .locator('.round-tab.active .n')

  // los ids salen de la API: seed_demo es deterministico pero el orden de los ids no es contrato
  const listado = await (await page.request.get('/api/matches/?limit=1')).json()
  const detalleNueva = await (await page.request.get(`/api/matches/${listado.matches[0].id}/`)).json()
  const nueva = detalleNueva.match
  expect(nueva.next_id).toBeNull()
  expect(nueva.prev_id).not.toBeNull()
  const detallePrevia = await (await page.request.get(`/api/matches/${nueva.prev_id}/`)).json()
  const previa = detallePrevia.match
  expect(previa.next_id).toBe(nueva.id)
  // las flechas necesitan al menos dos rondas en las dos partidas
  expect(detalleNueva.rounds.length).toBeGreaterThanOrEqual(2)
  expect(detallePrevia.rounds.length).toBeGreaterThanOrEqual(2)
  // en seed_demo las vecinas mas nuevas comparten mapa y marcador: el h1 no las distingue, la fecha si
  const fecha = (m) => m.played_at.slice(0, 16).replace('T', ' ')
  expect(fecha(previa)).not.toBe(fecha(nueva))
  const fechaEnPantalla = page.locator('.page-head p').first()

  await page.goto(`/partidas/${nueva.id}`)
  await expect(page.locator('h1')).toContainText(`${nueva.map} · ${nueva.score}`)
  await expect(fechaEnPantalla).toContainText(fecha(nueva))
  await expect(page.getByRole('button', { name: 'Partida siguiente →' })).toBeDisabled()

  // ir a otra ronda antes de cambiar de partida: la nueva tiene que volver a R1
  await page.keyboard.press('ArrowRight')
  await expect(activa).toHaveText('R2')

  await page.getByRole('link', { name: '← Partida anterior' }).click()
  await expect(page).toHaveURL(new RegExp(`/partidas/${previa.id}$`))
  await expect(page.locator('h1')).toContainText(`${previa.map} · ${previa.score}`)
  await expect(fechaEnPantalla).toContainText(fecha(previa))
  await expect(activa).toHaveText('R1')

  await page.keyboard.press('ArrowRight')
  await expect(activa).toHaveText('R2')
  await page.keyboard.press('ArrowLeft')
  await expect(activa).toHaveText('R1')
  await page.keyboard.press('ArrowLeft')
  await expect(activa).toHaveText('R1')

  await page.getByRole('link', { name: 'Partida siguiente →' }).click()
  await expect(page).toHaveURL(new RegExp(`/partidas/${nueva.id}$`))
  await expect(page.locator('h1')).toContainText(`${nueva.map} · ${nueva.score}`)
  await expect(fechaEnPantalla).toContainText(fecha(nueva))

  expect(errores).toEqual([])
})
