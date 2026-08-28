# 前端说明

AI 客服聊天界面前端,React + Vite.

## 本地开发

```bash
npm install
npm run dev
```

默认监听 http://localhost:5173,通过 Vite 代理转发 `/api` 到 http://127.0.0.1:8000(确保后端已启动).

## 构建生产产物

```bash
npm run build
```

产物输出到 `dist/`,FastAPI 通过 `app.frontend("/", directory="frontend/dist")` 挂载.

## 部署到 FastAPI Cloud

- 通过 `.fastapicloudignore` 中的 `!frontend/dist/` 放行构建产物
- 部署前需**先**本地 build,云端不会跑 `npm run build`(用 GitHub Actions 时需自定义 workflow)
