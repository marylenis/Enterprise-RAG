import { defineConfig } from 'vite'

export default defineConfig({
  root: '.',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: './index.html',
        chat: './chat.html',
      }
    }
  },
  server: {
    port: 5173,
    host: true
  }
})