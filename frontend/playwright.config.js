import { defineConfig, devices } from '@playwright/test'

import { BASE_URL } from './e2e/entorno.js'

/**
 * El e2e corre contra la app de verdad: Django sirviendo el build de React en
 * la misma URL, que es exactamente como la usa el usuario. No hay mocks de la
 * API; lo que se prueba es la cadena completa desde el ORM hasta el DOM.
 *
 * Solo Chromium: la app se usa en el navegador del usuario y dentro de Electron,
 * que tambien es Chromium. Probar tres motores seria pagar por nada.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  // un solo worker: detras hay un runserver de desarrollo con SQLite, que no
  // esta hecho para concurrencia. La suite es corta; la reproducibilidad importa mas.
  workers: 1,
  // sin reintentos: un e2e que se reintenta esconde justo el tipo de bug
  // intermitente que se supone que tiene que cazar
  retries: 0,
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  timeout: 30_000,
  expect: { timeout: 10_000 },

  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },

  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],

  // el script prepara la base y recien despues levanta Django; ver e2e/servidor.js
  webServer: {
    command: 'node e2e/servidor.js',
    url: `${BASE_URL}/api/health/`,
    reuseExistingServer: false,
    timeout: 60_000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
})
