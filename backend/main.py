"""FastAPI 入口文件.

托管 API(AI 客服聊天接口)+ 前端构建产物.

部署到 FastAPI Cloud 时:
- Application Directory 填 backend
- 前端构建产物 frontend/dist 由 .fastapicloudignore 放行上传
- 环境变量 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL 在控制台配置
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .chat_service import fallback_stream, stream_chat

logger = logging.getLogger("ai-customer-service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI 客服助手",
    description="基于 FastAPI + LLM 的流式对话客服系统",
    version="0.1.0",
)

# 开发期允许跨域,生产环境单应用部署同源可移除
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(..., min_length=1, max_length=50)


class HealthResponse(BaseModel):
    status: str
    frontend_loaded: bool


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """健康检查 + 探活接口,确认前端构建产物是否存在."""

    frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
    return HealthResponse(
        status="ok", frontend_loaded=(frontend_path / "index.html").exists()
    )


@app.post("/api/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    """流式聊天接口:接收历史消息,逐 token 返回 AI 回复.

    使用 Server-Sent Events (SSE) 协议,前端用 fetch + ReadableStream 解析.
    """

    messages_payload = [m.model_dump() for m in req.messages]

    async def event_generator():
        try:
            async for chunk in stream_chat(messages_payload):
                # SSE 格式:每条 data: 开头,以 \n\n 结束
                payload = json.dumps({"content": chunk}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:  # noqa: BLE001
            logger.exception("LLM 调用失败")
            err_payload = json.dumps(
                {"error": f"服务暂时不可用: {exc!s}"}, ensure_ascii=False
            )
            yield f"data: {err_payload}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲,保证流式
        },
    )


@app.post("/api/echo")
async def echo(req: ChatRequest) -> StreamingResponse:
    """本地调试用接口:不调 LLM,直接回显,便于前端 UI 联调."""

    last_user = next(
        (m.content for m in reversed(req.messages) if m.role == "user"), ""
    )
    reply = (
        f"🤖 [本地回显模式] 你说的是:{last_user}\n\n"
        "请配置 backend/chat_service.py 中的 LLM_API_KEY 启用真实对话."
    )

    async def gen():
        # fallback_stream 现在直接是 async generator,直接迭代即可
        async for ch in fallback_stream(reply):
            payload = json.dumps({"content": ch}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


# ---------- 前端托管 ----------
# 路径相对于 backend/,即 <repo>/frontend/dist
# 本地可能尚未 build,通过 health 接口可观察 frontend_loaded 字段
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.frontend("/", directory=str(_frontend_dist))
else:
    logger.warning(
        "前端构建产物不存在: %s — 请先 cd frontend && npm install && npm run build",
        _frontend_dist,
    )
