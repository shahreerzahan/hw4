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
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price price-lg">{formatPrice(product.price)}</p>
          <p className="product-detail-desc">{product.description}</p>

          <div className="detail-block">
            <h3>Colors</h3>
            <div className="chips">
              {product.colors.map((c) => (
                <span key={c} className="chip">{c}</span>
              ))}
            </div>
          </div>

          <div className="detail-block">
            <h3>Sizes &amp; Stock</h3>
            {totalStock === 0 && <p className="error">Sold out in every size, but check back soon!</p>}
            <table className="stock-table">
              <thead>
                <tr>
                  <th>Size</th>
                  <th>In stock</th>
                </tr>
              </thead>
              <tbody>
                {product.sizes.map((s) => (
                  <tr key={s.size} className={s.quantity === 0 ? 'sold-out' : ''}>
                    <td>{s.size}</td>
                    <td>
                      {s.quantity === 0 ? (
                        <span className="stock-badge out">Sold out</span>
                      ) : s.quantity <= LOW_STOCK ? (
                        <span className="stock-badge low">Only {s.quantity} left</span>
                      ) : (
                        <span className="stock-badge in">{s.quantity} available</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  )
}
