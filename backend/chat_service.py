"""AI 客服聊天服务模块.

封装对 LLM 的调用逻辑,支持流式输出.
使用 OpenAI 兼容协议,可通过环境变量切换不同的服务商
(OpenAI / DeepSeek / 月之暗面 / 智谱 / Ollama 等).
"""

from __future__ import annotations

import os
from typing import AsyncIterator

from openai import AsyncOpenAI

# 系统提示词:定义 AI 客服的人设和能力边界
DEFAULT_SYSTEM_PROMPT = """你是「云小智」,一名专业、友善、耐心的人工智能客服助手.

你的职责:
1. 用简洁清晰的语言回答用户问题
2. 如果不确定,坦诚告知并建议联系人工客服
3. 涉及金钱、隐私、医疗、法律等敏感话题时,主动提示风险
4. 优先使用 Markdown 格式回复,代码用代码块包裹

你的风格:
- 语气温和,称呼用户为「您」
- 一次只回答一个问题,不堆砌信息
- 必要时给出可操作的步骤
"""

# 从环境变量读取配置,带默认值方便本地开发
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_SYSTEM_PROMPT = os.getenv("LLM_SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)

# 客户端按需创建(避免无 Key 时启动报错)
_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    """获取或创建 OpenAI 兼容客户端."""
    global _client
    if _client is None:
        if not LLM_API_KEY:
            raise RuntimeError(
                "未配置 LLM_API_KEY 环境变量."
                "本地开发可在 backend/.env 中设置,部署到 FastAPI Cloud 时在控制台配置."
            )
        _client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    return _client


async def stream_chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.7,
) -> AsyncIterator[str]:
    """流式调用 LLM,逐块产出文本片段.

    Parameters
    ----------
    messages:
        OpenAI 格式的消息列表,如 [{"role": "user", "content": "你好"}].
    model:
        覆盖默认模型.
    temperature:
        采样温度,0~2,越高越发散.

    Yields
    ------
    str
        每个增量片段.
    """
    client = get_client()
    use_model = model or LLM_MODEL

    # 始终把系统提示词放在最前面
    full_messages: list[dict[str, str]] = [
        {"role": "system", "content": LLM_SYSTEM_PROMPT},
        *messages,
    ]

    stream = await client.chat.completions.create(
        model=use_model,
        messages=full_messages,  # type: ignore[arg-type]
        temperature=temperature,
        stream=True,
    )

    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        content = getattr(delta, "content", None)
        if content:
            yield content


async def fallback_stream(text: str) -> AsyncIterator[str]:
    """无 API Key 时的本地降级流式输出,便于本地调试 UI."""

    import asyncio

    for ch in text:
        yield ch
        # 真实场景下不需要 sleep,这里模拟打字机效果便于观察
        await asyncio.sleep(0.02)
