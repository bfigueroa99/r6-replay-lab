import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'
import { BASE_URL } from './entorno.js'

/** Ruta -> el h1 que tiene que aparecer. Son las ocho del menu. */
const PAGINAS = [
  ['/', 'Resumen'],
  ['/coach', 'Coach'],
  ['/operadores', 'Operadores'],
  ['/companeros', 'Compañeros'],
  ['/duelos', 'Duelos'],
  ['/tendencias', 'Tendencias'],
  ['/partidas', 'Partidas'],
  ['/datos', 'Datos'],
]

test.describe('todas las paginas cargan', () => {
  for (const [ruta, titulo] of PAGINAS) {
    test(`${titulo} (${ruta}) renderiza y no ensucia la consola`, async ({ page }) => {
      const errores = vigilarConsola(page)

      await page.goto(ruta)
      await expect(page.locator('h1')).toHaveText(titulo)
      // ninguna pagina deberia quedarse en "todavia no hay replays": el seed
      // tiene 200 rondas, asi que un empty state aca es un bug de datos
      await expect(page.locator('.empty-state')).toHaveCount(0)

      expect(errores, `errores de consola en ${ruta}`).toEqual([])
    })
  }
})

test('el menu navega sin recargar y carga los chunks lazy', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/')

  for (const [, titulo] of PAGINAS.slice(1)) {
    await page.getByRole('navigation').getByRole('link', { name: titulo, exact: true }).click()
    await expect(page.locator('h1')).toHaveText(titulo)
  }

  expect(errores).toEqual([])
})

test('el detalle de una partida se abre desde la lista', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/partidas')

  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/partidas\/\d+$/)
  await expect(page.locator('h1')).toContainText(/Club House|Border|Bank/)

  expect(errores).toEqual([])
})

test('el perfil de un jugador se abre desde Compañeros', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/companeros')

  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/jugadores\/\d+$/)
  await expect(page.locator('h1')).not.toBeEmpty()

  expect(errores).toEqual([])
})

test('tu perfil enlaza a los trackers y muestra Ubisoft sin salir a la red', async ({ page }) => {
  const errores = vigilarConsola(page)
  const afuera = []
  page.on('request', (request) => {
    if (!request.url().startsWith(BASE_URL)) afuera.push(request.url())
  })

  await page.goto('/')
  await page.locator('.topbar').getByRole('link', { name: 'BearF99' }).click()
  await expect(page).toHaveURL(/\/jugadores\/\d+$/)
  await expect(page.locator('h1')).toContainText('BearF99')

  // el profileID sale de seed_demo, que lo deriva del nick
  const pid = '14c9dacd-69a1-5ae1-80d8-ce1b96f8948f'
  await expect(page.getByRole('link', { name: /stats\.cc/ })).toHaveAttribute(
    'href',
    `https://stats.cc/siege/BearF99/${pid}`,
  )
  await expect(page.getByRole('link', { name: /R6 Tracker/ })).toHaveAttribute(
    'href',
    `https://r6.tracker.network/r6siege/profile/ubi/${pid}/overview`,
  )

  // la consulta guardada por el seed se ve; sin cuenta no hay boton para repetirla
  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Temporada en Ubisoft' }),
  })
  await expect(panel).toContainText('Oro 1')
  await expect(panel).toContainText('2950 MMR')
  await expect(panel).toContainText('Consultado el 01-09-2026 12:00 · temporada Y10S2.')
  await expect(panel.locator('code', { hasText: 'UBI_EMAIL' })).toBeVisible()
  await expect(panel.getByRole('button')).toHaveCount(0)

  // operadores, mapas y armas de la temporada; los dos primeros con su cruce contra los replays
  const detalle = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Operadores, mapas y armas en Ubisoft' }),
  })
  await expect(detalle.locator('tr', { hasText: 'Ash' }).locator('td')).toHaveText([
    'Ash', 'Ataque', '120', '55%', '1.20', '0.80', '50%', '39', '100%', '0.51',
  ])
  // CLUBHOUSE en Ubisoft es Club House en el replay
  await expect(detalle.locator('tr', { hasText: 'Clubhouse' }).locator('td')).toHaveText([
    'Clubhouse', '12', '90', '44%', '33%', '56%', '0.93', '70', '57%', '0.35',
  ])
  // las armas no tienen cruce: el replay no las trae
  await expect(detalle.locator('tr', { hasText: 'R4-C' }).locator('td')).toHaveText([
    'R4-C', 'Principal', 'Assault Rifle', '120', '55%', '90', '0.75', '50%',
  ])
  await expect(detalle).toContainText('Periodo según Ubisoft: del 01-06-2026 al 01-09-2026.')

  // otra playlist; un mapa que nunca jugaste en tus replays deja el cruce vacio
  await detalle.getByLabel('Playlist').selectOption('all')
  await expect(detalle.locator('tr', { hasText: 'Kafe' }).locator('td')).toHaveText([
    'Kafe Dostoyevsky', '4', '30', '40%', '—', '—', '0.80', '—', '—', '—',
  ])
  await expect(detalle.locator('tr', { hasText: 'Thermite' })).toBeVisible()

  // historial por temporada, cruzado por la version del juego de cada replay;
  // ordenado por numero y no por texto, que pondria Y9S4 primero
  const temporadas = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Temporadas en Ubisoft' }),
  })
  await expect(temporadas.locator('tbody tr').first().locator('td')).toHaveText([
    'Y10S2', '50', '60%', '400', '53%', '1.20', '0.75', '50%', '98', '57%', '0.77',
  ])
  await expect(temporadas.locator('tbody tr').nth(1)).toContainText('Y10S1')
  await expect(temporadas.locator('tbody tr').last().locator('td')).toHaveText([
    'Y9S4', '80', '50%', '640', '50%', '1.00', '0.62', '50%', '—', '—', '—',
  ])

  expect(afuera, 'la app pidio algo fuera de localhost').toEqual([])
  expect(errores).toEqual([])
})

test('una ruta que no existe no rompe la app', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/no-existe')

  await expect(page.getByText('Esa pagina no existe')).toBeVisible()
  await page.getByRole('link', { name: 'Volver al resumen' }).click()
  await expect(page.locator('h1')).toHaveText('Resumen')

  expect(errores).toEqual([])
})

test('la cabecera muestra el jugador y el volumen importado', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('.topbar')).toContainText('BearF99')
  await expect(page.locator('.topbar')).toContainText('29 partidas · 203 rondas')
})

test('Datos avisa cuando la carpeta de replays no existe', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/datos')

  // el e2e corre sin Siege: la carpeta detectada o por defecto no existe, y el
  // usuario tiene que enterarse ahi mismo de por que no aparecen partidas
  await expect(page.getByText('Esa carpeta no existe en este PC')).toBeVisible()
  await expect(page.getByText('Carpeta vigilada:')).toBeVisible()

  expect(errores).toEqual([])
})
