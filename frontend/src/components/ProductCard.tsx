import { Link } from 'react-router-dom'
import { formatPrice, type Product } from '../api'

export default function ProductCard({ product }: { product: Product }) {
  return (
    <Link to={`/products/${product.product_id}`} className="product-card">
      <div className="product-card-image">
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
