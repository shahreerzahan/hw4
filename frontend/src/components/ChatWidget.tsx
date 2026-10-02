import { useState } from 'react'
import DanTheBulldog from './DanTheBulldog'

// Placeholder only: the chatbot gets wired to the backend agent in a later problem.
export default function ChatWidget() {
  const [open, setOpen] = useState(false)

  return (
    <div className="chat-widget">
      {open && (
        <div className="chat-panel" role="dialog" aria-label="Chat with Dan">
          <div className="chat-header">
            <DanTheBulldog />
            <div className="chat-title">
              <strong>Dan the Bulldog</strong>
              <span>Your shopping buddy</span>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </div>
          <div className="chat-body">
            <div className="chat-bubble assistant">
              Woof, hi there! I'm Dan. I'm still learning the shop, but very soon I'll help you find the perfect fit.
            </div>
          </div>
          <form className="chat-input" onSubmit={(e) => e.preventDefault()}>
            <input type="text" placeholder="Chat coming soon…" disabled />
            <button type="submit" className="btn btn-primary" disabled>Send</button>
          </form>
        </div>
      )}
      <button
        className="chat-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Chat with Dan'}
      >
        {open ? '×' : <DanTheBulldog title="Chat with Dan" />}
      </button>
    </div>
  )
}
