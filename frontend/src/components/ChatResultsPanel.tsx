import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useChatResults } from '../chatResults'
import ProductCard from './ProductCard'
import DanTheBulldog from './DanTheBulldog'

// The products Dan found in the chat, shown as cards at the top of the current page.
// Cards link to the normal product pages. After moving to another page (e.g. by clicking a
// card), the results fold into a slim bar so the new page isn't pushed down; "Show" reopens them.
export default function ChatResultsPanel() {
  const { results, clearResults } = useChatResults()
  const { pathname } = useLocation()
  const ref = useRef<HTMLElement>(null)
  // Which page the shopper reopened the results on (otherwise they're open where they appeared).
  const [reopened, setReopened] = useState<{ id: number; path: string } | null>(null)

  // Bring each new set of results into view.
  useEffect(() => {
    if (results) ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [results])

  if (!results) return null
  const count = results.products.length
  const openOn = reopened?.id === results.id ? reopened.path : results.path
  const label = `${count} ${count === 1 ? 'item' : 'items'}`

  if (pathname !== openOn) {
    return (
      <section className="chat-results chat-results-collapsed" ref={ref} id="chat-results">
        <div className="chat-results-bar">
          <DanTheBulldog className="dan" />
          <span>
            Dan's results: <strong>{results.title}</strong> · {label}
          </span>
          <button type="button" className="btn btn-ghost" onClick={() => setReopened({ id: results.id, path: pathname })}>
            Show
          </button>
          <button type="button" className="chat-results-x" onClick={clearResults} aria-label="Clear Dan's results">
            ×
          </button>
        </div>
      </section>
    )
  }

  return (
    <section className="chat-results" ref={ref} id="chat-results" aria-live="polite" key={results.id}>
      <div className="chat-results-inner">
        <div className="section-head">
          <div className="chat-results-heading">
            <DanTheBulldog className="dan" />
            <div>
              <span className="eyebrow">Dan found {label} · “{results.query}”</span>
              <h2>{results.title}</h2>
            </div>
          </div>
          <button type="button" className="btn btn-ghost" onClick={clearResults}>
            Clear results
          </button>
        </div>
        <div className="product-grid">
          {results.products.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
        {results.seeAll && results.seeAll.count > count && (
          <div className="chat-results-more">
            <Link to={`/products?category=${encodeURIComponent(results.seeAll.category)}`} className="btn btn-primary">
              See all {results.seeAll.count} {results.seeAll.category} →
            </Link>
          </div>
        )}
      </div>
    </section>
  )
}
