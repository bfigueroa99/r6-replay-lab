import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

// Postea sobre la base del e2e sin rehacerla: corre con `workers: 1`,
// `fullyParallel: false` y `retries: 0` (playwright.config.js), y servidor.js
// arma la base una sola vez por corrida. Va en su propio archivo para correr
// despues de humo (orden alfabetico) y el afterEach la deja como estaba;
// ruleta.spec.js no depende de ella porque el catalogo de operadores no filtra.

let partidaId = null

test.afterEach(async ({ request }) => {
  if (partidaId == null) return
  // idempotente: si el test fallo a mitad, la partida vuelve a contar igual
  await request.post(`/api/matches/${partidaId}/exclude/`, {
    headers: { 'Content-Type': 'application/json' },
    data: { excluded: false },
  })
})

test('excluir y volver a contar una partida no ensucia la consola', async ({ page, request }) => {
  const errores = vigilarConsola(page)
  const respuesta = await request.get('/api/matches/?limit=1')
  partidaId = (await respuesta.json()).matches[0].id

  // El Inicio sigue pidiendo coach, tendencias y filtros despues de pintar el
  // conteo; un goto en ese momento los aborta y vigilarConsola los cuenta.
  const salirDelInicio = () => page.waitForLoadState('networkidle')
  const conteo = page
    .locator('.stat', { has: page.locator('.label', { hasText: /^Rondas por partida$/ }) })
    .locator('.sub')

  // seed_demo: 29 partidas de 7 rondas (RONDAS_POR_PARTIDA)
  await page.goto('/')
  await expect(conteo).toHaveText('203 rondas en 29 partidas')
  await salirDelInicio()

  await page.goto(`/partidas/${partidaId}`)
  await page.getByRole('button', { name: 'Excluir de mis números' }).click()
  await expect(page.getByRole('button', { name: 'Volver a contarla' })).toBeVisible()
  await expect(page.getByText('Esta partida no cuenta en tus números.')).toBeVisible()

  await page.goto('/')
  await expect(conteo).toHaveText('196 rondas en 28 partidas')
  await salirDelInicio()

  await page.goto(`/partidas/${partidaId}`)
  await page.getByRole('button', { name: 'Volver a contarla' }).click()
  await expect(page.getByRole('button', { name: 'Excluir de mis números' })).toBeVisible()
  await expect(page.getByText('Esta partida no cuenta en tus números.')).toHaveCount(0)

  await page.goto('/')
  await expect(conteo).toHaveText('203 rondas en 29 partidas')
  await salirDelInicio()

  expect(errores).toEqual([])
})
