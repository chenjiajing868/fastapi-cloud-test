# 后端说明

AI 客服聊天功能的后端服务,基于 FastAPI + OpenAI 兼容协议.

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量(可选,留空则只能使用 /api/echo 回显接口)
cp .env.example .env
# 编辑 .env 填入 LLM_API_KEY

# 启动服务
uvicorn main:app --reload --app-dir ..
# 或在 backend/ 目录下:
# uvicorn main:app --reload
```

启动后访问:
- API 文档:http://127.0.0.1:8000/docs
- 健康检查:http://127.0.0.1:8000/api/health
- 流式聊天:POST http://127.0.0.1:8000/api/chat
- 回显接口:POST http://127.0.0.1:8000/api/echo
- 前端页面:http://127.0.0.1:8000/(需先 build 前端)

## 部署到 FastAPI Cloud

1. Application Directory 填 `backend`
2. 环境变量在控制台配置:`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`
3. 先在本地构建前端:`cd frontend && npm install && npm run build`
4. 执行 `fastapi deploy`(确保 `.fastapicloudignore` 中的 `!frontend/dist/` 起作用)
