import { useState, useRef, useEffect } from 'react'
import styles from './Chat.module.css'

const WELCOME = '안녕하세요! 온누리상품권 가맹점 안내 챗봇입니다.\n궁금한 가맹점이나 지역을 검색해보세요. 😊'

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: 'bot', text: WELCOME },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // 백엔드가 기대하는 형식: [[user, bot], ...]
  function buildHistory(msgs) {
    const pairs = []
    for (let i = 0; i < msgs.length - 1; i++) {
      if (msgs[i].role === 'user' && msgs[i + 1]?.role === 'bot') {
        pairs.push([msgs[i].text, msgs[i + 1].text])
      }
    }
    return pairs
  }

  async function sendMessage() {
    const text = input.trim()
    if (!text || loading) return

    const newMessages = [...messages, { role: 'user', text }]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: buildHistory(newMessages),
        }),
      })

      if (!res.ok) throw new Error(`서버 오류 (${res.status})`)

      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'bot', text: data.reply }])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'bot', text: `오류가 발생했습니다: ${err.message}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <span className={styles.logo}>🏪</span>
        <h1>온누리상품권 가맹점 챗봇</h1>
      </header>

      <main className={styles.messageList}>
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`${styles.row} ${msg.role === 'user' ? styles.rowUser : styles.rowBot}`}
          >
            {msg.role === 'bot' && <span className={styles.avatar}>🤖</span>}
            <div
              className={`${styles.bubble} ${msg.role === 'user' ? styles.bubbleUser : styles.bubbleBot}`}
            >
              {msg.text.split('\n').map((line, j) => (
                <span key={j}>
                  {line}
                  {j < msg.text.split('\n').length - 1 && <br />}
                </span>
              ))}
            </div>
          </div>
        ))}

        {loading && (
          <div className={`${styles.row} ${styles.rowBot}`}>
            <span className={styles.avatar}>🤖</span>
            <div className={`${styles.bubble} ${styles.bubbleBot} ${styles.typing}`}>
              <span /><span /><span />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </main>

      <footer className={styles.inputArea}>
        <textarea
          className={styles.textarea}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="궁금한 가맹점이나 지역을 입력하세요... (Enter로 전송)"
          rows={1}
          disabled={loading}
        />
        <button
          className={styles.sendBtn}
          onClick={sendMessage}
          disabled={!input.trim() || loading}
        >
          전송
        </button>
      </footer>
    </div>
  )
}
