import { useState } from 'react'

// Placeholder only: the chatbot gets wired to the backend agent in a later problem.
export default function ChatWidget() {
  const [open, setOpen] = useState(false)

  return (
    <div className="chat-widget">
      {open && (
        <div className="chat-panel" role="dialog" aria-label="Campus Customs chat">
          <div className="chat-header">
            <span>Chat with Campus Customs</span>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </div>
          <div className="chat-body">
            <div className="chat-bubble assistant">
              Hey there, Bulldog! 👋 Our shopping assistant is getting suited up and will be here soon to help you find the perfect gear.
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
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? '×' : '💬'}
      </button>
    </div>
  )
}
