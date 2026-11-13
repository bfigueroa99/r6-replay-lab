import fs from 'node:fs'

import { expect, test } from '@playwright/test'

import { vigilarConsola } from './consola.js'
import { BASE_URL } from './entorno.js'

// backend/tests/test_partida_sin_rondas.py afirma que es la forma real del detalle sin
// rondas; si falla, se regenera con json.dumps(indent=2, ensure_ascii=False) de esa respuesta. Con fs y no con import attributes: el Node del PC puede ser otro
const SIN_RONDAS = JSON.parse(
  fs.readFileSync(new URL('./partida-sin-rondas.json', import.meta.url), 'utf8'),
)

/** Ruta -> el h1 que tiene que aparecer. Las del menu, menos la Ruleta (tiene su spec). */
const PAGINAS = [
  ['/', 'Resumen'],
  ['/coach', 'Coach'],
  ['/operadores', 'Operadores'],
  ['/companeros', 'Compañeros'],
  ['/duelos', 'Duelos'],
  ['/tendencias', 'Tendencias'],
  ['/partidas', 'Partidas'],
  ['/datos', 'Datos'],
  ['/ajustes', 'Ajustes'],
]

// Una ruta interceptada que sigue en vuelo cuando el test termina (la app
// vuelve a pedir /api/filters/ despues de la ultima asercion) tumbaba al worker
// con "route.fetch: Test ended". Lo que se pide despues de las aserciones no es
// parte de la prueba.
test.afterEach(async ({ page }) => {
  await page.unrouteAll({ behavior: 'ignoreErrors' })
})

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

test('Tendencias muestra la tabla por mitad', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', { hasText: 'Por mitad de la partida' })
  await expect(panel).toBeVisible()
  await expect(panel.getByRole('cell', { name: 'Primera mitad', exact: true })).toBeVisible()
  await expect(panel.getByRole('cell', { name: 'Segunda mitad', exact: true })).toBeVisible()
  // seed_demo alterna el lado cada ronda: la primera tras el cambio es R2 y las tres filas tienen rondas
  await expect(panel.getByText('Primera ronda de cada lado')).toBeVisible()
  for (const tramo of ['Ronda 1', 'Primera tras el cambio', 'Resto']) {
    await expect(panel.getByRole('cell', { name: tramo, exact: true })).toBeVisible()
  }
  await expect(panel.getByText('Según el lado con que arrancas')).toBeVisible()
  // seed_demo arranca siempre en ataque: defensa queda sin muestra y no hay veredicto
  await expect(panel.getByText('Lado inicial por mapa')).toBeVisible()
  await expect(panel.getByRole('cell', { name: 'Bank', exact: true })).toBeVisible()
  await expect(panel.getByRole('cell', { name: 'Poca muestra', exact: true }).first()).toBeVisible()

  expect(errores).toEqual([])
})

test('Tendencias muestra la prórroga por lado', async ({ page }) => {
  const errores = vigilarConsola(page)
  // seed_demo no tiene prorrogas: la API da las dos filas en cero y la UI una nota, no ceros
  const datos = await (await page.request.get('/api/trends/')).json()
  expect(datos.by_overtime_side.map((f) => [f.side, f.rounds])).toEqual([['Attack', 0], ['Defense', 0]])
  expect(datos.by_overtime_start_side.map((f) => [f.side, f.matches])).toEqual([['Attack', 0], ['Defense', 0]])
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', { hasText: 'Por mitad de la partida' })
  await expect(panel.getByRole('heading', { name: 'Prórroga por lado', exact: true })).toBeVisible()
  await expect(panel.getByText('Sin rondas de prórroga con estos filtros.')).toBeVisible()
  await expect(panel.getByRole('cell', { name: 'Prórroga en ataque', exact: true })).toHaveCount(0)

  expect(errores).toEqual([])
})

test('Tendencias muestra mapas y operadores que cambian', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', { hasText: 'Progreso' }).first()
  await expect(panel.getByRole('heading', { name: 'Mapas', exact: true })).toBeVisible()
  // con la ventana de 10 partidas el seed juega Bank en una y Border y Club House en la otra
  await expect(panel.getByText('Sin muestra en los dos periodos (10+ rondas en cada uno).')).toBeVisible()
  // cada operador del seed junta 10 a 14 rondas por periodo
  await expect(panel.locator('h3:text-is("Operadores") + .table-wrap tbody tr')).toHaveCount(6)
  await expect(panel.getByRole('cell', { name: /^Ash Ataque$/ })).toBeVisible()

  expect(errores).toEqual([])
})

test('Operadores muestra presencia y delta', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/operadores')

  const panel = page.locator('section.panel', { has: page.getByRole('heading', { name: 'Ataque', exact: true }) })
  await expect(panel.locator('th', { hasText: 'Presencia' })).toBeVisible()
  await expect(panel.locator('th', { hasText: 'vs. tu lado' })).toBeVisible()
  // seed: 39 de 116 rondas de ataque con Ash; todo el ataque se gana, asi que
  // el delta es 0 (y no -0). Columnas: operador, lado, rondas, presencia, ganadas, delta
  const ash = panel.locator('tr', { has: page.getByRole('cell', { name: 'Ash', exact: true }) })
  await expect(ash.locator('td').nth(3)).toHaveText('34%')
  await expect(ash.locator('td').nth(5)).toHaveText('0')

  expect(errores).toEqual([])
})

test('Operadores muestra tu pool por lado', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/operadores')

  // seed: 3 operadores por lado, todos en las ultimas 20 partidas y ninguno viejo
  const panel = page.locator('section.panel', { has: page.getByRole('heading', { name: 'Tu pool', exact: true }) })
  const ataque = panel.locator('div:has(> h3:text-is("Ataque"))')
  const defensa = panel.locator('div:has(> h3:text-is("Defensa"))')
  await expect(ataque).toContainText('3 operadores distintos')
  await expect(defensa).toContainText('3 operadores distintos')
  await expect(ataque).toContainText('Sin jugar hace más de 30 días: ninguno')
  await expect(ataque.locator('.chip', { hasText: /^Sledge$/ })).toHaveCount(1)
  await expect(ataque.locator('.chip', { hasText: /^Thermite$/ })).toHaveCount(0)

  await page.goto('/operadores?side=Attack')
  await expect(panel.locator('h3:text-is("Ataque")')).toBeVisible()
  await expect(panel.locator('h3:text-is("Defensa")')).toHaveCount(0)

  expect(errores).toEqual([])
})

test('Operadores muestra si repites o cambias de operador', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/operadores')

  // seed: rota operador cada ronda, gana todo el ataque y pierde toda la
  // defensa. 145 pares, todos cambian: 87 de ataque tras ganar, 58 de defensa
  // tras perder. Columnas: lado, tras, repite, winrate, cambia, winrate
  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Repetir o cambiar tras perder', exact: true }),
  })
  // La primera tabla del panel; la segunda es la de la ficha 126
  const filas = panel.locator('table').first().locator('tbody tr')
  await expect(filas).toHaveCount(4)
  await expect(filas.nth(0).locator('td')).toHaveText(['Total', 'Tras perder', '0', '—', '58', '0%'])
  await expect(filas.nth(1).locator('td')).toHaveText(['Total', 'Tras ganar', '0', '—', '87', '100%'])
  await expect(filas.nth(2).locator('td')).toHaveText(['Ataque', 'Tras ganar', '0', '—', '87', '100%'])
  await expect(filas.nth(3).locator('td')).toHaveText(['Defensa', 'Tras perder', '0', '—', '58', '0%'])

  await page.goto('/operadores?side=Defense')
  await expect(filas).toHaveCount(1)
  await expect(filas.nth(0).locator('td').first()).toHaveText('Defensa')

  await page.goto('/operadores?operator=Ash')
  await expect(panel.locator('table').first().locator('tr', { hasText: 'Ataque' }).locator('td').nth(4)).toHaveText('29')

  expect(errores).toEqual([])
})

test('Operadores muestra a qué operador cambias tras perder', async ({ page }) => {
  const errores = vigilarConsola(page)
  const datos = await (await page.request.get('/api/operators/after-result/')).json()
  // seed: la defensa pierde todo y rota Jager -> Mute -> Rook; la suma de los
  // pares es el «Cambia» de defensa tras perder (58). Mas rondas, primero
  const mayor = [...datos.switches].sort((x, y) => y.rounds - x.rounds)[0]
  expect(datos.switches.reduce((n, f) => n + f.rounds, 0)).toBe(datos.sides.Defense.after_loss.switch.rounds)
  await page.goto('/operadores')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Repetir o cambiar tras perder', exact: true }),
  })
  await expect(panel.getByRole('heading', { name: 'A qué operador cambias tras perder' })).toBeVisible()
  const filas = panel.locator('table').nth(1).locator('tbody tr')
  await expect(filas).toHaveCount(datos.switches.length)
  await expect(filas.nth(0).locator('td')).toHaveText([
    'Defensa',
    mayor.from_operator,
    mayor.to_operator,
    String(mayor.rounds),
    '0%',
  ])

  // El ataque gana todo: no hay cambios tras perder y se dice, no se rompe.
  // Antes de navegar, que termine lo que pidio la primera carga: un goto con
  // /api/filters/ en vuelo la aborta y la consola la cuenta como fallida.
  await page.waitForLoadState('networkidle')
  await page.goto('/operadores?side=Attack')
  await expect(panel.getByText('No cambiaste de operador tras perder con estos filtros.')).toBeVisible()

  expect(errores).toEqual([])
})

test('Operadores filtra por operador desde su propio selector', async ({ page }) => {
  const errores = vigilarConsola(page)
  const datos = await (await page.request.get('/api/operators/after-result/?operator=Ash')).json()
  await page.goto('/operadores')

  // Ataque y Defensa se piden sin `operator`; mientras recarga, la tabla vieja sigue a la vista
  const pedidosPool = []
  page.on('request', (req) => {
    if (new URL(req.url()).pathname === '/api/operators/') pedidosPool.push(req.url())
  })
  const nota = page.getByText('Con Ash elegido')
  await expect(nota).toHaveCount(0)
  const recarga = page.waitForResponse((resp) => resp.url().includes('/api/operators/after-result/?operator=Ash'))
  await page.getByLabel('Operador').selectOption('Ash')
  await recarga
  await expect(page).toHaveURL(/operator=Ash/)

  // seed: 3 operadores por lado; Ataque y Defensa no se vacian, la fila de Ash se resalta
  const ataque = page.locator('section.panel', { has: page.getByRole('heading', { name: 'Ataque', exact: true }) })
  const defensa = page.locator('section.panel', { has: page.getByRole('heading', { name: 'Defensa', exact: true }) })
  await expect(ataque.locator('tbody tr')).toHaveCount(3)
  await expect(defensa.locator('tbody tr')).toHaveCount(3)
  const ash = ataque.locator('tbody tr', { has: page.getByRole('cell', { name: 'Ash', exact: true }) })
  await expect(ash).toHaveClass(/\bme\b/)
  await expect(ash.locator('[aria-current="true"]')).toHaveText('Ash')
  await expect(ataque.locator('tbody tr.me')).toHaveCount(1)
  await expect(defensa.locator('tbody tr.me')).toHaveCount(0)
  await expect(nota).toBeVisible()
  expect(pedidosPool.length).toBeGreaterThan(0)
  expect(pedidosPool.filter((url) => url.includes('operator='))).toEqual([])

  // Repetir o cambiar si se filtra a Ash: el Cambia de ataque es el de la API
  const repetir = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Repetir o cambiar tras perder', exact: true }),
  })
  const filaAtaque = repetir.locator('table').first().locator('tr', { hasText: 'Ataque' })
  await expect(filaAtaque.locator('td').nth(4)).toHaveText(String(datos.sides.Attack.after_win.switch.rounds))

  await page.getByLabel('Operador').selectOption('')
  await expect(page).not.toHaveURL(/operator=/)
  await expect(page.locator('tbody tr.me')).toHaveCount(0)
  await expect(nota).toHaveCount(0)

  expect(errores).toEqual([])
})

test('Operadores sin rondas deja quitar el operador', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/operadores?operator=Ash&until=2000-01-01')

  await expect(page.getByText('0 rondas con estos filtros')).toBeVisible()
  const selector = page.getByLabel('Operador')
  await expect(selector).toHaveValue('Ash')
  await selector.selectOption('')
  await expect(page).not.toHaveURL(/operator=/)

  // Ash es de ataque: con defensa no hay fila que resaltar y la nota no aparece
  await page.goto('/operadores?side=Defense&operator=Ash')
  // level 2: el h3 Defensa de Tu pool se llama igual y, si ya cargo, el locator
  // sin nivel cae en strict mode. La nota sale de la misma respuesta que el h2
  await expect(page.getByRole('heading', { level: 2, name: 'Defensa', exact: true })).toBeVisible()
  await expect(page.getByText('Con Ash elegido')).toHaveCount(0)
  await expect(page.locator('tbody tr.me')).toHaveCount(0)

  expect(errores).toEqual([])
})

test('Operadores muestra el operador por sitio', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/operadores')

  // seed: el maximo es 8 rondas de un operador en un sitio, menos que el
  // minimo de 10, asi que el panel dice por que esta vacio
  const panel = page.locator('section.panel', { has: page.getByRole('heading', { name: 'Por sitio', exact: true }) })
  await expect(panel).toContainText('Ningún operador llega a 10 rondas en un sitio')

  // con el minimo bajo hay filas; todo el ataque del seed se gana y toda la
  // defensa se pierde, asi que ningun operador se separa del resto
  const resp = await page.request.get('/api/operators/sites/?min_rounds=5')
  expect(resp.ok()).toBe(true)
  const datos = await resp.json()
  expect(datos.rows.length).toBeGreaterThan(0)
  for (const fila of datos.rows) {
    expect(fila.verdict).toBe('ruido')
    expect(fila.winrate_delta).toBe(0)
  }

  // la tabla tambien se renderiza: misma request con el minimo bajo
  await page.route('**/api/operators/sites/**', async (route) => {
    const url = new URL(route.request().url())
    url.searchParams.set('min_rounds', '5')
    await route.fulfill({ response: await route.fetch({ url: url.toString() }) })
  })
  await page.reload()
  const filas = panel.locator('tbody tr')
  await expect(filas).toHaveCount(datos.rows.length)
  await expect(filas.first()).toContainText('Sin señal')
  await expect(panel.locator('th', { hasText: 'Veredicto' })).toBeVisible()

  // el seed no tiene deltas distintos de 0: dos filas fijas prueban que la
  // tabla sale en el orden del backend (|delta|) y no ordenada por mapa
  const fila = (map, operator, delta, verdict) => ({
    map, slug: map.toLowerCase(), map_id: 0, site: 'A Sitio', side: 'Attack', operator,
    rounds: 20, rounds_won: 10, winrate: 50, rest_rounds: 20, rest_winrate: 50 - delta,
    winrate_delta: delta, margin: 10, verdict,
  })
  await page.unroute('**/api/operators/sites/**')
  await page.route('**/api/operators/sites/**', (route) =>
    route.fulfill({
      json: { rows: [fila('Bank', 'Ash', -30, 'hunde'), fila('Oregon', 'Zofia', 5, 'ruido')], min_rounds: 10, bands: 2 },
    }),
  )
  await page.reload()
  await expect(filas).toHaveCount(2)
  await expect(filas.first()).toContainText('Bank')
  await expect(filas.first()).toContainText('Te hunde')
  await expect(filas.nth(1)).toContainText('Oregon')

  expect(errores).toEqual([])
})

test('Tendencias muestra el puesto en el lobby', async ({ page }) => {
  const errores = vigilarConsola(page)
  const { lobby_rank: puesto } = await (await page.request.get('/api/trends/')).json()
  expect(puesto.best_in_lobby.matches).toBeGreaterThan(0)
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', { hasText: 'Puesto en el lobby' })
  await expect(panel).toBeVisible()
  for (const etiqueta of ['Mejor de la partida', 'Mejor de tu equipo', 'Último de la partida']) {
    await expect(panel.getByText(etiqueta, { exact: true })).toBeVisible()
  }
  // los numeros salen de la API, no a mano: si cambia el seed el test sigue al dato
  const { count, matches } = puesto.best_in_lobby
  const sub = `${count} de ${matches} ${matches === 1 ? 'partida' : 'partidas'}`
  await expect(panel.locator('.stat', { hasText: 'Mejor de la partida' }).locator('.sub')).toHaveText(sub)

  expect(errores).toEqual([])
})

test('Tendencias muestra la inercia entre rondas', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', { hasText: 'Después de ganar o perder la ronda anterior' })
  await expect(panel).toBeVisible()
  // seed_demo alterna ganada y perdida: despues de ganar siempre pierdes y al reves
  const ganar = panel.locator('tr', { has: page.getByRole('cell', { name: 'Después de ganar', exact: true }) })
  const perder = panel.locator('tr', { has: page.getByRole('cell', { name: 'Después de perder', exact: true }) })
  // columnas: tramo, rondas, ganadas
  await expect(ganar.locator('td').nth(2)).toHaveText('0%')
  await expect(perder.locator('td').nth(2)).toHaveText('100%')
  await expect(panel.getByRole('cell', { name: 'Sin ronda anterior', exact: true })).toBeVisible()

  expect(errores).toEqual([])
})

test('Tendencias muestra las rondas segun el marcador', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', { hasText: 'Según el marcador' })
  await expect(panel).toBeVisible()
  // seed_demo gana las rondas pares: llega empatado a las pares y adelante a las impares
  await expect(panel.getByRole('cell', { name: 'Adelante', exact: true })).toBeVisible()
  await expect(panel.getByRole('cell', { name: 'Empatado', exact: true })).toBeVisible()
  await expect(panel.getByRole('cell', { name: 'Sin marcador', exact: true })).toHaveCount(0)

  expect(errores).toEqual([])
})

test('Tendencias muestra el match point', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Match point', exact: true }),
  })
  await expect(panel).toBeVisible()
  // seed_demo es ranked Y9S4: la ronda 5 llega 3-2 (tu match point) y la 6 llega 3-3 (prorroga)
  await expect(panel.getByRole('cell', { name: 'Tu match point', exact: true })).toBeVisible()
  await expect(panel.getByRole('cell', { name: 'Sin match point', exact: true })).toBeVisible()
  await expect(panel.getByRole('cell', { name: 'Sin marcador o sin regla', exact: true })).toHaveCount(0)

  expect(errores).toEqual([])
})

test('Tendencias muestra remontadas y derrumbes', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Remontadas y derrumbes', exact: true }),
  })
  await expect(panel).toBeVisible()
  // seed_demo alterna el marcador (nunca 2 de diferencia) y gana sus 29 partidas,
  // todas Y9S4: listas vacias y todas llegan +1 al cambio de lado
  await expect(panel.getByText('Ninguna remontada de 2 o más rondas todavía.')).toBeVisible()
  await expect(panel.getByText('Ningún derrumbe de 2 o más rondas todavía.')).toBeVisible()
  const filas = panel.locator('tbody tr')
  await expect(filas).toHaveCount(5)
  const masUno = filas.filter({ has: page.getByRole('cell', { name: '+1', exact: true }) })
  await expect(masUno.getByRole('cell', { name: '29', exact: true })).toHaveCount(2)
  await expect(masUno.getByRole('cell', { name: '100%', exact: true })).toBeVisible()

  expect(errores).toEqual([])
})

test('Tendencias muestra partidas cerradas y holgadas', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Partidas cerradas y holgadas', exact: true }),
  })
  await expect(panel).toBeVisible()
  // seed_demo gana sus 29 partidas 4-3 sin prorroga, todas Y9S4. Es sintetico: en ranked
  // un 3-3 va a prorroga, pero el panel lee la prorroga de `overtime_number`, como Mitades
  const filas = panel.locator('tbody tr')
  await expect(filas).toHaveCount(4)
  const unaRonda = filas.filter({ has: page.getByRole('cell', { name: '1 ronda', exact: true }) })
  await expect(unaRonda.getByRole('cell', { name: '29', exact: true })).toHaveCount(2)
  await expect(unaRonda.getByRole('cell', { name: '100%', exact: true })).toBeVisible()

  expect(errores).toEqual([])
})

test('Tendencias muestra como se cierran tus rondas', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', { hasText: 'Cómo se cierran tus rondas' })
  await expect(panel).toBeVisible()
  await expect(panel.getByRole('cell', { name: 'Ataque', exact: true })).toBeVisible()
  await expect(panel.getByRole('cell', { name: 'Defensa', exact: true })).toBeVisible()
  // seed_demo cierra todo por eliminacion salvo una ronda de Bank en ataque (el clutch
  // silencioso, cierre inferido): los numeros los afirman los tests de backend

  expect(errores).toEqual([])
})

test('Tendencias muestra cuando matas', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Cuándo matas', exact: true }),
  })
  await expect(panel).toBeVisible()
  // seed_demo: 99 bajas a rivales (las mismas que Bajas de Duelos), ninguna antes de 30 s
  const tramos = panel.locator('tbody tr')
  await expect(tramos).toHaveCount(4)
  const pico = tramos.filter({ has: page.getByRole('cell', { name: '90-120s', exact: true }) })
  await expect(pico.locator('td')).toHaveText(['90-120s', '53', '54%', '34', '19'])

  expect(errores).toEqual([])
})

test('Tendencias muestra cuando llega la apertura', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Cuándo llega la apertura', exact: true }),
  })
  await expect(panel).toBeVisible()
  // 4 tramos x 2 lados, siempre todos; seed_demo gana todo el ataque y pierde toda la defensa
  const filas = panel.locator('tbody tr')
  await expect(filas).toHaveCount(8)
  await expect(filas.nth(2).locator('td')).toHaveText(['Ataque', 'Tarde (90 s o más)', '66', '100%', '14%'])
  await expect(filas.nth(5).locator('td')).toHaveText(['Defensa', 'Medio (30–90 s)', '37', '0%', '0%'])

  expect(errores).toEqual([])
})

test('Tendencias muestra rondas cortas y largas', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Rondas cortas y largas', exact: true }),
  })
  await expect(panel).toBeVisible()
  // seed_demo: todas las rondas van de 180 a 20 en el reloj (160 s) y ninguna es posible
  // plant, asi que todo cae en "135 s o mas". El reparto lo prueban los tests de backend
  const tramos = panel.locator('table').first().locator('tbody tr')
  await expect(tramos).toHaveCount(5)
  const larga = tramos.filter({ has: page.getByRole('cell', { name: '135 s o más', exact: true }) })
  for (const texto of ['100% (116)', '0% (87)', '57% (203)', '1.00', '0.49']) {
    await expect(larga.getByRole('cell', { name: texto, exact: true })).toBeVisible()
  }
  const corta = tramos.filter({ has: page.getByRole('cell', { name: '0–45 s', exact: true }) })
  await expect(corta.getByRole('cell', { name: '—', exact: true })).toHaveCount(5)

  const promedios = panel.locator('table').nth(1).locator('tbody tr')
  const fila = (lado) => promedios.filter({ has: page.getByRole('cell', { name: lado, exact: true }) })
  await expect(fila('Ataque').locator('td')).toHaveText(['Ataque', '116', '160 s', '—'])
  await expect(fila('Defensa').locator('td')).toHaveText(['Defensa', '87', '—', '160 s'])
  await expect(fila('Total').locator('td')).toHaveText(['Total', '203', '160 s', '160 s'])

  expect(errores).toEqual([])
})

test('Tendencias muestra hora y dia de la semana', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/tendencias')

  const hora = page.locator('section.panel', { hasText: 'Por hora del día' })
  await expect(hora).toBeVisible()
  await expect(hora.getByRole('cell', { name: '21–24 h', exact: true })).toBeVisible()
  const dia = page.locator('section.panel', { hasText: 'Por día de la semana' })
  await expect(dia).toBeVisible()
  await expect(dia.getByRole('cell', { name: 'Lunes', exact: true })).toBeVisible()
  await expect(dia.getByRole('cell', { name: 'Domingo', exact: true })).toBeVisible()

  expect(errores).toEqual([])
})

test('Duelos muestra rivales repetidos con enlace al perfil', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/duelos')

  const panel = page.locator('section.panel', { hasText: 'Rivales repetidos' })
  await expect(panel).toBeVisible()
  // la ultima vez de la primera fila es la de la API: el orden inicial (partidas) es estable
  const { rivals } = await (await page.request.get('/api/duels/')).json()
  const [anio, mes, dia] = rivals[0].last_played.slice(0, 10).split('-')
  await expect(panel.locator('tbody tr').first()).toBeVisible()
  const cabeceras = await panel.locator('thead th').evaluateAll((ths) => ths.map((th) => th.textContent.trim()))
  const ultima = cabeceras.findIndex((t) => t.startsWith('Última vez'))
  expect(ultima).toBeGreaterThan(-1)
  await expect(panel.locator('tbody tr').first().locator('td').nth(ultima)).toHaveText(`${dia}-${mes}-${anio}`)
  // seed_demo repite los mismos rivales en todas las partidas
  const enlace = panel.locator('table tbody tr').first().getByRole('link').first()
  await expect(enlace).toHaveAttribute('href', /\/jugadores\/\d+$/)
  await enlace.click()
  await expect(page).toHaveURL(/\/jugadores\/\d+$/)

  expect(errores).toEqual([])
})

test('Duelos muestra el estado de vivos al morir', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/duelos')

  const panel = page.locator('section.panel', { hasText: 'Estado al morir' })
  await expect(panel).toBeVisible()
  // seed_demo: 173 muertes con evento, 87 con ventaja (4v3) y 86 en paridad (3v3)
  const grupos = panel.locator('table').first()
  await expect(grupos.locator('tbody tr')).toHaveCount(3)
  const ventaja = grupos.locator('tbody tr', { hasText: 'Con ventaja' })
  await expect(ventaja.getByRole('cell', { name: '87', exact: true })).toBeVisible()
  const estados = panel.locator('table').nth(1)
  await expect(estados.locator('tbody tr').first()).toContainText('4v3')
  await expect(estados.locator('tbody tr', { hasText: '3v3' }).getByRole('cell', { name: '86', exact: true })).toBeVisible()

  expect(errores).toEqual([])
})

test('Duelos muestra la ventaja numerica tirada', async ({ page }) => {
  const errores = vigilarConsola(page)
  // numeros de la API y no a mano: si cambia seed_demo el test no se toca
  const datos = await (await page.request.get('/api/duels/thrown-advantage/')).json()
  await page.goto('/duelos')

  const panel = page.locator('section.panel', { hasText: 'Ventaja numérica tirada' })
  await expect(panel.getByRole('heading', { name: 'Ventaja numérica tirada' })).toBeVisible()
  if (datos.rounds === 0) {
    await expect(panel).toContainText('No hay rondas con ventaja numérica con estos filtros.')
    expect(errores).toEqual([])
    return
  }
  await expect(panel).toContainText(`${datos.thrown} de ${datos.rounds} rondas con ventaja tiradas`)
  const grupos = panel.locator('table').first()
  await expect(grupos.locator('tbody tr')).toHaveCount(2)
  for (const [grupo, etiqueta] of [['one', 'Con uno más'], ['two_plus', 'Con dos o más']]) {
    const g = datos.groups.find((x) => x.group === grupo)
    const fila = grupos.locator('tbody tr', { hasText: etiqueta })
    await expect(fila.locator('td').nth(1)).toHaveText(String(g.rounds))
    await expect(fila.locator('td').nth(2)).toHaveText(String(g.thrown))
  }
  const ataque = datos.sides.find((x) => x.side === 'Attack')
  const filaAtaque = panel.locator('table').nth(1).locator('tbody tr', { hasText: 'Ataque' })
  await expect(filaAtaque.locator('td').nth(1)).toHaveText(String(ataque.rounds))
  await expect(filaAtaque.locator('td').nth(2)).toHaveText(String(ataque.thrown))
  const mapa = datos.maps[0]
  // celda exacta: "Club House" no tiene que tomar tambien la fila "Club House (Y10)"
  const filaMapa = panel.locator('table').nth(2).locator('tbody tr')
    .filter({ has: page.getByRole('cell', { name: mapa.map, exact: true }) })
  await expect(filaMapa.locator('td').nth(1)).toHaveText(String(mapa.rounds))
  await expect(filaMapa.locator('td').nth(2)).toHaveText(String(mapa.thrown))

  if (datos.recent.length) {
    const primera = datos.recent[0]
    const enlace = panel.locator('table').last().getByRole('link').first()
    await expect(enlace).toHaveAttribute('href', `/partidas/${primera.match_id}#ronda-${primera.round}`)
    await enlace.click()
    await expect(page).toHaveURL(new RegExp(`/partidas/${primera.match_id}#ronda-${primera.round}$`))
    await expect(page.locator('#rondas .round-tab.active .n')).toHaveText(`R${primera.round}`)
  }

  expect(errores).toEqual([])
})

test('Duelos muestra los operadores que te abren', async ({ page }) => {
  const errores = vigilarConsola(page)
  // numeros de la API y no a mano: si cambia seed_demo el test no se toca
  const datos = await (await page.request.get('/api/duels/?min_duels=3')).json()
  const filas = datos.opening_operators
  await page.goto('/duelos')

  const panel = page.locator('section.panel', { hasText: 'Operadores que te abren' })
  await expect(panel.getByRole('heading', { name: 'Operadores que te abren' })).toBeVisible()
  // seed_demo trae aperturas por operador: sin filas, el test no estaria mirando la tabla
  expect(filas.length).toBeGreaterThan(0)
  await expect(panel.locator('table tbody tr')).toHaveCount(filas.length)
  const primera = panel.locator('table tbody tr').first()
  await expect(primera.locator('td').nth(0)).toHaveText(filas[0].operator)
  await expect(primera.locator('td').nth(2)).toHaveText(String(filas[0].opened_you))

  expect(errores).toEqual([])
})

test('el CSV de rivales repetidos trae el récord de cada rival', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/duelos')

  const panel = page.locator('section.panel', { hasText: 'Rivales repetidos' })
  await expect(panel.locator('table tbody tr').first()).toBeVisible()
  const [descarga] = await Promise.all([
    page.waitForEvent('download'),
    panel.getByRole('button', { name: 'Descargar CSV' }).click(),
  ])
  const texto = fs.readFileSync(await descarga.path(), 'utf-8').replace(/^\ufeff/, '')
  const [cabecera, ...filas] = texto.split('\r\n').map((linea) => linea.split(';'))
  const col = (nombre) => cabecera.indexOf(nombre)
  expect(filas.length).toBeGreaterThan(0)
  // `record` no viene en las filas de la API: sin `csv:` la celda salia vacia.
  // Va con raya (–) y no con guion: "3-1" Excel lo abre como el 3 de enero
  for (const fila of filas) {
    expect(fila[col('Récord')]).toBe(`${fila[col('Ganadas')]}–${fila[col('Perdidas')]}`)
  }

  expect(errores).toEqual([])
})

test('el Resumen muestra tus records y enlaza a la partida', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/')

  const panel = page.locator('section.panel', { hasText: 'Tus récords' })
  await expect(panel).toBeVisible()
  const fila = panel.locator('tr', { hasText: 'Más bajas en una partida' })
  await expect(fila).toBeVisible()
  // seed_demo alterna el resultado ronda a ronda: toda racha es de una. Se
  // afirma antes del clic: recargar el Resumen corta sus requests en vuelo
  await expect(panel.locator('tr', { hasText: 'Racha de rondas' })).toContainText('1 ronda ganada')
  // el enlace tiene que abrir la partida del record, no una cualquiera
  const respuesta = await page.request.get('/api/overview/')
  const { match_id: matchId, map } = (await respuesta.json()).records.most_kills_match
  await fila.getByRole('link').click()
  await expect(page).toHaveURL(new RegExp(`/partidas/${matchId}$`))
  await expect(page.locator('h1')).toContainText(map)

  expect(errores).toEqual([])
})

test('el Inicio compara tu forma con tu historial', async ({ page }) => {
  const errores = vigilarConsola(page)
  // las etiquetas salen de la API: con otro seed cambia el tamano del resto
  const respuesta = await page.request.get('/api/compare/?by=matches&n=10&against=rest')
  const datos = await respuesta.json()
  expect(datos.against).toBe('rest')
  expect(datos.previous.rounds).toBeGreaterThan(0)
  await page.goto('/')

  const panel = page.locator('section.panel', { hasText: 'Tu forma contra tu historial' })
  await expect(panel).toBeVisible()
  const cabeceras = panel.locator('thead th')
  await expect(cabeceras.nth(1)).toContainText(datos.previous.label)
  await expect(cabeceras.nth(2)).toContainText(datos.current.label)
  await expect(panel.locator('tbody tr td:first-child')).toHaveText([
    'Rondas ganadas',
    'Rating',
    'KST',
    'Muertes sin trade',
  ])
  // los numeros de cada lado y su ruido, no solo las cabeceras: con las
  // columnas cruzadas o en cero el test tiene que caer
  const celdas = (m) => {
    const decimales = m.suffix === '' ? 2 : 0
    const valor = (v) => `${Number(v).toFixed(decimales)}${m.suffix}`
    return [valor(m.previous), valor(m.current), m.noise === null ? '—' : `±${Number(m.noise).toFixed(1)}`]
  }
  for (const [fila, clave] of [[0, 'winrate'], [1, 'rating']]) {
    const tds = panel.locator('tbody tr').nth(fila).locator('td')
    const [previo, actual, ruido] = celdas(datos.metrics.find((m) => m.key === clave))
    await expect(tds.nth(1)).toHaveText(previo)
    await expect(tds.nth(2)).toHaveText(actual)
    await expect(tds.nth(4)).toHaveText(ruido)
  }

  expect(errores).toEqual([])
})

test('un record de ronda abre la partida en esa ronda', async ({ page }) => {
  const errores = vigilarConsola(page)
  // los valores salen de la API: el test no depende de que partida o ronda sea
  const respuesta = await page.request.get('/api/overview/')
  const record = (await respuesta.json()).records.most_kills_round
  const etiqueta = `R${record.round_number + 1}`
  expect(etiqueta).toBe(record.round_label)
  // con R1 activa por defecto el test no distingue el salto de no hacer nada
  expect(record.round_number).toBeGreaterThan(0)

  await page.goto('/')
  const panel = page.locator('section.panel', { hasText: 'Tus récords' })
  await panel.locator('tr', { hasText: 'Más bajas en una ronda' }).getByRole('link').click()
  await expect(page).toHaveURL(new RegExp(`/partidas/${record.match_id}#ronda-${record.round_number + 1}$`))
  await expect(page.locator('#rondas .round-tab.active')).toContainText(etiqueta)
  await expect(page.locator('#rondas .round-detail h3').first()).toHaveText(new RegExp(`^${etiqueta}\\b`))

  // un ancla que no existe deja el detalle como siempre, en la primera ronda;
  // about:blank para que sea una carga nueva y no solo un cambio de hash
  await page.goto('about:blank')
  await page.goto(`/partidas/${record.match_id}#ronda-999`)
  await expect(page.locator('#rondas .round-tab.active')).toContainText('R1')
  await expect(page.locator('#rondas .round-detail h3').first()).toHaveText(/^R1\b/)

  expect(errores).toEqual([])
})

test('el detalle de una partida se abre desde la lista', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/partidas')

  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/partidas\/\d+$/)
  await expect(page.locator('h1')).toContainText(/Club House|Border|Bank/)
  await expect(page.getByText('Racha: 1 ganada desde R1 · 1 perdida desde R2')).toBeVisible()

  expect(errores).toEqual([])
})

test('el detalle de una partida muestra la matriz de duelos', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/partidas')
  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/partidas\/\d+$/)

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Matriz de duelos', exact: true }),
  })
  await expect(panel).toBeVisible()
  // seed_demo pone bajas tuyas y contra ti entre equipos distintos: la matriz no sale vacia
  await expect(panel.locator('table.matriz')).toHaveCount(2)
  await expect(panel.locator('td.con-dato').first()).toHaveText(/^\d+/)
  await panel.getByRole('button', { name: 'Solo aperturas' }).click()
  await expect(panel.locator('td.con-dato').first()).toBeVisible()

  expect(errores).toEqual([])
})

test('el detalle de una partida muestra los trades por equipo', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/partidas')
  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/partidas\/\d+$/)

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Trades por equipo', exact: true }),
  })
  await expect(panel).toBeVisible()
  const filas = panel.locator('table tbody tr')
  await expect(filas).toHaveCount(2)
  await expect(filas.nth(0).locator('td').first()).toHaveText('Tu equipo')
  await expect(filas.nth(1).locator('td').first()).toHaveText('Rival')

  // Los numeros salen de la misma respuesta que pinta la pagina: la tabla
  // tiene que mostrar las muertes y las sin trade de cada equipo tal cual.
  const id = page.url().match(/\/partidas\/(\d+)$/)[1]
  const detalle = await (await page.request.get(`/api/matches/${id}/`)).json()
  for (const [i, lado] of [[0, 'mine'], [1, 'rival']]) {
    const celdas = filas.nth(i).locator('td')
    await expect(celdas.nth(1)).toHaveText(String(detalle.team_trades[lado].deaths))
    await expect(celdas.nth(3)).toHaveText(String(detalle.team_trades[lado].untraded_deaths))
  }
  await expect(panel.getByText(/^Tu equipo dejó \d+ muertes? sin trade; el rival, \d+\.$/)).toBeVisible()

  expect(errores).toEqual([])
})

test('el detalle de una partida muestra las fases de la ronda', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/partidas')
  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/partidas\/\d+$/)

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Fases de la ronda', exact: true }),
  })
  await expect(panel).toBeVisible()
  const filas = panel.locator('table tbody tr')
  await expect(filas).toHaveCount(3)
  await expect(filas.nth(0).locator('td').first()).toHaveText('Temprano (<30 s)')
  await expect(filas.nth(2).locator('td').first()).toHaveText('Tarde (120 s o más)')

  // Las bajas de cada fase son las de la misma respuesta que pinta la pagina
  const id = page.url().match(/\/partidas\/(\d+)$/)[1]
  const detalle = await (await page.request.get(`/api/matches/${id}/`)).json()
  for (let i = 0; i < 3; i++) {
    const celdas = filas.nth(i).locator('td')
    await expect(celdas.nth(1)).toHaveText(String(detalle.phases.rows[i].mine))
    await expect(celdas.nth(2)).toHaveText(String(detalle.phases.rows[i].rival))
  }
  // seed_demo no tiene bajas antes de los 30 s: temprano queda en cero en toda partida
  await expect(filas.nth(0).locator('td').nth(1)).toHaveText('0')
  await expect(filas.nth(0).locator('td').nth(2)).toHaveText('0')
  // Numeros fijos de seed_demo (la partida mas nueva, demo-28 en Bank): sin
  // ellos un backend que devolviera ceros pasaria la comparacion de arriba.
  for (const [i, mias, rivales] of [[1, '4', '2'], [2, '1', '3']]) {
    await expect(filas.nth(i).locator('td').nth(1)).toHaveText(mias)
    await expect(filas.nth(i).locator('td').nth(2)).toHaveText(rivales)
  }

  expect(errores).toEqual([])
})

test('una partida sin rondas muestra su cabecera y un aviso', async ({ page }) => {
  const errores = vigilarConsola(page)
  // seed_demo no tiene partidas sin rondas: se toma una y se le vacia el detalle
  const { matches } = await (await page.request.get('/api/matches/?limit=1')).json()
  const { id, map } = matches[0]
  await page.route(`**/api/matches/${id}/`, async (route) => {
    const respuesta = await route.fetch()
    const json = await respuesta.json()
    await route.fulfill({ response: respuesta, json: { ...json, ...SIN_RONDAS } })
  })
  await page.goto(`/partidas/${id}`)

  await expect(page.locator('h1')).toContainText(map)
  const rondas = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Rondas', exact: true }),
  })
  await expect(rondas).toContainText('Esta partida no tiene rondas importadas.')
  // la matriz de duelos tambien usa .round-tab: se cuenta solo dentro de Rondas
  await expect(rondas.locator('.round-tab')).toHaveCount(0)
  await expect(page.getByRole('heading', { name: 'Scoreboard de la partida', exact: true })).toBeVisible()
  const fases = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Fases de la ronda', exact: true }),
  })
  await expect(fases).toContainText('Esta partida no tiene bajas con reloj entre equipos.')

  expect(errores).toEqual([])
})

test('el timeline marca la apertura de cada ronda', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/partidas')
  await page.locator('table tbody tr').first().getByRole('link').first().click()
  await expect(page).toHaveURL(/\/partidas\/\d+$/)

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Rondas', exact: true }),
  })
  const pestanas = panel.locator('.round-tab')
  await expect(pestanas.first()).toBeVisible()
  const total = await pestanas.count()
  let entries = 0
  for (let i = 0; i < total; i++) {
    await pestanas.nth(i).click()
    await expect(pestanas.nth(i)).toHaveClass(/active/)
    const bajas = panel.locator('.timeline li', { hasText: /mató a|murió/ })
    if ((await bajas.count()) === 0) continue
    const apertura = panel.locator('.timeline .chip', { hasText: /^apertura$/ })
    const entry = panel.locator('.timeline .chip', { hasText: /^entry$/ })
    // Una sola apertura por ronda, en la primera baja; el entry nunca en esa fila
    await expect(apertura).toHaveCount(1)
    await expect(bajas.first().locator('.chip', { hasText: /^apertura$/ })).toHaveCount(1)
    await expect(bajas.first().locator('.chip', { hasText: /^entry$/ })).toHaveCount(0)
    const n = await entry.count()
    expect(n).toBeLessThanOrEqual(1)
    // Las filas .mine son los Kill de tu equipo: el entry va en la primera
    if (n === 1) {
      await expect(panel.locator('.timeline li.mine').first().locator('.chip', { hasText: /^entry$/ })).toHaveCount(1)
    }
    entries += n
  }
  // seed_demo: toda ronda donde mueres primero y tu equipo despues mata lleva entry
  expect(entries).toBeGreaterThan(0)

  expect(errores).toEqual([])
})

test('el detalle salta a la siguiente ronda perdida', async ({ page }) => {
  const errores = vigilarConsola(page)
  // la primera partida del seed con alguna ronda perdida; el indice esperado con la misma regla
  const { matches } = await (await page.request.get('/api/matches/?limit=50')).json()
  let id = null
  let esperado = -1
  for (const m of matches) {
    const { rounds } = await (await page.request.get(`/api/matches/${m.id}/`)).json()
    const n = rounds.length
    // k < n: una partida cuya unica perdida es la R1 dejaria el boton sin moverse y el test no veria nada
    for (let k = 1; k < n && esperado === -1; k++) {
      if (rounds[k % n].my_team_won === false) esperado = k % n
    }
    if (esperado !== -1) {
      id = m.id
      break
    }
  }
  expect(id).not.toBeNull()

  await page.goto(`/partidas/${id}`)
  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Rondas', exact: true }),
  })
  const pestanas = panel.locator('.round-tab')
  const boton = panel.getByRole('button', { name: 'Siguiente ronda perdida' })
  await pestanas.first().click()
  await expect(boton).toBeEnabled()
  const url = page.url()
  await boton.click()
  await expect(pestanas.nth(esperado)).toHaveClass(/active/)
  await expect(pestanas.nth(esperado)).toHaveClass(/loss/)

  // con la tecla igual, desde la primera; el foco queda en la pestaña, no en un campo
  await pestanas.first().click()
  await expect(pestanas.first()).toHaveClass(/active/)
  await page.keyboard.press('p')
  await expect(pestanas.nth(esperado)).toHaveClass(/active/)
  // el salto no toca el hash, como cambiar de ronda a mano
  expect(page.url()).toBe(url)
  await expect(panel).toContainText('P para la siguiente perdida')

  expect(errores).toEqual([])
})

test('sin rondas perdidas el boton de la siguiente perdida queda deshabilitado', async ({ page }) => {
  const errores = vigilarConsola(page)
  const { matches } = await (await page.request.get('/api/matches/?limit=1')).json()
  const { id } = matches[0]
  await page.route(`**/api/matches/${id}/`, async (route) => {
    const respuesta = await route.fetch()
    const json = await respuesta.json()
    const rounds = json.rounds.map((r) => ({ ...r, my_team_won: true }))
    await route.fulfill({ response: respuesta, json: { ...json, rounds } })
  })
  await page.goto(`/partidas/${id}`)
  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Rondas', exact: true }),
  })
  await expect(panel.locator('.round-tab').first()).toHaveClass(/active/)
  await expect(panel.getByRole('button', { name: 'Siguiente ronda perdida' })).toBeDisabled()
  await page.keyboard.press('p')
  await expect(panel.locator('.round-tab').first()).toHaveClass(/active/)

  expect(errores).toEqual([])
})

test('la timeline marca un teamkill con TK', async ({ page }) => {
  const errores = vigilarConsola(page)
  // seed_demo no tiene teamkills: se cambia la victima de una baja por un compañero del autor
  const { matches } = await (await page.request.get('/api/matches/?limit=1')).json()
  const { id } = matches[0]
  const detalle = await (await page.request.get(`/api/matches/${id}/`)).json()
  let indice = -1
  let baja = null
  let companero = ''
  for (const [i, ronda] of detalle.rounds.entries()) {
    const kill = ronda.events.find((e) => e.kind === 'Kill')
    if (!kill) continue
    const autor = ronda.players.find((p) => p.username === kill.actor)
    const otro = autor && ronda.players.find((p) => p.team_index === autor.team_index && p.username !== kill.actor)
    if (otro) {
      indice = i
      baja = kill
      companero = otro.username
      break
    }
  }
  expect(indice).toBeGreaterThanOrEqual(0)
  await page.route(`**/api/matches/${id}/`, async (route) => {
    const respuesta = await route.fetch()
    const json = await respuesta.json()
    const ronda = json.rounds[indice]
    ronda.events = ronda.events.map((e) => (e.order === baja.order ? { ...e, target: companero } : e))
    await route.fulfill({ response: respuesta, json })
  })
  await page.goto(`/partidas/${id}`)

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Rondas', exact: true }),
  })
  // la matriz de duelos tambien usa .round-tab: se cuenta solo dentro de Rondas
  const pestanas = panel.locator('.round-tab')
  await pestanas.nth(indice).click()
  await expect(pestanas.nth(indice)).toHaveClass(/active/)
  const tk = panel.locator('.timeline .chip', { hasText: /^TK$/ })
  await expect(tk).toHaveCount(1)
  await expect(tk).toHaveAttribute('title', 'Baja entre compañeros: no suma a las bajas')
  const linea = panel.locator('.timeline li', { has: page.locator('.chip', { hasText: /^TK$/ }) })
  await expect(linea).toContainText(`${baja.actor} mató a ${companero}`)
  await expect(linea).not.toHaveClass(/mine|against/)

  // en otra ronda, sin la baja cambiada, ningun TK
  const otra = indice === 0 ? 1 : 0
  await pestanas.nth(otra).click()
  await expect(pestanas.nth(otra)).toHaveClass(/active/)
  await expect(panel.locator('.timeline .chip', { hasText: /^TK$/ })).toHaveCount(0)

  expect(errores).toEqual([])
})

test('el scoreboard de la partida muestra multikills', async ({ page }) => {
  const errores = vigilarConsola(page)
  // seed_demo: demo-17 tiene dos rondas tuyas de 2 bajas; la primera de la lista no tiene ninguna
  const respuesta = await page.request.get('/api/matches/?limit=200')
  const { matches } = await respuesta.json()
  const partida = matches.find((m) => m.match_id === 'demo-17')
  await page.goto(`/partidas/${partida.id}`)

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Scoreboard de la partida', exact: true }),
  })
  await expect(panel.locator('th', { hasText: 'Multikills' })).toBeVisible()
  await expect(panel.locator('tbody tr', { hasText: 'BearF99' })).toContainText('2×2K')
  await expect(panel.locator('tbody tr', { hasText: 'Chamo' })).not.toContainText('×')
  // BearF99 ya encabeza el orden inicial por bajas: el orden ascendente es el que prueba la columna
  await panel.locator('th', { hasText: 'Multikills' }).click()
  await expect(panel.locator('th', { hasText: 'Multikills' })).toContainText('↓')
  await expect(panel.locator('tbody tr').first()).toContainText('BearF99')
  await panel.locator('th', { hasText: 'Multikills' }).click()
  await expect(panel.locator('th', { hasText: 'Multikills' })).toContainText('↑')
  await expect(panel.locator('tbody tr').first()).not.toContainText('BearF99')
  await expect(panel.locator('tbody tr').last()).toContainText('BearF99')

  expect(errores).toEqual([])
})

test('el detalle de partida copia el resumen', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write'])
  const respuesta = await page.request.get('/api/matches/?limit=200')
  const { matches } = await respuesta.json()
  const partida = matches[0]
  await page.goto(`/partidas/${partida.id}`)

  await page.getByRole('button', { name: 'Copiar resumen' }).click()
  await expect(page.getByText('Copiado', { exact: true })).toBeVisible()
  const texto = await page.evaluate(() => navigator.clipboard.readText())
  expect(texto.startsWith(`${partida.map} · ${partida.score} · `)).toBe(true)

  expect(errores).toEqual([])
})

test('el detalle de partida copia una ronda', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write'])
  const { matches } = await (await page.request.get('/api/matches/?limit=200')).json()
  const detalle = await (await page.request.get(`/api/matches/${matches[0].id}/`)).json()
  // la primera ronda con una baja, para que el texto tenga una linea de la timeline
  const i = detalle.rounds.findIndex((r) => r.events.some((e) => e.kind === 'Kill'))
  expect(i).toBeGreaterThanOrEqual(0)
  const ronda = detalle.rounds[i]
  const primera = ronda.events.filter((e) => e.kind === 'Kill').sort((a, b) => a.order - b.order)[0]
  await page.goto(`/partidas/${matches[0].id}`)

  await page.locator('.round-tab').nth(i).click()
  await page.getByRole('button', { name: 'Copiar ronda' }).click()
  await expect(page.getByText('Ronda copiada', { exact: true })).toBeVisible()
  const texto = await page.evaluate(() => navigator.clipboard.readText())
  expect(texto.startsWith(`${detalle.match.map} · ${ronda.label} · `)).toBe(true)
  expect(texto).toContain(primera.actor)
  // autor y victima en la misma linea, con su reloj: no alcanza con que el nick aparezca
  expect(texto).toContain(`${primera.clock_raw || '—'} ${primera.actor} mató a ${primera.target}`)

  // Al cambiar de ronda el aviso no queda pegado a la otra
  expect(detalle.rounds.length).toBeGreaterThan(1)
  await page.locator('.round-tab').nth(i === 0 ? 1 : 0).click()
  await expect(page.getByText('Ronda copiada', { exact: true })).toHaveCount(0)

  expect(errores).toEqual([])
})

test('Tendencias copia el resumen de una sesion', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write'])
  const respuesta = await page.request.get('/api/sessions/')
  const { sessions } = await respuesta.json()
  const sesion = sessions.find((s) => s.index === 0)
  await page.goto('/tendencias')

  const panel = page.locator('.panel', { has: page.getByRole('heading', { name: 'Sesiones', exact: true }) })
  // La tabla abre ordenada por fecha desc: la primera fila es la sesion mas reciente
  await expect(panel.locator('tbody tr').first()).toContainText('1G 0P')
  await panel.getByRole('button', { name: 'Copiar' }).first().click()
  await expect(panel.getByText(`Sesión copiada (${sesion.start.slice(5, 16).replace('T', ' ')})`, { exact: true })).toBeVisible()
  const texto = await page.evaluate(() => navigator.clipboard.readText())
  expect(texto.startsWith(`Sesión del ${sesion.start.slice(0, 16).replace('T', ' ')}`)).toBe(true)
  expect(texto).toContain('1 partida: 1G 0P')
  // seed_demo: cada sesion es una partida, asi que no hay extremos que nombrar
  expect(texto).not.toContain('Mejor partida')

  expect(errores).toEqual([])
})

test('Tendencias tiene las columnas Mejor y Peor, con guion en una sesion de una partida', async ({ page }) => {
  const errores = vigilarConsola(page)
  const { sessions } = await (await page.request.get('/api/sessions/')).json()
  // seed_demo con el gap del e2e: cada sesion es una partida, sin extremos que nombrar
  expect(sessions[0].best_match).toBeNull()
  await page.goto('/tendencias')

  const panel = page.locator('.panel', { has: page.getByRole('heading', { name: 'Sesiones', exact: true }) })
  // evaluateAll no espera: sin esto lee la pagina mientras dice Cargando...
  await expect(panel.locator('tbody tr').first()).toBeVisible()
  const cabeceras = await panel.locator('thead th').evaluateAll((ths) => ths.map((th) => th.textContent.trim()))
  const mejor = cabeceras.findIndex((t) => t.startsWith('Mejor'))
  const peor = cabeceras.findIndex((t) => t.startsWith('Peor'))
  expect(mejor).toBeGreaterThan(-1)
  expect(peor).toBe(mejor + 1)
  const fila = panel.locator('tbody tr').first()
  await expect(fila.locator('td').nth(mejor)).toHaveText('—')
  await expect(fila.locator('td').nth(peor)).toHaveText('—')
  await expect(fila.locator('td').nth(mejor).getByRole('link')).toHaveCount(0)

  expect(errores).toEqual([])
})

test('el Resumen muestra tus multikills', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/')

  const stat = page.locator('.stat', { has: page.locator('.label', { hasText: /^Multikills$/ }) })
  await expect(stat.locator('.value')).toHaveText('14')
  await expect(stat.locator('.sub')).toHaveText('14×2K · 7% de tus rondas')

  expect(errores).toEqual([])
})

test('el Resumen muestra las aperturas que pesan', async ({ page }) => {
  const errores = vigilarConsola(page)
  const respuesta = page.waitForResponse((r) => r.url().includes('/api/overview/'))
  await page.goto('/')
  const total = (await (await respuesta).json()).overall

  // seed_demo: ninguna apertura ganada queda tradeada ni ninguna perdida vengada
  const panel = page.locator('.panel', { has: page.locator('h2', { hasText: 'Aperturas que pesan' }) })
  await expect(panel).toBeVisible()
  const fila = (nombre) => panel.locator('tbody tr', { has: page.locator('td', { hasText: nombre }) })
  await expect(fila(/^Ganada limpia$/).locator('td').nth(1)).toHaveText(String(total.opening_kills))
  await expect(fila(/^Ganada devuelta$/).locator('td').nth(1)).toHaveText('0')
  await expect(fila(/^Ganada devuelta$/).locator('td').nth(2)).toHaveText('—')
  await expect(fila(/^Perdida vengada$/).locator('td').nth(2)).toHaveText('—')
  await expect(fila(/^Perdida sin vengar$/).locator('td').nth(1)).toHaveText(String(total.opening_deaths))
  expect(total.opening_kills).toBeGreaterThan(0)
  expect(total.opening_deaths).toBeGreaterThan(0)

  expect(errores).toEqual([])
})

test('el Resumen muestra tus partidas', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/')

  // seed_demo: 29 partidas, todas ganadas, 203 rondas; Bank y Club House con 10, todos los mapas al 100 %
  const stat = (nombre) => page.locator('.stat', { has: page.locator('.label', { hasText: nombre }) })
  await expect(stat(/^Partidas ganadas$/).locator('.value')).toHaveText('100%')
  await expect(stat(/^Partidas ganadas$/).locator('.sub')).toHaveText('29 de 29')
  await expect(stat(/^Rondas por partida$/).locator('.value')).toHaveText('7.0')
  await expect(stat(/^Rondas por partida$/).locator('.sub')).toHaveText('203 rondas en 29 partidas')
  await expect(stat(/^Mejor mapa$/).locator('.value')).toHaveText('Bank')
  await expect(stat(/^Mejor mapa$/).locator('.sub')).toHaveText('100% en 10 partidas')
  await expect(stat(/^Peor mapa$/).locator('.value')).toHaveText('—')
  await expect(stat(/^Peor mapa$/).locator('.sub')).toHaveText('Ningún mapa por debajo')
  // Todas ganadas desde la primera, INICIO de seed_demo
  await expect(page.locator('.racha-actual')).toHaveText('Racha actual: 29 victorias seguidas desde 2026-08-01')

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

test('Compañeros muestra quien cae primero', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/companeros')

  const panel = page.locator('section.panel', { hasText: 'Primero en caer' })
  await expect(panel).toBeVisible()
  // seed_demo: 203 rondas tuyas, 53 en que caiste primero de tu equipo
  const total = panel.locator('tbody tr', { hasText: 'Total' })
  await expect(total).toContainText('203')
  await expect(total).toContainText('53 (26%)')

  expect(errores).toEqual([])
})

test('Compañeros muestra la conversion de clutch', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/companeros')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Clutches', exact: true }),
  })
  await expect(panel.getByRole('heading', { name: 'Conversión por rivales' })).toBeVisible()
  // seed_demo: los 1v1 son los clutches ganados; los 1v2 son intentos que se perdieron.
  // La primera tabla es la de conversion: la de ganados tambien tiene celdas 1v1
  const conversion = panel.locator('table').first()
  await expect(conversion.getByRole('row', { name: /^1v1 2 2 100%/ })).toBeVisible()
  await expect(conversion.getByRole('row', { name: /^1v2 8 0 0%/ })).toBeVisible()
  // uno de los dos ganados (Bank) fue sin bajas desde que quedaste solo
  await expect(conversion.getByRole('cell', { name: 'Silenciosos', exact: true })).toBeVisible()
  const fila1v1 = conversion.getByRole('row', { name: /^1v1 2 2 100%/ })
  await expect(fila1v1.getByRole('cell', { name: /1 \(50%\)/ })).toBeVisible()
  await expect(panel.getByText(/De tus 2 clutches ganados, 1 fue silencioso/)).toBeVisible()
  await expect(panel.getByText(/0 por eliminación, 1 sin eliminación/)).toBeVisible()

  expect(errores).toEqual([])
})

test('Compañeros muestra el clutch por mapa y sitio', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/companeros')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Clutches', exact: true }),
  })
  await expect(panel.getByRole('heading', { name: 'Clutch por mapa y sitio' })).toBeVisible()
  // seed_demo: Border junta 5 intentos (B Armory 3, A Ventilation 2); la segunda tabla es esta
  const porSitio = panel.locator('table').nth(1)
  const border = porSitio.getByRole('row', { name: 'Border Total 5 1 20%', exact: true })
  await expect(border).toBeVisible()
  await expect(border.locator('.muestra-chica')).toHaveCount(0)
  const armory = porSitio.getByRole('row', { name: /^Border B Armory, B Archives 3 1 33%/ })
  await expect(armory.locator('.muestra-chica')).toHaveCount(1)
  await expect(porSitio.getByRole('row', { name: /^Bank Total 3 1 33%/ })).toBeVisible()

  expect(errores).toEqual([])
})

test('Compañeros muestra el clutch por operador', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/companeros')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Clutches', exact: true }),
  })
  await expect(panel.getByRole('heading', { name: 'Clutch por operador' })).toBeVisible()
  // seed_demo: Rook en defensa junta 5 intentos y ninguno ganado; Jager 3, Zofia 2. La tercera tabla es esta
  const porOperador = panel.locator('table').nth(2)
  await expect(porOperador.locator('tbody tr')).toHaveCount(3)
  const rook = porOperador.getByRole('row', { name: 'Rook Defensa 5 0 0%', exact: true })
  await expect(rook).toBeVisible()
  await expect(rook.locator('.muestra-chica')).toHaveCount(0)
  const zofia = porOperador.getByRole('row', { name: /^Zofia Ataque 2 2 100%/ })
  await expect(zofia.locator('.muestra-chica')).toHaveCount(1)

  expect(errores).toEqual([])
})

test('Compañeros muestra los clutches de tus compañeros', async ({ page }) => {
  const errores = vigilarConsola(page)
  const { teammate_clutches: datos } = await (await page.request.get('/api/teammates/')).json()
  await page.goto('/companeros')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Clutches', exact: true }),
  })
  await expect(panel.getByRole('heading', { name: 'Clutches de tus compañeros' })).toBeVisible()
  // seed_demo hoy no deja a ningun habitual ultimo vivo: sale la nota. Si la semilla
  // cambia y da intentos, se afirma la tabla con los numeros de la API
  if (datos.rows.length) {
    const tabla = panel.locator('table', { has: page.getByRole('cell', { name: datos.rows[0].username }) })
    await expect(tabla.locator('tbody tr')).toHaveCount(datos.rows.length + 1)
    await expect(tabla.locator('tbody tr').first()).toContainText('Tú')
  } else {
    await expect(panel).toContainText('Ningún compañero habitual quedó último en una ronda contigo con estos filtros.')
  }

  expect(errores).toEqual([])
})

test('la tabla de clutches de compañeros pone tu fila primero', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.route('**/api/teammates/**', async (route) => {
    const respuesta = await route.fetch()
    const json = await respuesta.json()
    const teammate_clutches = {
      min_attempts: 5,
      me: { attempts: 6, won: 3, pct: 50, low_sample: false },
      rows: [
        { player_id: json.synergy[0]?.player_id ?? 1, username: 'Ocho', attempts: 8, won: 2, pct: 25, low_sample: false },
        { player_id: 999999, username: 'Tres', attempts: 3, won: 3, pct: 100, low_sample: true },
      ],
    }
    await route.fulfill({ response: respuesta, json: { ...json, teammate_clutches } })
  })
  await page.goto('/companeros')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Clutches', exact: true }),
  })
  const tabla = panel.locator('table', { has: page.getByRole('cell', { name: 'Ocho' }) })
  const filas = tabla.locator('tbody tr')
  await expect(filas).toHaveCount(3)
  await expect(filas.nth(0)).toHaveText(/^Tú\s*6\s*3\s*50%/)
  await expect(filas.nth(1)).toHaveText(/^Ocho\s*8\s*2\s*25%/)
  await expect(filas.nth(2)).toHaveText(/^Tres\s*3\s*3\s*100%/)
  await expect(filas.nth(0).getByRole('link')).toHaveCount(0)
  await expect(filas.nth(1).getByRole('link', { name: 'Ocho' })).toBeVisible()
  await expect(filas.nth(1).locator('.muestra-chica')).toHaveCount(0)
  await expect(filas.nth(2).locator('.muestra-chica')).toHaveCount(1)

  expect(errores).toEqual([])
})

test('Compañeros muestra el panel de teamkills', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/companeros')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Teamkills', exact: true }),
  })
  await expect(panel).toBeVisible()
  // seed_demo no tiene teamkills: el verdugo siempre es rival y tus bajas siempre sobre rivales
  await expect(panel).toContainText('Ningún teamkill en las rondas filtradas.')

  expect(errores).toEqual([])
})

test('Compañeros muestra solo, en dúo o en stack', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/companeros')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Solo, en dúo o en stack', exact: true }),
  })
  await expect(panel).toBeVisible()
  // seed_demo: Chamo, Seba y Nico juegan contigo las 29 partidas, asi que todo cae en Stack
  const filas = panel.locator('tbody tr')
  await expect(filas).toHaveCount(4)
  const stack = filas.filter({ has: page.getByRole('cell', { name: 'Stack', exact: true }) })
  for (const texto of ['29', '100%', '203', '57%', '1.00']) {
    await expect(stack.getByRole('cell', { name: texto, exact: true })).toBeVisible()
  }
  const solo = filas.filter({ has: page.getByRole('cell', { name: 'Solo', exact: true }) })
  await expect(solo.getByRole('cell', { name: '0', exact: true })).toHaveCount(3)
  await expect(panel).toContainText('Chamo')

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
  // las cabeceras de la tabla de playlists son botones (ordenan); ningun otro
  await expect(panel.locator('button:not(.th-orden)')).toHaveCount(0)

  // tus 203 rondas de seed_demo: 14 de 2 bajas
  const numeros = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Sus números', exact: true }),
  })
  await expect(numeros).toContainText('14×2K')

  expect(afuera, 'la app pidio algo fuera de localhost').toEqual([])
  expect(errores).toEqual([])
})

test('los POST de la UI mandan JSON', async ({ page }) => {
  const errores = vigilarConsola(page)
  // no se llega al backend: una importacion real cambiaria lo que ven las demas pruebas
  let tipo = null
  await page.route('**/api/import/', (route) => {
    tipo = route.request().headers()['content-type'] ?? ''
    route.fulfill({
      json: {
        running: false,
        origin: 'manual',
        total: 0,
        done: 0,
        current: '',
        started_at: null,
        finished_at: null,
        error: '',
        imported: [],
        count: 0,
        errors: 0,
      },
    })
  })

  await page.goto('/')
  await page.locator('.topbar').getByRole('button', { name: 'Importar replays' }).click()
  await expect(page.getByText('No había partidas nuevas para importar.')).toBeVisible()
  expect(tipo).toContain('application/json')

  expect(errores).toEqual([])
})

test('una ruta que no existe no rompe la app', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/no-existe')

  await expect(page.getByText('Esa página no existe')).toBeVisible()
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

test('Datos muestra Sin identificar sin pendientes', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/datos')

  // seed_demo no tiene IDs desconocidos: el panel se renderiza con las cuatro listas vacias
  const panel = page.locator('.panel', { hasText: 'Sin identificar' })
  await expect(panel).toContainText('no hay mapas, operadores, modos ni tipos de partida sin nombre')

  expect(errores).toEqual([])
})

test('Datos muestra las partidas por version del juego', async ({ page, request }) => {
  const errores = vigilarConsola(page)
  const { versions } = await (await request.get('/api/import/status/')).json()
  expect(versions.length).toBeGreaterThan(0)
  await page.goto('/datos')

  const titulo = page.getByRole('heading', { name: 'Partidas por versión del juego' })
  await expect(titulo).toBeVisible()
  const filas = titulo.locator('xpath=following-sibling::*[1]').locator('tbody tr')
  await expect(filas).toHaveCount(versions.length)
  // la primera fila es la version mas nueva; sin version, el rotulo de la UI
  const primera = filas.first()
  await expect(primera).toContainText(versions[0].game_version || 'Sin versión')
  await expect(primera).toContainText(String(versions[0].matches))

  expect(errores).toEqual([])
})

test('Datos ordena las versiones del juego como la API, no como texto', async ({ page }) => {
  const errores = vigilarConsola(page)
  // seed_demo no trae game_version: las versiones se inyectan sobre la respuesta real
  await page.route('**/api/import/status/', async (route) => {
    const respuesta = await route.fetch()
    const json = await respuesta.json()
    const fila = (game_version, code_version, matches) => ({
      game_version, code_version, matches, first: '2026-06-01T20:00:00', last: '2026-09-01T20:00:00',
    })
    await route.fulfill({
      response: respuesta,
      json: { ...json, versions: [fila('Y10S4', 30, 4), fila('Y9S4', 10, 7), fila('', 0, 2)] },
    })
  })
  await page.goto('/datos')

  const titulo = page.getByRole('heading', { name: 'Partidas por versión del juego' })
  const filas = titulo.locator('xpath=following-sibling::*[1]').locator('tbody tr')
  await expect(filas).toHaveCount(3)
  await expect(filas.nth(0)).toContainText('Y10S4')
  await expect(filas.nth(1)).toContainText('Y9S4')
  await expect(filas.nth(2)).toContainText('Sin versión')

  expect(errores).toEqual([])
})

test('Datos lista modos y tipos de partida sin nombre', async ({ page }) => {
  const errores = vigilarConsola(page)
  // seed_demo no trae desconocidos y no se toca: la respuesta se arma aca
  await page.route('**/api/unknown/', (route) =>
    route.fulfill({
      json: {
        maps: [],
        operators: [],
        gamemodes: [
          {
            id: '999', label: 'Unknown(999)', matches: 2, match_types: ['Ranked'],
            first_seen: '2026-09-01T20:00:00', last_seen: '2026-09-05T20:00:00', pending: '',
          },
        ],
        match_types: [
          {
            id: '77', label: 'Unknown(77)', matches: 1, gamemodes: ['Bomb'],
            first_seen: '2026-09-01T20:00:00', last_seen: '2026-09-01T20:00:00', pending: 'Evento',
          },
        ],
        overrides_path: 'data/overrides.json',
      },
    }),
  )
  await page.goto('/datos')

  await expect(page.getByText('Unknown(999)')).toBeVisible()
  await expect(page.getByText('Tipos de partida vistos: Ranked')).toBeVisible()
  await expect(page.getByPlaceholder('Nombre del tipo de partida')).toHaveValue('Evento')
  await page.getByPlaceholder('Nombre del modo de juego').fill('Arcade')
  await expect(page.getByRole('button', { name: 'Guardar y reetiquetar (1)' })).toBeEnabled()

  expect(errores).toEqual([])
})

test('el selector de tipo filtra el Inicio', async ({ page }) => {
  const errores = vigilarConsola(page)
  // seed_demo siembra todo Ranked y no se toca: el segundo tipo se suma aca
  let pedidosDeFiltros = 0
  await page.route('**/api/filters/', async (route) => {
    pedidosDeFiltros += 1
    const respuesta = await route.fetch()
    const json = await respuesta.json()
    await route.fulfill({ response: respuesta, json: { ...json, match_types: [...json.match_types, 'Unranked'] } })
  })
  await page.goto('/')

  const subtitulo = page.locator('.page-head p')
  await expect(subtitulo).toHaveText('29 partidas · 203 rondas analizadas')
  await expect(page.getByText('Solo ranked')).toHaveCount(0)
  const tipo = page.getByLabel('Tipo')
  await expect(tipo.locator('option')).toHaveText(['Todos', 'Ranked', 'Unranked'])

  const pedido = page.waitForRequest(/\/api\/overview\/\?.*match_type=Ranked/)
  await tipo.selectOption('Ranked')
  await pedido
  await expect(subtitulo).toHaveText('29 partidas · 203 rondas analizadas')

  await tipo.selectOption('Unranked')
  await expect(subtitulo).toHaveText('0 rondas con estos filtros')
  await expect(page.getByText('Ninguna ronda con estos filtros')).toBeVisible()
  await expect(page.locator('.filters')).toBeVisible()
  await expect(page.locator('.empty-state')).toHaveCount(0)

  await page.getByRole('button', { name: 'Limpiar' }).click()
  await expect(subtitulo).toHaveText('29 partidas · 203 rondas analizadas')
  await expect(tipo).toHaveValue('')
  // pasar por 0 rondas no vuelve a montar la barra (perderia el rango de
  // fechas abierto): /api/filters/ se pide una sola vez
  expect(pedidosDeFiltros).toBe(1)

  expect(errores).toEqual([])
})

test('un filtro sin rondas deja la barra en todas las páginas', async ({ page }) => {
  const errores = vigilarConsola(page)
  // ficha 85: los filtros viven en App y se comparten. seed_demo es todo
  // Ranked: un tipo sin partidas deja 0 rondas en todas las paginas
  await page.route('**/api/filters/', async (route) => {
    const respuesta = await route.fetch()
    const json = await respuesta.json()
    await route.fulfill({ response: respuesta, json: { ...json, match_types: [...json.match_types, 'Unranked'] } })
  })
  await page.goto('/')
  await page.getByLabel('Tipo').selectOption('Unranked')
  await expect(page.locator('.page-head p')).toHaveText('0 rondas con estos filtros')

  const nav = page.locator('nav')
  for (const [ruta, titulo] of PAGINAS.slice(1, 6)) {
    // por el menu; su href lleva los filtros en la query (ficha 96)
    await nav.locator(`a[href^="${ruta}"]`).click()
    await expect(page.locator('h1')).toHaveText(titulo)
    await expect(page.locator('.page-head p')).toHaveText('0 rondas con estos filtros')
    await expect(page.locator('.filters')).toBeVisible()
    await expect(page.getByLabel('Tipo')).toHaveValue('Unranked')
    await expect(page.locator('.empty-state')).toHaveCount(0)
  }

  // la ultima es Tendencias: Limpiar desde ahi vuelve a los numeros
  await page.getByRole('button', { name: 'Limpiar' }).click()
  await expect(page.locator('.page-head p')).toHaveText(
    'Cómo se mueven tus números en el tiempo y en qué momento de la partida te caes.',
  )
  await expect(page.getByLabel('Tipo')).toHaveValue('')
  await expect(page.locator('.empty-state')).toHaveCount(0)

  expect(errores).toEqual([])
})

test('Duelos con rondas pero sin duelos dice 0 duelos y no 0 rondas', async ({ page }) => {
  const errores = vigilarConsola(page)
  // ficha 86: seed_demo no tiene un filtro con rondas y sin duelos; se vacian
  // los duelos de la respuesta real y se dejan sus rondas tal cual
  await page.route(
    (url) => url.pathname === '/api/duels/',
    async (route) => {
      const respuesta = await route.fetch()
      const json = await respuesta.json()
      expect(json.rounds).toBeGreaterThan(0)
      await route.fulfill({
        response: respuesta,
        json: {
          ...json,
          totals: { kills: 0, deaths: 0, duels: 0, winrate: null },
          nemesis: [],
          operators: [],
          rivals: [],
        },
      })
    },
  )
  await page.goto('/duelos')
  await expect(page.locator('h1')).toHaveText('Duelos')
  // sin filtros puestos no hay "estos filtros" ni Limpiar del que hablar
  await expect(page.locator('.page-head p')).toHaveText('0 duelos')
  await expect(page.getByText('Hay rondas importadas, pero en ninguna mataste a un rival')).toBeVisible()
  await expect(page.locator('.empty-state')).toHaveCount(0)

  // con un filtro la barra se queda y el texto habla de el
  // se espera la respuesta filtrada: con la vieja en pantalla el texto ya
  // cambia, y el test terminaria con la ruta interceptada en vuelo
  const filtrada = page.waitForResponse((r) => new URL(r.url()).searchParams.get('side') === 'Attack')
  await page.getByLabel('Lado').selectOption({ index: 1 })
  await filtrada
  await expect(page.locator('.page-head p')).toHaveText('0 duelos con estos filtros')
  await expect(page.getByText('Hay rondas con estos filtros, pero en ninguna mataste a un rival')).toBeVisible()
  await expect(page.locator('.filters')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Limpiar' })).toBeVisible()
  await expect(page.locator('.empty-state')).toHaveCount(0)
  expect(errores).toEqual([])
})

test('el Coach muestra dónde quedas fuera de posición', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/coach')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Dónde quedas fuera de posición' }),
  })
  await expect(panel.getByText('El .rec no trae coordenadas')).toBeVisible()
  // Columnas: mapa, zona, rondas, fuera de posicion, resto, diferencia, margen, veredicto.
  // Numeros de seed_demo: 203 rondas, 118 fuera de posicion; 116 de ataque con 66.
  const sitios = panel.locator('h3:text-is("Sitios") + .table-wrap')
  const church = sitios.locator('tr', { has: page.getByRole('cell', { name: 'B Church, B Arsenal Room' }) })
  await expect(church.locator('td').nth(3)).toHaveText('85%')
  await expect(church.locator('td').nth(5)).toHaveText('+33.5')
  await expect(church.locator('td').nth(6)).toHaveText('±17.4')
  await expect(church.locator('td').nth(7)).toHaveText('Te agarran más')
  const ventilation = sitios.locator('tr', { has: page.getByRole('cell', { name: 'A Ventilation, A Workshop' }) })
  await expect(ventilation.locator('td').nth(3)).toHaveText('25%')
  await expect(ventilation.locator('td').nth(7)).toHaveText('Te sostienes')
  // Bank A Vault tiene 4 rondas: bajo el minimo de 5.
  await expect(sitios.getByRole('cell', { name: 'A Vault, A Gold Partition' })).toHaveCount(0)

  const spawns = panel.locator('h3:text-is("Spawns de ataque") + .table-wrap')
  const warehouse = spawns.locator('tr', { has: page.getByRole('cell', { name: 'Warehouse', exact: true }) })
  await expect(warehouse.locator('td').nth(3)).toHaveText('80%')
  await expect(warehouse.locator('td').nth(7)).toHaveText('Te agarran más')
  // Con un error estandar seria solido; con dos es ruido.
  const valley = spawns.locator('tr', { has: page.getByRole('cell', { name: 'Valley', exact: true }) })
  await expect(valley.locator('td').nth(7)).toHaveText('Sin señal')

  await expect(
    page.getByRole('heading', {
      name: 'En B Church, B Arsenal Room (Club House) te agarran fuera de posición el 85% de las rondas',
    }),
  ).toBeVisible()
  await expect(page.getByRole('heading', { name: 'En A Ventilation, A Workshop (Border) te sostienes' })).toBeVisible()

  expect(errores).toEqual([])
})

test('el Coach muestra la salida del spawn', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/coach')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Salida del spawn' }),
  })
  // seed_demo no tiene bajas antes de los 30 s: 116 rondas de ataque con spawn
  // en seis spawns (cinco de 20 y East Alley con 16), ninguna muerte temprana.
  await expect(panel.locator('.salida-ataque')).toContainText('en el 0% de las rondas (0 de 116)')
  await expect(panel.locator('tbody tr')).toHaveCount(6)
  // Columnas: mapa, spawn, rondas, mueres temprano, %, resto, diferencia, margen, bajas, veredicto.
  const boulevard = panel.locator('tr', {
    has: page.getByRole('cell', { name: 'Boulevard', exact: true }),
  })
  await expect(boulevard.locator('td').nth(0)).toHaveText('Bank')
  await expect(boulevard.locator('td').nth(2)).toHaveText('20')
  await expect(boulevard.locator('td').nth(3)).toHaveText('0')
  await expect(boulevard.locator('td').nth(8)).toHaveText('0')
  await expect(boulevard.locator('td').nth(9)).toHaveText('Sin señal')

  expect(errores).toEqual([])
})

test('el Coach muestra si repites el sitio tras perderlo', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/coach')

  const panel = page.locator('section.panel', {
    has: page.getByRole('heading', { name: 'Repetir el sitio tras perderlo' }),
  })
  // seed_demo pierde toda su defensa: 58 pares, 56 vuelven al mismo sitio y 2
  // cambian (uno en Bank y uno en Club House), winrate 0 en los dos.
  await expect(panel).toContainText('58 rondas perdidas en defensa seguidas de otra')
  const repite = panel.locator('.stat', { hasText: 'Repite el sitio' })
  await expect(repite.locator('.value')).toHaveText('56')
  await expect(repite.locator('.sub')).toHaveText('winrate 0%')
  const cambia = panel.locator('.stat', { hasText: 'Cambia de sitio' })
  await expect(cambia.locator('.value')).toHaveText('2')
  await expect(cambia.locator('.sub')).toContainText('pocas rondas')
  // Columnas: mapa, repite, winrate repitiendo, cambia, winrate cambiando.
  const club = panel.locator('tr', { has: page.getByRole('cell', { name: 'Club House', exact: true }) })
  await expect(club.locator('td').nth(1)).toHaveText('19')
  await expect(club.locator('td').nth(3)).toHaveText('1')
  await expect(panel.locator('tbody tr')).toHaveCount(3)

  expect(errores).toEqual([])
})

test('el Coach copia sus señales', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write'])
  const { insights } = await (await page.request.get('/api/coach/')).json()
  expect(insights.length).toBeGreaterThan(0)
  await page.goto('/coach')

  await page.getByRole('button', { name: 'Copiar señales' }).click()
  await expect(page.getByText('Copiado', { exact: true })).toBeVisible()
  let texto = await page.evaluate(() => navigator.clipboard.readText())
  expect(texto.startsWith('Coach · Sin filtros\n')).toBe(true)
  expect(texto).toContain(`- ${insights[0].title}`)

  // los filtros de la URL (ficha 96) llegan a la primera linea
  const conLado = await (await page.request.get('/api/coach/?side=Defense')).json()
  expect(conLado.insights.length).toBeGreaterThan(0)
  await page.goto('/coach?side=Defense')
  await page.getByRole('button', { name: 'Copiar señales' }).click()
  await expect(page.getByText('Copiado', { exact: true })).toBeVisible()
  texto = await page.evaluate(() => navigator.clipboard.readText())
  expect(texto.startsWith('Coach · Filtros: Solo defensa\n')).toBe(true)
  expect(texto).toContain(`- ${conLado.insights[0].title}`)

  expect(errores).toEqual([])
})

test('una señal del Coach abre el Resumen filtrado', async ({ page }) => {
  const errores = vigilarConsola(page)
  const { insights } = await (await page.request.get('/api/coach/')).json()
  const senal = insights.find((i) => i.key === 'operador-debil')
  expect(senal.filters.operator).toBeTruthy()
  const general = insights.find((i) => i.key === 'kst')
  expect(general).toBeTruthy()
  await page.goto('/coach')

  // una señal general no ofrece enlace
  const suya = page.locator('.insight').filter({ has: page.getByRole('heading', { name: general.title }) })
  await expect(suya).toBeVisible()
  await expect(suya.getByRole('link')).toHaveCount(0)

  const tarjeta = page.locator('.insight').filter({ has: page.getByRole('heading', { name: senal.title }) })
  await tarjeta.getByRole('link', { name: 'Ver esas rondas' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Resumen' })).toBeVisible()
  const destino = new URL(page.url())
  expect(destino.pathname).toBe('/')
  expect(destino.searchParams.get('operator')).toBe(senal.filters.operator)
  expect(destino.searchParams.get('side')).toBe(senal.filters.side)
  await expect(page.getByLabel('Operador')).toHaveValue(senal.filters.operator)
  await page.waitForLoadState('networkidle')
  expect(errores).toEqual([])
})

test('el sitio que trae una señal del Coach se ve en la barra y se quita', async ({ page }) => {
  const errores = vigilarConsola(page)
  const { insights } = await (await page.request.get('/api/coach/')).json()
  const senal = insights.find((i) => i.filters?.site)
  expect(senal).toBeTruthy()
  await page.goto('/coach')

  const tarjeta = page.locator('.insight').filter({ has: page.getByRole('heading', { name: senal.title }) })
  await tarjeta.getByRole('link', { name: 'Ver esas rondas' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Resumen' })).toBeVisible()
  const destino = new URL(page.url())
  expect(destino.searchParams.get('site')).toBe(senal.filters.site)
  // la señal de sitio es tambien la de mapa que pide la ficha: el mapa llega a la URL y al selector
  expect(senal.filters.map).toBeTruthy()
  expect(destino.searchParams.get('map')).toBe(senal.filters.map)
  await expect(page.getByLabel('Mapa')).toHaveValue(senal.filters.map)
  // el Resumen no tiene selector de sitio: sin esto el filtro quedaria puesto y sin verse
  const sitio = page.getByLabel('Sitio')
  await expect(sitio).toHaveValue(senal.filters.site)
  await sitio.selectOption('')
  await expect(page).not.toHaveURL(/site=/)
  await expect(page.getByLabel('Sitio')).toHaveCount(0)
  await page.waitForLoadState('networkidle')
  expect(errores).toEqual([])
})

test('Partidas filtra por resultado y por mapa', async ({ page }) => {
  const errores = vigilarConsola(page)
  await page.goto('/partidas')

  // seed_demo gana sus 29 partidas: "Victoria" las trae todas y "Derrota" ninguna
  const subtitulo = page.locator('.page-head p')
  await expect(subtitulo).toHaveText('29 partidas importadas.')
  await expect(page.getByLabel('Mapa')).toBeVisible()
  await expect(page.getByLabel('Periodo')).toBeVisible()
  await expect(page.getByLabel('Lado')).toHaveCount(0)
  await expect(page.getByLabel('Operador')).toHaveCount(0)

  const resultado = page.getByLabel('Resultado')
  let respuesta = page.waitForResponse(/\/api\/matches\/\?.*result=victoria/)
  await resultado.selectOption('victoria')
  await respuesta
  await expect(subtitulo).toHaveText('29 partidas con estos filtros.')
  const filas = page.locator('table tbody tr')
  await expect(filas).toHaveCount(29)
  await expect(filas.filter({ hasNot: page.locator('.chip.win') })).toHaveCount(0)

  await resultado.selectOption('derrota')
  await expect(subtitulo).toHaveText('0 partidas con estos filtros.')
  await expect(page.getByText('Ninguna partida con estos filtros')).toBeVisible()
  await expect(page.locator('.filters')).toBeVisible()
  await expect(page.locator('.empty-state')).toHaveCount(0)

  await page.getByRole('button', { name: 'Limpiar' }).click()
  await expect(subtitulo).toHaveText('29 partidas importadas.')
  await expect(resultado).toHaveValue('')

  const mapa = page.getByLabel('Mapa')
  const opcion = mapa.locator('option').nth(1)
  const valor = await opcion.getAttribute('value')
  const etiqueta = (await opcion.textContent()).trim()
  respuesta = page.waitForResponse(/\/api\/matches\/\?.*map=/)
  await mapa.selectOption(valor)
  await respuesta
  // la respuesta llega antes de que React la pinte: hasta entonces el
  // subtitulo ya dice "con estos filtros" pero con el total de antes (29), y
  // leerlo ahi hacia fallar el `< 29` de abajo cuando la maquina va cargada
  await expect(subtitulo).not.toHaveText('29 partidas con estos filtros.')
  await expect(subtitulo).toHaveText(/^\d+ partidas? con estos filtros\.$/)
  const n = Number((await subtitulo.textContent()).split(' ')[0])
  expect(n).toBeGreaterThan(0)
  expect(n).toBeLessThan(29)
  await expect(filas).toHaveCount(n)
  // la columna Mapa es la segunda
  for (const celda of await filas.locator('td:nth-child(2)').allTextContents()) {
    expect(celda.trim()).toBe(etiqueta)
  }

  await page.getByRole('button', { name: 'Limpiar' }).click()
  await expect(subtitulo).toHaveText('29 partidas importadas.')

  // una respuesta vieja que llega tarde no pisa la del filtro nuevo: la de
  // "Victoria" se demora hasta que "Derrota" ya respondio
  let soltarVictoria
  const victoriaDemorada = new Promise((resolve) => (soltarVictoria = resolve))
  await page.route(/\/api\/matches\/\?.*result=victoria/, async (route) => {
    await victoriaDemorada
    await route.continue()
  })
  await resultado.selectOption('victoria')
  respuesta = page.waitForResponse(/\/api\/matches\/\?.*result=derrota/)
  await resultado.selectOption('derrota')
  await respuesta
  await expect(subtitulo).toHaveText('0 partidas con estos filtros.')
  const tarde = page.waitForResponse(/\/api\/matches\/\?.*result=victoria/)
  soltarVictoria()
  await tarde
  await expect(page.getByText('Ninguna partida con estos filtros')).toBeVisible()
  await expect(page.locator('table tbody tr')).toHaveCount(0)

  expect(errores).toEqual([])
})

test('una partida o un jugador que no existe lo dice sin culpar a Django', async ({ page }) => {
  const errores = vigilarConsola(page)
  const casos = [
    ['/partidas/999999', 'Esa partida no existe', 'Partidas'],
    ['/partidas/abc', 'Esa partida no existe', 'Partidas'],
    ['/jugadores/999999', 'Ese jugador no existe', 'Compañeros'],
    ['/jugadores/abc', 'Ese jugador no existe', 'Compañeros'],
  ]
  for (const [ruta, titulo, lista] of casos) {
    await page.goto(ruta)
    await expect(page.locator('main h2')).toHaveText(titulo)
    await expect(page.getByText('Django')).toHaveCount(0)
    await page.locator('.empty-state a.btn').click()
    await expect(page.locator('h1')).toHaveText(lista)
    // la lista pide /api/filters/ al montar; sin esperarla, el goto de la
    // vuelta siguiente la corta en vuelo y la consola anota un ERR_ABORTED
    await page.waitForLoadState('networkidle')
  }

  // Chromium loguea cada 404 como "Failed to load resource" sin la URL en el
  // texto; se esperan exactamente los cuatro de los casos, asi un 404 de otra
  // cosa en estas paginas sigue haciendo fallar la prueba
  const de404 = errores.filter((e) => e.includes('status of 404'))
  expect(de404).toHaveLength(casos.length)
  expect(errores.filter((e) => !e.includes('status of 404'))).toEqual([])
})

test('con la API caida el aviso sigue culpando a Django', async ({ page }) => {
  // el abort es a proposito y ensucia la consola: este test no la mira
  await page.route('**/api/matches/**', (route) => route.abort())
  await page.goto('/partidas/1')
  const aviso = page.locator('.error')
  await expect(aviso).toContainText('No pude leer la API')
  await expect(aviso).toContainText('Revisa que Django esté corriendo.')
  await expect(aviso).not.toContainText('8000')
})
