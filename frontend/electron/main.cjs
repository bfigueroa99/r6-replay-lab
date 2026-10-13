/**
 * Proceso principal de Electron: la app de escritorio.
 *
 * Es la misma UI que sirve Django en el navegador, dentro de una ventana. El
 * proceso principal levanta el backend si no esta corriendo, espera a que
 * /api/health/ responda y recien ahi muestra la ventana, para que nadie vea un
 * "no se pudo conectar" mientras Python arranca.
 *
 * NO es un overlay, y no lo va a ser: ventana normal con marco, sin
 * always-on-top, sin transparencia, sin click-through y sin ningun hook al
 * juego. Es un no-goal del proyecto (ver CLAUDE.md), no una feature pendiente.
 */

const { app, BrowserWindow, Menu, dialog, ipcMain, shell } = require('electron')
const { spawn } = require('node:child_process')
const fs = require('node:fs')
const path = require('node:path')

const REPO = path.resolve(__dirname, '..', '..')
const BACKEND = path.join(REPO, 'backend')

const HOST = '127.0.0.1'
const PORT = Number(process.env.R6_PORT) || 8000
const DJANGO_URL = `http://${HOST}:${PORT}`

/** `--url=...` apunta la ventana a otro lado (el dev server de Vite) y no levanta Django. */
const urlFlag = process.argv.find((a) => a.startsWith('--url='))
const APP_URL = urlFlag ? urlFlag.slice('--url='.length) : DJANGO_URL
const DEV = process.argv.includes('--dev')

/** Ultimas lineas del backend, para poder mostrarlas si no llega a levantar. */
const logTail = []
let django = null
let win = null

// ------------------------------------------------------------------ backend

/** Interprete del venv del repo; si no esta, el que haya en el PATH. */
function pythonPath() {
  const candidates =
    process.platform === 'win32'
      ? [path.join(REPO, '.venv', 'Scripts', 'python.exe')]
      : [path.join(REPO, '.venv', 'bin', 'python3'), path.join(REPO, '.venv', 'bin', 'python')]
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) return candidate
  }
  return process.platform === 'win32' ? 'python' : 'python3'
}

async function apiIsUp() {
  try {
    const response = await fetch(`${APP_URL}/api/health/`, { signal: AbortSignal.timeout(1500) })
    return response.ok
  } catch {
    return false
  }
}

function note(line) {
  const text = String(line).trimEnd()
  if (!text) return
  logTail.push(text)
  if (logTail.length > 40) logTail.shift()
  // Sin consola (doble clic en el acceso directo) stdout puede ser un handle
  // invalido, y el write tira EBADF dentro del handler de datos del backend:
  // eso cortaba el arranque en la primera linea de log. El log es un extra.
  try {
    process.stdout.write(`[django] ${text}\n`)
  } catch {
    /* sin consola no hay donde escribir, y no pasa nada */
  }
}

/**
 * Como arrancar el backend segun donde estemos.
 *
 * Instalada, la app trae su propio ejecutable con Python adentro y no hay repo
 * ni venv. Desde el repo se usa el venv, que es lo que uno quiere mientras
 * desarrolla: los cambios en el codigo se ven sin reempaquetar.
 *
 * Los dos corren `serve.py` (empaquetado, es el punto de entrada del .exe):
 * migra, hace la copia semanal y deja vigilando la carpeta de replays. Asi
 * `npm run desktop` se comporta igual que la app instalada. serve.py ya
 * levanta runserver sin el autoreloader, que lanzaria un hijo propio capaz de
 * sobrevivir a que matemos al padre.
 */
function backendCommand() {
  if (app.isPackaged) {
    return {
      cmd: path.join(process.resourcesPath, 'backend', 'r6-backend.exe'),
      args: [],
      cwd: path.join(process.resourcesPath, 'backend'),
    }
  }
  return { cmd: pythonPath(), args: ['serve.py'], cwd: BACKEND }
}

function startDjango() {
  const { cmd, args, cwd } = backendCommand()
  const child = spawn(cmd, args, {
    cwd,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1',
      PYTHONIOENCODING: 'utf-8',
      R6_HOST: HOST,
      R6_PORT: String(PORT),
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  child.stdout.on('data', note)
  child.stderr.on('data', note)
  child.on('error', (err) => note(`no se pudo ejecutar el backend: ${err.message}`))
  return child
}

function stopDjango() {
  if (!django || django.exitCode !== null) {
    django = null
    return
  }
  // En Windows matar el pid deja huerfano el arbol; /T se lleva a los hijos.
  if (process.platform === 'win32') {
    spawn('taskkill', ['/pid', String(django.pid), '/T', '/F'], { stdio: 'ignore' })
  } else {
    django.kill('SIGTERM')
  }
  django = null
}

async function waitForApi(timeoutMs = 90_000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (await apiIsUp()) return true
    if (django && django.exitCode !== null) return false // murio al arrancar
    await new Promise((resolve) => setTimeout(resolve, 400))
  }
  return false
}

// ------------------------------------------------------------------ ventana

function createWindow() {
  win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 640,
    // el fondo de styles.css: sin esto la ventana parpadea en blanco al abrir
    backgroundColor: '#0d1117',
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  })

  win.once('ready-to-show', () => win.show())
  if (DEV) win.webContents.openDevTools({ mode: 'detach' })

  // Todo lo que no sea la app se abre en el navegador del sistema, no adentro.
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) shell.openExternal(url)
    return { action: 'deny' }
  })
  win.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith(APP_URL)) {
      event.preventDefault()
      shell.openExternal(url)
    }
  })

  win.on('closed', () => {
    win = null
  })
  return win
}

// ------------------------------------------------------------------ carpetas

/**
 * Abre en el Explorador una de las carpetas de la app. Devuelve '' si pudo, o
 * el motivo si no.
 *
 * Recibe un nombre y no una ruta a proposito: la ruta sale de la API, y solo
 * se abre si es una carpeta. `shell.openPath` sobre un archivo lo ejecuta, y
 * eso no lo puede decidir la pagina.
 */
async function abrirCarpeta(cual) {
  let ajustes
  try {
    const response = await fetch(`${APP_URL}/api/settings/`, { signal: AbortSignal.timeout(3000) })
    ajustes = await response.json()
  } catch (err) {
    return `No se pudo consultar al backend: ${err.message}`
  }
  const rutas = {
    replays: ajustes.replay_dir,
    copias: ajustes.backups?.dir,
    datos: ajustes.data_dir,
  }
  const dir = Object.hasOwn(rutas, cual) ? rutas[cual] : null
  if (!dir) return 'Carpeta desconocida.'
  if (!fs.existsSync(dir) || !fs.statSync(dir).isDirectory()) {
    return `No existe la carpeta ${dir}. Elígela en Ajustes.`
  }
  return shell.openPath(dir)
}

async function abrirCarpetaDeReplays() {
  const error = await abrirCarpeta('replays')
  if (error) {
    dialog.showMessageBox(win, {
      type: 'warning',
      message: 'No se pudo abrir la carpeta de replays',
      detail: error,
    })
  }
}

/** Solo la pagina de la app puede pedir esto, no un sitio externo que se colara. */
const deLaApp = (event) => (event.senderFrame?.url || '').startsWith(APP_URL)

ipcMain.handle('r6:elegir-carpeta', async (event, desde) => {
  if (!deLaApp(event)) return null
  const { canceled, filePaths } = await dialog.showOpenDialog(win, {
    title: 'Elige la carpeta MatchReplay de Siege',
    defaultPath: typeof desde === 'string' && desde ? desde : undefined,
    properties: ['openDirectory'],
  })
  return canceled || !filePaths.length ? null : filePaths[0]
})

ipcMain.handle('r6:abrir-carpeta', (event, cual) =>
  deLaApp(event) ? abrirCarpeta(String(cual)) : 'No permitido.',
)

function buildMenu() {
  Menu.setApplicationMenu(
    Menu.buildFromTemplate([
      {
        label: 'App',
        submenu: [
          { label: 'Recargar', accelerator: 'CmdOrCtrl+R', click: () => win?.reload() },
          { label: 'Ajustes', click: () => win?.loadURL(`${APP_URL}/ajustes`) },
          { label: 'Carpeta de replays', click: abrirCarpetaDeReplays },
          { label: 'Abrir en el navegador', click: () => shell.openExternal(APP_URL) },
          { type: 'separator' },
          { role: 'toggleDevTools', label: 'Herramientas de desarrollo' },
          { type: 'separator' },
          { role: 'quit', label: 'Salir' },
        ],
      },
      {
        label: 'Ver',
        submenu: [
          { role: 'zoomIn', label: 'Acercar' },
          { role: 'zoomOut', label: 'Alejar' },
          { role: 'resetZoom', label: 'Zoom normal' },
          { type: 'separator' },
          { role: 'togglefullscreen', label: 'Pantalla completa' },
        ],
      },
    ]),
  )
}

// ------------------------------------------------------------------ arranque

/** Dos ventanas peleando por el puerto 8000 no terminan bien. */
if (!app.requestSingleInstanceLock()) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (win) {
      if (win.isMinimized()) win.restore()
      win.focus()
    }
  })

  app.whenReady().then(async () => {
    buildMenu()
    createWindow()
    await win.loadFile(path.join(__dirname, 'loading.html'))

    // Si el usuario ya tiene `manage.py runserver` en otra consola, se usa ese
    // y no se toca: no queremos matarle el server al cerrar la ventana.
    if (!(await apiIsUp())) {
      if (urlFlag) {
        note(`nadie responde en ${APP_URL}; con --url no se levanta el backend`)
      } else {
        django = startDjango()
      }
    }

    if (await waitForApi()) {
      await win.loadURL(APP_URL)
      return
    }

    // Instalada no hay venv ni scripts: el consejo tiene que ser otro.
    const consejo = app.isPackaged
      ? `Si otro programa usa el puerto ${PORT}, cierralo y vuelve a abrir la app.`
      : 'Revisa que el venv este creado (scripts\\setup.ps1).'
    const { response } = await dialog.showMessageBox(win, {
      type: 'error',
      message: 'El backend no respondio',
      detail:
        `No hubo respuesta en ${APP_URL}.\n\n${consejo}\n\n` +
        `Ultimas lineas:\n${logTail.slice(-12).join('\n') || '(sin salida)'}`,
      buttons: ['Salir', 'Reintentar'],
      defaultId: 1,
    })
    if (response === 1) {
      app.relaunch()
    }
    app.quit()
  })

  app.on('window-all-closed', () => app.quit())
  app.on('before-quit', stopDjango)
  process.on('exit', stopDjango)
}
