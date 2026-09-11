import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'

/**
 * Los numeros que afirma este archivo salen de `manage.py seed_demo`, que es
 * deterministico. Si cambia la tabla PERFIL de ese comando, cambian estos.
 */
const B_CHURCH = 'B Church, B Arsenal Room'
const A_VENTILATION = 'A Ventilation, A Workshop'

/**
 * Los tres paneles tienen tabla, asi que todo locator de fila va acotado al
 * suyo: sin acotar, un `tbody tr` cuenta tambien las filas de spawns.
 */
const panel = (page, titulo) => page.locator('.panel', { hasText: titulo })
const SITIOS = 'POR SITIO DE BOMBA'
const SPAWNS = 'POR SPAWN DE ATAQUE'

const fila = (page, sitio) => panel(page, SITIOS).locator('tbody tr', { hasText: sitio }).first()

test('la pagina dice de entrada lo que el formato no entrega', async ({ page }) => {
  await page.goto('/posicionamiento')
  // no es decoracion: es la promesa de que la pestana no finge tener
  // coordenadas. Si alguien la saca, esto tiene que fallar.
  const aviso = page.locator('.panel', { hasText: 'LO QUE SE PUEDE Y LO QUE NO' })
  await expect(aviso).toContainText('no trae coordenadas')
  await expect(aviso).toContainText('sitio de bomba y spawn de ataque')
})

test('marca el sitio malo, el bueno, y se calla en los del medio', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/posicionamiento')

  await expect(fila(page, B_CHURCH)).toContainText('85%')
  await expect(fila(page, B_CHURCH)).toContainText('Te agarran ahí')

  await expect(fila(page, A_VENTILATION)).toContainText('25%')
  await expect(fila(page, A_VENTILATION)).toContainText('Te sostienes')

  // los cuatro del medio no pasan la banda de ruido y ninguno puede afirmar nada
  const sinSenal = panel(page, SITIOS).locator('tbody tr', { hasText: 'Sin señal' })
  await expect(sinSenal).toHaveCount(4)

  expect(errores).toEqual([])
})

test('el delta y la banda que se ven son los que calcula la API', async ({ page, request }) => {
  await page.goto('/posicionamiento')

  const datos = await (await request.get('/api/positioning/?min_rounds=5')).json()
  const api = datos.sites.find((s) => s.site === B_CHURCH)

  // la fila trae el signo explicito y la banda con el ±, que es como se leen
  await expect(fila(page, B_CHURCH)).toContainText(`+${Math.round(api.caught_out_delta)} pts`)
  await expect(fila(page, B_CHURCH)).toContainText(`±${Math.round(api.noise)}`)
  await expect(fila(page, B_CHURCH)).toContainText(`${api.rounds}`)
})

test('las tarjetas resumen el peor y el mejor sitio', async ({ page }) => {
  await page.goto('/posicionamiento')
  const peor = page.locator('.stat', { hasText: 'PEOR ZONA' })
  const mejor = page.locator('.stat', { hasText: 'MEJOR ZONA' })
  await expect(peor).toContainText(B_CHURCH)
  await expect(mejor).toContainText(A_VENTILATION)
})

test('la muestra minima saca las zonas flacas de la tabla', async ({ page }) => {
  await page.goto('/posicionamiento')
  const sitios = panel(page, SITIOS).locator('tbody tr')

  // el default son 5 rondas, y el sitio de 4 no llega
  await expect(sitios).toHaveCount(6)
  await expect(sitios.filter({ hasText: 'A Vault' })).toHaveCount(0)

  await page.getByLabel('Muestra mínima').selectOption('3')
  await expect(sitios).toHaveCount(7)
  await expect(sitios.filter({ hasText: 'A Vault' })).toHaveCount(1)

  await page.getByLabel('Muestra mínima').selectOption('8')
  await expect(sitios).toHaveCount(6)
})

test('el filtro de lado deja solo los spawns de ataque en juego', async ({ page }) => {
  await page.goto('/posicionamiento')
  await expect(panel(page, SPAWNS).locator('tbody tr').first()).toBeVisible()

  // en defensa no hay spawn registrado, asi que la tabla queda vacia y lo dice
  await page.getByLabel('Lado').selectOption('Defense')
  await expect(panel(page, SPAWNS).getByText(/Ningún spawn llega a/)).toBeVisible()
})

test('la tabla por lado compara ataque contra defensa', async ({ page }) => {
  await page.goto('/posicionamiento')
  const lados = panel(page, 'POR LADO').locator('tbody tr')
  await expect(lados).toHaveCount(2)
  await expect(lados.filter({ hasText: 'Ataque' })).toBeVisible()
  await expect(lados.filter({ hasText: 'Defensa' })).toBeVisible()
})

test('el CSV que se baja trae el veredicto', async ({ page }) => {
  await page.goto('/posicionamiento')

  const [descarga] = await Promise.all([
    page.waitForEvent('download'),
    panel(page, SITIOS).getByRole('button', { name: 'Descargar CSV' }).click(),
  ])

  expect(descarga.suggestedFilename()).toMatch(/^posicion-sitios-\d{4}-\d{2}-\d{2}\.csv$/)
  const contenido = await (await descarga.createReadStream()).toArray()
  const texto = Buffer.concat(contenido).toString('utf8')

  expect(texto).toContain('Veredicto')
  expect(texto).toContain(B_CHURCH)
  expect(texto).toContain('dormidero')
  // punto y coma y coma decimal, que es lo que abre Excel en espanol
  expect(texto.split('\r\n')[0]).toContain(';')
})

test('el coach nombra la zona en la que te agarran', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/coach')
  await expect(page.getByText(B_CHURCH).first()).toBeVisible()
  expect(errores).toEqual([])
})
