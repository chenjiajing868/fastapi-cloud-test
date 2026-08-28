import { useEffect, useRef, useState } from 'react'

const SUGGESTIONS = [
  '你能帮我做什么?',
  '介绍一下你自己',
  '请用 Markdown 给我一个示例回答',
]

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const abortRef = useRef(null)
  const scrollRef = useRef(null)

  // 自动滚到底部
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages])

  const sendMessage = async (text) => {
    const trimmed = text.trim()
    if (!trimmed || streaming) return

    const newMessages = [...messages, { role: 'user', content: trimmed }]
    setMessages(newMessages)
    setInput('')
    setStreaming(true)

    // 先插入一个空的 assistant 消息,后续流式追加
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }])

    // 中止上一次未完成的请求
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: newMessages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
        signal: controller.signal,
      })

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`)
      }

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()

      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        // SSE 以 \n\n 分隔
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data:')) continue
          const payload = line.slice(5).trim()
          if (payload === '[DONE]') continue

          try {
            const parsed = JSON.parse(payload)
            if (parsed.error) {
              setMessages((prev) => {
                const copy = [...prev]
                copy[copy.length - 1] = {
                  role: 'assistant',
                  content: `⚠️ ${parsed.error}`,
                }
                return copy
              })
              continue
            }
            if (parsed.content) {
              setMessages((prev) => {
                const copy = [...prev]
                const last = copy[copy.length - 1]
                if (last && last.role === 'assistant') {
                  copy[copy.length - 1] = {
                    role: 'assistant',
                    content: last.content + parsed.content,
                  }
                }
                return copy
              })
            }
          } catch {
            // 忽略解析失败的单条数据
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setMessages((prev) => {
          const copy = [...prev]
          copy[copy.length - 1] = {
            role: 'assistant',
            content: `⚠️ 请求失败: ${err.message}`,
          }
          return copy
        })
      }
    } finally {
      setStreaming(false)
      abortRef.current = null
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const handleClear = () => {
    if (streaming && abortRef.current) abortRef.current.abort()
    setMessages([])
    setStreaming(false)
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-avatar">🤖</div>
        <div className="header-info">
          <div className="header-title">云小智 · AI 客服</div>
          <div className="header-subtitle">
            <span className="status-dot" /> 在线 · 平均 1.2s 响应
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleClear}
            style={{
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              color: 'white',
              padding: '6px 12px',
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: 12,
            }}
          >
            清空
          </button>
        )}
      </header>

      <div className="messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="welcome">
            <h3>👋 你好,我是云小智</h3>
            <p>可以问我产品问题、技术问题,或者随便聊聊~</p>
            <div style={{ marginTop: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  style={{
                    padding: '10px 16px',
                    border: '1px solid #e5e7eb',
                    borderRadius: 10,
                    background: 'white',
                    cursor: 'pointer',
                    fontSize: 13,
                    color: '#4b5563',
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`msg-row ${m.role}`}>
            <div className="msg-avatar">
              {m.role === 'user' ? '我' : 'AI'}
            </div>
            <div
              className={`msg-bubble${
                streaming && i === messages.length - 1 && m.role === 'assistant'
                  ? ' cursor-blink'
                  : ''
              }`}
            >
              {m.content || (m.role === 'assistant' ? '正在思考...' : '')}
            </div>
          </div>
        ))}
      </div>

      <div className="input-bar">
        <textarea
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息,Enter 发送,Shift+Enter 换行..."
          disabled={streaming}
        />
        <button
          className="send-btn"
          onClick={() => sendMessage(input)}
          disabled={streaming || !input.trim()}
        >
          {streaming ? '生成中...' : '发送'}
        </button>
      </div>
    </div>
  )
}
