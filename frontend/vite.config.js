import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        chat: resolve(__dirname, 'chat.html'),
        documents: resolve(__dirname, 'documents.html'),
        analytics: resolve(__dirname, 'analytics.html'),
        quality: resolve(__dirname, 'quality.html'),
        settings: resolve(__dirname, 'settings.html'),
      },
    },
  },
  server: {
    host: true,
    port: 80, // For dev mode inside container if needed
  },
});