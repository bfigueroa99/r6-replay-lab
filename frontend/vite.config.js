import { configDefaults } from 'vitest/config'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En desarrollo el front corre en 5173 y las llamadas a /api se redirigen a
// Django en 8000, asi no hace falta configurar CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: { outDir: 'dist', emptyOutDir: true },
  // los *.spec.js de e2e/ son de Playwright, no de vitest: sin esto vitest los
  // carga, no entiende `test` de @playwright/test y marca el archivo como fallido
  test: { exclude: [...configDefaults.exclude, 'e2e/**'] },
})
