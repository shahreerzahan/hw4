import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CATEGORIES, fetchProducts, type Category, type Product } from '../api'
import ProductCard from '../components/ProductCard'

// Lowercase words with common spelling variants unified ("tee"/"t-shirt", "hoodies"/"hooded").
function words(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/\bt[\s-]?shirts?\b|\btees?\b/g, 'tshirt')
    .replace(/\bhood(s|ed|ies|ie)?\b/g, 'hoodie')
    .replace(/\b(quarter|1\s*\/?\s*4)[\s-]*zips?\b/g, 'quarterzip')
    .split(/[^a-z0-9]+/)
    .filter(Boolean)
    .map((w) => (w.length > 3 && w.endsWith('s') && !w.endsWith('ss') ? w.slice(0, -1) : w))
}

function searchText(p: Product): string {
  return [p.name, p.garment_type, p.category, p.description, ...p.colors, ...p.search_tags].join(' ')
}

export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  // Search and category live in the URL (?q=…&category=…), so filtered views can be shared
  // and Dan's "See all" link can open the page already filtered.
  const [params, setParams] = useSearchParams()
  const query = params.get('q') ?? ''
  const categoryParam = params.get('category')
  const category = (CATEGORIES as readonly string[]).includes(categoryParam ?? '') ? (categoryParam as Category) : null

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setError("We couldn't load the products. Is the backend running?"))
  }, [])

  // Pre-compute each product's search words once.
  const indexed = useMemo(
    () => (products ?? []).map((p) => ({ product: p, words: new Set(words(searchText(p))) })),
    [products],
  )

  const queryWords = words(query)
  const matchesQuery = (w: Set<string>) =>
    queryWords.every((q) => w.has(q) || [...w].some((x) => x.startsWith(q) && q.length >= 3))

  const searched = indexed.filter((i) => matchesQuery(i.words))
  const visible = searched.filter((i) => !category || i.product.category === category).map((i) => i.product)

  // How many search matches each category has (shown on the category buttons).
  const counts = new Map<Category, number>()
  for (const i of searched) counts.set(i.product.category, (counts.get(i.product.category) ?? 0) + 1)

  const update = (next: { q?: string; category?: Category | null }) => {
    const p = new URLSearchParams(params)
    if (next.q !== undefined) {
      if (next.q) p.set('q', next.q)
      else p.delete('q')
    }
    if (next.category !== undefined) {
      if (next.category) p.set('category', next.category)
      else p.delete('category')
    }
    setParams(p, { replace: true })
  }

  const filtered = Boolean(query || category)

  return (
    <>
      <section className="page-intro">
        <span className="eyebrow">The collection{products && ` · ${products.length} pieces`}</span>
        <h1>Shop all products</h1>
        <p className="lead">Hoodies, crewnecks, tees, and more, all ready to rep the Bulldogs.</p>
      </section>

      <section className="section section-tight">
        {products && (
          <div className="filters">
            <div className="search-box">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="2" />
                <path d="M20 20l-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              <input
                type="search"
                value={query}
                onChange={(e) => update({ q: e.target.value })}
                placeholder="Search by name, color, sport, college…"
                aria-label="Search products"
              />
              {query && (
                <button type="button" className="search-clear" onClick={() => update({ q: '' })} aria-label="Clear search">
                  ×
                </button>
              )}
            </div>
            <div className="category-chips" role="group" aria-label="Filter by category">
              <button
                type="button"
                className={`category-chip${!category ? ' active' : ''}`}
                onClick={() => update({ category: null })}
                aria-pressed={!category}
              >
                All <span>{searched.length}</span>
              </button>
              {CATEGORIES.map((c) => (
                <button
                  key={c}
                  type="button"
                  className={`category-chip${category === c ? ' active' : ''}`}
                  onClick={() => update({ category: category === c ? null : c })}
                  aria-pressed={category === c}
                  disabled={!counts.get(c) && category !== c}
                >
                  {c} <span>{counts.get(c) ?? 0}</span>
                </button>
              ))}
            </div>
            <p className="results-count" aria-live="polite">
              {filtered
                ? `${visible.length} ${visible.length === 1 ? 'item' : 'items'}${category ? ` in ${category}` : ''}${query ? ` matching “${query}”` : ''}`
                : `Showing all ${visible.length} items`}
              {filtered && (
                <button type="button" className="link-button" onClick={() => setParams({}, { replace: true })}>
                  Clear filters
                </button>
              )}
            </p>
          </div>
        )}

        {error && <p className="error">{error}</p>}
        {!products && !error && <p className="muted">Loading the goods…</p>}

        {products && visible.length === 0 && (
          <div className="empty-state">
            <h3>No matches yet</h3>
            <p className="muted">Try a different word or category, or ask Dan in the chat. He's great at finding things!</p>
            <button type="button" className="btn btn-ghost" onClick={() => setParams({}, { replace: true })}>
              Show all products
            </button>
          </div>
        )}

        {visible.length > 0 && (
          <div className="product-grid">
            {visible.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        )}
      </section>
    </>
  )
}
