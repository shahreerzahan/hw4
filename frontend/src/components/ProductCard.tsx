import { Link } from 'react-router-dom'
import { formatPrice, type Product } from '../api'

// Works for catalogue products and for the cards Dan puts on the page from the chat.
type CardData = Pick<Product, 'product_id' | 'name' | 'price' | 'description' | 'image_url' | 'badge'>

export default function ProductCard({ product }: { product: CardData }) {
  return (
    <Link to={`/products/${product.product_id}`} className="product-card">
      <div className="product-card-image">
        {product.badge && (
          <span className={`product-badge ${product.badge === 'New' ? 'new' : 'low'}`}>{product.badge}</span>
        )}
        <img src={product.image_url} alt={product.name} loading="lazy" />
      </div>
      <div className="product-card-body">
        <div className="product-card-row">
          <h3>{product.name}</h3>
          <p className="price">{formatPrice(product.price)}</p>
        </div>
        <p className="product-card-desc">{product.description}</p>
      </div>
    </Link>
  )
}
