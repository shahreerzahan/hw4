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
    <section className="section">
      <div className="section-head">
        <div>
          <h1>Shop All Products</h1>
          <p className="muted">
            Hoodies, crewnecks, tees, and more, all ready to rep the blue and white.
            {products && ` ${products.length} items.`}
          </p>
        </div>
      </div>

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
  )
}
