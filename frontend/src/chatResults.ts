import { createContext, useContext } from 'react'
import type { CardProduct } from './api'

/** Products Dan found in the chat, shown as cards on whatever page the shopper is on. */
export interface ChatResults {
  id: number
  title: string
  query: string
  products: CardProduct[]
  path: string // page the shopper was on when Dan found these
}

export interface ChatResultsState {
  results: ChatResults | null
  showResults: (title: string, query: string, products: CardProduct[], path: string) => void
  clearResults: () => void
}

export const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function useChatResults(): ChatResultsState {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}
