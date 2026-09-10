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
})
