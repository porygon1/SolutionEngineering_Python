import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  
  // Server configuration for Docker compatibility
  server: {
    host: true, // Allow external connections (0.0.0.0)
    port: 5173,
    strictPort: true, // Exit if port is already in use
    watch: {
      usePolling: true, // Enable polling for Docker environments
    },
    hmr: {
      clientPort: 5173, // Ensure HMR works in Docker
    },
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
  },
  
  // Preview server configuration
  preview: {
    host: true,
    port: 4173,
    strictPort: true,
  },
  
  // Build configuration
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable source maps in production for smaller builds
    minify: 'esbuild',
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['@heroicons/react', '@headlessui/react', 'framer-motion'],
          utils: ['axios', '@tanstack/react-query', 'clsx'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  
  // Path resolution
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@services': path.resolve(__dirname, './src/services'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
    },
  },
  
  // Environment variables prefix
  envPrefix: 'VITE_',
  
  // Optimize dependencies
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'axios',
      '@tanstack/react-query',
      'framer-motion',
      'lucide-react',
      'clsx',
      '@heroicons/react/24/outline',
      '@heroicons/react/24/solid',
      '@headlessui/react',
    ],
  },
  
  // Define global constants
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
}) 