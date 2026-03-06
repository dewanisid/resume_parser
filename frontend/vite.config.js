import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),   // Tailwind v4 works as a Vite plugin — no postcss.config needed
  ],
  resolve: {
    // This lets us write: import { Button } from '@/components/ui/button'
    // instead of a long relative path like: '../../components/ui/button'
    // shadcn/ui uses this pattern extensively
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    // The proxy forwards any request starting with /api from the Vite dev server
    // (port 5173) to the Django server (port 8000).
    // This means axios calls to '/api/v1/...' just work — no CORS issues in dev.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
