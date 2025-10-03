import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    strictPort: false,
    hmr: {
      clientPort: 443,
      host: 'bitter-trees-lead.loca.lt'
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        timeout: 300000,
        proxyTimeout: 300000
      }
    }
  },
  build: {
    outDir: 'dist'
  }
})

