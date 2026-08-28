import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite 配置:构建产物输出到 dist/(默认),相对路径 ../frontend/dist
// FastAPI 后端通过 app.frontend("/", directory="frontend/dist") 挂载
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // 开发期代理 /api 到 FastAPI,避免跨域
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
  },
})
