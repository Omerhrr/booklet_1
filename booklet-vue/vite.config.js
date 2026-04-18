import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  // Remove 'root' or set it to process.cwd()
  plugins: [
    vue(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      // Use this to dynamically find the src folder
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    //     watch: {
    //   // Use polling to avoid ENOSPC (inotify limit) errors
    //   usePolling: true,
    //   interval: 1000,
    // },
  },
  define: {
    __VITE_BACKEND_URL__: JSON.stringify(process.env.VITE_BACKEND_URL || 'http://localhost:8000'),
  },
})
