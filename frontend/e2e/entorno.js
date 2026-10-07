/**
 * Lo que comparten la config de Playwright y el global setup: donde esta el
 * repo, que interprete de Python usar y contra que base corre el e2e.
 *
 * La base es un archivo aparte dentro de `e2e/.tmp/` y nunca la de verdad: el
 * e2e siembra datos sinteticos con `manage.py seed_demo`, y apuntar eso a la
 * base real seria borrar el historial del usuario. Lo mismo el `.env` y la
 * carpeta de datos: la pagina Ajustes escribe el `.env` y las copias de
 * seguridad rotan las de `data/backups`.
 */

import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const AQUI = path.dirname(fileURLToPath(import.meta.url))

export const REPO = path.resolve(AQUI, '..', '..')
export const BACKEND = path.join(REPO, 'backend')
export const DIST = path.join(REPO, 'frontend', 'dist')
export const DB = path.join(AQUI, '.tmp', 'e2e.sqlite3')
export const DATOS = path.join(AQUI, '.tmp', 'data')
export const ENV_FILE = path.join(AQUI, '.tmp', '.env')
/** Una carpeta de replays que no existe, a proposito: ver servidor.js. */
export const SIN_REPLAYS = path.join(AQUI, '.tmp', 'sin-replays')

export const PUERTO = Number(process.env.E2E_PORT || 8099)
export const BASE_URL = `http://127.0.0.1:${PUERTO}`

/** El interprete del venv; si no esta, el del PATH. */
export function python() {
  const candidatos =
    process.platform === 'win32'
      ? [path.join(REPO, '.venv', 'Scripts', 'python.exe')]
      : [path.join(REPO, '.venv', 'bin', 'python')]
  for (const candidato of candidatos) {
    if (existsSync(candidato)) return candidato
  }
  return process.platform === 'win32' ? 'python' : 'python3'
}

/** El entorno de Django para el e2e: base, .env y datos propios, nada del usuario. */
export function entornoDjango() {
  return {
    ...process.env,
    SQLITE_PATH: DB,
    DATA_DIR: DATOS,
    R6_ENV_FILE: ENV_FILE,
    // sin esto el .env del usuario decide la ventana de trade y los numeros que
    // afirman las pruebas dejarian de depender solo del seed
    TRADE_WINDOW_SECONDS: '3',
    SESSION_GAP_MINUTES: '120',
    MIN_ROUNDS_DEFAULT: '5',
  }
}
