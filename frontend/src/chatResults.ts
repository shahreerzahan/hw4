import { createContext, useContext } from 'react'
import type { CardProduct, Category } from './api'

/** Products Dan found in the chat, shown as cards on whatever page the shopper is on. */
export interface ChatResults {
  id: number
  title: string
  query: string
  products: CardProduct[]
  path: string // page the shopper was on when Dan found these
  seeAll?: { category: Category; count: number } // link to the full category on the Products page
}

export interface ChatResultsState {
  results: ChatResults | null
  showResults: (
    title: string,
    query: string,
    products: CardProduct[],
    path: string,
    seeAll?: ChatResults['seeAll'],
  ) => void
  clearResults: () => void
}

export const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function useChatResults(): ChatResultsState {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}
