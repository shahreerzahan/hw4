import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type ProductDetail } from '../api'

const LOW_STOCK = 5

export default function ProductPage() {
  const { productId = '' } = useParams()
  // Results are tagged with the id they belong to, so stale data never shows after navigating.
  const [result, setResult] = useState<{ id: string; product?: ProductDetail; error?: string }>()

  useEffect(() => {
    fetchProduct(productId)
      .then((product) => setResult({ id: productId, product }))
      .catch(() => setResult({ id: productId, error: "Hmm, we couldn't find that product." }))
  }, [productId])

  const current = result?.id === productId ? result : undefined
  const product = current?.product
  const error = current?.error

  if (error) {
    return (
      <section className="section">
        <p className="error">{error}</p>
        <Link to="/products" className="link-arrow">← Back to all products</Link>
      </section>
    )
  }

  if (!product) {
    return (
      <section className="section">
        <p className="muted">Loading…</p>
      </section>
    )
  }

  const totalStock = product.sizes.reduce((sum, s) => sum + s.quantity, 0)

  return (
    <section className="section">
      <Link to="/products" className="link-arrow back-link">← Back to all products</Link>

      <div className="product-detail">
        <div className="product-detail-image">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div className="product-detail-info">
          <span className="eyebrow">{product.garment_type}</span>
          <h1>{product.name}</h1>
          <p className="price price-lg">{formatPrice(product.price)}</p>
          <p className="product-detail-desc">{product.description}</p>

          <div className="detail-block">
            <div className="detail-label">Colors</div>
            <div className="chips">
              {product.colors.map((c) => (
                <span key={c} className="chip">{c}</span>
              ))}
            </div>
          </div>

          <div className="detail-block">
            <div className="detail-label">Sizes &amp; stock</div>
            {totalStock === 0 && <p className="error">Sold out in every size, but check back soon!</p>}
            <div className="size-grid">
              {product.sizes.map((s) => {
                const status = s.quantity === 0 ? 'out' : s.quantity <= LOW_STOCK ? 'low' : 'in'
                return (
                  <div key={s.size} className={`size-tile ${status}`}>
                    <span className="size">{s.size}</span>
                    <span className={`stock ${status}`}>
                      {status === 'out'
                        ? 'Sold out'
                        : status === 'low'
                          ? `Only ${s.quantity} left`
                          : `${s.quantity} in stock`}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
