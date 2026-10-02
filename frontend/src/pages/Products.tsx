import { useEffect, useState } from 'react'
import { fetchProducts, type Product } from '../api'
import ProductCard from '../components/ProductCard'

export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setError("We couldn't load the products. Is the backend running?"))
  }, [])

  return (
    <>
      <section className="page-intro">
        <span className="eyebrow">The collection{products && ` · ${products.length} pieces`}</span>
        <h1>Shop all products</h1>
        <p className="lead">Hoodies, crewnecks, tees, and more, all ready to rep the Bulldogs.</p>
      </section>

      <section className="section section-tight">
        {error && <p className="error">{error}</p>}
        {!products && !error && <p className="muted">Loading the goods…</p>}

        {products && (
          <div className="product-grid">
            {products.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        )}
      </section>
    </>
  )
}
