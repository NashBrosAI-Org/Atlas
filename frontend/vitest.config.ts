import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// Test config kept separate from vite.config.ts so the build's `tsc -b` (which
// type-checks vite.config.ts) stays clean of the vitest/rolldown type friction.
export default defineConfig({
  plugins: [react()],
  esbuild: { jsx: 'automatic' },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test-setup.ts',
    css: false,
  },
})
