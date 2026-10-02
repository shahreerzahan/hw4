import { useEffect, useRef, useState, type FormEvent } from 'react'
import DanTheBulldog from './DanTheBulldog'
import { sendChat } from '../api'

const MAX_MESSAGE_CHARS = 1000

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  error?: boolean
}

const GREETING: Message = {
  id: 0,
  role: 'assistant',
  content: "Woof, hi there! I'm Dan. Looking for a cozy hoodie, a game-day tee, or a gift? Ask me anything about the shop!",
}

let nextId = 1

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Keep the newest message in view.
  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending, open])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    setMessages((m) => [...m, { id: nextId++, role: 'user', content: text }])
    setInput('')
    setSending(true)
    try {
      const { reply } = await sendChat(text)
      setMessages((m) => [...m, { id: nextId++, role: 'assistant', content: reply }])
    } catch (err) {
      setMessages((m) => [...m, { id: nextId++, role: 'assistant', content: (err as Error).message, error: true }])
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  return (
    <div className="chat-widget">
      {open && (
        <div className="chat-panel" role="dialog" aria-label="Chat with Dan">
          <div className="chat-header">
            <DanTheBulldog className="dan" />
            <div className="chat-title">
              <strong>Dan the Bulldog</strong>
              <span>Your shopping buddy</span>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </div>

          <div className="chat-body" ref={bodyRef} aria-live="polite">
            {messages.map((m) => (
              <div key={m.id} className={`chat-bubble ${m.role}${m.error ? ' error' : ''}`}>
                {m.content}
              </div>
            ))}
            {sending && (
              <div className="chat-bubble assistant typing" aria-label="Dan is typing">
                <span />
                <span />
                <span />
              </div>
            )}
          </div>

          <form className="chat-input" onSubmit={onSubmit}>
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask Dan about hoodies, gifts…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              maxLength={MAX_MESSAGE_CHARS}
              aria-label="Message"
            />
            <button type="submit" className="btn btn-primary" disabled={sending || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      )}
      <button
        className="chat-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Chat with Dan'}
      >
        {open ? '×' : <DanTheBulldog className="dan" title="Chat with Dan" />}
      </button>
    </div>
  )
}
