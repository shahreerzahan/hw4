import { useState, type ReactNode } from 'react'
import type { CardProduct } from '../api'
import { ChatResultsContext, type ChatResults } from '../chatResults'

let nextId = 1

export default function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatResults | null>(null)

  const showResults = (
    title: string,
    query: string,
    products: CardProduct[],
    path: string,
    seeAll?: ChatResults['seeAll'],
  ) => setResults({ id: nextId++, title, query, products, path, seeAll })

  return (
    <ChatResultsContext.Provider value={{ results, showResults, clearResults: () => setResults(null) }}>
      {children}
    </ChatResultsContext.Provider>
  )
}
