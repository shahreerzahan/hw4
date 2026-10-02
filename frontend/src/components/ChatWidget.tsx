import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useLocation } from 'react-router-dom'
import DanTheBulldog from './DanTheBulldog'
import { clearChatHistory, fetchChatHistory, sendChat, type CardProduct, type HistoryMessage } from '../api'
import { useAuth } from '../auth'
import { useChatResults } from '../chatResults'

const MAX_MESSAGE_CHARS = 1000
const GUEST_HISTORY = 10 // recent messages a guest's chat box sends back (nothing is saved for guests)

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  error?: boolean
  pagePath?: string // page a shopper message was sent from
  products?: CardProduct[] // cards this reply put on the page
  resultsTitle?: string | null
}

let nextId = 1

function greeting(firstName?: string): Message {
  return {
    id: 0,
    role: 'assistant',
    content: firstName
      ? `Woof, hi ${firstName}! Looking for a cozy hoodie, a game-day tee, or a gift? Ask me anything about the shop!`
      : "Woof, hi there! I'm Dan. Looking for a cozy hoodie, a game-day tee, or a gift? Ask me anything about the shop!",
  }
}

// App.tsx remounts this component (via `key`) whenever the shopper logs in or out, so each
// account starts from its own saved history and a guest never sees someone else's chat.
export default function ChatWidget() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>(() => [greeting(user?.first_name)])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const { showResults } = useChatResults()
  const location = useLocation()

  // Logged in: load the saved conversation from the database.
  useEffect(() => {
    if (!user) return
    fetchChatHistory()
      .then((items) => {
        if (!items.length) return
        const saved: Message[] = items.map((h) => ({
          id: nextId++,
          role: h.role,
          content: h.content,
          products: h.products.length ? h.products : undefined,
          resultsTitle: h.results_title,
        }))
        setMessages([greeting(user.first_name), ...saved])
      })
      .catch(() => {})
  }, [user])

  // Keep the newest message in view.
  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending, open])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  const guestHistory = (): HistoryMessage[] =>
    messages
      .filter((m) => m.id !== 0 && !m.error)
      .slice(-GUEST_HISTORY)
      .map((m) => ({
        role: m.role,
        content: m.content,
        product_ids: m.products?.map((p) => p.product_id),
        page_path: m.pagePath,
      }))

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    const pagePath = location.pathname
    const history = user ? [] : guestHistory() // logged-in memory comes from the server
    setMessages((m) => [...m, { id: nextId++, role: 'user', content: text, pagePath }])
    setInput('')
    setSending(true)
    try {
      const { reply, results_title, products } = await sendChat(text, pagePath, history)
      if (products.length) showResults(results_title ?? "Dan's picks", text, products, pagePath)
      setMessages((m) => [
        ...m,
        {
          id: nextId++,
          role: 'assistant',
          content: reply,
          products: products.length ? products : undefined,
          resultsTitle: results_title,
        },
      ])
    } catch (err) {
      setMessages((m) => [...m, { id: nextId++, role: 'assistant', content: (err as Error).message, error: true }])
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  // Re-show a reply's cards on the page (e.g. from a saved conversation), then scroll to them.
  const showCards = (m: Message) => {
    if (!m.products) return
    showResults(m.resultsTitle ?? "Dan's picks", 'from your chat', m.products, location.pathname)
    requestAnimationFrame(() => document.getElementById('chat-results')?.scrollIntoView({ behavior: 'smooth' }))
  }

  const onClear = async () => {
    if (!window.confirm('Clear your saved chat with Dan?')) return
    try {
      await clearChatHistory()
      setMessages([greeting(user?.first_name)])
    } catch (err) {
      setMessages((m) => [...m, { id: nextId++, role: 'assistant', content: (err as Error).message, error: true }])
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
              <span>{user ? `Chatting as ${user.first_name} · history saved` : 'Guest · log in to save your chat'}</span>
            </div>
            {user && messages.length > 1 && (
              <button type="button" className="chat-clear" onClick={onClear}>
                Clear
              </button>
            )}
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </div>

          <div className="chat-body" ref={bodyRef} aria-live="polite">
            {messages.map((m) => (
              <div key={m.id} className={`chat-bubble ${m.role}${m.error ? ' error' : ''}`}>
                {m.content}
                {m.products && (
                  <button type="button" className="chat-cards-chip" onClick={() => showCards(m)}>
                    {m.products.length === 1 ? 'See it on the page ↑' : `See all ${m.products.length} on the page ↑`}
                  </button>
                )}
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
