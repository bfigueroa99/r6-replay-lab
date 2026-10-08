/**
 * Levanta el backend del e2e: base propia, recien migrada y sembrada.
 *
 * Esto es un script y no el `globalSetup` de Playwright porque Playwright
 * arranca el `webServer` **antes** de correr el global setup: preparar la base
 * ahi llegaba tarde y Django moria con "unable to open database file". Como
 * ademas hay que encadenar tres comandos, hacerlo en Node en vez de en la linea
 * del shell evita depender de si el shell es cmd, PowerShell o bash.
 */

import { execFileSync, spawn } from 'node:child_process'
import { existsSync, mkdirSync, rmSync, writeFileSync } from 'node:fs'
import path from 'node:path'

import {
  BACKEND,
  DATOS,
  DB,
  DIST,
  ENV_FILE,
  PUERTO,
  SIN_REPLAYS,
  entornoDjango,
  python,
} from './entorno.js'

const py = python()
const opciones = { cwd: BACKEND, env: entornoDjango() }

if (!existsSync(path.join(DIST, 'index.html'))) {
  console.error(
    `\nNo hay build del frontend en ${DIST}.\n` +
      'Django sirve ese directorio, asi que sin el las pruebas verian la pagina ' +
      'de "falta compilar" en vez de la app. Corre `npm run e2e`, que compila solo.\n',
  )
  process.exit(1)
}

// la base se rehace entera en cada corrida: una que sobrevive entre corridas es
// una prueba que pasa por lo que quedo de la anterior
mkdirSync(path.dirname(DB), { recursive: true })
rmSync(DB, { force: true })
rmSync(DATOS, { recursive: true, force: true })
mkdirSync(DATOS, { recursive: true })
// la carpeta de replays va fijada a una que no existe: si se dejara buscarla
// sola, en un PC con Siege instalado encontraria la de verdad y las pruebas
// dependerian de que maquina las corre
writeFileSync(ENV_FILE, `REPLAY_DIR=${SIN_REPLAYS}\n`)

try {
  execFileSync(py, ['manage.py', 'migrate', '--no-input'], { ...opciones, stdio: 'pipe' })
  execFileSync(py, ['manage.py', 'seed_demo', '--force'], { ...opciones, stdio: 'pipe' })
} catch (error) {
  const salida = [error.stdout, error.stderr].filter(Boolean).join('\n')
  console.error(`\nNo pude preparar la base del e2e con ${py}:\n${salida || error.message}\n`)
  process.exit(1)
}

const servidor = spawn(
  py,
  ['manage.py', 'runserver', `127.0.0.1:${PUERTO}`, '--noreload'],
  { ...opciones, stdio: 'inherit' },
)
servidor.on('exit', (codigo) => process.exit(codigo ?? 0))
for (const senal of ['SIGINT', 'SIGTERM']) {
  process.on(senal, () => servidor.kill(senal))
}
