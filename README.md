# AI 客服聊天系统

基于 **FastAPI + React + LLM** 的流式 AI 客服聊天系统,单应用部署到 [FastAPI Cloud](https://fastapicloud.com),一个域名同时托管 API 和前端.

## 项目结构

```
fastapi-cloud-test/
├── backend/              # FastAPI 后端 ← Application Directory 填这个
│   ├── main.py           # FastAPI 入口
│   ├── chat_service.py   # LLM 调用层
│   ├── requirements.txt
│   └── .env.example
├── frontend/             # React 前端
│   ├── src/
│   ├── package.json
│   └── dist/             # 构建产物(.gitignore 排除,.fastapicloudignore 放行)
├── .gitignore
└── .fastapicloudignore   # 关键:把 frontend/dist/ 放回部署包
```

## 功能特性

- 流式输出(打字机效果)
- 多轮对话记忆
- 可配置系统提示词(客服人设)
- 中止生成(发送新消息自动取消上一次)
- 移动端适配
- 本地回显接口(`/api/echo`),无需 API Key 也能调试 UI

## 本地开发

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env       # 编辑填入 LLM_API_KEY
uvicorn main:app --reload --app-dir ..
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

Vite 通过代理把 `/api/*` 转发到 `http://127.0.0.1:8000`,无需 CORS 配置.

## 部署到 FastAPI Cloud

1. **配置 Application Directory** = `backend`
2. **配置环境变量**(控制台):
   - `LLM_API_KEY` — 必填
   - `LLM_BASE_URL` — 默认 `https://api.deepseek.com`
   - `LLM_MODEL` — 默认 `deepseek-chat`
3. **构建前端**:
   ```bash
   cd frontend && npm install && npm run build
   ```
4. **部署**:
   ```bash
   fastapi deploy
   ```

## API 接口

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/health` | GET | 健康检查 |
| `/api/chat` | POST | 流式聊天(SSE) |
| `/api/echo` | POST | 本地回显,无需 API Key |

`/docs` 自动生成 Swagger 文档.
