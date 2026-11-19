import fs from 'node:fs'

import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

test('cada fila de Partidas dibuja su tira de rondas y el CSV la exporta legible', async ({ page }) => {
  const errores = vigilarConsola(page)
  // los datos salen de la API: seed_demo es deterministico pero sus numeros no son contrato
  const listado = await (await page.request.get('/api/matches/?limit=1')).json()
  const partida = listado.matches[0]
  expect(partida.strip.length).toBeGreaterThan(0)

  await page.goto('/partidas')
  await expect(page.locator('table th', { hasText: 'Secuencia' })).toBeVisible()
  const fila = page.locator('table tbody tr', { has: page.locator(`a[href="/partidas/${partida.id}"]`) })
  const celdas = fila.locator('.tira-celda')
  await expect(celdas).toHaveCount(partida.strip.length)
  await expect(celdas.first()).toHaveAttribute('title', /^R1 · /)
  const ganadas = partida.strip.filter((r) => r.won === true).length
  await expect(fila.locator('.tira-celda.win')).toHaveCount(ganadas)

  const [descarga] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'Descargar CSV' }).click(),
  ])
  const texto = fs.readFileSync(await descarga.path(), 'utf-8').replace(/^\ufeff/, '')
  const [cabecera, ...filas] = texto.split('\r\n').map((linea) => linea.split(';'))
  const columna = cabecera.indexOf('Secuencia')
  expect(columna).toBeGreaterThan(-1)
  expect(filas.length).toBeGreaterThan(0)
  const secuencias = filas.map((f) => f[columna]).filter(Boolean)
  expect(secuencias.length).toBeGreaterThan(0)
  for (const celda of secuencias) {
    // sin `csv:` la columna saldria como [object Object] / [object Object] ...
    expect(celda).toMatch(/^[GP-](?: (?:\| )?[GP-])*$/)
  }

  expect(errores).toEqual([])
})
