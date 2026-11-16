import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';

export default defineConfig({
  plugins: [react()],
  root: resolve(import.meta.dirname, 'src/renderer'),
  base: './',
  build: { outDir: resolve(import.meta.dirname, 'dist/renderer'), emptyOutDir: true },
  server: { host: '127.0.0.1', port: 1420, strictPort: true },
});
