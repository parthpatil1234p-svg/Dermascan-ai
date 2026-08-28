import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react' // Standard React plugin used by modern Vite

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: './src/tests/setup.js',
    include: ['src/**/*.test.{js,jsx}'],
    exclude: ['e2e/**', 'node_modules/**', 'dist/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['src/**/*.{js,jsx}'],
      exclude: ['src/main.jsx', 'src/tests/**'],
    },
  },
  server: {
    port: 5173,
    allowedHosts: ['localhost', '127.0.0.1'],
    proxy: {
      // Forwards any front-end fetch('/api/...') request straight to your Python Uvicorn backend
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
