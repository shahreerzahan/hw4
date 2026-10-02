import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import ProductCard from '../components/ProductCard'

const FEATURED_IDS = [
  '2025-yale-vs-harvard-t-shirt',
  'baseball-left-chest-crewneck',
  'champion-reverse-weave-hoodie-1',
  'davenport-college-crewneck',
]

const HIGHLIGHTS = [
  {
    emoji: '🏈',
    title: 'Game Day Ready',
    text: 'From The Game to Friday night hockey, show up loud, proud, and dressed in blue.',
  },
  {
    emoji: '🏛️',
    title: 'Your College, Your Crew',
    text: 'Rep your residential college or your school. Davenport, Morse, Law, Art, and more.',
  },
  {
    emoji: '👨‍👩‍👧',
    title: 'The Whole Bulldog Family',
    text: 'Mom, Dad, Grandpa, little brother. Everyone deserves a spot in the cheering section.',
  },
]

export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts()
      .then((all) => {
        const picks = FEATURED_IDS.map((id) => all.find((p) => p.product_id === id)).filter(
          (p): p is Product => Boolean(p),
        )
        setFeatured(picks.length ? picks : all.slice(0, 4))
      })
      .catch(() => setFeatured([]))
  }, [])

  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <p className="eyebrow">Welcome home, Bulldogs 💙</p>
          <h1>Wear Your Yale Pride Everywhere You Go</h1>
          <p className="hero-sub">
            Cozy crewnecks, game-day tees, and hoodies made for late-night study sessions. Campus
            Customs is where New Haven spirit meets everyday comfort, and we saved you a seat.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-light btn-lg">Shop the Collection</Link>
            <Link to="/about" className="btn btn-outline-light btn-lg">Meet Campus Customs</Link>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="highlights">
          {HIGHLIGHTS.map((h) => (
            <div key={h.title} className="highlight">
              <div className="highlight-emoji">{h.emoji}</div>
              <h3>{h.title}</h3>
              <p>{h.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <h2>Fresh Picks for the Season 🍂</h2>
            <p className="muted">A few of our favorites right now. Grab them before they're gone!</p>
          </div>
          <Link to="/products" className="link-arrow">See everything →</Link>
        </div>
        <div className="product-grid">
          {featured.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </section>

      <section className="section">
        <div className="banner">
          <h2>Need a hand finding the perfect fit?</h2>
          <p>
            Tap the chat bubble in the corner. Our shopping assistant is warming up on the
            sidelines and will be ready to help you soon!
          </p>
        </div>
      </section>
    </>
  )
}
