import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'
import { copyFileSync, existsSync, mkdirSync } from 'fs'

export default defineConfig({
  main: {
    plugins: [
      externalizeDepsPlugin(),
      {
        name: 'copy-splash-assets',
        closeBundle() {
          const destDir = resolve(__dirname, 'out/main')
          if (!existsSync(destDir)) mkdirSync(destDir, { recursive: true })
          copyFileSync(resolve(__dirname, 'src/main/splash.html'), resolve(destDir, 'splash.html'))
          copyFileSync(resolve(__dirname, 'src/main/splash-icon.png'), resolve(destDir, 'splash-icon.png'))
        },
      },
    ],
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
  },
  renderer: {
    resolve: {
      alias: {
        '@': resolve('src/renderer/src'),
      },
    },
    plugins: [
      react({
        babel: {
          plugins: [['babel-plugin-react-compiler', {}]],
        },
      }),
      tailwindcss(),
    ],
  },
})
