/**
 * Pasada exploratoria de QA por todas las paginas de la app, en Chromium,
 * contra Django sirviendo el build de React (lo mismo que usa el usuario).
 *
 * El e2e afirma lo que alguien penso; esto barre lo que nadie penso: cada
 * ruta de App.jsx (mas un detalle de partida, un perfil de jugador y una ruta
 * que no existe), en escritorio y en celular, sobre una base vacia y sobre la
 * de `seed_demo` con un nick largo con tildes, ñ y emoji. Por pagina mira:
 * errores de consola y excepciones, pedidos fallidos, respuestas 4xx/5xx de
 * la propia app, pedidos fuera de localhost, desborde horizontal, textos
 * `NaN`/`undefined`/`null`/`[object Object]`/`Infinity` a la vista, estados
 * vacios con datos, botones sin nombre accesible, imagenes sin alt, y si el
 * foco con Tab se ve.
 *
 * Uso (desde la raiz del repo, con `cd frontend && npm run build` hecho):
 *   git show "$EQUIPO_REF:scripts/equipo-dev/qa-paginas.mjs" > "$TMPDIR/qa-paginas.mjs"
 *   node "$TMPDIR/qa-paginas.mjs" [--base demo|vacia|ambas] [--salida DIR] [--autoprueba]
 * Necesita Chromium de Playwright (en la nube, PLAYWRIGHT_BROWSERS_PATH).
 *
 * Salida: `HALLAZGO <base> <vista> <ruta> <tipo>: <detalle>` (rompe: consola,
 * excepcion, http, red, pedido) y `AVISO ...` (desborde, texto, vacio, a11y,
 * foco); captura de cada pagina con hallazgo en --salida. Al final
 * `QA_PAGINAS_OK (<n> paginas, <a> avisos)` (salida 0) o
 * `QA_PAGINAS_FALLA: <k> hallazgos` (salida 1). Con --autoprueba: rompe a
 * proposito un pedido y una pagina y verifica que los vea.
 */

import { execFileSync, spawn } from 'node:child_process'
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import net from 'node:net'
import os from 'node:os'
import path from 'node:path'

const args = process.argv.slice(2)
const opcion = (nombre, defecto) => {
  const i = args.indexOf(nombre)
  return i >= 0 && args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : defecto
}
const AUTOPRUEBA = args.includes('--autoprueba')
const BASES = { demo: ['demo'], vacia: ['vacia'], ambas: ['vacia', 'demo'] }[opcion('--base', 'ambas')]
const SALIDA = opcion('--salida', '')
const VISTAS = { escritorio: { width: 1280, height: 800 }, celular: { width: 375, height: 740 } }
const NICK_RARO = 'Ñandú_ÁÉÍÓÚ_ü_' + 'x'.repeat(30) + ' 🙂'

const REPO = execFileSync('git', ['rev-parse', '--show-toplevel'], { encoding: 'utf8' }).trim()
const BACKEND = path.join(REPO, 'backend')
const requerir = createRequire(path.join(REPO, 'frontend', 'package.json'))
const { chromium } = requerir('@playwright/test')

if (!existsSync(path.join(REPO, 'frontend', 'dist', 'index.html'))) {
  console.error('Falta el build: cd frontend && npm run build')
  process.exit(2)
}

const python = () => {
  const venv = path.join(REPO, '.venv', 'bin', 'python')
  return existsSync(venv) ? venv : 'python3'
}

/** Rutas estaticas de App.jsx: una ruta nueva entra sola. */
function rutasDeApp() {
  const app = readFileSync(path.join(REPO, 'frontend', 'src', 'App.jsx'), 'utf8')
  return [...app.matchAll(/path="(\/[^"]*)"/g)].map((m) => m[1]).filter((r) => !r.includes(':'))
}

function puertoLibre() {
  return new Promise((ok) => {
    const s = net.createServer()
    s.listen(0, '127.0.0.1', () => {
      const { port } = s.address()
      s.close(() => ok(port))
    })
  })
}

async function levantar(base, tmp) {
  const datos = path.join(tmp, 'data')
  mkdirSync(datos, { recursive: true })
  writeFileSync(path.join(tmp, '.env'), `REPLAY_DIR=${path.join(tmp, 'sin-replays')}\n`)
  const entorno = {
    ...process.env,
    SQLITE_PATH: path.join(tmp, 'db.sqlite3'),
    DATA_DIR: datos,
    OVERRIDES_PATH: path.join(datos, 'overrides.json'),
    R6_ENV_FILE: path.join(tmp, '.env'),
    AUTO_IMPORT: 'false',
    UBI_EMAIL: '',
    UBI_PASSWORD: '',
  }
  const py = python()
  const correr = (...a) => execFileSync(py, ['manage.py', ...a], { cwd: BACKEND, env: entorno, stdio: 'pipe' })
  correr('migrate', '--no-input')
  if (base === 'demo') {
    correr('seed_demo', '--force')
    // un nick largo con tildes, ñ y emoji en un compañero: el borde que el seed no trae
    correr('shell', '-c', `from replays.models import Player, RoundPlayer
p = Player.objects.filter(is_me=False).order_by('pk').first()
RoundPlayer.objects.filter(player=p).update(username=${JSON.stringify(NICK_RARO)})
p.username = ${JSON.stringify(NICK_RARO)}; p.save()`)
  }
  const puerto = await puertoLibre()
  const servidor = spawn(py, ['manage.py', 'runserver', `127.0.0.1:${puerto}`, '--noreload'], {
    cwd: BACKEND,
    env: entorno,
    stdio: 'ignore',
  })
  const url = `http://127.0.0.1:${puerto}`
  for (let i = 0; i < 100; i++) {
    try {
      const r = await fetch(`${url}/api/health/`)
      if (r.ok) return { servidor, url }
    } catch {
      // todavia arrancando
    }
    await new Promise((ok) => setTimeout(ok, 200))
  }
  servidor.kill()
  throw new Error(`Django no arranco en ${url}`)
}

async function rutasDinamicas(url) {
  const extra = ['/no-existe']
  try {
    const partidas = await (await fetch(`${url}/api/matches/?limit=1`)).json()
    if (partidas.matches?.length) extra.push(`/partidas/${partidas.matches[0].id}`)
    const comp = await (await fetch(`${url}/api/teammates/?min_rounds=1`)).json()
    const raro = comp.synergy?.find((s) => s.username === NICK_RARO) || comp.synergy?.[0]
    if (raro) extra.push(`/jugadores/${raro.player_id}`)
  } catch {
    // base vacia: sin detalles
  }
  return extra
}

async function revisar(navegador, url, base, vista, ruta, roto) {
  const hallazgos = []
  const avisos = []
  const ctx = await navegador.newContext({ viewport: VISTAS[vista] })
  const page = await ctx.newPage()
  if (roto) await roto(page)
  page.on('console', (m) => m.type() === 'error' && hallazgos.push(['consola', m.text()]))
  page.on('pageerror', (e) => hallazgos.push(['excepcion', e.message]))
  page.on('requestfailed', (r) => {
    if (r.url().startsWith(url)) hallazgos.push(['pedido', `${r.url()} (${r.failure()?.errorText})`])
  })
  page.on('request', (r) => {
    const u = r.url()
    if (!u.startsWith(url) && !u.startsWith('data:') && !u.startsWith('blob:')) hallazgos.push(['red', u])
  })
  page.on('response', (r) => {
    if (r.url().startsWith(url) && r.status() >= 400) hallazgos.push(['http', `${r.status()} ${r.url().slice(url.length)}`])
  })
  try {
    await page.goto(url + ruta, { waitUntil: 'networkidle', timeout: 20000 })
  } catch (e) {
    hallazgos.push(['carga', e.message.split('\n')[0]])
  }
  await page.waitForTimeout(300)
  const r = await page.evaluate(() => {
    const visible = (el) => {
      const s = getComputedStyle(el)
      const b = el.getBoundingClientRect()
      return s.visibility !== 'hidden' && s.display !== 'none' && b.width > 0 && b.height > 0
    }
    const texto = document.body.innerText || ''
    const raros = [...new Set(texto.match(/\b(NaN|undefined|null|Infinity)\b|\[object Object\]/g) || [])]
    const ancho = window.innerWidth
    const desborde = document.documentElement.scrollWidth > ancho + 1
    let culpable = ''
    if (desborde) {
      // el mas adentro de los que se pasan: el que hay que arreglar, no su contenedor
      const pasados = [...document.querySelectorAll('body *')].filter((e) => visible(e) && e.getBoundingClientRect().right > ancho + 1)
      const hoja = pasados.find((e) => !pasados.some((o) => o !== e && e.contains(o))) || pasados[0]
      if (hoja) {
        const clase = hoja.className && typeof hoja.className === 'string' ? '.' + hoja.className.split(' ')[0] : ''
        const txt = (hoja.innerText || '').trim().slice(0, 40).replace(/\s+/g, ' ')
        culpable = `${hoja.tagName.toLowerCase()}${clase} "${txt}" llega a ${Math.round(hoja.getBoundingClientRect().right)} px`
      }
    }
    const botones = [...document.querySelectorAll('button, [role=button]')].filter(
      (b) => visible(b) && !(b.innerText || '').trim() && !b.getAttribute('aria-label') && !b.getAttribute('title'),
    ).length
    const imagenes = [...document.querySelectorAll('img')].filter((i) => !i.hasAttribute('alt')).length
    return {
      h1: document.querySelector('h1')?.innerText?.trim() || '',
      raros,
      desborde,
      culpable,
      vacios: document.querySelectorAll('.empty-state').length,
      botones,
      imagenes,
    }
  })
  if (!r.h1 && ruta !== '/no-existe') avisos.push(['a11y', 'la pagina no tiene h1'])
  if (r.raros.length) avisos.push(['texto', `a la vista: ${r.raros.join(', ')}`])
  if (r.desborde) avisos.push(['desborde', `scroll horizontal en ${VISTAS[vista].width} px (${r.culpable || 'sin culpable visible'})`])
  if (base === 'demo' && r.vacios && !['/no-existe', '/ajustes', '/ruleta'].includes(ruta)) {
    avisos.push(['vacio', `${r.vacios} estado(s) vacio(s) con la base sembrada`])
  }
  if (r.botones) avisos.push(['a11y', `${r.botones} boton(es) sin nombre accesible`])
  if (r.imagenes) avisos.push(['a11y', `${r.imagenes} imagen(es) sin alt`])
  // Teclado: los primeros 12 Tab tienen que mostrar donde esta el foco.
  let sinIndicador = 0
  let enfocables = 0
  for (let i = 0; i < 12; i++) {
    await page.keyboard.press('Tab')
    const f = await page.evaluate(() => {
      const el = document.activeElement
      if (!el || el === document.body) return null
      const s = getComputedStyle(el)
      const marca = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || s.boxShadow !== 'none'
      return { marca }
    })
    if (!f) break
    enfocables++
    if (!f.marca) sinIndicador++
  }
  if (enfocables && sinIndicador === enfocables) avisos.push(['foco', `${enfocables} elementos con Tab y ninguno muestra el foco`])
  if ((hallazgos.length || avisos.length) && SALIDA) {
    mkdirSync(SALIDA, { recursive: true })
    const nombre = `${base}-${vista}-${ruta.replace(/[^a-z0-9]+/gi, '_') || 'raiz'}.png`
    await page.screenshot({ path: path.join(SALIDA, nombre), fullPage: true }).catch(() => {})
  }
  await ctx.close()
  return { hallazgos, avisos }
}

async function main() {
  const navegador = await chromium.launch()
  const todos = []
  const todosAvisos = []
  let paginas = 0
  const tmpBase = mkdtempSync(path.join(os.tmpdir(), 'qa-paginas-'))
  try {
    for (const base of AUTOPRUEBA ? ['demo'] : BASES) {
      const tmp = path.join(tmpBase, base)
      mkdirSync(tmp, { recursive: true })
      const { servidor, url } = await levantar(base, tmp)
      try {
        let rutas = [...rutasDeApp(), ...(await rutasDinamicas(url))]
        let roto = null
        if (AUTOPRUEBA) {
          rutas = ['/']
          // la violacion que dice detectar: un 500 de la API y una excepcion en la pagina
          roto = async (page) => {
            await page.route('**/api/overview/**', (r) => r.fulfill({ status: 500, body: 'roto' }))
            await page.addInitScript(() => setTimeout(() => { throw new Error('autoprueba') }, 0))
          }
        }
        for (const ruta of rutas) {
          for (const vista of Object.keys(VISTAS)) {
            paginas++
            const { hallazgos, avisos } = await revisar(navegador, url, base, vista, ruta, roto)
            for (const [tipo, det] of hallazgos) todos.push(`HALLAZGO ${base} ${vista} ${ruta} ${tipo}: ${det}`)
            for (const [tipo, det] of avisos) todosAvisos.push(`AVISO ${base} ${vista} ${ruta} ${tipo}: ${det}`)
          }
        }
      } finally {
        servidor.kill()
      }
    }
  } finally {
    await navegador.close()
    rmSync(tmpBase, { recursive: true, force: true })
  }
  if (AUTOPRUEBA) {
    const vio500 = todos.some((h) => h.includes(' http: 500 /api/overview/'))
    const vioExc = todos.some((h) => h.includes('excepcion: autoprueba'))
    console.log(vio500 && vioExc ? 'AUTOPRUEBA_OK: ve un 500 de la API y una excepcion de la pagina'
      : `AUTOPRUEBA_FALLA: 500=${vio500} excepcion=${vioExc}`)
    return vio500 && vioExc ? 0 : 1
  }
  for (const l of [...new Set(todos)]) console.log(l)
  for (const l of [...new Set(todosAvisos)]) console.log(l)
  if (todos.length) {
    console.log(`QA_PAGINAS_FALLA: ${new Set(todos).size} hallazgos en ${paginas} paginas`)
    return 1
  }
  console.log(`QA_PAGINAS_OK (${paginas} paginas, ${new Set(todosAvisos).size} avisos)`)
  return 0
}

main().then((c) => process.exit(c), (e) => {
  console.error(e)
  process.exit(2)
})
