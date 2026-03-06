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
    // listen on all interfaces so the port is reachable from outside the container
    host: true,
    // File-change detection inside Docker requires polling because Linux inotify
    // events don't propagate into containers. Has no effect when running locally.
    watch: {
      usePolling: true,
    },
    // The proxy forwards any request starting with /api from the Vite dev server
    // (port 5173) to the Django server.
    // API_TARGET defaults to localhost:8000 for local dev.
    // docker-compose overrides it to http://api:8000 (Docker service name).
    proxy: {
      '/api': {
        target: process.env.API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
